# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Test helper shared by every declaration module's suite.

Declarations report confirmed payroll only (OCA ``done``, Enterprise
``validated``), so a test that computes a payslip has to confirm it before
generating. Running each engine's real confirmation is slow and drags in
accounting and PDF generation, so the state is written directly — with the
Enterprise ``done_date`` too, which its ``has_wrong_data`` compute compares
against and fails on when left empty.
"""
from datetime import datetime


def confirm_payslips(slips):
    """Put *slips* in the installed engine's first confirmed state."""
    state = slips.env["cssk.payroll.declaration.mixin"]._payslip_states()[0]
    vals = {"state": state}
    if "done_date" in slips._fields:
        vals["done_date"] = datetime.now()
    slips.write(vals)
    return slips
