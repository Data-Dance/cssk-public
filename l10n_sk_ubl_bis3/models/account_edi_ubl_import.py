# -*- coding: utf-8 -*-
"""Read ``cbc:TaxPointDate`` (BT-7) back into ``taxable_supply_date``.

The mirror of the export mapping in ``account.edi.xml.ubl_sk`` — but it cannot
live there. An inbound document is routed by its CustomizationID
(``account.move._get_import_file_type``), and a plain Peppol BIS 3 invoice
resolves to ``account.edi.xml.ubl_bis3`` whatever the sender's country, so a
Slovak vendor bill never passes through the Slovak builder on the way in.

19.0 has two import pipelines, and a BIS 3 document takes the newer one:
``account.edi.xml.ubl_bis3._import_invoice_ubl_cii`` hands straight to
``account.edi.ubl._ubl_import_invoice``, which collects ``to_write`` through
``_import_ubl_invoice_add_*`` steps. ``account.edi.common._import_invoice_ubl_cii``
with its ``_import_fill_invoice`` is the older path and still serves UBL 2.0 /
2.1 documents that carry no EN 16931 CustomizationID. Both are extended here,
on the model that defines each, which every UBL flavour shares.

Country-neutral by design: BT-7 means the same thing everywhere and the field
is core's, shown wherever a localisation asks for it. A document without the
element leaves the field alone, so the usual default (the invoice date, for a
Slovak or Czech company) still applies.
"""
from odoo import fields, models


class AccountEdiUBL(models.AbstractModel):
    _inherit = 'account.edi.ubl'

    def _import_ubl_invoice_add_issue_date(self, collected_values):
        # EXTENDS 'account_edi_ubl_cii' — the step that reads the header dates.
        # Written in the same ``to_write`` as ``invoice_date``, so the explicit
        # value is protected from the recompute that the date change triggers.
        super()._import_ubl_invoice_add_issue_date(collected_values)
        tax_point_date_str = collected_values['tree'].findtext('./{*}TaxPointDate')
        if tax_point_date_str and 'taxable_supply_date' in collected_values['invoice']._fields:
            collected_values['to_write']['taxable_supply_date'] = fields.Date.from_string(tax_point_date_str)


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_20'

    def _import_fill_invoice(self, invoice, tree, qty_factor):
        # EXTENDS 'account_edi_ubl_cii' — the legacy path (no CustomizationID).
        logs = super()._import_fill_invoice(invoice, tree, qty_factor)
        tax_point_date_str = tree.findtext('./{*}TaxPointDate')
        if tax_point_date_str and 'taxable_supply_date' in invoice._fields:
            invoice.taxable_supply_date = fields.Date.from_string(tax_point_date_str)
        return logs
