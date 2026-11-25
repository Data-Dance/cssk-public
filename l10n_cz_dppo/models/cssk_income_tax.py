# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPDP9: file the Rozvaha and the Výkaz zisku a ztráty inside the return.

The return points at the two ``l10n_cz_fs`` statements the accountant has
already computed (and possibly corrected by override) for the same period, and
the export reads their rows. It does not compute a závěrka of its own: that
would be a second account → row mapping next to the one in ``l10n_cz_fs``,
and two mappings of one form drift apart without either looking wrong.

Linking is explicit rather than a search for "the" statement of the period,
because a period can hold a draft, a filed one and an opravná závěrka at once,
and which of them goes to the finanční úřad is the accountant's decision.
"""

import base64
import re
from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import single_email_re
from odoo.tools.safe_eval import safe_eval

from . import dppdp9_vykazy as vykazy

#: ``VetaD/@uv_mena`` accepts these and nothing else (DPPDP9 popis struktury).
_UV_CURRENCIES = ("CZK", "EUR", "USD", "GBP")


def _thousands(value):
    """Whole thousands, half away from zero — the výkazy are filed "v tis."
    (``VetaD/@uz_rad = T``). Decimal, because a float ``round`` of 2500.0 /
    1000 goes to the even neighbour and files 2 instead of 3."""
    return int((Decimal(repr(round(value or 0.0, 2))) / 1000).quantize(
        Decimal(1), rounding=ROUND_HALF_UP))


#: VetaD/typ_dapdpp — druh daňového přiznání, from the XSD's code list.
#: A is the ordinary return for the tax period; the others are the returns a
#: liquidation, insolvency, merger or change of period calls for.
DPPDP9_RETURN_KINDS = [
    ("A", "A – za zdaňovací období"),
    ("B", "B – při vstupu do likvidace"),
    ("C", "C – v průběhu likvidace"),
    ("D", "D – před zánikem bez likvidace"),
    ("G", "G – ukončení činnosti v rámci privatizace"),
    ("H", "H – před návrhem na použití likvidačního zůstatku"),
    ("J", "J – před rozhodným dnem fúze / rozdělení"),
    ("K", "K – před změnou právní formy"),
    ("L", "L – před změnou zdaňovacího období"),
    ("M", "M – od vzniku poplatníka"),
    ("O", "O – před změnou daňového rezidentství"),
    ("P", "P – k účinnosti rozhodnutí o úpadku"),
    ("R", "R – v průběhu insolvenčního řízení"),
    ("T", "T – ke dni konečné zprávy"),
    ("V", "V – při ukončení svěřenského fondu"),
    ("Y", "Y – vypořádání majetku svěřenského fondu"),
    ("Z", "Z – před zánikem svěřenského fondu"),
]

#: VetaD/typ_zo — the letter of § 21a ZDP naming the tax period.
DPPDP9_PERIOD_KINDS = [
    ("A", "a) kalendářní rok"),
    ("B", "b) hospodářský rok"),
    ("C", "c) období od rozhodného dne fúze / rozdělení"),
    ("D", "d) účetní období delší než 12 měsíců"),
]

#: VetaD/typ_popldpp — typ poplatníka.
DPPDP9_TAXPAYER_KINDS = [
    ("1", "1 – ostatní"),
    ("2", "2 – daňový nerezident (§ 17 odst. 4)"),
    ("3", "3 – veřejně prospěšný poplatník (§ 17a)"),
    ("4", "4 – investiční fond"),
    ("5", "5 – investiční společnost"),
    ("6", "6 – instituce penzijního pojištění / penzijní společnost"),
    ("7", "7 – základní investiční fond po část období (§ 20a)"),
    ("8", "8 – investiční pobídka dle usnesení vlády"),
    ("9", "9 – investiční pobídka, sleva dle § 35a"),
    ("0", "0 – investiční pobídka, sleva dle § 35b"),
]


class CSSKIncomeTaxReturn(models.Model):
    _inherit = "cssk.income.tax.return"

    # VetaD of DPPDP9. typ_dapdpp was hard-coded "B" — a return ON ENTERING
    # LIQUIDATION — and typ_zo "1", which is no letter of § 21a at all; both
    # are now chosen, with the ordinary case as the default.
    l10n_cz_return_kind = fields.Selection(
        DPPDP9_RETURN_KINDS, string="Typ daňového přiznání", default="A",
        help="VetaD/typ_dapdpp. A for the ordinary return for the tax period.")
    l10n_cz_period_kind = fields.Selection(
        DPPDP9_PERIOD_KINDS, string="Zdaňovací období (§ 21a)",
        compute="_compute_l10n_cz_period_kind", store=True, readonly=False,
        help="VetaD/typ_zo, derived from the period: a calendar year is a), "
        "another twelve-month year b), anything longer d). Set c) by hand for "
        "the period from a merger's decisive day.")
    l10n_cz_taxpayer_kind = fields.Selection(
        DPPDP9_TAXPAYER_KINDS, string="Typ poplatníka", default="1",
        help="VetaD/typ_popldpp.")
    l10n_cz_discovery_date = fields.Date(
        string="Důvody zjištěny dne",
        help="VetaD/d_zjist — required for a dodatečné přiznání.")
    l10n_cz_filing_code = fields.Char(related="statement_type_id.fa_xml_value")

    @api.depends("date_from", "date_to")
    def _compute_l10n_cz_period_kind(self):
        for rec in self:
            start, end = rec.date_from, rec.date_to
            if not start or not end:
                rec.l10n_cz_period_kind = "A"
                continue
            twelve = start + relativedelta(years=1, days=-1)
            if (start.month, start.day) == (1, 1) and end == twelve:
                rec.l10n_cz_period_kind = "A"
            elif end == twelve:
                rec.l10n_cz_period_kind = "B"
            elif end > twelve:
                rec.l10n_cz_period_kind = "D"
            else:
                # A shorter period (the first one, a liquidation) takes the
                # letter of the period its last day falls in; a calendar year
                # unless the company keeps a hospodářský rok.
                rec.l10n_cz_period_kind = rec.l10n_cz_period_kind or "A"

    l10n_cz_fs_balance_sheet_id = fields.Many2one(
        "cssk.fs.statement", string="Rozvaha",
        domain="[('company_id', '=', company_id),"
               " ('statement_kind', '=', 'balance_sheet'),"
               " ('date_to', '=', date_to)]",
        help="The computed Rozvaha filed with this return as DPPDP9 VetaUA "
             "(aktiva) and VetaUD (pasiva). Link it together with the Výkaz "
             "zisku a ztráty, or leave both empty to file the return without "
             "the výkazy (the závěrka then goes as an E-příloha).")
    l10n_cz_fs_profit_loss_id = fields.Many2one(
        "cssk.fs.statement", string="Výkaz zisku a ztráty",
        domain="[('company_id', '=', company_id),"
               " ('statement_kind', '=', 'profit_loss'),"
               " ('date_from', '=', date_from), ('date_to', '=', date_to)]",
        help="The computed Výkaz zisku a ztráty (druhové členění) filed "
             "with this return as DPPDP9 VetaUB.")

    # --- Žádost o předání účetní závěrky do sbírky listin (věta UZ) -------
    l10n_cz_registry_request = fields.Boolean(
        string="Předat účetní závěrku do sbírky listin",
        help="§ 21b zákona o účetnictví: an obchodní korporace may hand its "
             "účetní závěrka to the sbírka listin through the income tax "
             "return. The return then carries the request (věta UZ, tiskopis "
             "25 5404/I) with the scope ticked below. The duty to publish is "
             "met when the return is filed (§ 21b odst. 6 písm. b)).")
    l10n_cz_registry_balance_sheet = fields.Boolean(
        string="Předat Rozvahu", default=True,
        help="pr11_rozv. The Rozvaha linked to the return.")
    l10n_cz_registry_profit_loss = fields.Boolean(
        string="Předat Výkaz zisku a ztráty", default=True,
        help="pr11_vzz. Untick where the unit does not publish it (§ 21a "
             "odst. 9: a small or micro unit with no audit duty).")
    l10n_cz_registry_email = fields.Char(
        string="E-mail pro potvrzení",
        help="pr11_email: where the tax office confirms the handover. Not "
             "the address of the rejstříkový soud.")
    l10n_cz_uz_not_approved = fields.Boolean(
        string="Účetní závěrka nebyla schválena",
        help="VetaD/neschval_uz: the figures come from a závěrka the "
             "competent body has not approved yet.")
    l10n_cz_uz_not_audited = fields.Boolean(
        string="Účetní závěrka nebyla ověřena auditorem",
        help="VetaD/neaudit_uz: the figures come from a závěrka the auditor "
             "has not verified yet.")
    l10n_cz_notes_attachment_ids = fields.Many2many(
        "ir.attachment", "l10n_cz_dppdp9_notes_att_rel", "return_id",
        "attachment_id", string="Příloha účetní závěrky", copy=False,
        help="Filed as the prescribed e-příloha PP_OPISPUV.")
    l10n_cz_cash_flow_attachment_ids = fields.Many2many(
        "ir.attachment", "l10n_cz_dppdp9_cash_flow_att_rel", "return_id",
        "attachment_id", string="Přehled o peněžních tocích", copy=False,
        help="Filed as the prescribed e-příloha PP_PTOK.")
    l10n_cz_equity_attachment_ids = fields.Many2many(
        "ir.attachment", "l10n_cz_dppdp9_equity_att_rel", "return_id",
        "attachment_id", string="Přehled o změnách vlastního kapitálu",
        copy=False, help="Filed as the prescribed e-příloha PP_ZVKAP.")

    #: For the form: the výkaz fields mean nothing on a Slovak DPPO.
    l10n_cz_country_code = fields.Char(related="version_id.country_id.code")

    # ------------------------------------------------------------------
    def _l10n_cz_is_dppdp9(self):
        self.ensure_one()
        return (self.version_id.country_id.code or "").upper() == "CZ"

    def _eval_aggregate(self, formula, computed):
        """Offer the DPPDP9 formulas the year the period BEGAN.

        One DPPDP9 structure covers every period the Finanční správa still
        accepts (2021 onwards), so what changed in the law is gated on the
        period, not on a version. The case that needs it is the § 21 odst. 1
        rate: zákon č. 349/2023 Sb. (čl. XV bod 40) raised it from 19 % to
        21 % from 1. 1. 2024, and its čl. XVI bod 1 keeps the earlier wording
        "za zdaňovací období započaté přede dnem nabytí účinnosti" — so a
        hospodářský rok begun in 2023 is still taxed at 19 %.
        """
        if self._l10n_cz_is_dppdp9() and self.date_from:
            computed = dict(computed, period_start_year=self.date_from.year)
        return super()._eval_aggregate(formula, computed)

    def _eval_asset_diff(self, which):
        """ř. 50 / ř. 150 from the tax asset register, calendar years only.

        The pokyny (25 5404/1) put on ř. 50 "celkový rozdíl, o který souhrn
        odpisů hmotného a nehmotného majetku (§ 26 zákona) uplatněných v
        účetnictví převyšuje souhrn odpisů tohoto majetku stanovených podle
        § 26 až 33 zákona", and the opposite case on ř. 150: one of the two,
        never both. That is ``addback`` / ``deduction`` of the register.

        The tax depreciation board is kept by calendar year, so for a period
        that crosses a year end (a hospodářský rok, a period longer than
        twelve months) the register would add the tax depreciation of both
        calendar years to the accounting depreciation of one period. Such a
        return gets 0 on both rows and says so; the accountant enters the
        difference by override.
        """
        if (self._l10n_cz_is_dppdp9() and self.date_from and self.date_to
                and self.date_from.year != self.date_to.year):
            return 0.0
        value = super()._eval_asset_diff(which)
        if self._l10n_cz_is_dppdp9():
            # The form is in whole crowns and each row is filed rounded on
            # its own; a row carrying haléře would let the filed ř. 70 differ
            # by a crown from the filed rows it adds up.
            value = float(Decimal(repr(round(value or 0.0, 2))).quantize(
                Decimal(1), rounding=ROUND_HALF_UP))
        return value

    #: subtotal → (the typed row of the other items, the register row)
    _L10N_CZ_SUBTOTALS = {"r70": ("r70_other", "r50"),
                          "r170": ("r170_other", "r150")}

    def _l10n_cz_check_subtotals(self):
        """Refuse a typed ř. 70 / ř. 170 that is not the sum of its rows.

        The subtotals were typed rows before 19.0.1.7.0 and an override still
        wins over the formula, which is what keeps the base of an older
        return where it was. But the file now carries ř. 50 / ř. 150 next to
        the subtotal, and a subtotal that does not contain them is an
        inconsistent return the XSD cannot see.
        """
        self.ensure_one()
        values = {line.code: line for line in self.line_ids}
        for total, (other, register) in self._L10N_CZ_SUBTOTALS.items():
            line = values.get(total)
            if not line or not line.is_overridden or other not in values \
                    or register not in values:
                continue
            parts = values[other].value + values[register].value
            if abs(line.value - parts) > 0.5:
                raise UserError(_(
                    "%(total)s is typed as %(typed).2f, but its rows add up "
                    "to %(parts).2f (%(register)s %(reg).2f + other items "
                    "%(oth).2f). Clear the override on %(total)s, enter the "
                    "items other than the depreciation difference on the "
                    "\"ostatní položky\" row and compute again.",
                    total=line.name, typed=line.value, parts=parts,
                    register=values[register].code, reg=values[register].value,
                    oth=values[other].value))

    def action_compute_lines(self):
        res = super().action_compute_lines()
        for rec in self:
            if (rec._l10n_cz_is_dppdp9() and rec.date_from and rec.date_to
                    and rec.date_from.year != rec.date_to.year
                    and hasattr(rec.company_id,
                                "_cssk_asset_book_tax_difference")
                    and not rec.line_ids.filtered(
                        lambda l: l.code in ("r50", "r150")
                        and l.is_overridden)):
                rec.message_post(body=_(
                    "ř. 50 and ř. 150 were not computed: the period crosses "
                    "a calendar year end and the tax depreciation plan is "
                    "kept by calendar year. Enter the difference between "
                    "accounting and tax depreciation on one of the two rows "
                    "by override."))
        return res

    # ------------------------------------------------------------------
    # Sbírka listin (§ 21b zákona o účetnictví)
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._l10n_cz_bind_attachments()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field, *_rest in self._L10N_CZ_E_PRILOHY):
            self._l10n_cz_bind_attachments()
        return res

    def _l10n_cz_bind_attachments(self):
        """Attach the uploaded files to their return.

        The upload widget creates them with no record (``res_id`` 0), and
        such an attachment is readable by its uploader only: the colleague
        who exports the return would file it without them, or not at all.
        """
        for rec in self:
            for field, *_rest in self._L10N_CZ_E_PRILOHY:
                # Only what this user uploaded: binding with ``sudo`` any
                # loose attachment whose id was written into the field would
                # hand its content to whoever can read the return.
                loose = rec[field].sudo().filtered(
                    lambda att: not att.res_id
                    and att.res_model in (False, rec._name)
                    and att.create_uid == self.env.user)
                if loose:
                    loose.write({"res_model": rec._name, "res_id": rec.id})

    #: (field, PredepsanaPriloha/@kod, VetaD count attribute, VetaUZ flag)
    _L10N_CZ_E_PRILOHY = (
        ("l10n_cz_notes_attachment_ids", "PP_OPISPUV", "pril_uz", "pr11_puz"),
        ("l10n_cz_cash_flow_attachment_ids", "PP_PTOK", "p_ptok", "pr11_ppt"),
        ("l10n_cz_equity_attachment_ids", "PP_ZVKAP", "p_zvkap", "pr11_pzvk"),
    )
    #: DPPDP9 popis struktury, e-přílohy: the accepted file types, and a
    #: signed (PKCS#7) or zipped file of one of them.
    _L10N_CZ_E_PRILOHA_TYPES = (
        "doc", "docx", "rtf", "xls", "xlsx", "pdf", "jpg", "jpeg", "txt",
        "csv", "p7s", "zip")
    #: "Součet velikostí všech souborů … může být nejvýše 10 240 kilobajtů."
    _L10N_CZ_E_PRILOHA_LIMIT = 10240 * 1024

    def _l10n_cz_e_prilohy(self):
        """``[{cislo, nazev, jm_souboru, kod, data}]`` in the filing order."""
        self.ensure_one()
        out = []
        for field, kod, _count, _flag in self._L10N_CZ_E_PRILOHY:
            label = self._fields[field].string
            for att in self[field].sorted("id"):
                # ``raw``, not ``datas``: under a ``bin_size`` context
                # ``datas`` is the size as text, and would be filed.
                raw = att.raw or b""
                # A bare file name: no folders, no control characters.
                name = re.split(r"[\\/]", att.name or "")[-1]
                name = "".join(ch for ch in name if ch.isprintable())
                out.append({
                    "cislo": str(len(out) + 1),
                    "nazev": label,
                    "jm_souboru": name.strip()[:255],
                    "kod": kod,
                    "data": base64.b64encode(raw).decode(),
                    "size": len(raw),
                })
        return out

    def _l10n_cz_check_registry_request(self):
        """Refuse a request the tax office would not hand over.

        § 21b odst. 5: where the request is not made in the prescribed way
        the závěrka is NOT passed on, and the unit learns of it late. None
        of this is in the XSD: a request with no Rozvaha behind it, a file
        of a type EPO does not take and a malformed e-mail all validate.
        """
        self.ensure_one()
        prilohy = self._l10n_cz_e_prilohy()
        for item in prilohy:
            ext = item["jm_souboru"].rpartition(".")[2].lower()
            if "." not in item["jm_souboru"] \
                    or ext not in self._L10N_CZ_E_PRILOHA_TYPES:
                raise UserError(_(
                    "%(file)s cannot be filed as an e-příloha. EPO accepts "
                    "DOC, DOCX, RTF, XLS, XLSX, PDF, JPG, JPEG, TXT and CSV "
                    "files, or one of them signed (P7S) or zipped (ZIP).",
                    file=item["jm_souboru"] or item["nazev"]))
            if not item["data"]:
                raise UserError(_(
                    "%(file)s is empty.", file=item["jm_souboru"]))
        total = sum(item["size"] for item in prilohy)
        if total > self._L10N_CZ_E_PRILOHA_LIMIT:
            raise UserError(_(
                "The attached files have %(size)s kB together; EPO accepts "
                "at most 10 240 kB of e-přílohy in one filing.",
                size=round(total / 1024)))
        if not self.l10n_cz_registry_request:
            return
        statements = self._l10n_cz_vykaz_statements()
        wanted = (self.l10n_cz_registry_balance_sheet
                  or self.l10n_cz_registry_profit_loss)
        if wanted and len(statements) != 2:
            raise UserError(_(
                "The request to hand the účetní závěrka to the sbírka listin "
                "names the Rozvaha or the Výkaz zisku a ztráty, but no "
                "statements are linked to the return. Link both; the "
                "registry receives what the return carries."))
        if not (wanted or prilohy):
            raise UserError(_(
                "The request to hand the účetní závěrka to the sbírka listin "
                "names nothing to hand over (§ 21b odst. 3 zákona o "
                "účetnictví asks for its scope). Tick the Rozvaha or the "
                "Výkaz zisku a ztráty, or attach the příloha."))
        email = (self.l10n_cz_registry_email or "").strip()
        if email and not single_email_re.fullmatch(email):
            raise UserError(_(
                "%(email)s is not a valid e-mail address for the "
                "confirmation of the handover.", email=email))

    def _l10n_cz_registry_context(self):
        """``(VetaD attributes, VetaUZ attributes or None, e-přílohy)``."""
        self.ensure_one()
        prilohy = self._l10n_cz_e_prilohy()
        header = {}
        for _field, kod, count, _flag in self._L10N_CZ_E_PRILOHY:
            number = len([item for item in prilohy if item["kod"] == kod])
            if number:
                header[count] = str(number)
        if self.l10n_cz_uz_not_approved:
            header["neschval_uz"] = "A"
        if self.l10n_cz_uz_not_audited:
            header["neaudit_uz"] = "A"
        request = None
        if self.l10n_cz_registry_request:
            def flag(value):
                return "A" if value else "N"
            request = {
                "pr11_rozv": flag(self.l10n_cz_registry_balance_sheet),
                "pr11_vzz": flag(self.l10n_cz_registry_profit_loss),
                "pr11_uzmus": "N",
            }
            for _field, kod, _count, name in self._L10N_CZ_E_PRILOHY:
                request[name] = flag(
                    any(item["kod"] == kod for item in prilohy))
            email = (self.l10n_cz_registry_email or "").strip()
            if email:
                request["pr11_email"] = email
        return header, request, prilohy

    def _l10n_cz_vykaz_statements(self):
        """``{kind: statement}`` for the linked výkazy, or ``{}``."""
        self.ensure_one()
        linked = {
            "balance_sheet": self.l10n_cz_fs_balance_sheet_id,
            "profit_loss": self.l10n_cz_fs_profit_loss_id,
        }
        return {k: st for k, st in linked.items() if st}

    # ------------------------------------------------------------------
    # ř. 10 ↔ Výkaz zisku a ztráty
    # ------------------------------------------------------------------
    #: Absolute tolerance of the tie, in the accounting currency. Both
    #: figures are sums of the same posted lines, so they agree to the haléř;
    #: this absorbs float noise only.
    _L10N_CZ_FS_TOL = 0.5
    #: The Výkaz zisku a ztráty row ř. 10 is tied to — "** Výsledek
    #: hospodaření před zdaněním", the same code in the plný and the zkrácený
    #: rozsah of ``l10n_cz_fs``.
    _L10N_CZ_FS_RESULT_ROW = "VHB"

    def _l10n_cz_find_profit_loss(self):
        """The Výkaz zisku a ztráty this return is compared with.

        The one linked to the return if there is one — that is the statement
        filed with it. Otherwise a computed statement of the company for
        exactly the return's period; an overlapping period is a different
        result and comparing with it would report a difference that is not
        there. Returns an empty recordset when there is none.
        """
        self.ensure_one()
        if self.l10n_cz_fs_profit_loss_id:
            return self.l10n_cz_fs_profit_loss_id
        statements = self.env["cssk.fs.statement"].search([
            ("company_id", "=", self.company_id.id),
            ("statement_kind", "=", "profit_loss"),
            ("date_from", "=", self.date_from),
            ("date_to", "=", self.date_to),
            ("state", "not in", ("draft", "cancelled")),
        ], order="id desc").filtered(lambda st: any(
            line.code == self._L10N_CZ_FS_RESULT_ROW
            for line in st.line_ids))
        # A statement that was filed is the závěrka; a preview is somebody's
        # working copy. Among equals, the most recent.
        filed = statements.filtered(
            lambda st: st.state in ("exported", "submitted"))
        return (filed or statements)[:1]

    def _l10n_cz_fs_comparison_rows(self, statement):
        """``[{code, label, filed, computed, diff, kind, detail}]``.

        The income-tax return starts from the accounting result: DPPDP9 ř. 10
        (výsledek hospodaření před zdaněním) is the row "**" of the Výkaz
        zisku a ztráty. This is an exact tie — a difference means the two
        filings disagree on the accounting result (ř. 10 entered by hand, a
        statement not recomputed after a late entry, an edited mapping), so
        it is a difference, never an expected one.
        """
        self.ensure_one()
        result = statement.line_ids.filtered(
            lambda line: line.code == self._L10N_CZ_FS_RESULT_ROW)[:1]
        r10 = self.line_ids.filtered(lambda line: line.code == "r10")[:1]
        filed, computed = r10.value or 0.0, result.current_value or 0.0
        diff = filed - computed
        agrees = abs(diff) <= self._L10N_CZ_FS_TOL
        return [{
            "code": "vzz_r10",
            "label": _("Výsledek hospodaření před zdaněním "
                       "(VZZ ** = DPPO ř. 10)"),
            "filed": filed, "computed": computed, "diff": diff,
            "kind": "ok" if agrees else "amount",
            "detail": False if agrees else _(
                "DPPO ř. 10 %(r10).2f ≠ VZZ ** %(vzz).2f (rozdíl "
                "%(diff).2f). Zkontrolujte období, ruční úpravu ř. 10 "
                "a zda byl výkaz přepočten po posledním zaúčtování.",
                r10=filed, vzz=computed, diff=diff),
        }]

    def action_l10n_cz_compare_fs(self):
        """Porovnání účetní závěrky (VZZ) ↔ DPPO ř. 10 — on screen."""
        self.ensure_one()
        statement = self._l10n_cz_find_profit_loss()
        if not statement:
            raise UserError(_(
                "No computed Výkaz zisku a ztráty found for this period. "
                "Compute the profit and loss statement for %(df)s – %(dt)s "
                "first, or link it to the return.",
                df=self.date_from, dt=self.date_to))
        if (statement.company_id != self.company_id
                or statement.date_from != self.date_from
                or statement.date_to != self.date_to):
            # Only a linked statement can get here; the search is exact.
            raise UserError(_(
                "%(statement)s covers %(from)s – %(to)s, but the return "
                "covers %(rfrom)s – %(rto)s. The výkazy filed with a "
                "return are those of its own zdaňovací období.",
                statement=statement.display_name, **{
                    "from": statement.date_from, "to": statement.date_to,
                    "rfrom": self.date_from, "rto": self.date_to}))
        if not any(line.code == self._L10N_CZ_FS_RESULT_ROW
                   for line in statement.line_ids):
            raise UserError(_(
                "%(statement)s has no row \"** Výsledek hospodaření před "
                "zdaněním\" to compare with. Compute it on the l10n_cz_fs "
                "Výkaz zisku a ztráty.", statement=statement.display_name))
        self._cssk_upsert_comparison_rows(
            self._l10n_cz_fs_comparison_rows(statement), "filing",
            _("účetní závěrka %s", statement.display_name))
        return self._cssk_comparison_action(
            "filing", _("DPPO ↔ účetní závěrka — %s", self.display_name))

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec._l10n_cz_is_dppdp9():
                rec._l10n_cz_check_vykazy()
                rec._l10n_cz_check_subtotals()
                rec._l10n_cz_check_registry_request()
                if rec.l10n_cz_filing_code in ("D", "E") \
                        and not rec.l10n_cz_discovery_date:
                    raise UserError(_(
                        "A dodatečné přiznání needs the date its reasons were "
                        "found (Důvody zjištěny dne, d_zjist)."))
        return res

    def _l10n_cz_check_vykazy(self):
        """Refuse a výkaz that would be filed wrong rather than file it.

        Everything here fails as a named error because the XSD cannot catch
        any of it: a Rozvaha of another date, a half-linked pair or a row
        missing from the statement all validate, and EPO reads a missing row
        as zero.
        """
        self.ensure_one()
        statements = self._l10n_cz_vykaz_statements()
        if not statements:
            return
        if len(statements) != 2:
            raise UserError(_(
                "Link both the Rozvaha and the Výkaz zisku a ztráty, or "
                "neither. The DPPDP9 files the účetní závěrka as a whole "
                "(uv_rozsah covers both výkazy); one without the other is "
                "an incomplete závěrka."))
        scopes = {st.version_id.l10n_cz_fs_scope or "abridged"
                  for st in statements.values()}
        if len(scopes) > 1:
            raise UserError(_(
                "The linked Rozvaha and Výkaz zisku a ztráty are computed in "
                "different rozsahy (plný and zkrácený). The DPPDP9 return "
                "files one rozsah for both výkazy (uv_rozsah). Compute both "
                "in the plný rozsah — always permitted, vyhláška č. 500/2002 "
                "Sb., § 3a odst. 1 and 3 — or both in the zkrácený rozsah "
                "where the unit may use it."))
        rng = self._l10n_cz_vykaz_range()
        currency = self.company_id.currency_id.name
        if currency not in _UV_CURRENCIES:
            raise UserError(_(
                "The výkazy are kept in %(currency)s, but DPPDP9 accepts only "
                "CZK, EUR, USD or GBP as the accounting currency (uv_mena, "
                "§ 24a zákona o účetnictví).", currency=currency))
        for kind, st in statements.items():
            label = st.display_name
            if st.company_id != self.company_id:
                raise UserError(_(
                    "%(statement)s belongs to another company.",
                    statement=label))
            if st.statement_kind != kind:
                raise UserError(_(
                    "%(statement)s is not a %(kind)s.",
                    statement=label, kind=kind.replace("_", " ")))
            if st.date_to != self.date_to or (
                    kind == "profit_loss" and st.date_from != self.date_from):
                raise UserError(_(
                    "%(statement)s covers %(from)s – %(to)s, but the return "
                    "covers %(rfrom)s – %(rto)s. The výkazy filed with a "
                    "return are those of its own zdaňovací období.",
                    statement=label, **{
                        "from": st.date_from, "to": st.date_to,
                        "rfrom": self.date_from, "rto": self.date_to}))
            if st.state in ("draft", "cancelled") or not st.line_ids:
                raise UserError(_(
                    "%(statement)s has not been computed. Compute it (and "
                    "review it) before filing it with the return.",
                    statement=label))
            missing = vykazy.fs_codes(kind, rng) - set(
                st.line_ids.mapped("code"))
            if missing:
                raise UserError(_(
                    "%(statement)s has no row %(codes)s, which the DPPDP9 "
                    "výkaz is filled from. It was computed on a version that "
                    "is not the l10n_cz_fs Rozvaha / VZZ; filing it would "
                    "report those rows as zero.",
                    statement=label, codes=", ".join(sorted(missing))))
            if kind == "balance_sheet" and not any(
                    st.version_id.line_def_ids.mapped(
                        "account_formula_correction")):
                # The l10n_cz_fs 19.0.1.1.0 migration leaves a row an
                # accountant has edited alone; if it left ALL of them, the
                # sheet has no korekce column and VetaUA would file
                # brutto = netto with every oprávka silently dropped.
                raise UserError(_(
                    "%(statement)s was computed on a Rozvaha version whose "
                    "rows state no korekce (oprávky, opravné položky) "
                    "separately, so the DPPDP9 aktiva cannot be filed in "
                    "brutto / korekce / netto. Move the correction accounts "
                    "of B.I.–C.III. into the correction formula of their "
                    "rows and recompute.", statement=label))

    def _l10n_cz_vykaz_range(self):
        """``"P"`` where every linked statement is of the plný rozsah, else
        ``"Z"``. A version without a rozsah predates the plný one and is the
        zkrácený rozsah; a mixed pair never gets this far
        (``_l10n_cz_check_vykazy`` refuses it)."""
        self.ensure_one()
        statements = self._l10n_cz_vykaz_statements()
        if statements and all(
                st.version_id.l10n_cz_fs_scope == "full"
                for st in statements.values()):
            return vykazy.FULL
        return vykazy.ABRIDGED

    # ------------------------------------------------------------------
    def _l10n_cz_vykaz_rows(self):
        """``{věta: [attribute dict, …]}`` for the linked výkazy.

        Brutto is derived as netto + korekce AFTER rounding, so the filed
        columns satisfy brutto − korekce = netto exactly, as EPO checks,
        even on a row whose netto the accountant overrode.
        """
        self.ensure_one()
        statements = self._l10n_cz_vykaz_statements()
        if len(statements) != 2:
            return {}
        values = {}
        for kind, st in statements.items():
            current = {ln.code: ln.current_value for ln in st.line_ids}
            prior = {ln.code: ln.prior_value for ln in st.line_ids}
            values[kind] = (current, prior, self._l10n_cz_corrections(st))

        out = {}
        row_map = vykazy.rows(self._l10n_cz_vykaz_range())
        for (veta, row), (designation, codes) in sorted(
                row_map.items(), key=lambda it: (it[0][0], it[0][1])):
            current, prior, correction = values[vykazy.TABLES[veta]]
            netto = _thousands(sum(current.get(c, 0.0) for c in codes))
            netto_min = _thousands(sum(prior.get(c, 0.0) for c in codes))
            if veta == "UA":
                korekce = _thousands(sum(correction.get(c, 0.0) for c in codes))
                if korekce < 0:
                    # The form states korekce unsigned; a negative one is a
                    # debit balance on an oprávka / opravná položka, which is
                    # a booking to fix, not a sign to drop.
                    raise UserError(_(
                        "Rozvaha row %(row)s (%(designation)s) has a negative "
                        "korekce of %(value)s thousand: its oprávky / "
                        "opravné položky carry a debit balance. Correct the "
                        "booking; DPPDP9 files korekce without a sign.",
                        row=row, designation=designation, value=korekce))
                cells = {"kc_brutto": netto + korekce, "kc_korekce": korekce,
                         "kc_netto": netto, "kc_netto_min": netto_min}
            else:
                cells = {"kc_sled": netto, "kc_min": netto_min}
            if not any(cells.values()):
                continue
            attrs = {"c_radku": str(row)}
            attrs.update({k: str(v) for k, v in cells.items() if v})
            out.setdefault(veta, []).append(attrs)
        return out

    def _l10n_cz_corrections(self, statement):
        """``{code: korekce}`` for every row of ``statement``.

        A leaf reports the correction column it computed; an aggregate is
        its own formula over its children's corrections — the formulas that
        sum netto rows are linear, so they sum korekce rows too."""
        corrections = {}
        stored = {ln.code: ln.correction_value for ln in statement.line_ids}
        for ldef in statement._cssk_eval_order():
            if ldef.kind == "aggregate":
                corrections[ldef.code] = float(safe_eval(
                    ldef.aggregate_formula or "0", dict(corrections)) or 0.0)
            elif ldef.account_formula_correction:
                corrections[ldef.code] = stored.get(ldef.code, 0.0)
            else:
                corrections[ldef.code] = 0.0
        return corrections

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        linked = (self._l10n_cz_is_dppdp9()
                  and len(self._l10n_cz_vykaz_statements()) == 2)
        rows = self._l10n_cz_vykaz_rows() if linked else {}
        header, request, prilohy = (
            self._l10n_cz_registry_context() if self._l10n_cz_is_dppdp9()
            else ({}, None, []))
        ctx["registry_request"] = request
        ctx["e_prilohy"] = prilohy
        ctx["vykazy"] = rows
        # Keyed on the LINK, not on the rows: a linked závěrka that rounds to
        # nothing is still a filed závěrka, and must not read as "none".
        ctx["vykazy_header"] = {
            "uv_vyhl": vykazy.DECREE,
            "uv_rozsah": self._l10n_cz_vykaz_range(),
            "uv_mena": self.company_id.currency_id.name,
            "uz_rad": "T",
            "d_uv": self.date_to.strftime("%d.%m.%Y"),
        } if linked else {}
        ctx["vykazy_header"] = dict(ctx["vykazy_header"], **header)
        return ctx

    def action_export_xml(self):
        res = super().action_export_xml()
        for rec in self:
            if rec._l10n_cz_is_dppdp9() and rec.l10n_cz_registry_request \
                    and not rec.l10n_cz_notes_attachment_ids:
                rec.message_post(body=_(
                    "The request to hand the účetní závěrka to the sbírka "
                    "listin was exported without a příloha účetní závěrky. "
                    "The příloha is part of every závěrka (§ 18 odst. 1 "
                    "zákona o účetnictví); attach it and export again, or "
                    "file it with the rejstříkový soud yourself."))
            if rec._l10n_cz_is_dppdp9() and not rec._l10n_cz_vykaz_statements():
                # Legal, and worth saying: a return without its výkazy is
                # complete only if the závěrka goes as an E-příloha.
                rec.message_post(body=_(
                    "Exported without the Rozvaha and Výkaz zisku a ztráty: "
                    "no statements are linked. Attach the účetní závěrka to "
                    "the filing as an E-příloha, or link the statements and "
                    "export again."))
        return res
