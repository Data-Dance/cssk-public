{
    'name': 'Slovakia - DPPO reviewed Tables A and B',
    'version': '19.0.1.0.0', 'license': 'AGPL-3', 'author': 'votrelec',
    'category': 'Accounting/Localizations', 'countries': ['sk'],
    'website': 'https://github.com/Data-Dance/cssk-public',
    'summary': 'Reviewed DPPOv25 Tables A/B and native tax-row reconciliation',
    'depends': ['l10n_sk_dppo'],
    'data': ['security/ir.model.access.csv', 'security/rules.xml', 'views/annexes.xml', 'report/annexes.xml'],
    'installable': True,
}
