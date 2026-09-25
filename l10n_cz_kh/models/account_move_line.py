# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_resolve_section_code(self):
        """CZ kontrolní hlášení (DPHKH1) section resolver, line level.

        Returns a *natural* code; the per-document 10 000 CZK split (A4 detail
        vs A5 aggregate, B2 vs B3) is decided at populate time, so domestic
        standard supplies/acquisitions are tagged ``A4`` / ``B2`` here.

        NOTE: best-effort decision tree — needs CZ-accountant validation
        (esp. the §92a reverse-charge commodity list and the §44 bad-debt
        adjustments).
        """
        res = super()._cssk_resolve_section_code()
        if res:
            return res
        company = self.company_id
        if company.account_fiscal_country_id.code != "CZ":
            return False
        taxes = self._cssk_taxes()
        if self.parent_state != "posted" or not taxes or self.tax_line_id:
            return False
        move = self.move_id._cssk_vat_document()
        is_out = move.move_type in ("out_invoice", "out_refund")
        is_in = move.move_type in ("in_invoice", "in_refund")
        if not (is_out or is_in):
            # A journal entry can still report VAT. Self-assessed acquisitions
            # are recorded that way — as an internal document rather than a
            # bill — and so are manual corrections; skipping every non-invoice
            # move drops them out of the statement silently. Where the move
            # type cannot give the direction, the taxes can, provided they all
            # point the same way (a mixed entry is ambiguous and left alone).
            uses = set(taxes.mapped("type_tax_use"))
            is_out = uses == {"sale"}
            is_in = uses == {"purchase"}
            if not (is_out or is_in):
                return False
        is_rc = bool(taxes.filtered("cssk_control_is_reverse_charge"))
        is_eu = self._cssk_cz_is_eu()
        if is_out:
            if is_rc:
                return "A1"   # domestic reverse-charge supplied (§92a)
            if is_eu:
                return False  # intra-EU supply -> EC sales list, not KH
            return "A4"       # domestic taxable supply (split A4/A5 by amount)
        # inbound
        if is_eu:
            return "A2"       # acquisition from another member state
        if is_rc:
            return "B1"       # domestic reverse-charge received
        return "B2"           # domestic received supply (split B2/B3)

    def _cssk_cz_is_eu(self):
        """Whether this is an intra-EU acquisition rather than a domestic one.

        Decided by the VAT number the supply was **made under**, not by where
        the counterparty is from. A German supplier registered for Czech VAT
        invoicing under its CZ number makes a *domestic* supply: it belongs in
        B2, and the company files it there. Reading the partner's country
        instead sent every such document to A2 — on one imported agenda, five
        documents of one supplier alone, 1.5 M of section B2 reported in the
        wrong section entirely.

        ``_cssk_partner_vat_for_statement`` already prefers
        ``cssk_control_partner_vat_override`` for exactly this case (multi-VAT
        foreign branches, SK ``entry_vat``); until now the override changed
        which VAT was *reported* without changing which section reported it.

        The partner's country remains the fallback, and is the answer whenever
        no VAT is known.
        """
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        if not eu:
            return False
        vat = self._cssk_partner_vat_for_statement().strip().upper()
        prefix = vat[:2] if len(vat) > 2 and vat[:2].isalpha() else None
        if prefix:
            country = self.env["res.country"].search([("code", "=", prefix)], limit=1)
            if country:
                return bool(country in eu.country_ids and prefix != "CZ")
        cc = self.move_id._cssk_vat_document(
        ).partner_id.commercial_partner_id.country_id
        return bool(cc in eu.country_ids and cc.code != "CZ")

    def _cz_kh_commodity_code(self):
        """§92a kód předmětu plnění (KH A.1/B.1), from the product first, then
        the reverse-charge tax. Empty for supplies that don't carry a code."""
        self.ensure_one()
        code = self.product_id.product_tmpl_id.cssk_kh_commodity_code
        if code:
            return code
        tax = self._cssk_taxes().filtered(
            lambda t: t.cssk_control_is_reverse_charge
            and t.cssk_kh_commodity_code)[:1]
        return tax.cssk_kh_commodity_code or ""

    def _cz_kh_commodity_code_for_doc(self):
        """First §92a code among these lines (a document files under one code)."""
        for line in self:
            code = line._cz_kh_commodity_code()
            if code:
                return code
        return ""
