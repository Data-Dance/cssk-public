# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The three cross-check buttons of the Czech suite.

Named ``action_l10n_cz_…`` and shown on Czech filings only: the Slovak suite
has its own buttons on the same three models, and a database can hold both.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError


def _need_return(statement, vat_return):
    if not vat_return:
        # ``env._``: a module-level helper has no ``self`` for ``_`` to
        # read the language from.
        raise UserError(statement.env._(
            "No computed přiznání k DPH covers %(from)s – %(to)s. Compute "
            "the VAT return for the period first.",
            **{"from": statement.date_from, "to": statement.date_to}))


class CSSKControlStatement(models.Model):
    _inherit = "cssk.control.statement"

    def action_l10n_cz_reconcile_dph(self):
        """Kontrolní hlášení ↔ přiznání: the kontrolní řádky of věta C."""
        self.ensure_one()
        recon = self.env["l10n.cz.dph.reconciliation"]
        vat_return = recon.find_vat_return(self)
        _need_return(self, vat_return)
        self._cssk_upsert_comparison_rows(
            recon.reconcile_kh(self, vat_return), "filing",
            _("přiznání k DPH %s", vat_return.display_name))
        return self._cssk_comparison_action(
            "filing", _("KH ↔ přiznání — %s", self.display_name))


class CSSKEcSummaryStatement(models.Model):
    _inherit = "cssk.ec.summary.statement"

    l10n_cz_country_code = fields.Char(related="country_id.code")

    def action_l10n_cz_reconcile_dph(self):
        """Souhrnné hlášení ↔ přiznání ř. 20, 21 and 31."""
        self.ensure_one()
        recon = self.env["l10n.cz.dph.reconciliation"]
        vat_return = recon.find_vat_return(self)
        _need_return(self, vat_return)
        self._cssk_upsert_comparison_rows(
            recon.reconcile_sh(self, vat_return), "filing",
            _("přiznání k DPH %s", vat_return.display_name))
        return self._cssk_comparison_action(
            "filing", _("SH ↔ přiznání — %s", self.display_name))


class CSSKVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    def action_l10n_cz_reconcile_books(self):
        """Přiznání ↔ účet 343."""
        self.ensure_one()
        recon = self.env["l10n.cz.dph.reconciliation"]
        self._cssk_upsert_comparison_rows(
            recon.reconcile_books(self), "ledger",
            _("účetnictví — účet 343 a tržby skupiny 60"))
        return self._cssk_comparison_action(
            "ledger", _("Přiznání ↔ účetnictví — %s", self.display_name))
