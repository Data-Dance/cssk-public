import re
import uuid

from lxml import etree

from odoo import fields, models
from odoo.addons.account.tools import dict_to_xml
from odoo.addons.account_edi_isdoc.models.account_edi_xml_isdoc import (
    ISDOC_NS, ISDOC_VERSION, ISDOC_DOCUMENT_TYPE,
)
from odoo.addons.account_edi_isdoc.tools import isdoc_invoice


class AccountEdiXmlISDOC(models.AbstractModel):
    _inherit = 'account.edi.xml.isdoc'

    def _export_order_proforma(self, order):
        """ Generate an ISDOC 6.0.2 proforma (DocumentType 4) from a sale order. """
        self._validate_taxes(order.order_line.tax_ids)
        if not order.isdoc_uuid:
            order.isdoc_uuid = str(uuid.uuid4()).upper()

        company = order.company_id
        currency = order.currency_id
        dp = currency.decimal_places
        lines = order.order_line.filtered(lambda line: not line.display_type)

        # The shared total/monetary builders only read currency_id + amount_* (present on
        # sale.order too), so we duck-type the order as the 'invoice' with no deposits.
        vals = {
            'invoice': order,
            'regular_lines': lines,
            'deposit_lines': order.order_line.browse(),
        }
        line_nodes = [
            self._isdoc_line_node(
                index, line.name, line.product_uom_qty or 0.0, line.price_subtotal, line.price_total,
                self._line_tax_percent(line), line.product_uom_id.name, line.product_id, dp)
            for index, line in enumerate(lines, 1)
        ]
        issue_date = (order.date_order or fields.Datetime.now()).date().isoformat()

        node = {
            'version': ISDOC_VERSION,
            'DocumentType': self._text(ISDOC_DOCUMENT_TYPE['proforma']),
            'ID': self._text(order.name),
            'UUID': self._text(order.isdoc_uuid),
            'IssuingSystem': self._text("Odoo"),
            'IssueDate': self._text(issue_date),
            'VATApplicable': self._text('true' if order.amount_tax else 'false'),
            'ElectronicPossibilityAgreementReference': {
                '_text': company.partner_id.website or 'http://',
                'languageID': 'cs',
            },
            'LocalCurrencyCode': self._text(currency.name),
            'CurrRate': self._text('1'),
            'RefCurrRate': self._text('1'),
            'AccountingSupplierParty': {'Party': self._get_party_node(company.partner_id)},
            'AccountingCustomerParty': {'Party': self._get_party_node(order.partner_id.commercial_partner_id)},
            'InvoiceLines': {'InvoiceLine': line_nodes},
            'TaxTotal': self._get_tax_total_node(vals),
            'LegalMonetaryTotal': self._get_monetary_total_node(vals),
        }
        payment_means = self._get_order_payment_means(order, dp)
        if payment_means:
            node['PaymentMeans'] = payment_means

        xml_content = dict_to_xml(node, nsmap={None: ISDOC_NS}, template=isdoc_invoice.Invoice)
        self._apply_namespace(xml_content)
        self._postprocess_bank_groups(xml_content)

        errors = [c for c in self._export_order_constraints(order).values() if c]
        return etree.tostring(xml_content, xml_declaration=True, encoding='UTF-8'), set(errors)

    def _get_order_payment_means(self, order, dp):
        bank = order.company_id.partner_id.bank_ids[:1]
        if not bank:
            return None
        details = {}
        if order.validity_date:
            details['PaymentDueDate'] = self._text(order.validity_date.isoformat())
        account_id, bank_code, iban = bank._cz_account_parts()  # from l10n_cz_base
        details['ID'] = self._text(account_id)
        details['BankCode'] = self._text(bank_code)
        details['Name'] = self._text(bank.bank_id.name or '')
        details['IBAN'] = self._text(iban)
        details['BIC'] = self._text(bank.bank_id.bic or '')
        var_symbol = re.sub(r'\D', '', order.name or '')
        if var_symbol:
            details['VariableSymbol'] = self._text(var_symbol)
        return {'Payment': {
            'PaidAmount': self._text(self.format_float(order.amount_total, dp)),
            'PaymentMeansCode': self._text('42'),
            'Details': details,
        }}

    def _export_order_constraints(self, order):
        constraints = {}
        for role, partner in (('supplier', order.company_id.partner_id),
                              ('customer', order.partner_id.commercial_partner_id)):
            constraints[f'isdoc_{role}_name'] = self._check_required_fields(partner, 'name')
            constraints[f'isdoc_{role}_address'] = self._check_required_fields(partner, ['street', 'city', 'zip'])
            constraints[f'isdoc_{role}_country'] = self._check_required_fields(partner, 'country_id')
        return constraints
