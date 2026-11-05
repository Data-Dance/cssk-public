"""Name the KURZ journal in Slovak, Czech and English.

Earlier versions created it with only its national name, stored as the
English source, so an English-speaking user saw "Kurzové rozdiely"."""

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_sk_currency_revaluation.hooks import adopt_kurz_journal_names


def migrate(cr, version):
    adopt_kurz_journal_names(api.Environment(cr, SUPERUSER_ID, {}), "sk")
