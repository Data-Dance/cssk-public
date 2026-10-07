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

from decimal import ROUND_HALF_UP, Decimal

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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

    #: For the form: the výkaz fields mean nothing on a Slovak DPPO.
    l10n_cz_country_code = fields.Char(related="version_id.country_id.code")

    # ------------------------------------------------------------------
    def _l10n_cz_is_dppdp9(self):
        self.ensure_one()
        return (self.version_id.country_id.code or "").upper() == "CZ"

    def _l10n_cz_vykaz_statements(self):
        """``{kind: statement}`` for the linked výkazy, or ``{}``."""
        self.ensure_one()
        linked = {
            "balance_sheet": self.l10n_cz_fs_balance_sheet_id,
            "profit_loss": self.l10n_cz_fs_profit_loss_id,
        }
        return {k: st for k, st in linked.items() if st}

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec._l10n_cz_is_dppdp9():
                rec._l10n_cz_check_vykazy()
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
            missing = vykazy.fs_codes(kind) - set(st.line_ids.mapped("code"))
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
        for (veta, row), (designation, codes) in sorted(
                vykazy.ROWS.items(), key=lambda it: (it[0][0], it[0][1])):
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
        ctx["vykazy"] = rows
        # Keyed on the LINK, not on the rows: a linked závěrka that rounds to
        # nothing is still a filed závěrka, and must not read as "none".
        ctx["vykazy_header"] = {
            "uv_vyhl": vykazy.DECREE,
            "uv_rozsah": vykazy.RANGE,
            "uv_mena": self.company_id.currency_id.name,
            "uz_rad": "T",
            "d_uv": self.date_to.strftime("%d.%m.%Y"),
        } if linked else {}
        return ctx

    def action_export_xml(self):
        res = super().action_export_xml()
        for rec in self:
            if rec._l10n_cz_is_dppdp9() and not rec._l10n_cz_vykaz_statements():
                # Legal, and worth saying: a return without its výkazy is
                # complete only if the závěrka goes as an E-příloha.
                rec.message_post(body=_(
                    "Exported without the Rozvaha and Výkaz zisku a ztráty: "
                    "no statements are linked. Attach the účetní závěrka to "
                    "the filing as an E-příloha, or link the statements and "
                    "export again."))
        return res
