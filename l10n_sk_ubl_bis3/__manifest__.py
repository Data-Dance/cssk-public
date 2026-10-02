# -*- coding: utf-8 -*-
{
    'name': "Slovakia - Peppol BIS Billing 3.0 (eFaktúra)",
    'version': '19.0.3.0.0',
    'category': 'Accounting/Localizations/EDI',
    'summary': "Slovak e-invoicing: Peppol BIS Billing 3.0 / UBL 2.1 export",
    'description': """
Slovak electronic invoicing (eFaktúra)
======================================

Enables the Peppol BIS Billing 3.0 (UBL 2.1 / EN 16931) format for Slovak
companies, as required by the mandatory Slovak e-invoicing regime
(domestic B2B from 1 January 2027).

Important: Slovakia has **no national billing CIUS**. The mandated invoice
is unmodified Peppol BIS Billing 3.0, which Odoo's ``account.edi.xml.ubl_bis3``
already produces. This module is therefore deliberately thin. It:

* registers the format for Slovakia (``SK`` is missing from Odoo's
  ``PEPPOL_DEFAULT_COUNTRIES``, so the generic Peppol format is not
  auto-suggested for Slovak partners out of the box);
* provides ``account.edi.xml.ubl_sk`` as a stable extension point for any
  future Slovak-specific tweaks;
* maps the Slovak *variabilný symbol* (VS) onto ``cac:PaymentMeans/cbc:PaymentID``
  (BT-83) for bank reconciliation.

Out of scope (handled by a certified Peppol Access Point, not the ERP):
the Slovak Tax Data Document (TDD, ``urn:peppol:taxdata:sk-1``) and the
5-corner CTC reporting to Finančná správa.
""",
    'author': "Data Dance s.r.o.",
    'website': "https://www.datadance.eu",
    'license': "AGPL-3",
    'depends': [
        'account_edi_ubl_cii',
        'l10n_sk',
        # for res.partner.l10n_sk_dic — the number Peppol EAS 0245 designates
        'l10n_sk_base',
    ],
    'data': [],
    'installable': True,
    # Auto-installs once a Slovak CoA and the UBL/CII engine are both present,
    # mirroring l10n_ro_edi / l10n_pl_edi.
    'auto_install': True,
    'uninstall_hook': 'uninstall_hook',
}
