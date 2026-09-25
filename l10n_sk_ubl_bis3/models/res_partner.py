# -*- coding: utf-8 -*-
"""Slovak Peppol party identification: EAS 0245, carrying the DIČ.

Core 19.0 gets Slovakia wrong twice, in one line
(``account_edi_ubl_cii/models/account_edi_common.py:100``)::

    'SK': {'9950': 'vat', '0245': 'company_registry'},

``_compute_peppol_eas`` iterates that mapping in **dict order** and takes the
first entry whose field holds a usable value, so a Slovak partner with an
IČ DPH is identified as ``9950:SK2020317068``. And the fallback, ``0245``, is
filled from ``company_registry`` — the **IČO** — even though core's own
selection label for that code reads "SK Tax identification number (DIČ)".

The Slovak participant identifier is ``0245:<DIČ>``, a ten-digit number, and it
is not the eight-digit IČO. An access point answers an unknown participant with
a *validation* error rather than a "not found", so the wrong scheme reads as a
malformed request and costs an hour before anyone suspects the identifier.

Odoo agrees: `PR #275798 <https://github.com/odoo/odoo/pull/275798>`_ reorders
the same mapping to put ``0245`` first, with a ``TODO`` to point it at the DIČ
field once `PR #280178 <https://github.com/odoo/odoo/pull/280178>`_ lands. Both
are still open, and the mandate is January 2027, so this module does it now —
and points ``0245`` at the real number rather than at upstream's interim of
``company_registry`` filled from ``vat`` minus its prefix.

Done by overriding the two computes rather than by re-ordering
``EAS_MAPPING['SK']`` in place. That dict is a module-global, and Python imports
it once per PROCESS: mutating it would reach every database the worker serves,
including ones where this module is not installed and whose registries
therefore carry none of these overrides. A localisation must not change how
another database identifies its partners.
"""

import re

from odoo import api, fields, models
from odoo.addons.account_edi_ubl_cii.models.account_edi_common import EAS_MAPPING
from odoo.addons.account_edi_ubl_cii.models.res_partner import (
    sanitize_peppol_endpoint,
)



class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_edi_format = fields.Selection(
        selection_add=[('ubl_bis3_sk', "Slovakia (Peppol BIS 3.0)")],
    )

    def _get_edi_builder(self, invoice_edi_format):
        # EXTENDS 'account_edi_ubl_cii'
        if invoice_edi_format == 'ubl_bis3_sk':
            return self.env['account.edi.xml.ubl_sk']
        return super()._get_edi_builder(invoice_edi_format)

    def _get_ubl_cii_formats_info(self):
        # EXTENDS 'account_edi_ubl_cii'
        # SK is intentionally absent from Odoo core's PEPPOL_DEFAULT_COUNTRIES,
        # so the generic 'ubl_bis3' is not offered for Slovak partners. Register
        # our SK entry as the single format for SK -> it becomes the auto-suggested
        # one (see account_edi_ubl_cii res.partner._get_suggested_ubl_cii_edi_format).
        formats_info = super()._get_ubl_cii_formats_info()
        formats_info['ubl_bis3_sk'] = {
            'countries': ['SK'],
            'on_peppol': True,
            # Below core's ubl_bis3 (200). Today SK is absent from
            # PEPPOL_DEFAULT_COUNTRIES so this is the only SK entry and wins by
            # default. PR #275798 adds SK to that list, at which point
            # _get_suggested_ubl_cii_edi_format picks min() by sequence over
            # ['ubl_bis3', 'ubl_bis3_sk'] — equal sequences would break the tie
            # on dict order and silently drop the VS -> BT-83 mapping on the
            # _get_suggested_peppol_edi_format path that edi_base_peppol uses.
            'sequence': 150,
            'embed_attachments': True,
        }
        return formats_info

    def _get_suggested_invoice_edi_format(self):
        # EXTENDS 'account' - auto-default the stored field for Slovak partners.
        if self.country_code == 'SK':
            return 'ubl_bis3_sk'
        return super()._get_suggested_invoice_edi_format()

    # -------------------------------------------------------------------------
    # Slovak participant identifier: 0245 + DIČ
    # -------------------------------------------------------------------------

    def _l10n_sk_get_dic(self):
        """The DIČ to publish as the Peppol endpoint, or ''.

        Falls back to deriving it from the VAT number because the IČ DPH *is*
        ``SK`` + the DIČ, so a VAT payer needs nothing re-entered for its
        participant id to be right. A subject registered for income tax but not
        for VAT has no IČ DPH at all — which is the case the DIČ field exists
        for — and there the stored value is the only source.
        """
        self.ensure_one()
        if 'l10n_sk_dic' in self._fields and (dic := (self.l10n_sk_dic or '').strip()):
            return dic
        # Exactly ten digits, not merely "digits": a malformed VAT such as
        # 'SK123' would otherwise derive '123' and register the company on the
        # network under an identifier that is nobody's.
        vat = (self.vat or '').strip().upper().replace(' ', '')
        if re.fullmatch(r'SK\d{10}', vat):
            return vat[2:]
        return ''

    def _peppol_eas_endpoint_depends(self):
        # EXTENDS 'account_edi_ubl_cii' - the endpoint now moves with the DIČ.
        return super()._peppol_eas_endpoint_depends() + ['l10n_sk_dic']

    def _get_peppol_endpoint_value(self, country_code, field, eas):
        # EXTENDS 'account_edi_ubl_cii'
        # Keyed on the EAS code, not on `field`: EAS_MAPPING['SK']['0245'] still
        # reads 'company_registry' upstream and this module no longer edits it,
        # so the field name that arrives here is the wrong one by definition.
        # The code is what says which number is meant.
        if country_code == 'SK' and eas == '0245':
            return sanitize_peppol_endpoint(self._l10n_sk_get_dic(), eas)
        return super()._get_peppol_endpoint_value(country_code, field, eas)

    @api.depends(lambda self: self._peppol_eas_endpoint_depends())
    def _compute_peppol_eas(self):
        # EXTENDS 'account_edi_ubl_cii' - prefer 0245 for Slovakia.
        #
        # Core walks EAS_MAPPING['SK'] in dict order, so 9950 (the IČ DPH) wins
        # for any VAT payer. It also recomputes ONLY when the stored value is
        # not already a valid code for the country -- which is how a scheme
        # somebody chose deliberately survives. Both halves are preserved here:
        # the set of partners eligible to change is taken BEFORE super() using
        # exactly core's test, so this moves defaults and never a choice.
        eligible = self.filtered(
            lambda p: p._deduce_country_code() == 'SK'
            and p.peppol_eas not in EAS_MAPPING.get('SK', {})
        )
        super()._compute_peppol_eas()
        for partner in eligible:
            # Only with a number to publish: flipping the scheme while leaving
            # the endpoint behind would label an IČ DPH as a DIČ, since
            # _compute_peppol_endpoint keeps the previous value when the new
            # one is empty.
            if partner._l10n_sk_get_dic():
                partner.peppol_eas = '0245'
        return
