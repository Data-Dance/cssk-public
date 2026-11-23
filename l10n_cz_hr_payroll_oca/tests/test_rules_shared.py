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
            ("module", "=", "l10n_cz_hr_payroll_oca"),
            ("model", "in", ("hr.salary.rule", "hr.salary.rule.category")),
        ])
        self.assertTrue(data, "the module ships rules")
        owned = [
            "%s %s" % (d.model, d.name) for d in data
            if self.env[d.model].browse(d.res_id).company_id
        ]
        self.assertFalse(owned, "rules or categories tied to one company")

    def test_employee_form_offers_the_shipped_structures(self):
        """OCA payroll's own domain on the employee form is the employee's
        company only, which hid every structure shipped here."""
        from lxml import etree
        from odoo.tools.safe_eval import safe_eval

        arch = etree.fromstring(
            self.env["hr.employee"].get_view(view_type="form")["arch"])
        fields_found = arch.xpath("//field[@name='struct_id']")
        self.assertTrue(fields_found, "the form has the structure field")
        domain = safe_eval(
            fields_found[0].get("domain"),
            {"company_id": self.env.company.id})
        shipped = self.env["ir.model.data"].search([
            ("module", "=", "l10n_cz_hr_payroll_oca"),
            ("model", "=", "hr.payroll.structure"),
        ]).mapped("res_id")
        self.assertTrue(shipped, "the module ships structures")
        offered = self.env["hr.payroll.structure"].search(
            domain + [("id", "in", shipped)])
        self.assertEqual(sorted(offered.ids), sorted(shipped))
