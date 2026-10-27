from odoo import models


class AccountEdiCommon(models.AbstractModel):
    _inherit = 'account.edi.common'

    def _l10n_sk_is_domestic_reverse_charge_sale(self, tax):
        """A sale tax flagged as domestic reverse charge (§ 69 ods. 12).

        ``cssk_control_is_reverse_charge`` (l10n_cssk_kv_kh_base) marks it. The
        tax is 0 % with no UBL category of its own, so core classified it 'E'
        (exempt) and a Peppol invoice for a prenos daňovej povinnosti claimed an
        exempt supply. Peppol BIS 3 wants 'AE' with reason VATEX-EU-AE.
        """
        return bool(
            tax
            and not tax.ubl_cii_tax_category_code
            and tax.type_tax_use == 'sale'
            and 'cssk_control_is_reverse_charge' in tax._fields
            and tax.cssk_control_is_reverse_charge
        )

    def _get_tax_category_code(self, customer, supplier, tax):
        if self._l10n_sk_is_domestic_reverse_charge_sale(tax):
            return 'AE'
        return super()._get_tax_category_code(customer, supplier, tax)

    def _get_tax_exemption_reason(self, customer, supplier, tax):
        if self._l10n_sk_is_domestic_reverse_charge_sale(tax) and not tax.ubl_cii_tax_exemption_reason_code:
            # BR-AE-10: an 'AE' breakdown carries VATEX-EU-AE or a reason text.
            return {
                'tax_exemption_reason_code': 'VATEX-EU-AE',
                'tax_exemption_reason': "Prenesenie daňovej povinnosti",
            }
        return super()._get_tax_exemption_reason(customer, supplier, tax)
