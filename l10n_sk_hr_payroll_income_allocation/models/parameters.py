# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date
from .allocation import months

RATE_PARAMETERS = {
    'np_ee': 'sickness_ee', 'np_er': 'sickness_er',
    'sp_ee': 'pension_ee', 'sp_er': 'pension_er',
    'ip_ee': 'disability_ee', 'ip_er': 'disability_er',
    'pvn_ee': 'unemployment_ee', 'pvn_er': 'unemployment_er',
    'pvn_er_no_shorttime': 'unemployment_er_no_shorttime',
    'up_er': 'accident_er', 'gp_er': 'guarantee_er',
    'rfs_er': 'reserve_er', 'pfp_er': 'shorttime_er',
}


def dated_statutory(env, start, end):
    """Read each insurance month's values through the native dated table.

    An unknown historical period raises the native missing-parameter error.
    Values are archived in the input digest; changing a parameter invalidates
    a retry rather than silently changing a previously reviewed calculation.
    """
    get_value = env['hr.rule.parameter']._get_parameter_value
    result = {}
    for month in months(start, end):
        day = date.fromisoformat(month + '-01')
        result[month] = {
            'oop': str(get_value('l10n_sk_dohoda_oop', day)),
            'maximum': str(get_value('l10n_sk_monthly_taxable_max', day)),
            'rates': {key: str(get_value('l10n_sk_social_' + suffix, day))
                      for key, suffix in RATE_PARAMETERS.items()},
        }
    return result
