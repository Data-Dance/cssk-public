# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from ..hooks import JOURNAL_CODE


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.model
    def _l10n_cz_salary_journal(self, company, contract, batch_journal=None):
        """The journal a Czech payslip of *company* is posted in.

        The engine's own order, the contract's journal and then the batch's,
        as long as the journal is of that company; else the *Salaries*
        journal this module creates with the Czech chart.
        """
        Journal = self.env["account.journal"]
        for journal in (contract.journal_id, batch_journal or Journal):
            if journal and journal.company_id == company:
                return journal
        return Journal.with_company(company).search(
            [
                *Journal._check_company_domain(company),
                ("type", "=", "general"),
                ("code", "=", JOURNAL_CODE),
            ],
            limit=1,
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Give a Czech payslip a journal of its own company.

        The engine's default is the first general journal of any company the
        user may see, and the contract's journal is read only in the form's
        onchange and in a batch. A payslip of a Czech company created in a
        database with another company's chart then carried that company's
        journal, and its entry could not be posted (accounts of one company,
        journal of another). Nothing is changed when a journal is given or
        for another country.
        """
        Version = self.env["hr.version"]
        Company = self.env["res.company"]
        batch_journal = self.env["account.journal"].browse(
            self.env.context.get("journal_id"))
        for vals in vals_list:
            if vals.get("journal_id"):
                continue
            contract = Version.browse(vals.get("contract_id"))
            company = (
                Company.browse(vals.get("company_id"))
                or contract.company_id
                or self.env.company
            )
            if company.country_id.code != "CZ":
                continue
            journal = self._l10n_cz_salary_journal(
                company, contract, batch_journal)
            if journal:
                vals["journal_id"] = journal.id
        return super().create(vals_list)

    @api.onchange("contract_id")
    def onchange_contract(self):
        res = super().onchange_contract()
        company = self.company_id or self.contract_id.company_id
        if (
            company.country_id.code == "CZ"
            and self.journal_id.company_id != company
        ):
            journal = self._l10n_cz_salary_journal(company, self.contract_id)
            if journal:
                self.journal_id = journal
        return res
