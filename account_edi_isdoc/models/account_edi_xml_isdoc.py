import io
import re
import uuid
import zipfile

from lxml import etree

from odoo import _, models, Command
from odoo.exceptions import UserError
from odoo.tools import html2plaintext
from odoo.tools.float_utils import float_is_zero
from odoo.addons.account.tools import dict_to_xml
from odoo.addons.account_edi_ubl_cii.models.account_edi_common import FloatFmt
from odoo.addons.account_edi_isdoc.tools import isdoc_invoice

# ISDOC 6.0.2 - Czech national e-invoicing standard.
# Schema: http://isdoc.cz/namespace/2013 (xsd/isdoc-invoice-6.0.2.xsd)
ISDOC_NS = "http://isdoc.cz/namespace/2013"
ISDOC_MANIFEST_NS = "http://isdoc.cz/namespace/2013/manifest"
ISDOC_VERSION = "6.0.2"

# <DocumentType> code list (isdoc-invoice-6.0.2.xsd, DocumentTypeType)
ISDOC_DOCUMENT_TYPE = {
    'invoice': '1',          # daňový doklad - faktura
    'credit_note': '2',      # opravný daňový doklad (dobropis)
    'debit_note': '3',       # opravný daňový doklad (vrubopis)
    'proforma': '4',         # zálohová faktura (neplátce / bez DPH)
    'advance': '5',          # zálohový daňový doklad (s DPH)
    'advance_credit': '6',   # opravný daňový doklad k zálohovému (s DPH)
    'simplified': '7',       # zjednodušený daňový doklad
}

# Order of the <BankAccount> group inside a transfer <Details> (after PaymentDueDate).
# These are min=1 in the schema, so they must all be present even when empty (e.g. IBAN/BIC).
ISDOC_BANK_GROUP = ('ID', 'BankCode', 'Name', 'IBAN', 'BIC')


