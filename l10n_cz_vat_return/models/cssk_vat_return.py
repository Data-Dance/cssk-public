# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

#: line_filter keys of DPHDP3 ř. 33 / ř. 34 -> the side of the document
#: whose bad-debt corrections they collect.
BAD_DEBT_FILTERS = {
    "cz_bad_debt_creditor": "sale",      # ř. 33, věřitel, § 46 a násl.
    "cz_bad_debt_debtor": "purchase",    # ř. 34, dlužník, § 74b
}


class CsskVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    cz_filing_code = fields.Char(related="statement_type_id.fa_xml_value")
    cz_country_code = fields.Char(related="country_id.code")
    cz_discovery_date = fields.Date(
        string="Důvody zjištěny dne",
        help="d_zjist — the day the reasons for a dodatečné přiznání were "
        "found. Required for a dodatečné (D) or dodatečné/opravné (E) return.")

    # ------------------------------------------------------------------
    # Bad-debt corrections (l10n_cz_statutory ``l10n_cz_bad_debt``)
    # ------------------------------------------------------------------
    # A correction of tax on an unrecoverable receivable is reported TWICE
    # (GFŘ, Informace k opravě základu daně u nedobytných pohledávek,
    # 4. 12. 2019): on its ordinary row, ř. 1/2 for the creditor and ř. 40/41
    # for the debtor, with its own negative base and tax, "a současně" on
    # ř. 33 / ř. 34 as a positive memo of that tax. ř. 62 and ř. 63 do not
    # read ř. 33 / ř. 34 (``dphdp3_epo2.xsd``), so the ordinary row is the one
    # that changes the tax due. The document's lines carry the ordinary tags
    # and reach those rows by themselves; ř. 33 / ř. 34 add their tax.
    def _cz_bad_debt_moves(self, move_ids):
        return self.env["account.move"].search([
            ("id", "in", list(move_ids)), ("l10n_cz_bad_debt", "!=", False)])

    def _cz_bad_debt_tax_lines(self, side):
        """Tax lines of this period's flagged documents on ``side``."""
        self.ensure_one()
        all_ids = self._cssk_period_move_ids(
            self.company_id, self.date_from, self.date_to)
        moves = self._cz_bad_debt_moves(all_ids)
        moves = moves.filtered(
            lambda m: m.is_sale_document(include_receipts=True)
            if side == "sale" else m.is_purchase_document(include_receipts=True))
        return moves.line_ids.filtered(
            lambda l: l.tax_line_id and l.tax_tag_ids)

    def _eval_tags(self, formula, move_lines, line_filter=None):
        side = BAD_DEBT_FILTERS.get(line_filter)
        if side is None or self.country_id.code != "CZ":
            return super()._eval_tags(formula, move_lines, line_filter)
        # Hand-tagged entries (VAT 33 / VAT 34) keep counting.
        # A flagged document is added below, so a tag on it must not count too.
        total = super()._eval_tags(
            formula,
            move_lines.filtered(lambda l: not l.move_id.l10n_cz_bad_debt),
            None)
        balance = sum(self._cz_bad_debt_tax_lines(side).mapped("balance"))
        # Both rows are positive for the correction the section describes:
        # the creditor's credit note DEBITS output tax, the debtor's CREDITS
        # input tax.
        return total + (balance if side == "sale" else -balance)

    def _tag_source_domain(self, formula, move_ids=None):
        """ř. 33 / ř. 34 drill into the flagged documents' tax lines as well."""
        domain = super()._tag_source_domain(formula, move_ids)
        if self.country_id.code != "CZ":
            return domain
        ldef = self.version_id.line_def_ids.filtered(
            lambda d: d.tag_formula == formula and d.line_filter in BAD_DEBT_FILTERS)[:1]
        if not ldef:
            return domain
        lines = self._cz_bad_debt_tax_lines(BAD_DEBT_FILTERS[ldef.line_filter])
        if not lines:
            return domain
        Tag = self.env["account.account.tag"]
        tags = Tag.browse()
        for _sign, name in self._iter_tag_terms(formula):
            tags |= Tag._get_tax_tags(name, self.country_id.id)
        own_moves = set(move_ids or [])
        if tags and own_moves:
            own_moves = set(self.env["account.move.line"].search([
                ("move_id", "in", list(own_moves)),
                ("tax_tag_ids", "in", tags.ids)]).move_id.ids)
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("move_id", "in", sorted(own_moves | set(lines.move_id.ids))),
                ("tax_tag_ids", "in", (tags | lines.tax_tag_ids).ids)]

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.cz_country_code != "CZ":
                continue
            if rec.cz_filing_code in ("D", "E") and not rec.cz_discovery_date:
                raise UserError(_(
                    "A dodatečné přiznání needs the date its reasons were "
                    "found (Důvody zjištěny dne, d_zjist)."))
        return res
