# Copyright 2023-2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Banks",
    "summary": "Czech and Slovak banks with their codes and BICs, generated "
    "from the ČNB and NBS registries",
    # 19.0.2.0.0, not 1.0.0: this continues l10n_banks_cz_sk 19.0.1.0.0, and
    # migrations/ only run when the version moves past the one installed.
    "version": "19.0.2.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "depends": ["base_bank_from_iban"],
    "data": [
        "data/res_bank_cz.xml",
        "data/res_bank_sk.xml",
    ],
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
