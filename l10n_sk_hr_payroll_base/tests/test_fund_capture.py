# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The engine-neutral finalisation both payroll bridges store."""

from odoo.tests import BaseCase, tagged

from ..fund_assessment import fund_assessment
from ..fund_capture import (
    FUND_RULE_CODES,
    _FundCapture,
    finalize_fund_rows,
    may_write_evidence,
    writer_context,
)


def _compare(value1, value2):
    """A currency's compare_amounts at two decimals."""
    delta = round(value1, 2) - round(value2, 2)
    return 0 if abs(delta) < 0.005 else (1 if delta > 0 else -1)


def _record(fund, side, base, rate, amount, code):
    return fund_assessment(
        fund=fund, side=side, base=base, rate=rate, amount=amount,
        facts={"rule_code": code},
    )


@tagged("post_install", "-at_install")
class TestFinalizeFundRows(BaseCase):
    def finalize(self, entries, topup=None):
        return finalize_fund_rows(entries, compare_amounts=_compare, topup=topup)

    def health(self, amount=25.0, total=-25.0):
        return (
            "HEALTH",
            _record("health", "employee", 500, 5, amount, "HEALTH"),
            total,
        )

    def test_employee_side_is_stored_positive_against_a_negative_line(self):
        rows = self.finalize([
            ("SICK", _record("sickness", "employee", 500, 1.4, 7, "SICK"), -7.0),
            ("SICKEMPLOYER", _record("sickness", "employer", 500, 1.4, 7,
                                     "SICKEMPLOYER"), 7.0),
        ])
        self.assertEqual(
            [(row["fund"], row["side"], row["amount"]) for row in rows],
            [("sickness", "employee", "7"), ("sickness", "employer", "7")],
        )

    def test_signed_negative_base_and_charge_are_kept(self):
        rows = self.finalize([
            ("ACCIDENT", _record("accident", "employer", -500.246, 0.8, -4.01,
                                 "ACCIDENT"), -4.01),
        ])
        self.assertEqual((rows[0]["base"], rows[0]["amount"]), ("-500.246", "-4.01"))

    def test_fund_rule_without_a_record_is_missing(self):
        self.assertFalse(self.finalize([self.health(), ("SICK", None, -7.0)]))

    def test_other_rules_without_a_record_are_ignored(self):
        self.assertTrue(self.finalize([self.health(), ("NET", None, 400.0)]))

    def test_every_fund_rule_code_is_required(self):
        self.assertEqual(
            FUND_RULE_CODES,
            {
                "SICK", "PENSION", "DISABILITY", "UNEMPLOYMENT",
                "SICKEMPLOYER", "PENSIONEMPLOYER", "DISABILITYEMPLOYER",
                "UNEMPLOYMENTEMPLOYER", "SHORTTIMEEMPLOYER", "GUARANTEEEMPLOYER",
                "ACCIDENT", "RESERVEFUNDEMPLOYER", "HEALTH", "HEALTHEMPLOYER",
            },
        )

    def test_record_without_a_line_is_missing(self):
        self.assertFalse(self.finalize([self.health(total=None)]))

    def test_charge_different_from_the_native_line_is_missing(self):
        self.assertFalse(self.finalize([self.health(total=-50.0)]))

    def test_sub_cent_difference_within_currency_rounding_is_accepted(self):
        self.assertTrue(self.finalize([self.health(amount=25.001, total=-25.0)]))

    def test_invalid_record_is_missing(self):
        self.assertFalse(
            self.finalize([self.health(), ("SICK", {"invalid": True}, -7.0)])
        )

    def test_duplicate_fund_and_side_is_missing(self):
        self.assertFalse(self.finalize([self.health(), self.health()]))

    def test_nothing_recorded_is_missing(self):
        self.assertFalse(self.finalize([]))
        self.assertFalse(self.finalize([("NET", None, 400.0)]))

    def test_recorded_zero_is_not_missing(self):
        rows = self.finalize([
            ("GUARANTEEEMPLOYER", _record("guarantee", "employer", 0, 0.25, 0,
                                          "GUARANTEEEMPLOYER"), 0.0),
        ])
        self.assertEqual((rows[0]["base"], rows[0]["amount"]), ("0", "0"))

    def test_topup_adds_a_charge_not_a_base(self):
        rows = self.finalize([self.health()], topup=-3.5)
        self.assertEqual(
            (rows[0]["base"], rows[0]["amount"], rows[0]["facts"]),
            ("500", "28.5", {"rule_code": "HEALTH", "topup": 3.5}),
        )

    def test_topup_keeps_the_row_order(self):
        employer = ("HEALTHEMPLOYER",
                    _record("health", "employer", 500, 11, 55, "HEALTHEMPLOYER"),
                    55.0)
        rows = self.finalize([self.health(), employer], topup=-1.0)
        self.assertEqual([row["side"] for row in rows], ["employee", "employer"])

    def test_topup_without_an_employee_health_row_is_missing(self):
        # The top-up charges the employee health row; without one the charge
        # would be dropped from the stored evidence, so nothing is stored.
        employer = ("HEALTHEMPLOYER",
                    _record("health", "employer", 500, 11, 55, "HEALTHEMPLOYER"),
                    55.0)
        sick = ("SICK", _record("sickness", "employee", 500, 1.4, 7, "SICK"), -7.0)
        for topup in (-3.5, 0.0):
            with self.subTest(topup=topup):
                self.assertFalse(self.finalize([employer, sick], topup=topup))
        self.assertTrue(self.finalize([employer, sick]))

    def test_topup_after_an_unusable_health_record_is_missing(self):
        self.assertFalse(self.finalize([self.health(total=-50.0)], topup=-3.5))

    def test_no_topup_rule_leaves_the_row_untouched(self):
        rows = self.finalize([self.health()])
        self.assertEqual(rows[0]["facts"], {"rule_code": "HEALTH"})

    def test_custom_fund_codes(self):
        entries = [self.health(), ("CUSTOM", None, 1.0)]
        self.assertTrue(self.finalize(entries))
        self.assertFalse(
            finalize_fund_rows(entries, compare_amounts=_compare,
                               fund_codes={"CUSTOM"})
        )


@tagged("post_install", "-at_install")
class TestFundCaptureCapability(BaseCase):
    def test_capability_starts_empty(self):
        capture = _FundCapture([3, 4, 3])
        self.assertEqual(capture.supported, {3, 4})
        self.assertEqual(
            (capture.rows, capture.localdicts, capture.emissions), ({}, {}, {})
        )

    def test_writer_context_is_not_forgeable_by_value(self):
        self.assertTrue(may_write_evidence(writer_context()))
        key = next(iter(writer_context()))
        for forged in (True, "1", object(), {}):
            self.assertFalse(may_write_evidence({key: forged}))
        self.assertFalse(may_write_evidence({}))
