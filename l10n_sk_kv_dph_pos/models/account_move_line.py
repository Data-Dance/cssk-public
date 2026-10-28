# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

#: Sections the plain Slovak resolver gives a domestic taxable sale. A POS
#: session's sale is the same supply, recorded by eKasa, so it goes to D.1.
_EKASA_FROM = ("A.1", "D.2")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("move_id.pos_session_ids")
    def _compute_cssk_control_section_code(self):
        return super()._compute_cssk_control_section_code()

    def _cssk_resolve_section_code(self):
        """The closing entry of a POS session is eKasa turnover: D.1.

        Poučenie na vyplnenie kontrolného výkazu (MF/015393/2020-731), D.1:
        "Údaje uvádza platiteľ dane (dodávateľ), ktorý je povinný evidovať
        tržby pokladnicou e-kasa klient", and D.2 takes "len tie dodania
        tovaru alebo služby, ktoré nezahrnul do D.1". Every point-of-sale sale
        of a Slovak payer is recorded by one (zákon č. 384/2025 Z. z.,
        zákon č. 289/2008 Z. z. before 2026), and
        the session's closing entry is where Odoo posts those sales — it
        carries no partner, so the plain resolver read it as a supply to a
        private individual and filed it in D.2.

        Left alone: an explicit journal override (the user said what the
        journal is), a reverse charge (A.2), anything the resolver excludes,
        and an INVOICED POS order — that is an ordinary invoice, and "faktúry
        sú uvedené v A.1".
        """
        res = super()._cssk_resolve_section_code()
        # sudo: an accountant who posts or recomputes need not have any
        # Point of Sale right, and whether a session exists is not theirs to
        # be refused — it was an AccessError on every SK sale.
        if (res in _EKASA_FROM
                and not self.journal_id.cssk_control_section_override
                and self.company_id.account_fiscal_country_id.code == "SK"
                and self.move_id._cssk_vat_document().sudo().pos_session_ids):
            return "D.1"
        return res

    def _cssk_direction_sign(self):
        """A POS session's closing entry is the session's SALES.

        It is an ``entry``, and the shared rule reads an entry as received
        unless it declares a direction (``cssk_vat_direction``), so the
        session's turnover came out negative — every sale as a refund. The
        session is the declaration: what it posts are the till's sales and,
        netted into them, its returns. A direction the document does declare
        still wins.
        """
        self.ensure_one()
        document = self.move_id._cssk_vat_document()
        if not document.cssk_vat_direction and document.sudo().pos_session_ids:
            return -1.0
        return super()._cssk_direction_sign()
