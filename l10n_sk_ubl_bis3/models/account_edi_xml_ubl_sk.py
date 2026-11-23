# -*- coding: utf-8 -*-
import re

from odoo import _, api, models


class AccountEdiXmlUbl_Sk(models.AbstractModel):
    """Slovak flavour of Peppol BIS Billing 3.0.

    Slovakia has no national billing CIUS, so this builder is a near-empty
    subclass of the generic Peppol builder: the emitted XML (CustomizationID,
    ProfileID, party identification via EAS_MAPPING['SK'], VAT, IBAN, reverse
    charge) is already conformant. This class exists as a stable extension
    point and adds only the Slovak *variabilný symbol* convention.
    """
    _name = 'account.edi.xml.ubl_sk'
    _inherit = 'account.edi.xml.ubl_bis3'
    _description = "SK Peppol BIS Billing 3.0"

    def _export_invoice_filename(self, invoice):
        # OVERRIDE 'account.edi.xml.ubl_bis3'
        return f"{invoice.name.replace('/', '_')}_ubl_bis3_sk.xml"

    # NOTE: We deliberately do NOT override _get_customization_id /
    # _ubl_add_customization_id_node: Slovakia uses the plain Peppol BIS
    # Billing 3.0 CustomizationID, with no national CIUS deviation.

    # -------------------------------------------------------------------------
    # Dátum dodania (taxable_supply_date) -> cbc:TaxPointDate (BT-7)
    # -------------------------------------------------------------------------

    def _add_invoice_header_nodes(self, document_node, vals):
        """Carry the date of supply as the EN 16931 VAT point date.

        § 74 ods. 1 písm. d) zákona o DPH makes the date of supply a mandatory
        element of a Slovak invoice, and core already keeps it on the move as
        ``taxable_supply_date`` (``l10n_sk`` shows the field and defaults it to
        the invoice date). Core's UBL writer never reads it: ``cbc:TaxPointDate``
        is filled only from a Studio field, ``x_studio_peppol_tax_point_date``,
        so the date left the document silently. A Slovak recipient reads BT-7
        as *dátum dodania*; without it the invoice date stands in for it.

        BT-7 and the VAT point date *code* (BT-8, ``cac:InvoicePeriod/
        cbc:DescriptionCode``) are mutually exclusive (BR-CO-3). Core never
        writes BT-8, so writing BT-7 here cannot collide with it. The node's
        position is fixed by the UBL 2.1 template, not by insertion order.
        Core's Studio mapping runs after this and still wins when that field
        is set, which keeps an explicit per-invoice override possible.

        Written only when it differs from the issue date (BT-2). § 74 ods. 1
        písm. d) asks for the date of supply "if it differs from the date the
        invoice was made out", and Finančná správa's transposition of Peppol
        BIS (v1.13, BT-7) says the same: the date goes on the invoice only
        when BT-7 ≠ BT-2 and it is known. ``l10n_sk`` defaults the field to
        the invoice date, so it used to go out on every invoice. A reader of
        a file without BT-7 takes the issue date, as the import here does.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._add_invoice_header_nodes(document_node, vals)
        invoice = vals['invoice']
        if invoice.taxable_supply_date and invoice.taxable_supply_date != invoice.invoice_date:
            document_node['cbc:TaxPointDate'] = {'_text': invoice.taxable_supply_date}

    # -------------------------------------------------------------------------
    # IČO -> cac:PartyLegalEntity/cbc:CompanyID (BT-30 / BT-47), scheme 0158
    # -------------------------------------------------------------------------

    @api.model
    def _l10n_sk_ico(self, partner):
        """The partner's IČO as it goes into the file, or ``''``.

        ``company_registry`` holds it. Spaces are dropped and a short all-digit
        value is left-padded to eight digits (IČO issued before 1996 had six).
        Anything that is not purely digits is not an IČO and is returned as
        ``''``, so a foreign register number typed into the field is never
        published under the Slovak scheme.
        """
        ico = re.sub(r'\s', '', partner.company_registry or '')
        if not ico.isdigit() or len(ico) > 8:
            return ''
        return ico.zfill(8)

    def _ubl_add_party_legal_entity_nodes(self, vals):
        """A Slovak party is legally identified by its IČO, not its IČ DPH.

        Core fills ``cac:PartyLegalEntity/cbc:CompanyID`` (BT-30 seller,
        BT-47 buyer) with the VAT number for every country it has no special
        case for, so a Slovak invoice carried the IČ DPH twice — here and in
        ``cac:PartyTaxScheme`` (BT-31 / BT-48), where it belongs — and the IČO
        nowhere. Finančná správa's field catalogue asks for the IČO in BT-30 /
        BT-47 whenever the subject has one; ISO 6523 ICD ``0158`` is the Slovak
        IČO register.

        A Slovak party with no IČO on record gets no CompanyID at all rather
        than its VAT number under a legal-registration label. BR-CO-26 still
        holds for a VAT payer through BT-31.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_party_legal_entity_nodes(vals)
        commercial_partner = vals['party_vals']['partner'].commercial_partner_id
        if commercial_partner.country_code != 'SK':
            return
        ico = self._l10n_sk_ico(commercial_partner)
        vals['party_node']['cac:PartyLegalEntity'] = [{
            'cbc:RegistrationName': {'_text': commercial_partner.name},
            'cbc:CompanyID': {
                '_text': ico or None,
                'schemeID': '0158' if ico else None,
            },
        }]

    def _ubl_add_accounting_supplier_party_legal_entity_nodes(self, vals):
        """The seller's legal form and register entry (BT-33).

        Seller only: the buyer's ``cac:PartyLegalEntity`` has no such term.
        The element's place is given by ``_get_document_template`` below.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_accounting_supplier_party_legal_entity_nodes(vals)
        commercial_partner = vals['party_vals']['partner'].commercial_partner_id
        if commercial_partner.country_code != 'SK':
            return
        text = self._l10n_sk_legal_form_text(commercial_partner)
        for node in vals['party_node'].get('cac:PartyLegalEntity') or []:
            if text:
                node['cbc:CompanyLegalForm'] = {'_text': text}

    def _get_document_template(self, vals):
        """Core's template, with ``cbc:CompanyLegalForm`` in the seller's
        ``cac:PartyLegalEntity``.

        The renderer refuses a node the template does not list, and core's
        lists none for BT-33. The template is a module-level dict shared by
        every builder, so the path down to the seller's legal entity is
        copied, never edited; UBL 2.1 puts the element after
        ``cbc:CompanyID``, before the registration address.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        template = dict(super()._get_document_template(vals))
        supplier = template['cac:AccountingSupplierParty'] = dict(template['cac:AccountingSupplierParty'])
        party = supplier['cac:Party'] = dict(supplier['cac:Party'])
        legal_entity = {}
        for key, value in party['cac:PartyLegalEntity'].items():
            legal_entity[key] = value
            if key == 'cbc:CompanyID':
                legal_entity['cbc:CompanyLegalForm'] = {}
        # Should core rename the anchor, the element is still listed.
        legal_entity.setdefault('cbc:CompanyLegalForm', {})
        party['cac:PartyLegalEntity'] = legal_entity
        return template

    @api.model
    def _l10n_sk_legal_form_text(self, partner):
        """The seller's additional legal information (BT-33), or ``''``.

        § 3a Obchodného zákonníka: business documents carry the legal form
        and, for an entrepreneur in a register, the register and the entry
        number. Finančná správa's transposition (BT-33) puts exactly that
        here: "<Spoločnosť s ručením obmedzeným> zapísaná do <Obchodného
        registra …>, oddiel <…>, vložka číslo <…>".

        Both come from ``l10n_sk_trade_registry`` when it is installed (the
        legal form and the § 3a sentence it keeps on the contact). It is not
        a dependency: without it there is nothing to say and the element is
        left out, which Peppol allows.
        """
        if 'l10n_sk_trade_registry_statement' not in partner._fields:
            return ''
        form = (partner.l10n_sk_legal_form or '').strip()
        statement = (partner.l10n_sk_trade_registry_statement or '').strip()
        if form and statement:
            # The composed sentence opens with "Zapísaná" / "Zapísaný"; a
            # sentence somebody typed over it is joined as it stands.
            if statement.startswith("Zapísan"):
                statement = "z" + statement[1:]
            return "%s, %s" % (form, statement)
        return form or statement

    # -------------------------------------------------------------------------
    # Opravná faktúra: the original invoice (BT-25 / BT-26) and type code 383
    # -------------------------------------------------------------------------

    def _l10n_sk_corrected_invoices(self, invoice):
        """The invoice(s) a credit note or debit note corrects.

        ``reversed_entry_id`` is set by the credit-note wizard and
        ``debit_origin_id`` by the debit-note one (``account_debit_note``,
        which is not a dependency, hence the field test).
        """
        originals = invoice.reversed_entry_id
        if 'debit_origin_id' in invoice._fields:
            originals |= invoice.debit_origin_id
        return originals.filtered(lambda m: m.name and m.name != '/')

    @api.model
    def _l10n_sk_typed_original_numbers(self, invoice):
        """The corrected invoice numbers typed on a credit note by hand."""
        numbers = []
        for number in re.split(r'[,;\n]', invoice.l10n_sk_original_invoice_ref or ''):
            number = number.strip()
            if number and number not in numbers:
                numbers.append(number)
        return numbers

    def _l10n_sk_correction_reason(self, invoice):
        """The reason typed in the credit-note or debit-note wizard, or ``''``.

        Neither wizard keeps it in a field of its own: it is the tail of the
        ``ref`` they write, "Storno: FAK/2026/00001, reason" (credit note,
        the prefix in the customer's language) or "FAK/2026/00001, reason"
        (debit note). Only a tail that follows the original's number and a
        comma is taken.
        """
        for original in self._l10n_sk_corrected_invoices(invoice):
            match = re.search(
                r'(?<![0-9A-Za-z])%s(?![0-9A-Za-z])\s*,(.*)' % re.escape(original.name),
                invoice.ref or '', flags=re.DOTALL)
            if match and match.group(1).strip():
                return match.group(1).strip()
        return ''

    def _ubl_add_notes_nodes(self, vals):
        """Say why the invoice is corrected, in the invoice note (BT-22).

        The reason is the one thing on a correcting document the recipient
        cannot work out from the figures, and ``ref``, where the wizard puts
        it, no longer leaves with the file (see
        ``_ubl_add_order_reference_node``). It goes first in the single note
        Peppol allows, before the terms and conditions.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_notes_nodes(vals)
        invoice = vals.get('invoice')
        node = vals['document_node'].get('cbc:Note')
        if not invoice or not isinstance(node, dict):
            return
        reason = self._l10n_sk_correction_reason(invoice)
        if not reason:
            return
        text = self.with_context(lang=invoice.partner_id.lang or self.env.lang).env._(
            "Reason for the correction: %(reason)s", reason=reason)
        node['_text'] = ' '.join(filter(None, [text, node.get('_text')]))

    def _l10n_sk_ref_quotes_original(self, invoice):
        """Whether ``ref`` is a wizard-made text quoting the corrected invoice
        ("Storno: FAK/2026/00001, reason") rather than an order number."""
        # Whole number only: FAK/2026/0001 must not match inside FAK/2026/00010.
        return bool(invoice.ref) and any(
            re.search(r'(?<![0-9A-Za-z])%s(?![0-9A-Za-z])' % re.escape(original.name), invoice.ref)
            for original in self._l10n_sk_corrected_invoices(invoice)
        )

    def _ubl_add_billing_reference_nodes(self, vals):
        """Name the corrected invoice: number (BT-25) and issue date (BT-26).

        § 71 ods. 2 zákona o DPH: a document that changes an invoice must carry
        the sequence number of the original. Core looks for it in
        ``matched_credit_ids`` of the credit note's receivable line; on a
        customer credit note that line is the credit side, so the lookup comes
        back empty — a credit note fully reconciled with its invoice was seen
        to go out with no ``cac:BillingReference`` — and a debit note is never
        looked at. The link the wizards record is used instead; anything core
        does find is kept, and gains the issue date where it is one of the
        linked originals.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_billing_reference_nodes(vals)
        invoice = vals.get('invoice')
        if not invoice:
            return
        nodes = vals['document_node'].setdefault('cac:BillingReference', [])
        by_name = {
            node['cac:InvoiceDocumentReference']['cbc:ID']['_text']: node
            for node in nodes
            if node.get('cac:InvoiceDocumentReference')
        }
        for original in self._l10n_sk_corrected_invoices(invoice):
            node = by_name.get(original.name)
            if node is None:
                node = by_name[original.name] = {
                    'cac:InvoiceDocumentReference': {'cbc:ID': {'_text': original.name}},
                }
                nodes.append(node)
            node['cac:InvoiceDocumentReference']['cbc:IssueDate'] = {
                '_text': original.invoice_date,
            }
        # A credit note typed by hand has no link; the numbers the user gave
        # are written as they stand, with the date where one of our own
        # invoices to this customer bears that number.
        for number in self._l10n_sk_typed_original_numbers(invoice):
            if number in by_name:
                continue
            reference = {'cbc:ID': {'_text': number}}
            original = self.env['account.move'].search([
                ('company_id', '=', invoice.company_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('name', '=', number),
                ('commercial_partner_id', '=', invoice.commercial_partner_id.id),
            ], limit=1)
            if original.invoice_date:
                reference['cbc:IssueDate'] = {'_text': original.invoice_date}
            by_name[number] = {'cac:InvoiceDocumentReference': reference}
            nodes.append(by_name[number])

    def _ubl_add_order_reference_node(self, vals):
        """Keep the wizard's "Reversal of: …" text out of the order reference.

        Core writes ``invoice.ref`` into ``cac:OrderReference/cbc:ID`` (BT-13,
        the buyer's purchase order). On a credit note or debit note made by
        the wizard, ``ref`` is the generated "Storno: FAK/2026/00001, reason",
        which is not an order number and now duplicates BT-25. When the
        reference merely quotes the corrected invoice, the original's own
        order reference is used, or the document number as core does for an
        empty ``ref``. A reference the user typed that does not quote the
        original is left alone.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_order_reference_node(vals)
        invoice = vals.get('invoice')
        if not invoice or not invoice.ref:
            return
        if not self._l10n_sk_ref_quotes_original(invoice):
            return
        order_ref = next(
            (original.ref for original in self._l10n_sk_corrected_invoices(invoice)
             if original.ref and not self._l10n_sk_ref_quotes_original(original)),
            None,
        )
        vals['document_node']['cac:OrderReference']['cbc:ID']['_text'] = order_ref or invoice.name

    def _ubl_add_invoice_type_code_node(self, vals):
        """A debit note (ťarchopis) is type 383, not a plain 380 invoice.

        BIS Billing 3.0 has no DebitNote document, so core rightly emits a
        debit note as a UBL ``Invoice`` — but with type code 380, which makes
        it indistinguishable from a new invoice at the recipient. 383 is in
        the BIS 3 invoice type code list for exactly this. Self-billing keeps
        core's 389.
        """
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_invoice_type_code_node(vals)
        invoice = vals.get('invoice')
        node = vals['document_node'].get('cbc:InvoiceTypeCode')
        if (
            invoice and node and str(node.get('_text')) == '380'
            and 'debit_origin_id' in invoice._fields and invoice.debit_origin_id
        ):
            node['_text'] = 383

    # -------------------------------------------------------------------------
    # Slovak variabilný symbol (VS) -> cbc:PaymentID (BT-83)
    # -------------------------------------------------------------------------

    def _l10n_sk_get_variable_symbol(self, invoice):
        """Slovak VS: up to 10 digits used by banks to match incoming payments.

        A VS is numeric only, so normalise the source (the canonical
        l10n_cssk_payment_symbols field when installed, else an explicit
        payment_reference, otherwise the invoice number) to digits and
        keep the last 10. Falls back to the raw source if it has no digits.
        """
        source = ''
        if 'l10n_cssk_variable_symbol' in invoice._fields:
            source = invoice.l10n_cssk_variable_symbol or ''
        source = source or invoice.payment_reference or invoice.name or ''
        digits = re.sub(r'\D', '', source)
        return digits[-10:] if digits else source

    def _ubl_add_payment_means_nodes(self, vals):
        # EXTENDS 'account.edi.xml.ubl_bis3'
        super()._ubl_add_payment_means_nodes(vals)
        invoice = vals.get('invoice')
        if not invoice:
            return
        variable_symbol = self._l10n_sk_get_variable_symbol(invoice)
        for node in vals['document_node']['cac:PaymentMeans']:
            payment_id = node.get('cbc:PaymentID')
            if payment_id is not None:
                payment_id['_text'] = variable_symbol

    # -------------------------------------------------------------------------
    # A Slovak party must be identifiable before the document leaves
    # -------------------------------------------------------------------------

    def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS 'account.edi.xml.ubl_bis3'
        constraints = super()._export_invoice_constraints(invoice, vals)
        constraints.update(self._l10n_sk_peppol_constraints(invoice, vals))
        return constraints

    def _l10n_sk_peppol_constraints(self, invoice, vals):
        """Refuse a Slovak party with no DIČ, here rather than at the gateway.

        The DIČ is no longer guessed from the VAT number, so a partner without
        one has no Slovak participant identifier — and the failure would
        otherwise surface at the access point as a *validation* error on an
        unknown participant, which reads as a malformed request and sends
        whoever is debugging it looking at the payload instead of at the
        contact. Worse, a partner with no DIČ keeps core's 9950 default and
        would go out under its IČ DPH, which is wrong but perfectly well
        formed, so nothing would complain at all.

        Named per party, so the message says which one to go and fix.
        """
        constraints = {}
        for role, partner in (
            ('supplier', invoice.company_id.partner_id.commercial_partner_id),
            ('customer', invoice.commercial_partner_id),
        ):
            if partner.country_code != 'SK':
                continue
            # Gated on the MISSING DIČ alone, not on the partner already being
            # on 0245. Gating on the scheme missed the case that matters: with
            # no DIČ recorded, _compute_peppol_eas never promotes the partner,
            # so it keeps core's 9950 default and sailed straight past this
            # check — exporting under the IČ DPH, which is the very bug this
            # module exists to fix. Measured on one real agenda: of 1204
            # Slovak trading partners with no DIČ, 1076 sat on 9950 and only
            # 127 on 0245, so the old gate caught about a tenth of them.
            #
            # A partner deliberately registered under another scheme is still
            # fine, as long as its DIČ is recorded — this asks for the number,
            # not for a particular scheme.
            if not partner._l10n_sk_get_dic():
                constraints[f'l10n_sk_ubl_bis3_{role}_dic_required'] = _(
                    "No DIČ is recorded for %(partner)s, so it has no Slovak "
                    "Peppol participant identifier: EAS 0245 carries the DIČ, "
                    "and it is currently published as %(eas)s. Set 'DIČ' on the "
                    "contact — it is not the VAT number and cannot be derived "
                    "from it.",
                    partner=partner.display_name,
                    eas=partner.peppol_eas or _("nothing"),
                )
            constraints.update(self._l10n_sk_party_constraints(role, partner))
        return constraints

    def _l10n_sk_party_constraints(self, role, partner):
        """What a Slovak invoice must say about a Slovak party, checked here.

        § 74 ods. 1 písm. a) and b) zákona o DPH: the address of the seat of
        both the supplier and the customer. EN 16931 itself asks only for the
        country (BR-09 / BR-11), so a contact with no street went out as a
        valid document that is not a valid Slovak invoice. Finančná správa's
        field catalogue marks BT-35 / BT-37 / BT-38 (seller) and BT-50 /
        BT-52 / BT-53 (buyer) as required.

        And a *Company ID* that is not an IČO is said so, rather than being
        left out of BT-30 / BT-47 without a word (see ``_l10n_sk_ico``).
        """
        constraints = {}
        missing = [
            label for field, label in (
                ('street', _("street")), ('city', _("city")), ('zip', _("postcode")),
            ) if not (partner[field] or '').strip()
        ]
        if missing:
            constraints[f'l10n_sk_ubl_bis3_{role}_address_required'] = _(
                "The address of %(partner)s is incomplete (missing: "
                "%(fields)s). A Slovak invoice must carry the full address of "
                "the supplier and of the customer (§ 74 ods. 1 of the VAT "
                "Act).",
                partner=partner.display_name,
                fields=", ".join(missing),
            )
        if (partner.company_registry or '').strip() and not self._l10n_sk_ico(partner):
            constraints[f'l10n_sk_ubl_bis3_{role}_ico_invalid'] = _(
                "The Company ID of %(partner)s, '%(value)s', is not an IČO: "
                "an IČO has 8 digits. Correct it on the contact, or clear it "
                "if the contact has none.",
                partner=partner.display_name,
                value=partner.company_registry,
            )
        return constraints
