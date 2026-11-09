# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The confirmed-state literals must exist in the engine they belong to.

A state literal that matches nothing raises nothing: a domain on a state the
selection does not have silently finds no payslip, and a declaration built on
it reports zero. So every literal is checked against the live selection of
the engine that is installed.
"""
from odoo.tests import TransactionCase, tagged

from ..models.hr_payroll_declaration import CONFIRMED_PAYSLIP_STATES


@tagged("post_install", "-at_install")
class TestPayslipStates(TransactionCase):

    def _selection(self):
        field = self.env["hr.payslip"]._fields["state"]
        return {value for value, _label in
                field._description_selection(self.env)}

    def setUp(self):
        super().setUp()
        if "hr.payslip" not in self.env:
            self.skipTest("no payroll engine installed")

    def _engine(self):
        # OCA ``payroll`` has the ``verify`` (Waiting) step; Enterprise not.
        return "oca" if "verify" in self._selection() else "ee"

    def test_every_literal_exists_in_its_engine(self):
        selection = self._selection()
        for state in CONFIRMED_PAYSLIP_STATES[self._engine()]:
            self.assertIn(state, selection, "payslip state %r does not exist"
                          % state)

    def test_only_confirmed_states_are_reported(self):
        mixin = self.env["cssk.payroll.declaration.mixin"]
        states = set(mixin._payslip_states())
        self.assertEqual(states, set(CONFIRMED_PAYSLIP_STATES[self._engine()]))
        self.assertFalse(states & {"draft", "verify", "cancel"})
        domain = mixin._payslip_period_domain(
            self.env.company, "2025-01-01", "2025-01-31")
        state_leaves = [leaf for leaf in domain if leaf[0] == "state"]
        self.assertEqual(len(state_leaves), 1)
        self.assertEqual(state_leaves[0][1], "in")
        self.assertEqual(set(state_leaves[0][2]), states)
