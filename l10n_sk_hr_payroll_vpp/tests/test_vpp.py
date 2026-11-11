# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Runtime test — proves VPP generation + XSD validation on BOTH payroll
engines, scoped to a dohoda (DoVP) employee. Detects whichever SK payroll
engine is installed, drives it to a computed dohoda payslip, generates the VPP
declaration and validates the produced XML against the shipped
``VPP-v2026.xsd``."""

import base64
from datetime import date
from unittest.mock import patch

from lxml import etree

from odoo.addons.l10n_cssk_payroll_declaration_base.tests.common import (
    confirm_payslips,
)
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError
from odoo.tools import file_path

NS = {"v": "http://socpoist.sk/xsd/vpp2026"}


@tagged("post_install", "-at_install")
class TestVpp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.engine = cls._detect_engine()
        cls.company = cls.env["res.company"].create(
            {
                "name": "SK VPP Co",
                "country_id": cls.env.ref("base.sk").id,
                "company_registry": "12345679",
                "l10n_sk_sp_vs": "1234567890",
            }
        )
        cls.env.user.company_ids |= cls.company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        if cls.engine == "oca":
            cls.env.user.group_ids |= cls.env.ref("payroll.group_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary"
            )
        else:
            cls.env.user.group_ids |= cls.env.ref("hr_payroll.group_hr_payroll_manager")
            cls.structure = cls.env.ref(
                "l10n_sk_hr_payroll.hr_payroll_structure_sk_employee_salary"
            )
        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "SK 40h", "company_id": cls.company.id}
        )

    @classmethod
    def _detect_engine(cls):
        if cls.env.ref(
            "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_employee_salary",
            raise_if_not_found=False,
        ):
            return "oca"
        return "ee"

    def _dohodar_payslip(
        self, agreement="dovp", wage=1000.0, regular=None, identification="8501011234"
    ):
        emp_vals = {
            "name": "Dohodar Peter",
            "company_id": self.company.id,
            "resource_calendar_id": self.calendar.id,
            "identification_id": identification,  # rodné číslo
            "date_version": date(2026, 1, 1),
            "contract_date_start": date(2026, 1, 1),
            "wage": wage,
        }
        # The structure decides the employment form and a contract may not
        # disagree with it, so a dohoda sits on the dohoda's own structure
        # (OCA) or structure type (Enterprise) rather than having its
        # agreement type set underneath the employment one.
        structure = self.structure
        if self.engine == "oca":
            if agreement != "none":
                structure = self.env.ref(
                    "l10n_sk_hr_payroll_oca.hr_payroll_structure_sk_%s" % agreement
                )
            emp_vals["struct_id"] = structure.id
        else:
            structure_type = self.structure.type_id
            if agreement != "none":
                structure_type = self.env.ref(
                    "l10n_sk_hr_payroll_ee.structure_type_%s_sk" % agreement
                )
                structure = structure_type.default_struct_id
            emp_vals["structure_type_id"] = structure_type.id
        employee = self.env["hr.employee"].with_company(self.company).create(emp_vals)
        self.assertEqual(employee.version_id.l10n_sk_agreement_type, agreement)
        if regular is not None:
            employee.version_id.l10n_sk_income_regular = regular

        slip = (
            self.env["hr.payslip"]
            .with_company(self.company)
            .create(
                {
                    "name": "Payslip",
                    "employee_id": employee.id,
                    "struct_id": structure.id,
                    "company_id": self.company.id,
                    "date_from": date(2026, 3, 1),
                    "date_to": date(2026, 3, 31),
                }
            )
        )
        if self.engine == "ee":
            slip = slip.with_context(salary_simulation=True)
        slip.compute_sheet()
        confirm_payslips(slip)
        return employee, slip

    def test_generate_and_validate(self):
        employee, slip = self._dohodar_payslip()
        totals = {line.code: line.total for line in slip.line_ids}
        social_er = abs(round(totals.get("SOCIALEMPLOYERTOTAL", 0.0), 2))
        self.assertGreater(social_er, 0.0, "employer social must be computed")
        # DoVP is irregular income -> no sickness / unemployment employee side.
        self.assertAlmostEqual(abs(totals.get("SICK", 0.0)), 0.0, 2)
        self.assertAlmostEqual(abs(totals.get("UNEMPLOYMENT", 0.0)), 0.0, 2)

        decl = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create(
                {
                    "company_id": self.company.id,
                    "year": "2026",
                    "month": "3",
                }
            )
        )
        self.assertTrue(decl.version_id, "VPP version should default")
        decl.action_generate()
        self.assertEqual(decl.state, "generated")

        xml_bytes = base64.b64decode(decl.xml_attachment_id.datas)
        schema = etree.XMLSchema(
            etree.parse(file_path("l10n_sk_hr_payroll_vpp/data/VPP-v2026.xsd"))
        )
        root = etree.fromstring(xml_bytes)
        schema.assertValid(root)

        # Header shape.
        self.assertEqual(root.find("v:cisloVykazu", NS).text, "03992026")
        self.assertEqual(root.find("v:obdobieVyplPrijmov", NS).text, "032026")

        # spoluPoistne is the sum of the social fund rows the form reports.
        # It used to be asserted against SOCIALEMPLOYERTOTAL +
        # SOCIALEMPLOYEETOTAL, which on the OCA engine include health
        # insurance — the test ratified the over-statement.
        funds = (
            "SICKEMPLOYER",
            "SICK",
            "PENSIONEMPLOYER",
            "PENSION",
            "DISABILITYEMPLOYER",
            "DISABILITY",
            "UNEMPLOYMENTEMPLOYER",
            "UNEMPLOYMENT",
            "ACCIDENT",
            "GUARANTEEEMPLOYER",
            "RESERVEFUNDEMPLOYER",
        )
        expected = round(sum(abs(round(totals.get(c, 0.0), 2)) for c in funds), 2)
        self.assertGreater(expected, 0.0)
        spolu = float(root.find(".//v:poistne/v:spoluPoistne", NS).text)
        self.assertAlmostEqual(spolu, expected, 2)

        # Per-employee annex present with rodné číslo and dohoda typZec.
        annex = root.findall(".//v:poistneZamestnanca", NS)
        self.assertEqual(len(annex), 1)
        self.assertEqual(annex[0].get("rc"), "8501011234")
        self.assertEqual(annex[0].get("typZec"), "ZECD1N")
        self.assertEqual(annex[0].get("obdobie"), "032026")

    def test_non_dohoda_excluded(self):
        """A standard employment payslip must NOT appear on the VPP."""
        from odoo.exceptions import UserError

        employee, slip = self._dohodar_payslip(agreement="none")
        decl = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
        # No dohoda payslip in the period -> generation refuses (nothing to file)
        with self.assertRaises(UserError):
            decl.action_generate()

    def _vpp(self, month="3"):
        return (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": month})
        )

    def test_regular_income_dohoda_excluded(self):
        """A dohoda with REGULAR income is reported on the MVP, not here.

        The selection used to key on the agreement kind alone, so a monthly
        DoPČ landed on the VPP (as ZECD2N, irregular) and on the MVP too
        (cssk-public#12).
        """
        _employee, slip = self._dohodar_payslip(agreement="dopc", regular=True)
        decl = self._vpp()
        self.assertNotIn(slip, decl._get_period_payslips())

    def legacy_correction(self):
        self.env = self.env(context=dict(self.env.context, lang="en_US"))
        employee, slip = self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()
        correction = self._vpp()
        correction.write(
            {"correction_type": "corrective", "replaced_vpp_id": original.id}
        )
        return employee, slip, original, correction

    def test_reviewed_legacy_correction_without_recomputing_filed_payroll(self):
        _employee, slip, original, correction = self.legacy_correction()
        content = original.submitted_attachment_id.raw
        lines = slip.line_ids.ids
        # Simulate an installed recorder's response for an older unrecorded
        # month without binding the framework test to either storage schema.
        with patch.object(
            type(slip), "_cssk_recorded_fund_bases", return_value=False, create=True
        ):
            with self.assertRaisesRegex(UserError, "Precise recorded fund bases"):
                correction._collect_payslip_totals(slip)
            with self.assertRaisesRegex(UserError, "reviewed reason"):
                correction.action_confirm_legacy_fund_bases()
            correction.fund_bases_fallback_reason = (
                "Synthetic review of archived original payroll and filing"
            )
            correction.action_confirm_legacy_fund_bases()
            self.assertEqual(correction.fund_bases_confirmed_by, self.env.user)
            self.assertTrue(correction.fund_bases_confirmed_at)
            confirmed_at = correction.fund_bases_confirmed_at
            messages_before = correction.message_ids.ids
            correction.action_confirm_legacy_fund_bases()
            correction.fund_bases_fallback_reason = (
                correction.fund_bases_fallback_reason
            )
            self.assertEqual(correction.fund_bases_confirmed_at, confirmed_at)
            self.assertEqual(correction.message_ids.ids, messages_before)
            correction.action_generate()
            self.assertTrue(correction.fund_bases_warning)
        self.assertEqual(correction.state, "generated")
        self.assertEqual(original.submitted_attachment_id.raw, content)
        self.assertEqual(slip.line_ids.ids, lines)
        messages = " ".join(str(body) for body in correction.message_ids.mapped("body"))
        self.assertIn("Synthetic review of archived original payroll", messages)
        self.assertIn(self.env.user.display_name, messages)

    def test_legacy_consent_is_not_a_caller_flag_or_a_forgeable_field(self):
        _employee, slip, _original, correction = self.legacy_correction()
        with patch.object(
            type(slip), "_cssk_recorded_fund_bases", return_value=False, create=True
        ):
            with self.assertRaisesRegex(UserError, "Precise recorded fund bases"):
                correction.with_context(
                    allow_unrecorded_funds=True
                )._collect_payslip_totals(slip)
            for field, value in (
                ("fund_bases_confirmed_by", self.env.user.id),
                ("fund_bases_confirmed_at", "2026-03-31 12:00:00"),
                ("fund_bases_confirmation_digest", "forged"),
            ):
                with self.subTest(field=field):
                    with self.assertRaisesRegex(UserError, "declaration action"):
                        correction.write({field: value})
                    with self.assertRaisesRegex(UserError, "declaration action"):
                        self._vpp().with_context(**{"default_" + field: value}).copy()

    def test_legacy_consent_expires_after_source_or_reason_changes(self):
        employee, slip, _original, correction = self.legacy_correction()
        with patch.object(
            type(slip), "_cssk_recorded_fund_bases", return_value=False, create=True
        ):
            correction.fund_bases_fallback_reason = "Synthetic verified legacy source"
            correction.action_confirm_legacy_fund_bases()
            self.assertTrue(correction._legacy_fund_fallback_is_confirmed(slip))
            correction.correction_reference = (
                "Synthetic changed original filing reference"
            )
            self.assertFalse(correction._legacy_fund_fallback_is_confirmed(slip))
            correction.action_confirm_legacy_fund_bases()
            employee.version_id.wage += 10
            self.assertFalse(correction._legacy_fund_fallback_is_confirmed(slip))
            with self.assertRaisesRegex(UserError, "Precise recorded fund bases"):
                correction._collect_payslip_totals(slip)
            correction.action_confirm_legacy_fund_bases()
            correction.fund_bases_fallback_reason = "Synthetic revised review"
            self.assertFalse(correction.fund_bases_confirmed_by)
            self.assertFalse(correction.fund_bases_confirmed_at)
            with self.assertRaisesRegex(UserError, "Precise recorded fund bases"):
                correction._collect_payslip_totals(slip)

    def test_engine_without_recorder_keeps_native_original_and_correction(self):
        _employee, slip = self._dohodar_payslip()
        with patch.object(type(slip), "_cssk_recorded_fund_bases", None, create=True):
            original = self._vpp()
            original.action_generate()
            self.assertFalse(original.fund_bases_warning)
            original.action_submit()
            correction = self._vpp()
            correction.write(
                {"correction_type": "corrective", "replaced_vpp_id": original.id}
            )
            correction.action_generate()
            self.assertEqual(correction.state, "generated")
            self.assertFalse(correction.fund_bases_warning)

    def test_legacy_review_requires_the_declaration_company_in_scope(self):
        other = self.env["res.company"].create(
            {
                "name": "Synthetic unselected legacy review company",
                "country_id": self.env.ref("base.sk").id,
            }
        )
        report = (
            self.env["l10n.sk.vpp"]
            .with_company(other)
            .create(
                {
                    "company_id": other.id,
                    "year": "2026",
                    "month": "3",
                    "correction_type": "corrective",
                    "fund_bases_fallback_reason": "Synthetic out-of-scope review attempt",
                }
            )
        )
        with self.assertRaises(AccessError):
            report.with_context(
                allowed_company_ids=self.company.ids
            ).action_confirm_legacy_fund_bases()

    def test_irregular_income_dohoda_included(self):
        """Irregular income is what the VPP is for, whatever the agreement
        kind — DoBPŠ included, which the old kind list left out."""
        _e1, dopc = self._dohodar_payslip(agreement="dopc", regular=False)
        _e2, dobps = self._dohodar_payslip(
            agreement="dobps", regular=False, identification="9001011236"
        )
        decl = self._vpp()
        self.assertEqual(decl._get_period_payslips(), dopc | dobps)
        decl.action_generate()
        root = etree.fromstring(base64.b64decode(decl.xml_attachment_id.datas))
        etree.XMLSchema(
            etree.parse(file_path("l10n_sk_hr_payroll_vpp/data/VPP-v2026.xsd"))
        ).assertValid(root)
        codes = {
            row.get("rc"): row.get("typZec")
            for row in root.findall(".//v:poistneZamestnanca", NS)
        }
        self.assertEqual(codes, {"8501011234": "ZECD2N", "9001011236": "ZECD3N"})

    def test_later_contract_change_keeps_the_past_period(self):
        """The payslip's own contract version decides, not today's.

        A regular DoPČ paid in March, then re-agreed as irregular from
        April: the March payslip stays off the VPP. Read from the employee's
        current version, it would move onto it.
        """
        employee, slip = self._dohodar_payslip(agreement="dopc", regular=True)
        march = employee.version_id
        employee.create_version(
            {
                "date_version": date(2026, 4, 1),
                "l10n_sk_income_regular": False,
            }
        )
        self.assertNotEqual(employee.version_id, march)
        self.assertFalse(employee.version_id.l10n_sk_income_regular)
        self.assertTrue(march.l10n_sk_income_regular)
        self.assertNotIn(slip, self._vpp()._get_period_payslips())

    def test_sp_vs_is_editable_on_the_form(self):
        """The variable symbol is required by the preflight but was on no
        form at all; it is edited on the declaration form now."""
        arch = self.env["l10n.sk.vpp"].get_views([(False, "form")])["views"]["form"][
            "arch"
        ]
        self.assertIn('name="sp_vs"', arch)
        decl = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create({"company_id": self.company.id, "year": "2026", "month": "3"})
        )
        decl.sp_vs = "9988776655"
        self.assertEqual(self.company.l10n_sk_sp_vs, "9988776655")

    def test_corrective_full_replacement_and_retained_original(self):
        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()  # Local test status, no authority transport.
        filed = original.submitted_attachment_id
        original_bytes = base64.b64decode(filed.datas)
        before = etree.fromstring(original_bytes)
        self._dohodar_payslip(wage=500, identification="8501021234")
        correction = self._vpp()
        correction.write(
            {"correction_type": "corrective", "replaced_vpp_id": original.id}
        )
        correction.action_generate()
        after = etree.fromstring(base64.b64decode(correction.xml_attachment_id.datas))
        self.assertEqual(after.find("v:typVykazu", NS).text, "O")
        self.assertEqual(
            after.find("v:cisloVykazu", NS).text, before.find("v:cisloVykazu", NS).text
        )
        self.assertGreater(
            float(after.find(".//v:spoluPoistne", NS).text),
            float(before.find(".//v:spoluPoistne", NS).text),
        )
        self.assertEqual(
            {row.get("rc") for row in after.findall(".//v:poistneZamestnanca", NS)},
            {"8501011234", "8501021234"},
        )
        self.assertEqual(base64.b64decode(filed.datas), original_bytes)
        self.assertEqual(original.state, "submitted")

    def test_corrective_requires_exact_filed_period(self):
        from odoo.exceptions import UserError

        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        correction = self._vpp()
        correction.write(
            {"correction_type": "corrective", "replaced_vpp_id": original.id}
        )
        with self.assertRaises(UserError):
            correction.action_generate()
        original.action_submit()
        correction.month = "4"
        with self.assertRaises(UserError):
            correction.action_generate()

    def test_generated_identity_and_filed_retention(self):
        from odoo.exceptions import UserError

        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        with self.assertRaises(UserError):
            original.correction_type = "corrective"
        original.action_submit()
        filed = original.submitted_attachment_id
        with self.assertRaises(UserError):
            original.month = "4"
        original.action_reset_to_draft()
        original.month = "4"
        self.assertEqual(original.submitted_attachment_id, filed)
        self.assertIn(filed, original.filed_history_ids)

    def test_regular_cannot_replace_a_filing(self):
        from odoo.exceptions import UserError

        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()
        report = self._vpp()
        report.replaced_vpp_id = original
        with self.assertRaises(UserError):
            report.action_generate()

    def test_corrective_prefills_unique_original_for_api_create_and_write(self):
        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()
        correction = self._vpp()
        correction.correction_type = "corrective"
        self.assertEqual(correction.replaced_vpp_id, original)
        direct = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create(
                {
                    "company_id": self.company.id,
                    "year": original.year,
                    "month": original.month,
                    "correction_type": "corrective",
                }
            )
        )
        self.assertEqual(direct.replaced_vpp_id, original)

    def test_corrective_prefills_unique_original_in_unsaved_form(self):
        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()
        form = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .new(
                {
                    "company_id": self.company.id,
                    "year": original.year,
                    "month": original.month,
                    "correction_type": "corrective",
                }
            )
        )
        form._onchange_replaced_vpp()
        self.assertEqual(form.replaced_vpp_id, original)
        form.correction_type = "regular"
        form._onchange_replaced_vpp()
        self.assertFalse(form.replaced_vpp_id)

    def test_prefill_never_guesses_between_multiple_filed_candidates(self):
        self._dohodar_payslip()
        for _index in range(2):
            original = self._vpp()
            original.action_generate()
            original.action_submit()
        correction = self._vpp()
        correction.correction_type = "corrective"
        self.assertFalse(correction.replaced_vpp_id)
        correction.replaced_vpp_id = original
        correction.action_generate()

    def test_prefill_respects_period_and_explicit_missing_link(self):
        self._dohodar_payslip()
        original = self._vpp()
        original.action_generate()
        original.action_submit()
        correction = self._vpp()
        correction.write({"month": "4", "correction_type": "corrective"})
        self.assertFalse(correction.replaced_vpp_id)
        correction.month = original.month
        self.assertEqual(correction.replaced_vpp_id, original)
        explicit = (
            self.env["l10n.sk.vpp"]
            .with_company(self.company)
            .create(
                {
                    "company_id": self.company.id,
                    "year": original.year,
                    "month": original.month,
                    "correction_type": "corrective",
                    "replaced_vpp_id": False,
                }
            )
        )
        self.assertFalse(explicit.replaced_vpp_id)


@tagged("post_install", "-at_install")
class TestSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copies are CURRENT — nothing local can answer that,
    and a schema revised in place by the authority validates exactly as
    before. What this checks is that the bundled bytes are the ones recorded
    in SCHEMA_VERSION, and that no schema sits in data/ unpinned.
    """

    @staticmethod
    def _data_dir():
        import os

        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(here, "data")

    def _pins(self):
        import os

        pins = {}
        path = os.path.join(self._data_dir(), "SCHEMA_VERSION")
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if (
                    len(parts) == 3
                    and parts[0].endswith(".xsd")
                    and "/" not in parts[0]
                ):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os

        pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(self._data_dir(), name)
            self.assertTrue(os.path.exists(path), "%s is pinned but missing" % name)
            with open(path, "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(),
                digest,
                "%s does not match its pin — if this is a deliberate "
                "refresh, update data/SCHEMA_VERSION" % name,
            )

    def test_every_bundled_schema_is_pinned(self):
        import os

        on_disk = {f for f in os.listdir(self._data_dir()) if f.endswith(".xsd")}
        self.assertEqual(
            on_disk,
            set(self._pins()),
            "unpinned schema(s): %s" % sorted(on_disk - set(self._pins())),
        )
