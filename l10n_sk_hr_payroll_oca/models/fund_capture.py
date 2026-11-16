# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Capture actual rule values without changing native payroll arithmetic.

The engine-free parts (capability, finalisation, evidence, guard, reader
skeleton) live in l10n_sk_hr_payroll_base; this bridge keeps the OCA capture
hooks, the stored field, refund pairing and the payslip identity.
"""

from odoo import _, api, fields, models

from odoo.addons.l10n_sk_hr_payroll_base.fund_capture import (
    CAPTURE_KEY,
    _FundCapture,
    finalize_fund_rows,
)
from odoo.addons.l10n_sk_hr_payroll_base.models.payslip_fund_mixin import (
    FundEvidenceError,
)

#: The OCA engine's separate health minimum rule.
TOPUP_CODE = "HEALTHDOPLATOK"


class FundCapturePayslip(models.Model):
    _name = "hr.payslip"
    _inherit = ["hr.payslip", "l10n.sk.payslip.fund.mixin"]

    l10n_sk_fund_assessment = fields.Json(
        string="Recorded payroll fund bases",
        readonly=True,
        copy=False,
    )

    @api.model_create_multi
    def create(self, values_list):
        self._l10n_sk_check_fund_evidence_values(values_list)
        return super().create(values_list)

    def write(self, values):
        self._l10n_sk_check_fund_evidence_values([values])
        return super().write(values)

    def _l10n_sk_can_record_funds(self):
        """Unsupported metadata must never prevent the native calculation."""
        self.ensure_one()
        if (
            not self.date_from
            or not self.date_to
            or (self.date_from.year, self.date_from.month)
            != (self.date_to.year, self.date_to.month)
        ):
            return False
        # Exactly the contracts get_lines_dict() computes over: a contract_id
        # outside the period computes nothing, so it is not supported either.
        version = self._get_employee_contracts()
        return bool(
            len(version) == 1
            and version.employee_id == self.employee_id
            and version.company_id == self.company_id
        )

    def _l10n_sk_fund_identity(self):
        self.ensure_one()
        return {
            "company": self.company_id.id,
            "employee": self.employee_id.id,
            "contract": self.contract_id.id,
            "from": str(self.date_from),
            "to": str(self.date_to),
            "structure": self.struct_id.id,
            "credit_note": self.credit_note,
        }

    def _l10n_sk_computed_contract(self):
        """The one contract the stored lines were computed on, or empty.

        Read from the payslip lines, which is stored data and does not follow
        later changes of the employee's contracts the way a fresh fallback
        would. Where ``contract_id`` is set it must be that contract.
        """
        self.ensure_one()
        contracts = self.line_ids.contract_id
        if len(contracts) != 1 or (self.contract_id and contracts != self.contract_id):
            return contracts.browse()
        return contracts

    def _l10n_sk_checked_fund_assessment(self):
        # The identity names contract_id, which an API-created payslip leaves
        # empty; the profile describes the version actually computed on. Tie
        # the two: the profile must describe the contract of the lines.
        records = super()._l10n_sk_checked_fund_assessment()
        profile = self.l10n_sk_fund_assessment.get("profile") or {}
        computed = self._l10n_sk_computed_contract()
        if not computed or profile.get("version") != computed.id:
            raise FundEvidenceError(
                _("The recorded payroll fund bases no longer match the payslip.")
            )
        return records

    def _get_baselocaldict(self, contracts):
        result = super()._get_baselocaldict(contracts)
        if self._l10n_sk_is_recording_funds():
            result["l10n_sk_fund_records"] = []
        return result

    def _compute_payslip_line(self, rule, localdict, lines_dict):
        localdict.pop("l10n_sk_fund_record", None)
        result, lines = super()._compute_payslip_line(rule, localdict, lines_dict)
        if not self._l10n_sk_is_recording_funds():
            return result, lines
        entries = result.get("l10n_sk_fund_records")
        if entries is None:
            return result, lines
        record = result.pop("l10n_sk_fund_record", None)
        # The native total as this rule left it; finalisation compares it.
        native = result["result_rules"].dict.get(rule.code)
        native_total = native.total if record is not None and native else None
        entries.append((rule.code, record, native_total))
        return result, lines

    def localdict_hook(self, localdict):
        result = super().localdict_hook(localdict)
        if not self._l10n_sk_is_recording_funds():
            return result
        capture = self.env.context[CAPTURE_KEY]
        entries = result.get("l10n_sk_fund_records")
        if entries is None:
            capture.rows[self.id] = False
            return result
        rules = result["result_rules"].dict
        capture.rows[self.id] = finalize_fund_rows(
            entries,
            compare_amounts=self.company_id.currency_id.compare_amounts,
            topup=rules[TOPUP_CODE].total if TOPUP_CODE in rules else None,
        )
        return result

    def compute_sheet(self):
        capture = _FundCapture(
            self.filtered(lambda slip: slip._l10n_sk_can_record_funds()).ids
        )
        recording = self.with_context(**{CAPTURE_KEY: capture})
        with self.env.cr.savepoint():
            recording._l10n_sk_store_fund_evidence(False)
            result = super(FundCapturePayslip, recording).compute_sheet()
            recording._l10n_sk_store_captured_funds(capture)
            return result

    def _l10n_sk_refund_original(self):
        self.ensure_one()
        if not self.credit_note:
            return self.browse()
        original = self.search([("refunded_id", "=", self.id)])
        if len(original) != 1 or original.state not in {"done", "cancel"}:
            return self.browse()
        names = (
            "company_id",
            "employee_id",
            "contract_id",
            "date_from",
            "date_to",
            "struct_id",
        )
        if any(self[name] != original[name] for name in names) or (
            self._l10n_sk_fund_salary_facts() != original._l10n_sk_fund_salary_facts()
        ):
            return self.browse()
        return original

    def _cssk_recorded_fund_bases(self):
        return self._l10n_sk_read_recorded_fund_bases()

    def _cssk_effective_fund_payslips(self):
        removed = self.browse()
        for refund in self.filtered("credit_note"):
            original = refund._l10n_sk_refund_original()
            if original and original in self:
                removed |= original | refund
        return self - removed

    def _cssk_fund_record_direction(self):
        """OCA uses positive copied lines and a native credit-note direction."""
        self.ensure_one()
        return -1 if self.credit_note else 1