class AccountEdiXmlISDOC(models.AbstractModel):
    _name = 'account.edi.xml.isdoc'
    _inherit = 'account.edi.common'
    _description = "ISDOC 6.0.2 (CZ)"

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def format_float(self, amount, precision_digits=2):
        if amount is None:
            return None
        return FloatFmt(amount, precision_digits)

    def _export_invoice_filename(self, invoice):
        return f"{invoice.name.replace('/', '_')}.isdoc"

    @staticmethod
    def _text(value):
        """ Wrap a scalar as a leaf node for dict_to_xml (bare scalars become attributes). """
        return {'_text': value}

    @staticmethod
    def _split_street(partner):
        """ ISDOC wants StreetName + BuildingNumber separately; Odoo stores a combined street.
        Split off a trailing house number (incl. forms like '1141/11'). """
        street = (partner.street or '').strip()
        m = re.search(r'^(.*?)[\s,]+(\d+[\w/]*)$', street)
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return street, (partner.street2 or '').strip()

    def _get_document_type_code(self, invoice):
        # Advance tax documents (DocumentType 5/6, daňový doklad k přijaté platbě) are emitted
        # by the account_edi_isdoc_sale_advance bridge; the core knows only invoices/credit notes.
        is_refund = invoice.move_type in ('out_refund', 'in_refund')
        return ISDOC_DOCUMENT_TYPE['credit_note'] if is_refund else ISDOC_DOCUMENT_TYPE['invoice']

    def _line_tax_percent(self, line):
        # Both account.move.line and sale.order.line expose `tax_ids`.
        return sum(line.tax_ids.filtered(lambda t: t.amount_type == 'percent').mapped('amount'))

    def _isdoc_line_node(self, index, name, qty, subtotal, total, percent, uom_name, product, dp):
        """ Build one <InvoiceLine> from primitives (shared by invoice and proforma export). """
        item = {'Description': self._text(html2plaintext(name) if name else product.name)}
        if product.barcode:
            item['CatalogueItemIdentification'] = {'ID': self._text(product.barcode)}
        if product.default_code:
            item['SellersItemIdentification'] = {'ID': self._text(product.default_code)}
        unit = subtotal / qty if qty else subtotal
        unit_incl = total / qty if qty else total
        return {
            'ID': self._text(str(index)),
            'InvoicedQuantity': {'_text': self.format_float(qty, 6), 'unitCode': uom_name or 'ks'},
            'LineExtensionAmount': self._text(self.format_float(subtotal, dp)),
            'LineExtensionAmountTaxInclusive': self._text(self.format_float(total, dp)),
            'LineExtensionTaxAmount': self._text(self.format_float(total - subtotal, dp)),
            'UnitPrice': self._text(self.format_float(unit, dp)),
            'UnitPriceTaxInclusive': self._text(self.format_float(unit_incl, dp)),
            'ClassifiedTaxCategory': {
                'Percent': self._text(self.format_float(percent, 2)),
                'VATCalculationMethod': self._text('0'),
                'VATApplicable': self._text('true' if percent else 'false'),
            },
            'Item': item,
        }

    def _isdoc_split_lines(self, invoice):
        """ (regular_lines, deposit_lines): deposit_lines are advance deductions reported as
        already-claimed deposits (TaxedDeposits) instead of invoice lines. """
        product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        deposit_lines = self._isdoc_deduction_lines(product_lines)
        return product_lines - deposit_lines, deposit_lines

    def _isdoc_deduction_lines(self, product_lines):
        """ Lines on a final invoice that deduct already-invoiced advances. Override point:
        the core handles generic Odoo down payments (negative is_downpayment lines on a final
        invoice); the CZ advance bridge adds is_advance_tracking deductions. """
        aml = self.env['account.move.line']
        if 'is_downpayment' not in aml._fields:
            return aml
        move = product_lines.move_id[:1]
        if not move or move._is_downpayment():  # a down-payment invoice's own lines aren't deductions
            return aml
        return product_lines.filtered('is_downpayment')

    def _isdoc_group_by_rate(self, lines, currency, sign=1):
        """ {percent: {'taxable','inclusive','tax'}} summed (and rounded) over `lines`. """
        groups = {}
        for line in lines:
            percent = round(self._line_tax_percent(line), 2)
            g = groups.setdefault(percent, {'taxable': 0.0, 'inclusive': 0.0})
            g['taxable'] += sign * line.price_subtotal
            g['inclusive'] += sign * line.price_total
        for g in groups.values():
            g['taxable'] = currency.round(g['taxable'])
            g['inclusive'] = currency.round(g['inclusive'])
            g['tax'] = currency.round(g['inclusive'] - g['taxable'])
        return groups

    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------

    def _export_invoice(self, invoice):
        """ Generate an ISDOC 6.0.2 XML for a given invoice. Returns (bytes, set(errors)). """
        self._validate_taxes(invoice.invoice_line_ids.tax_ids)

        # ISDOC mandates a <UUID>; generate and persist a stable one on first export.
        if not invoice.isdoc_uuid:
            invoice.isdoc_uuid = str(uuid.uuid4()).upper()

        vals = {'invoice': invoice.with_context(lang=invoice.partner_id.lang)}
        document_node = self._get_invoice_node(vals)

        errors = [c for c in self._export_invoice_constraints(invoice, vals).values() if c]

        xml_content = dict_to_xml(document_node, nsmap={None: ISDOC_NS}, template=isdoc_invoice.Invoice)
        # dict_to_xml emits bare tags (ISDOC uses no element prefixes); move the whole tree
        # into the ISDOC namespace so it is genuinely namespaced (not just declared) and our
        # {ns}-qualified post-processing matches.
        self._apply_namespace(xml_content)
        self._postprocess_bank_groups(xml_content)

        return etree.tostring(xml_content, xml_declaration=True, encoding='UTF-8'), set(errors)

    @staticmethod
    def _apply_namespace(root):
        for el in list(root.iter()):
            el.tag = f'{{{ISDOC_NS}}}{etree.QName(el).localname}'

    def _export_invoice_isdocx(self, invoice, pdf=None):
        """ Build an ``.isdocx`` archive: a ZIP holding the ISDOC XML, a manifest.xml
        (per isdoc-manifest-6.0.2.xsd) pointing at it, and optionally the PDF rendering. """
        xml_content, errors = self._export_invoice(invoice)
        isdoc_filename = self._export_invoice_filename(invoice)

        manifest = etree.Element(f'{{{ISDOC_MANIFEST_NS}}}manifest', nsmap={None: ISDOC_MANIFEST_NS})
        etree.SubElement(manifest, f'{{{ISDOC_MANIFEST_NS}}}maindocument', filename=isdoc_filename)
        manifest_bytes = etree.tostring(manifest, xml_declaration=True, encoding='UTF-8')

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(isdoc_filename, xml_content)
            archive.writestr('manifest.xml', manifest_bytes)
            if pdf:
                archive.writestr(f"{invoice.name.replace('/', '_')}.pdf", pdf)
        return buffer.getvalue(), errors

    def _postprocess_bank_groups(self, root):
        """ Ensure every transfer <Details> carries the full ordered BankAccount group.

        dict_to_xml drops empty leaves, but ID/BankCode/Name/IBAN/BIC are min=1 in the schema
        (and may legitimately be empty, e.g. IBAN/BIC). Insert any missing ones in order, right
        after <PaymentDueDate>.
        """
        for details in root.iter(f'{{{ISDOC_NS}}}Details'):
            present = {etree.QName(child).localname: child for child in details}
            if 'PaymentDueDate' not in present:  # cash branch, no bank group
                continue
            anchor = present['PaymentDueDate']
            insert_at = list(details).index(anchor) + 1
            for tag in ISDOC_BANK_GROUP:
                if tag in present:
                    insert_at = list(details).index(present[tag]) + 1
                    continue
                el = etree.SubElement(details, f'{{{ISDOC_NS}}}{tag}')
                details.remove(el)
                details.insert(insert_at, el)
                insert_at += 1

    # -------------------------------------------------------------------------
    # EXPORT: node builders
    # -------------------------------------------------------------------------

    def _get_invoice_node(self, vals):
        invoice = vals['invoice']
        company = invoice.company_id
        currency = invoice.currency_id
        dp = currency.decimal_places
        is_refund = invoice.move_type in ('out_refund', 'in_refund')
        sign = -1 if is_refund else 1
        has_tax = bool(invoice.amount_tax) or any(
            self._line_tax_percent(l) for l in invoice.invoice_line_ids
        )
        vals['regular_lines'], vals['deposit_lines'] = self._isdoc_split_lines(invoice)

        node = {
            'version': ISDOC_VERSION,
            'DocumentType': self._text(self._get_document_type_code(invoice)),
            'ID': self._text(invoice.name),
            'UUID': self._text(invoice.isdoc_uuid),
            'IssuingSystem': self._text("Odoo"),
            'IssueDate': self._text(invoice.invoice_date and invoice.invoice_date.isoformat()),
            'VATApplicable': self._text('true' if has_tax else 'false'),
            'ElectronicPossibilityAgreementReference': {
                '_text': company.partner_id.website or 'http://',
                'languageID': 'cs',
            },
            'LocalCurrencyCode': self._text(currency.name),
            'CurrRate': self._text('1'),
            'RefCurrRate': self._text('1'),
            'AccountingSupplierParty': {'Party': self._get_party_node(company.partner_id)},
            'AccountingCustomerParty': {'Party': self._get_party_node(invoice.commercial_partner_id)},
            'InvoiceLines': {'InvoiceLine': self._get_invoice_line_nodes(vals)},
            'TaxTotal': self._get_tax_total_node(vals),
            'LegalMonetaryTotal': self._get_monetary_total_node(vals),
        }
        # TaxPointDate is the DUZP (datum uskutečnění zdanitelného plnění),
        # which is NOT the issue date: a supply delivered on the 30th and
        # invoiced on the 3rd belongs to the earlier VAT period, and the
        # recipient books the deduction by this element.
        tax_point = invoice.taxable_supply_date or invoice.invoice_date
        if tax_point:
            node['TaxPointDate'] = self._text(tax_point.isoformat())

        # Credit note -> reference to the reversed invoice.
        origin = invoice.reversed_entry_id
        if is_refund and origin:
            node['OriginalDocumentReferences'] = {'OriginalDocumentReference': {
                'ID': self._text(origin.name),
                'IssueDate': self._text(origin.invoice_date and origin.invoice_date.isoformat()),
                'UUID': self._text(origin.isdoc_uuid) if origin.isdoc_uuid else None,
            }}

        # Already-invoiced advance payments deducted on this final invoice.
        if vals['deposit_lines']:
            nontaxed, taxed = self._get_deposits_nodes(vals)
            if nontaxed:
                node['NonTaxedDeposits'] = {'NonTaxedDeposit': nontaxed}
            if taxed:
                node['TaxedDeposits'] = {'TaxedDeposit': taxed}

        payment_means = self._get_payment_means_node(vals, sign, dp)
        if payment_means:
            node['PaymentMeans'] = payment_means
        return node

    def _get_party_node(self, partner):
        ico = partner.company_registry or ''
        street, building = self._split_street(partner)
        party = {
            'PartyIdentification': {
                'ID': self._text(ico or (partner.vat or '').replace(partner.country_id.code or '', '')),
            },
            'PartyName': {'Name': self._text(partner.name)},
            'PostalAddress': {
                'StreetName': self._text(street),
                'BuildingNumber': self._text(building),
                'CityName': self._text(partner.city),
                'PostalZone': self._text(partner.zip),
                'Country': {
                    'IdentificationCode': self._text(partner.country_id.code),
                    'Name': self._text(partner.country_id.name),
                },
            },
        }
        if ico:
            party['PartyIdentification']['CatalogFirmIdentification'] = self._text(ico)
        if partner.vat:
            party['PartyTaxScheme'] = {
                'CompanyID': self._text(partner.vat),
                'TaxScheme': self._text('VAT'),
            }
        contact = {}
        if partner.phone:
            contact['Telephone'] = self._text(partner.phone)
        if partner.email:
            contact['ElectronicMail'] = self._text(partner.email)
        if contact:
            party['Contact'] = contact
        return party

    def _get_invoice_line_nodes(self, vals):
        dp = vals['invoice'].currency_id.decimal_places
        return [
            self._isdoc_line_node(
                index, line.name, line.quantity or 0.0, line.price_subtotal, line.price_total,
                self._line_tax_percent(line), line.product_uom_id.name, line.product_id, dp)
            for index, line in enumerate(vals['regular_lines'], 1)
        ]

    def _get_tax_total_node(self, vals):
        invoice = vals['invoice']
        currency = invoice.currency_id
        dp = currency.decimal_places
        # Full amounts come from the regular lines; the deducted advances are "already claimed".
        full = self._isdoc_group_by_rate(vals['regular_lines'], currency)
        claimed = self._isdoc_group_by_rate(vals['deposit_lines'], currency, sign=-1)
        zero = {'taxable': 0.0, 'inclusive': 0.0, 'tax': 0.0}

        subtotals = []
        total_tax = 0.0
        for percent in sorted(set(full) | set(claimed)):
            f = full.get(percent, zero)
            c = claimed.get(percent, zero)
            total_tax += f['tax']
            subtotals.append({
                'TaxableAmount': self._text(self.format_float(f['taxable'], dp)),
                'TaxAmount': self._text(self.format_float(f['tax'], dp)),
                'TaxInclusiveAmount': self._text(self.format_float(f['inclusive'], dp)),
                'AlreadyClaimedTaxableAmount': self._text(self.format_float(c['taxable'], dp)),
                'AlreadyClaimedTaxAmount': self._text(self.format_float(c['tax'], dp)),
                'AlreadyClaimedTaxInclusiveAmount': self._text(self.format_float(c['inclusive'], dp)),
                'DifferenceTaxableAmount': self._text(self.format_float(f['taxable'] - c['taxable'], dp)),
                'DifferenceTaxAmount': self._text(self.format_float(f['tax'] - c['tax'], dp)),
                'DifferenceTaxInclusiveAmount': self._text(self.format_float(f['inclusive'] - c['inclusive'], dp)),
                'TaxCategory': {
                    'Percent': self._text(self.format_float(percent, 2)),
                    'VATApplicable': self._text('true' if percent else 'false'),
                },
            })
        return {
            'TaxSubTotal': subtotals,
            'TaxAmount': self._text(self.format_float(currency.round(total_tax), dp)),
        }

    def _get_monetary_total_node(self, vals):
        invoice = vals['invoice']
        currency = invoice.currency_id
        dp = currency.decimal_places
        # Full = regular lines; claimed = deducted advances; difference = net (= invoice totals).
        full = self._isdoc_group_by_rate(vals['regular_lines'], currency)
        claimed = self._isdoc_group_by_rate(vals['deposit_lines'], currency, sign=-1)
        full_untaxed = currency.round(sum(g['taxable'] for g in full.values()))
        full_total = currency.round(sum(g['inclusive'] for g in full.values()))
        claimed_untaxed = currency.round(sum(g['taxable'] for g in claimed.values()))
        claimed_total = currency.round(sum(g['inclusive'] for g in claimed.values()))
        return {
            'TaxExclusiveAmount': self._text(self.format_float(full_untaxed, dp)),
            'TaxInclusiveAmount': self._text(self.format_float(full_total, dp)),
            'AlreadyClaimedTaxExclusiveAmount': self._text(self.format_float(claimed_untaxed, dp)),
            'AlreadyClaimedTaxInclusiveAmount': self._text(self.format_float(claimed_total, dp)),
            'DifferenceTaxExclusiveAmount': self._text(self.format_float(invoice.amount_untaxed, dp)),
            'DifferenceTaxInclusiveAmount': self._text(self.format_float(invoice.amount_total, dp)),
            'PaidDepositsAmount': self._text(self.format_float(claimed_total, dp)),
            'PayableAmount': self._text(self.format_float(invoice.amount_total, dp)),
        }

    def _get_deposits_nodes(self, vals):
        """ Build (NonTaxedDeposit list, TaxedDeposit list) from the deducted advance lines. """
        dp = vals['invoice'].currency_id.decimal_places
        nontaxed, taxed = [], []
        for line in vals['deposit_lines']:
            percent = self._line_tax_percent(line)
            doc_id, var_symbol = self._isdoc_deposit_source(line)
            net = -line.price_subtotal
            inclusive = -line.price_total
            if percent:
                taxed.append({
                    'ID': self._text(doc_id),
                    'VariableSymbol': self._text(var_symbol),
                    'TaxableDepositAmount': self._text(self.format_float(net, dp)),
                    'TaxInclusiveDepositAmount': self._text(self.format_float(inclusive, dp)),
                    'ClassifiedTaxCategory': {
                        'Percent': self._text(self.format_float(percent, 2)),
                        'VATCalculationMethod': self._text('0'),
                        'VATApplicable': self._text('true'),
                    },
                })
            else:
                nontaxed.append({
                    'ID': self._text(doc_id),
                    'VariableSymbol': self._text(var_symbol),
                    'DepositAmount': self._text(self.format_float(net, dp)),
                })
        return nontaxed, taxed

    def _isdoc_deposit_source(self, line):
        """ (document_id, variable_symbol) of the advance invoice this deduction settles. """
        doc_id = line.name or line.move_id.name
        var_symbol = ''
        if 'sale_line_ids' in line._fields:
            sources = line.sale_line_ids.invoice_lines.move_id.filtered(lambda m: m._is_downpayment())
            if sources:
                doc_id = sources[0].name or doc_id
                var_symbol = sources[0].variable_symbol or ''
        if not var_symbol:
            var_symbol = re.sub(r'\D', '', doc_id or '') or '0'
        return doc_id, var_symbol

    def _get_payment_means_node(self, vals, sign, dp):
        invoice = vals['invoice']
        bank = invoice.partner_bank_id
        if not bank:
            return None
        details = {}
        if invoice.invoice_date_due:
            details['PaymentDueDate'] = self._text(invoice.invoice_date_due.isoformat())
        account_id, bank_code, iban = bank._cz_account_parts()  # from l10n_cz_base
        details['ID'] = self._text(account_id)
        details['BankCode'] = self._text(bank_code)
        details['Name'] = self._text(bank.bank_id.name or '')
        details['IBAN'] = self._text(iban)
        details['BIC'] = self._text(bank.bank_id.bic or '')
        if invoice.variable_symbol:  # from l10n_cz_base
            details['VariableSymbol'] = self._text(invoice.variable_symbol)
        if invoice.constant_symbol:
            details['ConstantSymbol'] = self._text(invoice.constant_symbol)
        if invoice.specific_symbol:
            details['SpecificSymbol'] = self._text(invoice.specific_symbol)
        return {'Payment': {
            'PaidAmount': self._text(self.format_float(sign * invoice.amount_total, dp)),
            'PaymentMeansCode': self._text('42'),
            'Details': details,
        }}

    # -------------------------------------------------------------------------
    # EXPORT: constraints
    # -------------------------------------------------------------------------

    def _export_invoice_constraints(self, invoice, vals):
        constraints = self._invoice_constraints_common(invoice)
        supplier = invoice.company_id.partner_id
        customer = invoice.commercial_partner_id
        for role, partner in (('supplier', supplier), ('customer', customer)):
            constraints[f'isdoc_{role}_name'] = self._check_required_fields(partner, 'name')
            constraints[f'isdoc_{role}_address'] = self._check_required_fields(partner, ['street', 'city', 'zip'])
            constraints[f'isdoc_{role}_country'] = self._check_required_fields(partner, 'country_id')
            if not partner.company_registry and not partner.vat:
                constraints[f'isdoc_{role}_id'] = _(
                    "%(partner)s must have an ICO (Company ID) or a VAT number for ISDOC.",
                    partner=partner.display_name,
                )
        if invoice.currency_id != invoice.company_id.currency_id:
            constraints['isdoc_foreign_currency'] = _(
                "ISDOC export currently supports only invoices in the company currency (%(cur)s).",
                cur=invoice.company_id.currency_id.name,
            )
        return constraints

    # -------------------------------------------------------------------------
    # IMPORT
    # -------------------------------------------------------------------------

    @staticmethod
    def _q(tag):
        # Namespace-agnostic on import: ISDOC 1.x-5.x use the ".../invoice" namespace,
        # 6.x uses ".../2013"; the element names are identical, so match any namespace.
        return f'{{*}}{tag}'

    def _get_import_document_amount_sign(self, tree):
        """ Map <DocumentType> to (move_type, qty_factor). ISDOC amounts are always
        positive (credit notes carry DocumentType 2/6), so qty_factor is 1. """
        doc_type = (tree.findtext(self._q('DocumentType')) or '').strip()
        if doc_type in ('2', '6'):  # credit note / credit note for advance
            return 'refund', 1
        if doc_type:  # 1/3/4/5/7 -> handled as invoice (advance/proforma refined later)
            return 'invoice', 1
        return None, 1

    def _import_fill_invoice(self, invoice, tree, qty_factor):
        q = self._q
        logs = []
        invoice_values = {}

        # ==== Partner ====
        # Vendor bill -> the supplier is our partner; customer invoice -> the customer.
        party_tag = 'AccountingSupplierParty' if invoice.move_type in ('in_invoice', 'in_refund') \
            else 'AccountingCustomerParty'
        party_node = tree.find(f'{q(party_tag)}/{q("Party")}')
        partner_logs = []
        if party_node is not None:
            partner, partner_logs = self._import_partner(
                invoice.company_id, **self._import_isdoc_party_vals(party_node))
            invoice.partner_id = partner.id  # set before lines/bank so they resolve correctly

        # ==== Currency, dates ====
        invoice_values['currency_id'], currency_logs = self._import_currency(tree, q('LocalCurrencyCode'))
        if issue_date := tree.findtext(q('IssueDate')):
            invoice_values['invoice_date'] = issue_date
        # The supplier's DUZP. The deduction period (cssk_vat_deduction_date)
        # is deliberately left alone: it is when WE claim, which the
        # supplier's document cannot know.
        if tax_point := tree.findtext(q('TaxPointDate')):
            invoice_values['taxable_supply_date'] = tax_point
        if due_date := tree.findtext(f'{q("PaymentMeans")}/{q("Payment")}/{q("Details")}/{q("PaymentDueDate")}'):
            invoice_values['invoice_date_due'] = due_date

        # ==== ref, uuid, payment_reference, origin, narration ====
        if ref := tree.findtext(q('ID')):
            invoice_values['ref'] = ref
        if isdoc_uuid := tree.findtext(q('UUID')):
            invoice_values['isdoc_uuid'] = isdoc_uuid
        if var_symbol := tree.findtext(
                f'{q("PaymentMeans")}/{q("Payment")}/{q("Details")}/{q("VariableSymbol")}'):
            invoice_values['payment_reference'] = var_symbol
        # VS/KS/SS onto the symbol fields (legacy aliases of the canonical
        # l10n_cssk_* fields), digits-sanitised to satisfy their validation
        for element, field_name, size in (
            ('VariableSymbol', 'variable_symbol', 10),
            ('ConstantSymbol', 'constant_symbol', 4),
            ('SpecificSymbol', 'specific_symbol', 10),
        ):
            raw = tree.findtext(
                f'{q("PaymentMeans")}/{q("Payment")}/{q("Details")}/{q(element)}')
            if raw and (digits := re.sub(r'\D', '', raw)[-size:]):
                invoice_values[field_name] = digits
        invoice_values['invoice_origin'] = (
            tree.findtext(f'{q("OrderReferences")}/{q("OrderReference")}/{q("ExternalOrderID")}')
            or tree.findtext(f'{q("OriginalDocumentReferences")}/{q("OriginalDocumentReference")}/{q("ID")}')
            or None
        )
        invoice_values['narration'] = self._import_description(tree, xpaths=[q('Note')])

        # ==== Lines (+ deducted advance payments + payable rounding) ====
        line_vals, line_logs = self._import_isdoc_lines(invoice, tree, qty_factor)
        line_vals += self._import_isdoc_deposits(invoice, tree, qty_factor)
        line_vals += self._import_isdoc_rounding(invoice, tree, qty_factor)
        invoice_values['invoice_line_ids'] = [Command.create(vals) for vals in line_vals]

        invoice.write(invoice_values)

        # ==== Bank account (normalised to IBAN via l10n_cz_base) ====
        # Done after the write: writing currency_id re-fires _compute_partner_bank_id, which
        # would otherwise clobber a manually set partner_bank_id (for refunds bank_partner_id
        # flips to the company, resolving to empty).
        self._import_isdoc_bank(invoice, tree)

        return logs + partner_logs + currency_logs + line_logs

    def _import_isdoc_party_vals(self, party_node):
        q = self._q
        street = (party_node.findtext(f'{q("PostalAddress")}/{q("StreetName")}') or '').strip()
        building = (party_node.findtext(f'{q("PostalAddress")}/{q("BuildingNumber")}') or '').strip()
        return {
            'name': party_node.findtext(f'{q("PartyName")}/{q("Name")}'),
            'vat': party_node.findtext(f'{q("PartyTaxScheme")}/{q("CompanyID")}'),
            'phone': party_node.findtext(f'{q("Contact")}/{q("Telephone")}'),
            'email': party_node.findtext(f'{q("Contact")}/{q("ElectronicMail")}'),
            'postal_address': {
                'country_code': party_node.findtext(
                    f'{q("PostalAddress")}/{q("Country")}/{q("IdentificationCode")}'),
                'street': (street + ' ' + building).strip(),
                'city': party_node.findtext(f'{q("PostalAddress")}/{q("CityName")}'),
                'zip': party_node.findtext(f'{q("PostalAddress")}/{q("PostalZone")}'),
            },
        }

    def _import_isdoc_bank(self, invoice, tree):
        """ Attach the document's bank account (the issuer's) to the partner and the move.
        The account is normalised to IBAN via l10n_cz_base; ISDOC may carry an explicit
        <IBAN> or only the legacy <ID>/<BankCode>. """
        q = self._q
        if not invoice.partner_id:
            return
        details = tree.find(f'{q("PaymentMeans")}/{q("Payment")}/{q("Details")}')
        if details is None:
            return
        iban = (details.findtext(q('IBAN')) or '').strip()
        if not iban:
            account_id = (details.findtext(q('ID')) or '').strip()
            bank_code = (details.findtext(q('BankCode')) or '').strip()
            if account_id and bank_code:
                iban = self.env['res.partner.bank']._cz_legacy_to_iban(f'{account_id}/{bank_code}') or ''
        if not iban:
            return
        try:
            bank = self.env['res.partner.bank']._find_or_create_bank_account(
                account_number=iban, partner=invoice.partner_id, company=invoice.company_id)
        except UserError as e:
            invoice._message_log(body=_("The bank account couldn't be imported: %s", e))
            return
        if bank:
            invoice.partner_bank_id = bank.id

    def _import_isdoc_lines(self, invoice, tree, qty_factor):
        q = self._q
        logs = []
        tax_type = invoice.journal_id.type
        currency = invoice.currency_id or invoice.company_id.currency_id
        vals_list = []
        for line in tree.findall(f'{q("InvoiceLines")}/{q("InvoiceLine")}'):
            name = (line.findtext(f'{q("Item")}/{q("Description")}') or '').strip()
            qty = float(line.findtext(q('InvoicedQuantity')) or '1')
            subtotal = float(line.findtext(q('LineExtensionAmount')) or '0')
            unit = float(line.findtext(q('UnitPrice')) or '0')
            default_code = line.findtext(f'{q("Item")}/{q("SellersItemIdentification")}/{q("ID")}')
            barcode = line.findtext(f'{q("Item")}/{q("CatalogueItemIdentification")}/{q("ID")}')
            product = self.env['product.product']._retrieve_product(
                name=name, default_code=default_code or '', barcode=barcode or '')

            quantity = qty
            price_unit = unit or (subtotal / qty if qty else subtotal)
            # Infer a discount if the line subtotal differs from price_unit * qty.
            discount = 0.0
            gross = price_unit * qty
            if qty and not float_is_zero(gross, precision_rounding=currency.rounding) \
                    and currency.compare_amounts(gross, subtotal):
                discount = 100.0 * (1 - subtotal / gross)
            elif not qty and not currency.is_zero(subtotal):
                # Zero-quantity adjustment/rounding line that still carries an amount: keep it.
                quantity = 1.0
                price_unit = subtotal

            line_values = {
                'name': name,
                'price_unit': price_unit,
                'tax_nodes': line.findall(f'{q("ClassifiedTaxCategory")}/{q("Percent")}'),
            }
            tax_ids, tax_logs = self._retrieve_taxes(invoice, line_values, tax_type)
            logs += tax_logs

            vals_list.append({
                'name': name or (product.display_name or _("Line")),
                'product_id': product.id,
                'quantity': quantity * qty_factor,
                'price_unit': line_values['price_unit'],
                'discount': discount,
                'tax_ids': [Command.set(tax_ids)],
            })
        return vals_list, logs

    def _import_isdoc_deposits(self, invoice, tree, qty_factor):
        """ Deducted advance payments (TaxedDeposits/NonTaxedDeposits) become negative lines,
        so the imported total matches the document's PayableAmount. """
        q = self._q
        tax_type = invoice.journal_id.type
        vals_list = []
        for deposit in tree.findall(f'{q("TaxedDeposits")}/{q("TaxedDeposit")}'):
            dep_id = deposit.findtext(q('ID')) or ''
            net = float(deposit.findtext(q('TaxableDepositAmount')) or '0')
            line_values = {
                'name': dep_id,
                'price_unit': -net * qty_factor,
                'tax_nodes': deposit.findall(f'{q("ClassifiedTaxCategory")}/{q("Percent")}'),
            }
            tax_ids, _logs = self._retrieve_taxes(invoice, line_values, tax_type)
            vals_list.append({
                'name': _("Advance payment %s", dep_id) if dep_id else _("Advance payment"),
                'quantity': 1,
                'price_unit': line_values['price_unit'],
                'tax_ids': [Command.set(tax_ids)],
            })
        for deposit in tree.findall(f'{q("NonTaxedDeposits")}/{q("NonTaxedDeposit")}'):
            dep_id = deposit.findtext(q('ID')) or ''
            net = float(deposit.findtext(q('DepositAmount')) or '0')
            vals_list.append({
                'name': _("Advance payment %s", dep_id) if dep_id else _("Advance payment"),
                'quantity': 1,
                'price_unit': -net * qty_factor,
                'tax_ids': [Command.set([])],
            })
        return vals_list

    def _import_isdoc_rounding(self, invoice, tree, qty_factor):
        """ Czech invoices are often rounded to whole crowns via <PayableRoundingAmount>;
        add it as a line so the imported total matches <PayableAmount>. """
        q = self._q
        currency = invoice.currency_id or invoice.company_id.currency_id
        rounding = float(tree.findtext(f'{q("LegalMonetaryTotal")}/{q("PayableRoundingAmount")}') or '0')
        if currency.is_zero(rounding):
            return []
        return [{
            'name': _("Rounding"),
            'quantity': 1,
            'price_unit': rounding * qty_factor,
            'tax_ids': [Command.set([])],
        }]
