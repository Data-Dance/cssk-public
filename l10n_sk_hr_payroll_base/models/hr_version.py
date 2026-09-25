# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Expose the applicability table to the salary rules of both engines.

``hr.version`` is core ``hr`` in Odoo 19, and the salary-rule namespace of both
engines hands the version to every rule — as ``contract`` on the OCA engine and
``version`` on Enterprise — so a method here is reachable from a rule condition
on either without this module knowing which engine is installed.
"""

from odoo import models

from ..applicability import EMPLOYMENT, applies


class HrVersion(models.Model):
    _inherit = "hr.version"

    def l10n_sk_applies(self, concept):
        """Whether *concept* applies to this contract.

        Called straight from salary-rule conditions::

            result = contract.l10n_sk_applies('SICKNESS_INSURANCE')

        so that the rule states WHICH question it is asking and the answer
        lives in one table, rather than each rule re-deriving it from the
        agreement type and hoping every other rule derived it the same way.
        """
        self.ensure_one()
        return applies(concept, self.l10n_sk_employment_form(),
                       self.l10n_sk_income_is_regular())

    def l10n_sk_employment_form(self):
        """This contract's employment form, defaulting to a pracovný pomer.

        The agreement fields are declared by the country payroll modules, and
        this base depends on neither of them, so they are probed. A database
        with only this module installed has no agreements in it.
        """
        self.ensure_one()
        if "l10n_sk_agreement_type" not in self._fields:
            return EMPLOYMENT
        return self.l10n_sk_agreement_type or EMPLOYMENT

    def l10n_sk_income_is_regular(self):
        """Whether the remuneration is a regular monthly income.

        A pracovný pomer always is, by definition; the flag is only meaningful
        for agreements.
        """
        self.ensure_one()
        if self.l10n_sk_employment_form() == EMPLOYMENT:
            return True
        if "l10n_sk_income_regular" not in self._fields:
            return True
        return bool(self.l10n_sk_income_regular)

    def l10n_sk_is_agreement(self):
        """Whether this is a dohoda rather than a pracovný pomer."""
        self.ensure_one()
        return self.l10n_sk_employment_form() != EMPLOYMENT
