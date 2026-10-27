# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from odoo import models

# DPHDP3 row a base line reports, read off its VAT-return tag ("VAT 3 Base",
# "VAT 25"). Only the BASE tags: a tax line carries "VAT 3 Tax" and is never
# classified (``tax_line_id`` lines are skipped before this is consulted).
_DP_ROW_RE = re.compile(r"^[+-]?VAT (\d+)(?: Base)?$")

# Rows of the přiznání whose base is reported in KH oddíl A.2 — the KH
# structure's own definition of celk_zd_a2: "odpovídá řádkům: 3, 4, 5, 6, 9,
# 12 a 13 přiznání k DPH". 3/4 + 9 are acquisitions from another member state
# (§ 25, § 19), 5/6 services from an EU supplier (§ 108 odst. 3 písm. a)) and
# 12/13 the other supplies a non-established person makes here, where the
# recipient is liable (§ 108 odst. 3) — a service from a third country is the
# everyday case.
_DP_ROWS_A2 = frozenset({3, 4, 5, 6, 9, 12, 13})
# Domestic reverse charge (§ 92a): ř. 10/11 received, ř. 25 supplied.
_DP_ROWS_B1 = frozenset({10, 11})
_DP_ROWS_A1 = frozenset({25})
# Import of goods (§ 23, ř. 7/8). Not part of the kontrolní hlášení at all —
# Metodická informace k vyplnění KH (1. 1. 2024), bod 1.2: "Do kontrolního
# hlášení se neuvádí údaje týkající se dovozu zboží (§ 23), řádek daňového
# přiznání: 7, 8".
_DP_ROWS_IMPORT = frozenset({7, 8})


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
        rows = self._cz_kh_return_rows()
        if is_out:
            # The supplied side of § 92a is recognised by its row as well as by
            # the flag: the flag is set on the PURCHASE taxes only, so the
            # stock "0% RC" sale tax (ř. 25) never reached A.1.
            if is_rc or rows & _DP_ROWS_A1:
                return "A1"   # domestic reverse-charge supplied (§92a)
            if is_eu and not self._cz_kh_charges_output_vat(taxes):
                # Zero-rated intra-EU supply -> EC sales list, not KH. A supply
                # to an EU customer that CHARGES Czech VAT is a domestic taxable
                # supply all the same (ř. 1/2) and belongs in A.4/A.5.
                return False
            return "A4"       # domestic taxable supply (split A4/A5 by amount)
        # inbound
        if rows & _DP_ROWS_IMPORT:
            return False      # import of goods (§ 23) is not reported in KH
        if is_eu:
            return "A2"       # acquisition from another member state
        if is_rc or rows & _DP_ROWS_B1:
            return "B1"       # domestic reverse-charge received
        if rows & _DP_ROWS_A2 and not self._cz_kh_has_cz_dic():
            # Recipient-liable supply by a non-established person (§ 108
            # odst. 3) — e.g. a service from a third country. Reported in A.2,
            # not B.2: B.2 is the deduction of VAT another plátce charged.
            # A supplier invoicing under a CZ DIČ is a domestic supplier
            # whatever the tax on the line says, as in ``_cssk_cz_is_eu``.
            return "A2"
        return "B2"           # domestic received supply (split B2/B3)

    def _cz_kh_return_rows(self):
        """DPHDP3 rows this base line reports, from its VAT-return tags."""
        rows = set()
        for tag in self.tax_tag_ids.with_context(lang="en_US"):
            match = _DP_ROW_RE.match((tag.name or "").strip())
            if match:
                rows.add(int(match.group(1)))
        return rows

    @staticmethod
    def _cz_kh_charges_output_vat(taxes):
        """Whether any of these taxes actually charges VAT (a non-zero
        amount), groups looked through to their children."""
        return any(t.amount for t in taxes.flatten_taxes_hierarchy())

    def _cz_kh_has_cz_dic(self):
        """Whether the counterparty is identified by a CZECH DIČ.

        A.4 reports the customer's DIČ "kmenová část" — a Czech registration.
        A customer known only by another member state's VAT number has none,
        and stripping its prefix would file a foreign number as a Czech one.
        """
        self.ensure_one()
        vat = "".join(self._cssk_partner_vat_for_statement().split()).upper()
        if not self._cssk_partner_vat_stripped():
            return False
        return not vat[:2].isalpha() or vat[:2] == "CZ"

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
        """First §92a code among these lines.

        Kept for callers outside this module only: the KH itself groups A.1 /
        B.1 rows per code (see ``l10n.cz.kh.row.mixin._cz_move_buckets``),
        because a document carrying two kinds of supply is filed on two rows.
        """
        for line in self:
            code = line._cz_kh_commodity_code()
            if code:
                return code
        return ""
