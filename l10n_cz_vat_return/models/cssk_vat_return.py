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
    # A correction of tax on an unrecoverable receivable is reported on ř. 33
    # (creditor) or ř. 34 (debtor) and on no ordinary row. Its taxes are the
    # ordinary ones, so its lines carry the ordinary tags; the return
    # therefore leaves flagged documents out of the period it reads every
    # ordinary row from — for the figure AND its drill-down, which must agree
    # — and ř. 33 / ř. 34 add their tax back.
    def _cssk_period_move_ids(self, company, date_from, date_to):
        move_ids = super()._cssk_period_move_ids(company, date_from, date_to)
        if (self.env.context.get("cz_with_bad_debt")
                or company.account_fiscal_country_id.code != "CZ"
                or not move_ids):
            return move_ids
        flagged = set(self._cz_bad_debt_moves(move_ids).ids)
        return [mid for mid in move_ids if mid not in flagged]

    def _cz_bad_debt_moves(self, move_ids):
        return self.env["account.move"].search([
            ("id", "in", list(move_ids)), ("l10n_cz_bad_debt", "!=", False)])

    def _cz_bad_debt_tax_lines(self, side):
        """Tax lines of this period's flagged documents on ``side``."""
        self.ensure_one()
        all_ids = self.with_context(cz_with_bad_debt=True)._cssk_period_move_ids(
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
        total = super()._eval_tags(formula, move_lines, None)
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
