# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from collections import Counter
from copy import deepcopy

from odoo.exceptions import UserError
from odoo.modules.module import Manifest
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools.misc import file_path


@tagged("post_install", "-at_install")
class TestRuleParameterDates(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.parameters = cls.env["hr.rule.parameter"]
        cls.values = cls.env["hr.rule.parameter.value"]
        cls.parameter = cls.parameters.create(
            {"name": "Effective date test", "code": "test_effective_parameter_date"}
        )

    def value(self, amount, date="2027-01-01"):
        return self.values.create(
            {
                "rule_parameter_id": self.parameter.id,
                "date_from": date,
                "parameter_value": amount,
            }
        )

    def lookup(self, date="2027-01-01"):
        return self.parameters._get_parameter_value(self.parameter.code, date)

    def test_missing_parameter_and_missing_effective_value_keep_native_errors(self):
        with self.assertRaisesRegex(UserError, "No salary rule parameter found"):
            self.parameters._get_parameter_value(
                "missing_effective_parameter", "2027-01-01"
            )
        self.value("10", "2027-02-01")
        with self.assertRaisesRegex(UserError, "No value defined for rule parameter"):
            self.lookup()

    def test_effective_date_boundaries_keep_historical_and_future_values_separate(self):
        self.value("10", "2026-01-01")
        self.value("20", "2027-01-01")
        self.value("30", "2028-01-01")
        for date, expected in [
            ("2026-01-01", 10),
            ("2026-12-31", 10),
            ("2027-01-01", 20),
            ("2027-12-31", 20),
            ("2028-01-01", 30),
        ]:
            with self.subTest(date=date):
                self.assertEqual(self.lookup(date), expected)

    def test_matching_legacy_definitions_remain_usable(self):
        original = self.value("50.0")
        original.copy({"parameter_value": "100 / 2"})
        self.assertEqual(self.lookup(), 50.0)
        self.assertIsInstance(self.lookup(), float)

    def test_native_copy_with_conflicting_value_refuses_a_date_tie(self):
        original = self.value("1")
        copied = original.copy({"parameter_value": "2"})
        self.assertEqual(copied.date_from, original.date_from)
        self.assertEqual(copied.rule_parameter_id, original.rule_parameter_id)
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            self.lookup()

    def test_older_conflict_does_not_block_a_later_unambiguous_date(self):
        original = self.value("1", "2026-01-01")
        original.copy({"parameter_value": "2"})
        self.value("3", "2027-01-01")
        self.assertEqual(self.lookup(), 3)
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            self.lookup("2026-12-31")

    def test_nested_definitions_match_independently_of_mapping_order(self):
        original = self.value("{'bands': [(0.19, 100)], 'enabled': True}")
        original.copy({"parameter_value": "{'enabled': True, 'bands': [(0.19, 100)]}"})
        self.assertEqual(self.lookup(), {"bands": [(0.19, 100)], "enabled": True})

    def test_equal_python_numbers_do_not_hide_nested_type_conflicts(self):
        original = self.value("{'value': [1]}")
        original.copy({"parameter_value": "{'value': [True]}"})
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            self.lookup()

    def test_lookup_preserves_original_definition_bytes_and_metadata(self):
        original = self.value("[(0.19, 100), (0.25, 200)]")
        copied = original.copy()
        rows = original | copied
        before = deepcopy(
            rows.read(["parameter_value", "date_from", "write_date", "write_uid"])
        )
        self.assertEqual(self.lookup(), [(0.19, 100), (0.25, 200)])
        rows.invalidate_recordset()
        self.assertEqual(
            rows.read(["parameter_value", "date_from", "write_date", "write_uid"]),
            before,
        )

    def test_readonly_payroll_user_reads_matching_rows_and_refuses_conflicts(self):
        reader = new_test_user(
            self.env,
            login="effective.parameter.reader",
            groups="base.group_user,payroll.group_payroll_user",
        )
        self.assertFalse(reader.has_group("payroll.group_payroll_manager"))
        self.assertFalse(reader.has_group("base.group_system"))
        parameters = self.parameters.with_user(reader)
        values = self.values.with_user(reader)
        self.assertFalse(parameters.has_access("write"))
        self.assertFalse(values.has_access("write"))
        original = self.value("50.0")
        copied = original.copy()
        self.assertEqual(
            parameters._get_parameter_value(self.parameter.code, "2027-01-01"), 50.0
        )
        copied.parameter_value = "60.0"
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            parameters._get_parameter_value(self.parameter.code, "2027-01-01")
        copied.parameter_value = "50.0"
        # Restoring test setup changes write metadata; the reader itself must not.
        before = deepcopy((original | copied).read(["parameter_value", "write_date"]))
        parameters._get_parameter_value(self.parameter.code, "2027-01-01")
        (original | copied).invalidate_recordset()
        self.assertEqual(
            (original | copied).read(["parameter_value", "write_date"]), before
        )

    def test_int_and_float_with_the_same_value_match(self):
        original = self.value("1")
        original.copy({"parameter_value": "1.0"})
        self.assertEqual(self.lookup(), 1)
        self.parameter.parameter_value_ids.unlink()
        original = self.value("{'bands': [(0, 100)]}")
        original.copy({"parameter_value": "{'bands': [(0.0, 100.0)]}"})
        self.assertEqual(self.lookup(), {"bands": [(0, 100)]})

    def test_bool_and_int_with_the_same_value_still_conflict(self):
        original = self.value("1")
        original.copy({"parameter_value": "True"})
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            self.lookup()

    def test_conflict_beyond_the_second_row_of_a_tie_is_found(self):
        # The first query reads two rows; a third definition on the same
        # date must still be compared.
        self.value("4", "2026-01-01")
        original = self.value("5")
        original.copy()
        original.copy({"parameter_value": "6"})
        with self.assertRaisesRegex(
            UserError, "Conflicting salary rule parameter values"
        ):
            self.lookup()
        self.assertEqual(self.lookup("2026-12-31"), 4)


@tagged("post_install", "-at_install")
class TestParameterData(TransactionCase):
    def test_an_xml_id_is_declared_once_in_a_data_file(self):
        # A second record under the same id overwrites the first on load.
        manifest = Manifest.for_addon("l10n_sk_hr_payroll_oca")
        for name in manifest["data"]:
            if not name.endswith(".xml"):
                continue
            with open(file_path(f"l10n_sk_hr_payroll_oca/{name}")) as handle:
                ids = re.findall(r'<record\b[^>]*?\bid="([^"]+)"', handle.read())
            twice = sorted(k for k, n in Counter(ids).items() if n > 1)
            with self.subTest(file=name):
                self.assertEqual(twice, [])

    def test_living_minimum_changes_on_1_july_2024(self):
        # The amount is set each 1 July (§ 5 zákona 601/2003 Z. z.).
        lookup = self.env["hr.rule.parameter"]._get_parameter_value
        self.assertEqual(lookup("l10n_sk_zivotne_minimum", "2024-06-30"), 268.88)
        self.assertEqual(lookup("l10n_sk_zivotne_minimum", "2024-07-01"), 273.99)
        self.assertEqual(lookup("l10n_sk_zivotne_minimum", "2025-06-30"), 273.99)
        self.assertEqual(lookup("l10n_sk_zivotne_minimum", "2025-07-01"), 284.13)
