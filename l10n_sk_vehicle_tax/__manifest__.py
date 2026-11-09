{
    'name': 'Slovakia - Motor vehicle tax',
    'version': '19.0.1.1.0', 'license': 'AGPL-3', 'author': 'Data Dance s.r.o., votrelec',
    'website': 'https://www.datadance.eu',
    'category': 'Accounting/Localizations', 'countries': ['sk'],
    'depends': ['l10n_cssk_core', 'l10n_sk_base', 'base_iban', 'fleet'],
    'summary': 'Dated vehicle tax assessment and DMVv25 filing',
    'data': ['security/ir.model.access.csv', 'security/rules.xml',
             'report/dmv25.xml', 'data/version.xml', 'views/vehicle_tax.xml', 'views/fleet_vehicle.xml'],
    'installable': True,
}
