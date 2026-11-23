# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Prehľad filled from amounts entered by hand.

Needs no payroll engine, which is the point: a company whose wages are
computed by an outside payroll office has no payslips in the database. Until
19.0.2.2.0 the overview could be created there but never generated."""
import base64
from datetime import date

from lxml import etree

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import file_path


@tagged("post_install", "-at_install")
class TestPrehladManual(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "SK Rucny Prehlad s.r.o.",
            "country_id": cls.env.ref("base.sk").id,
            "company_registry": "12345679",
            "l10n_sk_dic": "1234567890",
            "street": "Hlavna 1",
            "city": "Bratislava",
            "zip": "81101",
        })
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.schema = etree.XMLSchema(etree.parse(file_path(
            "l10n_sk_hr_payroll_monthly_tax_overview/data/prehlad2026.xsd")))

    def _prehlad(self, **vals):
        base = {
            "company_id": self.company.id,
            "year": "2026",
            "month": "9",
            "payment_date": date(2026, 10, 26),
            "manual_entry": True,
        }
        base.update(vals)
        return self.env["l10n.sk.prehlad"].with_company(
            self.company).create(base)

    def _root(self, decl):
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        self.schema.assertValid(root)
        return root

    def test_default_follows_the_payroll_engine(self):
        """Ticked by itself exactly where there is nothing else to fill the
        form from."""
        decl = self.env["l10n.sk.prehlad"].with_company(self.company).create({
            "company_id": self.company.id, "year": "2026", "month": "9"})
        self.assertEqual(decl.manual_entry, "hr.payslip" not in self.env)

    def test_generates_from_the_entered_amounts(self):
        """The figures of a real filing: income 4 416.50, advances 539.34, no
        bonus. Rows 4 and 8 follow from row 1."""
        decl = self._prehlad(
            manual_taxable_income=4416.50, manual_tax_advance=539.34)
        decl.action_generate()
        self.assertEqual(decl.state, "generated")
        self.assertFalse(decl.line_ids)
        root = self._root(decl)
        self.assertEqual(root.findtext("hlavicka/zdanovacieObdobie/mesiac"), "9")
        self.assertEqual(root.findtext("telo/cast1/r00"), "4416.50")
        self.assertEqual(root.findtext("telo/cast1/r01/datum"), "26.10.2026")
        self.assertEqual(root.findtext("telo/cast1/r01/suma"), "539.34")
        self.assertEqual(root.findtext("telo/cast1/r04"), "539.34")
        self.assertEqual(root.findtext("telo/cast1/r05"), "0.00")
        self.assertEqual(root.findtext("telo/cast1/r08"), "539.34")
        self.assertEqual(root.findtext("telo/cast2/rA"), "0.00")

    def test_bonus_is_capped_at_the_advances(self):
        """Row 5 takes the bonus only up to row 4; the rest is row C."""
        decl = self._prehlad(
            manual_taxable_income=915.0, manual_tax_advance=40.0,
            manual_child_bonus=100.0)
        decl.action_generate()
        root = self._root(decl)
        self.assertEqual(root.findtext("telo/cast1/r05"), "40.00")
        self.assertEqual(root.findtext("telo/cast1/r08"), "0.00")
        self.assertEqual(root.findtext("telo/cast2/rA"), "100.00")
        self.assertEqual(root.findtext("telo/cast2/rB"), "40.00")
        self.assertEqual(root.findtext("telo/cast2/rC"), "60.00")

    def test_a_month_with_nothing_paid_can_be_filed(self):
        """All zeros is a valid overview, not a missing one."""
        decl = self._prehlad()
        decl.action_generate()
        root = self._root(decl)
        self.assertEqual(root.findtext("telo/cast1/r00"), "0.00")
        self.assertEqual(root.findtext("telo/cast1/r08"), "0.00")

    def test_negative_amounts_are_refused(self):
        with self.assertRaises(ValidationError):
            self._prehlad(manual_tax_advance=-1.0)

    def test_amounts_are_locked_once_generated(self):
        """The file must keep saying what the record says."""
        decl = self._prehlad(
            manual_taxable_income=1000.0, manual_tax_advance=100.0)
        decl.action_generate()
        with self.assertRaises(UserError):
            decl.manual_tax_advance = 90.0
        decl.action_reset_to_draft()
        decl.manual_tax_advance = 90.0
        decl.action_generate()
        self.assertEqual(
            self._root(decl).findtext("telo/cast1/r01/suma"), "90.00")

    def test_corrective_from_entered_amounts(self):
        first = self._prehlad(
            manual_taxable_income=1000.0, manual_tax_advance=100.0)
        first.action_generate()
        first.action_submit()
        fix = self._prehlad(
            manual_taxable_income=1000.0, manual_tax_advance=110.0,
            correction_type="corrective")
        fix.action_generate()
        root = self._root(fix)
        self.assertEqual(root.findtext("hlavicka/druhPrehladu/opravny"), "1")
        self.assertEqual(root.findtext("telo/cast1/r01/suma"), "110.00")

    def test_quarter_refund_adds_up_the_entered_months(self):
        """III. časť: Σ r. C of the quarter, each month from the overview
        entered for it (the latest one, where a month was corrected)."""
        self.env["res.partner.bank"].create({
            "acc_number": "SK3112000000198742637541",
            "partner_id": self.company.partner_id.id,
        })
        july = self._prehlad(month="7", manual_tax_advance=40.0,
                             manual_child_bonus=100.0)     # r. C = 60
        july.action_generate()
        august = self._prehlad(month="8", manual_tax_advance=40.0,
                               manual_child_bonus=30.0)    # r. C = 0
        august.action_generate()
        august.action_submit()
        fix = self._prehlad(month="8", manual_tax_advance=40.0,
                            manual_child_bonus=50.0,
                            correction_type="corrective")  # r. C = 10
        fix.action_generate()
        # A draft states nothing yet and must not be picked up.
        self._prehlad(month="8", manual_tax_advance=40.0,
                      manual_child_bonus=999.0, correction_type="corrective")
        decl = self._prehlad(
            manual_tax_advance=20.0, manual_child_bonus=25.0,
            request_bonus_refund=True)                     # r. C = 5
        decl.action_generate()
        root = self._root(decl)
        self.assertEqual(
            root.findtext("telo/cast3/poukazatBonus/ziadam"), "1")
        self.assertEqual(
            root.findtext("telo/cast3/poukazatBonus/suma"), "75.00")

    def test_quarter_refund_needs_every_month(self):
        """With no payslips to fall back on, a month nobody entered would
        silently count as zero and under-claim the refund."""
        if "hr.payslip" in self.env:
            self.skipTest("a payroll engine recomputes the missing month")
        self.env["res.partner.bank"].create({
            "acc_number": "SK3112000000198742637541",
            "partner_id": self.company.partner_id.id,
        })
        self._prehlad(month="7", manual_child_bonus=10.0).action_generate()
        self._prehlad(month="8", manual_child_bonus=10.0)   # draft only
        decl = self._prehlad(manual_child_bonus=10.0,
                             request_bonus_refund=True)
        with self.assertRaises(UserError):
            decl.action_generate()

    def test_without_manual_entry_payslips_are_still_required(self):
        decl = self._prehlad(manual_entry=False, manual_taxable_income=1000.0)
        with self.assertRaises(UserError):
            decl.action_generate()
