# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Engine-neutral fund evidence; no payroll engine is imported here.

Each bridge owns the JSON/storage fields, inherits this mixin alongside its
native hr.payslip and supplies
_l10n_sk_fund_identity and _l10n_sk_fund_salary_facts;
actual charged bases are supplied by salary rules, never reconstructed here.
Confirmation, source locking and native child-row policies belong to the
engine's lifecycle adapter, not to this abstract protocol.
"""

from odoo import _, models
from odoo.exceptions import UserError

from ..fund_assessment import fund_assessment, index_assessments


class FundEvidenceError(UserError):
    """An unreadable record is missing evidence, not a payroll/ACL failure."""


class PayslipFundMixin(models.AbstractModel):
    _name = "l10n.sk.payslip.fund.mixin"
    _description = "Recorded payroll fund evidence"

    def l10n_sk_fund_record(self, fund, side, base, rate, amount, facts=None):
        """Rule helper returning data only; RPC cannot write generated evidence."""
        self.ensure_one()
        try:
            return fund_assessment(
                fund=fund, side=side, base=base, rate=rate, amount=amount, facts=facts
            )
        except ValueError:
            return False  # Optional metadata must not stop native payroll.

    def _l10n_sk_checked_fund_assessment(self):
        self.ensure_one()
        evidence = self.l10n_sk_fund_assessment
        if not evidence or evidence.get("schema") != 1 or not evidence.get("complete"):
            raise FundEvidenceError(
                _(
                    "Recalculate the unconfirmed payslip to record its payroll fund bases."
                )
            )
        if (
            evidence.get("identity") != self._l10n_sk_fund_identity()
            or evidence.get("salary") != self._l10n_sk_fund_salary_facts()
        ):
            raise FundEvidenceError(
                _("The recorded payroll fund bases no longer match the payslip.")
            )
        try:
            records = index_assessments(evidence["records"])
        except (ValueError, KeyError) as error:
            raise FundEvidenceError(
                _("The recorded payroll fund bases are invalid.")
            ) from error
        return list(records.values())
