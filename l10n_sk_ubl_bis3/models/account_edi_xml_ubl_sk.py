# -*- coding: utf-8 -*-
import re

from odoo import _, models


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
        return constraints
