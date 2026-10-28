# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models

from odoo.addons.l10n_cz_kh.models.account_move_line import _DP_ROWS_A1


class AccountEdiXmlIsdoc(models.AbstractModel):
    _inherit = 'account.edi.xml.isdoc'

    def _isdoc_is_local_reverse_charge(self, line):
        """Whether `line` is a supply in the Czech domestic reverse charge.

        The same test ``l10n_cz_kh`` applies when it puts a supply in A.1: a
        tax flagged as reverse charge, or the VAT-return row 25 the chart's
        "0% RC" sale tax reports on (that tax carries no flag). Only customer
        invoices and credit notes: the export never builds anything else.
        """
        if line._name != 'account.move.line':
            return False  # a sale order line of the ISDOC proforma
        if line.move_id.move_type not in ('out_invoice', 'out_refund'):
            return False
        if line.company_id.account_fiscal_country_id.code != 'CZ':
            return False
        if any(line.tax_ids.mapped('cssk_control_is_reverse_charge')):
            return True
        return bool(line._cz_kh_return_rows() & _DP_ROWS_A1)

    def _isdoc_tax_group_key(self, line):
        # EXTENDS account_edi_isdoc: a reverse-charge supply has its own
        # breakdown row, never merged with an exempt supply at the same 0 %.
        return (super()._isdoc_tax_group_key(line),
                self._isdoc_is_local_reverse_charge(line))

    def _isdoc_tax_category_node(self, key):
        # EXTENDS account_edi_isdoc
        percent, reverse_charge = key
        node = super()._isdoc_tax_category_node(percent)
        if reverse_charge:
            node['VATApplicable'] = self._text('true')
            node['LocalReverseChargeFlag'] = self._text('true')
        return node

    def _get_invoice_line_nodes(self, vals):
        # EXTENDS account_edi_isdoc
        nodes = super()._get_invoice_line_nodes(vals)
        for node, line in zip(nodes, vals['regular_lines']):
            if not self._isdoc_is_local_reverse_charge(line):
                continue
            category = node['ClassifiedTaxCategory']
            # Předmětem daně: taxable, only the customer pays it (§ 92a odst. 1).
            category['VATApplicable'] = self._text('true')
            code = line._cz_kh_commodity_code()
            if code:
                category['LocalReverseCharge'] = {
                    'LocalReverseChargeCode': self._text(code),
                }
        return nodes

    def _get_invoice_node(self, vals):
        # EXTENDS account_edi_isdoc: an invoice made only of reverse-charge
        # lines books no VAT, but it is subject to VAT all the same.
        node = super()._get_invoice_node(vals)
        if any(self._isdoc_is_local_reverse_charge(line)
               for line in vals['regular_lines']):
            node['VATApplicable'] = self._text('true')
        return node

    def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS account_edi_isdoc
        constraints = super()._export_invoice_constraints(invoice, vals)
        missing = [
            line for line in vals.get('regular_lines', [])
            if self._isdoc_is_local_reverse_charge(line)
            and not line._cz_kh_commodity_code()
        ]
        if missing:
            # LocalReverseChargeCode is mandatory inside LocalReverseCharge,
            # and the customer files it in KH B.1 — there is no default to
            # fall back on, as the control statement itself refuses one.
            constraints['isdoc_kh_commodity_code'] = _(
                "These reverse-charge lines have no KH commodity code (§ 92a): "
                "%(lines)s. Set it on the product or on the reverse-charge tax.",
                lines=", ".join(line.name or line.product_id.display_name or "?"
                                for line in missing),
            )
        return constraints
