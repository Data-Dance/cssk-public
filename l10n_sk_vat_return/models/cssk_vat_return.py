# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK DPH return kontrolné pravidlá (content checks beyond the XSD).

Source of truth: the official DPHv25 eForm itself (FS SR,
``pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.616.html``), whose
embedded ``vypocet_rNN`` functions compute each daň row as
``round(základ × sadzba, 2)`` — pinning the EXACT rate per riadok-pair:
19 % (§ 27 ods. 2), 5 % (§ 27 ods. 3) and 23 % (základná, § 27 ods. 1). The
poučenie gives the same pairing in prose; the eForm resolves the ods. 2 vs
ods. 3 split numerically (e.g. ``vypocet_r02 = round(r01 × 0.19)``,
``vypocet_r02a = round(r01a × 0.05)``, ``vypocet_r04 = round(r03 × 0.23)``).

The XSD validates data types only, not this content relation, so a base/tax
tagged into the wrong rate band is XSD-valid but wrong; this kontrola catches
it. (The DPH eForm itself recomputes daň from základ, so it would silently
overwrite a wrong figure; we instead flag the inconsistency in our tag-derived
values.)

The base/tax rate PAIRING is version DATA (``rate_pairs`` on the version
record, seeded in ``data/cssk_vat_return_version_data.xml``), not code: the
pairing follows the form vintage (DPHv25 uses 19/5/23; the 2024 form 10/20).
Likewise the settlement / amendment line codes (r32 / r33 / r36) come from
the version's ``own_tax_line_code`` / ``excess_line_code`` /
``diff_line_code``.
"""
import logging
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_cssk_core.tools import split_street

_logger = logging.getLogger(__name__)

#: Who files (tlačivo, 1. strana: "postavenie osoby, ktorá podáva daňové
#: priznanie"), mapped to the six ``osoba`` flags of the XSD.
SK_FILER_STATUS = [
    ("platitel", "Platiteľ dane (§ 4)"),
    ("registrovana", "Osoba registrovaná pre daň podľa § 7 alebo § 7a"),
    ("inaPovinna", "Iná osoba povinná podať priznanie (§ 78 ods. 3, 4 a 9)"),
    ("zdanitelna", "Zdaniteľná osoba podľa § 3 ods. 5 uplatňujúca odpočítanie dane"),
    ("zastupca", "Daňový zástupca podľa § 69a"),
    ("zastupca69aa", "Daňový zástupca podľa § 69aa"),
]
_SK_ZASTUPCA_69AA_FROM = date(2018, 1, 1)


class CSSKVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    # --- hlavička of the SK DPH (filled on the export) -----------------------
    l10n_sk_country_code = fields.Char(related="country_id.code")
    l10n_sk_filer_status = fields.Selection(
        SK_FILER_STATUS,
        string="Postavenie osoby (SK)",
        default="platitel",
        help="Who files this return, as ticked on the first page of the "
        "Slovak DPH form. A VAT payer under § 4 is the usual case; a person "
        "registered under § 7 or § 7a (no right of deduction), a person "
        "liable under § 78 ods. 3, 4 a 9, and the tax representatives file "
        "on the same form with a different box ticked.",
    )
    l10n_sk_par79_conditions_met = fields.Boolean(
        string="Splnenie podmienok § 79 ods. 2 (SK)",
        help="§ 79 ods. 3: a VAT payer meeting the § 79 ods. 2 conditions "
        "(monthly tax period, VAT payer for at least 12 calendar months, and "
        "tax, customs and insurance arrears of at most 1 000 € over the last "
        "6 months) marks it on the return for the excess deduction to be "
        "refunded within 30 days. Odoo cannot check the arrears, so you "
        "declare it. Exported only when the return shows an excess deduction.",
    )
    l10n_sk_authorized_name = fields.Char(
        string="Oprávnená osoba — meno a priezvisko (SK)",
        help="The person authorised to file on the filer's behalf (for "
        "example a representative under § 9 daňového poriadku). Leave empty "
        "when the filer files for itself.",
    )
    l10n_sk_authorized_phone = fields.Char(string="Oprávnená osoba — telefón (SK)")
    l10n_sk_authorized_email = fields.Char(string="Oprávnená osoba — e-mail (SK)")
    l10n_sk_declaration_date = fields.Date(
        string="Dátum vyhlásenia (SK)",
        help="Date of the declaration that the figures are correct and "
        "complete. Left empty, the date of the XML export is used.",
    )

    @api.constrains("l10n_sk_par79_conditions_met", "period_type")
    def _check_l10n_sk_par79(self):
        for ret in self:
            if ret.l10n_sk_par79_conditions_met and ret.period_type != "month":
                # § 79 ods. 2 písm. a): "zdaňovacím obdobím platiteľa je
                # kalendárny mesiac".
                raise ValidationError(_(
                    "The § 79 ods. 2 refund within 30 days is available only "
                    "for a monthly tax period."))
            if (ret.l10n_sk_par79_conditions_met
                    and ret.l10n_sk_filer_status != "platitel"):
                raise ValidationError(_(
                    "Only a VAT payer can claim the § 79 ods. 2 refund "
                    "within 30 days."))

    @api.constrains("l10n_sk_filer_status", "date_from")
    def _check_l10n_sk_filer_status(self):
        for ret in self:
            if (ret.l10n_sk_filer_status == "zastupca69aa" and ret.date_from
                    and ret.date_from < _SK_ZASTUPCA_69AA_FROM):
                raise ValidationError(_(
                    "A tax representative under § 69aa files from "
                    "1. 1. 2018; the form for an earlier period has no such "
                    "box."))

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self.country_id.code != "SK":
            return ctx
        ulica, cislo = split_street(self.company_id.partner_id)
        excess_code = self.version_id.excess_line_code
        excess = {line.code: line.value for line in self.line_ids}.get(
            excess_code, 0.0) if excess_code else 0.0
        declared = self.l10n_sk_declaration_date or fields.Date.context_today(self)
        ctx.update({
            "sk_ulica": ulica,
            "sk_cislo": cislo,
            "sk_osoba": {
                key: "1" if self.l10n_sk_filer_status == key else "0"
                for key, _label in SK_FILER_STATUS
            },
            "sk_splnenie_podmienok": (
                "1" if self.l10n_sk_par79_conditions_met and excess > 0
                else "0"),
            "sk_datum_vyhlasenia": declared.strftime("%d.%m.%Y"),
        })
        return ctx

    def _cssk_preflight_export(self):
        """The XSD types ``danovyUrad`` as a plain string, so a return with no
        tax office validates and exports with the element empty."""
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.country_id.code != "SK":
                continue
            if not rec.company_id.l10n_cssk_tax_authority_id.submission_code:
                raise UserError(_(
                    "Company '%(company)s' has no tax office with a submission "
                    "code, but the VAT return must name it (danovyUrad). Set "
                    "the Tax Authority on the company (Settings → Users & "
                    "Companies → Companies → %(company)s) and export again.",
                    company=rec.company_id.display_name))
        return res

    def _cssk_check_kontroly(self):
        res = super()._cssk_check_kontroly()
        if self.country_id.code == "SK" and not self.l10n_sk_authorized_name:
            warning = _(
                "• Oprávnená osoba: no authorised person is filled in on the "
                "return. That is correct when the filer files for itself; "
                "otherwise fill it in before filing.")
            self.cssk_export_warnings = "\n".join(
                filter(None, [self.cssk_export_warnings, warning]))
        return res

    def _kontroly_rules(self):
        rules = super()._kontroly_rules()
        if self.country_id.code != "SK":
            return rules
        version = self.version_id
        # daň = základ × sadzba pairing, from version DATA (rate_pairs)
        for pair in (version.rate_pairs or []):
            base, tax, rate = pair
            rates = rate if isinstance(rate, (list, tuple)) else [rate]
            rules.append({"type": "rate", "base": base, "tax": tax,
                          "rates": [float(r) for r in rates]})
        own_code = version.own_tax_line_code
        excess_code = version.excess_line_code
        # vlastná daňová povinnosť a nadmerný odpočet sú nezáporné a navzájom
        # sa vylučujú (§ 78 / § 79 zákona o DPH).
        if own_code:
            rules.append({"type": "nonneg", "code": own_code})
            # r35 = r32 − r34 musí byť ≥ 0, t. j. odpočítaný nadmerný odpočet
            # (r34) nesmie byť vyšší ako vlastná daňová povinnosť — DPHv25
            # poučenie bod 49.
            rules.append({"type": "le", "a": "r34", "b": own_code})
        if excess_code:
            rules.append({"type": "nonneg", "code": excess_code})
        if own_code and excess_code:
            rules.append({"type": "exclusive", "a": own_code, "b": excess_code})
        return rules

    def action_compute_lines(self):
        res = super().action_compute_lines()
        if self.original_return_id and self.country_id.code == "SK":
            self._fill_dodatocne_diff()
        return res

    def _fill_dodatocne_diff(self):
        """Dodatočné priznanie: the difference row (DPHv25 r36, from the
        version's ``diff_line_code``) = "Rozdiel oproti poslednej známej
        dani" = (táto čistá daň) − (čistá daň pôvodného priznania), kde čistá
        daň = own_tax − excess (r32 − r33 on DPHv25). Pulled from
        ``original_return_id`` so the accountant doesn't re-key it; skipped
        if the row was manually overridden or the version declares no
        settlement/difference codes."""
        self.ensure_one()
        version = self.version_id
        own_code = version.own_tax_line_code
        excess_code = version.excess_line_code
        diff_code = version.diff_line_code
        if not (own_code and excess_code and diff_code):
            return
        orig = {l.code: l.value for l in self.original_return_id.line_ids}
        cur = {l.code: l.value for l in self.line_ids}
        diff = ((cur.get(own_code, 0.0) - cur.get(excess_code, 0.0))
                - (orig.get(own_code, 0.0) - orig.get(excess_code, 0.0)))
        row = self.line_ids.filtered(lambda l: l.code == diff_code)
        if row and not row.is_overridden:
            row.value = diff

    # ------------------------------------------------------------------
    # § 69 ods. 3 — the split the pre-2021 vzory need and no tag can make
    # ------------------------------------------------------------------
    def _cssk_tag_line_filter(self, key, lines):
        """Separate § 69 ods. 3 from § 69 ods. 2 a 9 až 12.

        The vzory in force 2012-2020 put "služba, pri ktorej príjemca platí
        daň podľa § 69 ods. 3" on r11/r12, apart from § 69 ods. 2 a 9 až 12 on
        r09/r10. The 2021 vzor merged them, so ``l10n_sk`` has ONE
        reverse-charge family carrying tags 09/10 and the tag cannot say which
        paragraph a line is.

        What the paragraph actually turns on is WHO SUPPLIED: § 69 ods. 3 is a
        service from a person not established in Slovakia. So that is what is
        read, per line, from the supplier — no configuration, and right for the
        shared taxes. ``l10n_sk_dph_69_par`` overrides it on a tax a company
        uses for one paragraph only, which the country test would misread: a
        dedicated domestic-construction prenos tax (§ 69 ods. 12) whoever the
        supplier is, or a § 69 ods. 2 goods-with-installation tax, whose
        supplier IS foreign but whose row is r09/r10.

        Deliberately NOT defaulted to "all of it is § 69 ods. 3": that would
        move every domestic construction reverse charge onto r11/r12, which is
        the error the split exists to prevent.
        """
        if key not in ("69_3", "not_69_3"):
            return super()._cssk_tag_line_filter(key, lines)

        sk = self.env.ref("base.sk")

        def is_69_3(line):
            marker = "auto"
            taxes = line.tax_line_id or line.tax_ids
            markers = {t.l10n_sk_dph_69_par or "auto" for t in taxes}
            # One line, one answer: a mix is not decidable and falls back to
            # the supplier, which is the rule the taxes themselves default to.
            if len(markers) == 1:
                marker = markers.pop()
            if marker == "69_3":
                return True
            if marker == "69_other":
                return False
            partner = line.move_id.partner_id
            country = partner.commercial_partner_id.country_id or partner.country_id
            # No country recorded is not evidence of a foreign supplier. Treat
            # it as domestic so an unmaintained partner cannot move an amount
            # onto r11/r12 unnoticed; the unfiled-row kontrola is what asks
            # about it.
            return bool(country) and country != sk

        want = key == "69_3"
        return lines.filtered(lambda line: is_69_3(line) == want)

    # ------------------------------------------------------------------
    # § 53 — a received debit note corrects the deduction, it is not one
    # ------------------------------------------------------------------
    # A supplier's ťarchopis (opravná faktúra under § 25 ods. 1 písm. c)
    # raises a deduction already claimed, and § 53 ods. 1 písm. b) puts that on
    # r28: "suma dane, o ktorú sa opravuje odpočítaná daň podľa § 53 ...
    # nadväzne na opravu základu dane podľa § 25", minus when the deduction
    # rises (DPHv25 poučenie bod 43). Where the recipient self-assesses, the
    # base and tax are corrected on r24 / r25 at the same time.
    #
    # That is exactly what the REFUND legs of every Slovak purchase tax say —
    # 28 on the deduction, 24_PR / 25 on a self-assessment — so a supplier
    # credit note already lands right. Odoo books a debit note as an ordinary
    # bill linked by ``debit_origin_id``, so it takes the INVOICE legs instead
    # and files the increase on r20/r21 (and a self-assessed one on r09/r10 and
    # r19) as though it were a new supply. Measured on a POHODA SK agenda,
    # 2026-01: two debit notes −110.89 belong on r28; Odoo put +23.61 / +87.28
    # on r20 / r21. r33 agrees either way — the tlačivo does not.
    #
    # So a debit note is reported under the tags of the refund legs. The
    # balance keeps its own sign, which is the opposite of a credit note's, so
    # the increase comes out negative on r28 and positive on r24 / r25 with no
    # sign handling of its own. Only the return reads it this way: the lines
    # keep their tags, so the VAT closing, KV DPH and every other report are
    # untouched.
    def _cssk_sk_is_debit_note(self, move):
        """A received correction booked as a bill, read the way KV DPH reads it.

        Declared first, then derived — the same rule as the KV resolver, so the
        two forms cannot disagree on which documents are corrections. An
        imported ťarchopis whose original is in another agenda has no
        ``debit_origin_id`` and is declared through ``cssk_vat_correction``.
        """
        if move.move_type != "in_invoice":
            return False
        declared = (move.cssk_vat_correction
                    if "cssk_vat_correction" in move._fields else False)
        if declared:
            return declared == "yes"
        return bool("debit_origin_id" in move._fields and move.debit_origin_id)

    def _cssk_sk_debit_note_lines(self, move_lines):
        # Only lines that carry tags are read (the period's move lines are
        # selected that way), so a base line whose INVOICE leg has no tag but
        # whose refund leg has one would be missed. No Slovak tax is shaped
        # like that: a domestic tax tags neither base, a self-assessed one
        # both.
        if self.country_id.code != "SK":
            return move_lines.browse()
        moves = move_lines.move_id.filtered(self._cssk_sk_is_debit_note)
        return move_lines.filtered(lambda l: l.move_id in moves)

    @api.model
    def _cssk_sk_refund_tags(self, line):
        """The tags ``line`` would carry had its document been a refund."""
        rep = line.tax_repartition_line_id
        if rep:
            if rep.document_type == "refund":
                return line.tax_tag_ids
            tax = rep.tax_id

            def legs(reps):
                # Paired by type, then by the sign of the factor, then in
                # order: a self-assessed tax has a +100 deduction leg and a
                # −100 output leg on both sides, which is what lines them up.
                return reps.filtered(
                    lambda r: r.repartition_type == rep.repartition_type
                    and (r.factor_percent < 0) == (rep.factor_percent < 0)
                ).sorted(lambda r: (r.sequence, r.id))

            invoice = legs(tax.invoice_repartition_line_ids)
            refund = legs(tax.refund_repartition_line_ids)
            index = list(invoice).index(rep) if rep in invoice else -1
            if 0 <= index < len(refund):
                return refund[index].tag_ids
            # Every Slovak purchase tax has matching legs on both sides; one
            # edited out of shape cannot be read as a refund, and is reported
            # as booked rather than guessed at.
            _logger.warning(
                "l10n_sk_vat_return: %s has no refund leg matching %s; debit "
                "note %s is reported under its own tags",
                tax.display_name, rep.display_name, line.move_id.display_name)
            return line.tax_tag_ids
        if line.tax_ids:
            return line.tax_ids.flatten_taxes_hierarchy().refund_repartition_line_ids.filtered(
                lambda r: r.repartition_type == "base").tag_ids
        return line.tax_tag_ids

    def _eval_tags(self, formula, move_lines, line_filter=None):
        debit_notes = self._cssk_sk_debit_note_lines(move_lines)
        if not debit_notes:
            return super()._eval_tags(formula, move_lines, line_filter)
        total = super()._eval_tags(formula, move_lines - debit_notes, line_filter)
        refund_tags = {l.id: self._cssk_sk_refund_tags(l) for l in debit_notes}
        Tag = self.env["account.account.tag"]
        for term_sign, term in self._iter_tag_terms(formula):
            tags = Tag._get_tax_tags(term, self.country_id.id)
            if not tags:
                continue
            matched = debit_notes.filtered(lambda l: refund_tags[l.id] & tags)
            if line_filter:
                matched = self._cssk_tag_line_filter(line_filter, matched)
            total += term_sign * sum(matched.mapped("balance"))
        return total

    def _tag_source_domain(self, formula, move_ids=None):
        """Drill into the debit notes by the tags the figure read them with.

        The figure takes a debit note's lines out of the rows their own tags
        name and into the rows their refund legs name, so the drill-down must
        do the same — or r21 lists a document it did not count and r28 misses
        one it did, and neither reconciles. When debit notes are involved the
        domain names the lines outright, together with their own tags, which is
        the shape the reconciliation check reads.
        """
        domain = super()._tag_source_domain(formula, move_ids)
        if not domain or self.country_id.code != "SK":
            return domain
        AML = self.env["account.move.line"]
        if move_ids is None:
            move_ids = self._cssk_period_move_ids(
                self.company_id, self.date_from, self.date_to)
        # Moves first: almost every period has no debit note, and this is
        # called once per row of the form.
        moves = self.env["account.move"].browse(move_ids).filtered(
            self._cssk_sk_is_debit_note)
        if not moves:
            return domain
        debit_notes = self._period_move_lines(moves.ids)
        Tag = self.env["account.account.tag"]
        tags = Tag.browse()
        for _sign, name in self._iter_tag_terms(formula):
            tags |= Tag._get_tax_tags(name, self.country_id.id)
        own = AML.search(domain)
        ordinary = own - debit_notes
        relocated = debit_notes.filtered(
            lambda l: self._cssk_sk_refund_tags(l) & tags)
        if not relocated and ordinary == own:
            return domain
        lines = ordinary | relocated
        if not lines:
            return [("id", "in", [])]
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("id", "in", sorted(lines.ids)),
                ("tax_tag_ids", "in", lines.tax_tag_ids.ids)]
