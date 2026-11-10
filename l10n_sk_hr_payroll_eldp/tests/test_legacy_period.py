# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEldpLegacyPeriod(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.company = cls.env["res.company"].create(
            {
                "name": "Historic ELDP test",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "12345679",
                "l10n_sk_sp_vs": "1234567890",
                "city": "Bratislava",
                "zip": "81101",
                "street": "Test 1",
            }
        )
        cls.env.user.company_ids |= cls.company

    def _report(self, year=None):
        values = {"company_id": self.company.id}
        if year:
            values["year"] = str(year)
        return self.env["l10n.sk.eldp"].with_company(self.company).create(values)

    def test_default_is_last_eldp_reporting_year(self):
        self.assertEqual(self._report().year, "2025")

    def test_2026_period_is_not_a_new_eldp_filing(self):
        report = self._report(2026)
        for action in (report._preflight, report.action_generate):
            with self.assertRaisesRegex(UserError, "before 1 January 2026"):
                action()
        self.assertFalse(report.xml_attachment_id)

    def test_2027_period_is_not_a_new_eldp_filing(self):
        with self.assertRaisesRegex(UserError, "before 1 January 2026"):
            self._report(2027)._preflight()

    def test_older_period_can_be_filed_after_abolition(self):
        self.assertTrue(self._report(2025)._preflight())

    def test_old_generated_future_file_is_not_submitted_or_deleted(self):
        report = self._report(2026)
        payload = b"<historic-generated-file/>"
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Historic ELDP 2026.xml",
                "res_model": report._name,
                "res_id": report.id,
                "datas": base64.b64encode(payload),
                "mimetype": "application/xml",
            }
        )
        # Emulate an old generated record, without claiming this fixture is
        # a valid schema file or an authority-accepted filing.
        report.write({"state": "generated", "xml_attachment_id": attachment.id})
        with self.assertRaisesRegex(UserError, "before 1 January 2026"):
            report.action_submit()
        self.assertEqual(report.state, "generated")
        self.assertFalse(report.submitted_attachment_id)
        self.assertEqual(base64.b64decode(attachment.datas), payload)
