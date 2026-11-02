# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRulesAreShared(TransactionCase):
    """The salary rules and categories this module ships belong to no company.

    OCA payroll defaults ``company_id`` to the INSTALLING user's company, so
    without it every rule landed in whichever company happened to be active at
    install: the structures (already company-less) then showed no rules to any
    other company, and its payroll could not run.
    """

    def test_shipped_rules_and_categories_have_no_company(self):
        data = self.env["ir.model.data"].search([
            ("module", "=", "l10n_sk_hr_payroll_surcharges_oca"),
            ("model", "in", ("hr.salary.rule", "hr.salary.rule.category")),
        ])
        self.assertTrue(data, "the module ships rules")
        owned = [
            "%s %s" % (d.model, d.name) for d in data
            if self.env[d.model].browse(d.res_id).company_id
        ]
        self.assertFalse(owned, "rules or categories tied to one company")
