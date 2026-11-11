# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The declaration-facing protocol; no engine or country storage dependency."""

from decimal import Decimal

from odoo import _, fields, models
from odoo.exceptions import UserError


class DeclarationFundBases(models.AbstractModel):
    _inherit = "cssk.payroll.declaration.mixin"

    fund_bases_warning = fields.Text(
        string="Unrecorded fund bases",
        readonly=True,
        copy=False,
        help="Payslips for which this original declaration used the legacy gross-based fallback.",
    )

    def _payslip_fund_bases(self, slip):
        """Convenience singular reader; the batch protocol owns adapter access."""
        slip.ensure_one()
        records, _missing = self._payslip_fund_records(slip)
        return records[slip.id]

    def _payslip_fund_records(self, slips):
        """Return records by payslip ID and the payslips without any records.

        An installed bridge implements ``_cssk_recorded_fund_bases`` and owns
        its identity, salary and shape validation. Missing or inconsistent
        evidence is False: originals warn and corrections refuse. Access
        failures must still propagate. Recorded zero is not missing evidence.
        """
        result, missing = {}, slips.browse()
        for slip in slips:
            slip.check_access("read")
            reader = getattr(slip, "_cssk_recorded_fund_bases", None)
            records = reader() if reader else False
            result[slip.id] = records or False
            if not records:
                missing |= slip
        return result, missing

    def _collect_payslip_fund_bases(self, slips, *, required=None):
        """The framework owns original/corrective missing-evidence policy.

        Originals, including historical ELDP, warn and retain their existing
        fallback. Corrections require complete evidence, including when stored
        evidence has become inconsistent with an edited source.
        No gross calculation is invented here: country reports own it.
        ``required`` may select specific fund keys; None adds no requirement
        beyond the bridge's complete-record validation.
        """
        self.ensure_one()
        result, missing = {}, slips.browse()
        if any(slip.company_id != self.company_id for slip in slips):
            raise UserError(_("Use payslips from the declaration company."))
        recorded, _without_records = self._payslip_fund_records(slips)
        for slip in slips:
            if slip.company_id != self.company_id:
                raise UserError(_("Use payslips from the declaration company."))
            records = recorded[slip.id]
            keys = {(row["fund"], row["side"]) for row in records or []}
            needed = required(slip, records) if callable(required) else required
            if not records or (needed is not None and not set(needed).issubset(keys)):
                missing |= slip
                result[slip.id] = False
            else:
                result[slip.id] = records
        if missing and self.is_correction:
            raise UserError(
                _(
                    "Precise recorded fund bases are required for this declaration. "
                    "Review the original payroll sources for: %(slips)s",
                    slips=", ".join(missing.mapped("display_name")),
                )
            )
        warning = (
            _(
                "Legacy gross-based fallback was used because recorded fund bases "
                "are missing for: %(slips)s",
                slips=", ".join(missing.mapped("display_name")),
            )
            if missing
            else False
        )
        if self.fund_bases_warning != warning:
            self.fund_bases_warning = warning
            if warning:
                # Plain text goes through mail.thread's escaping. Do not make
                # employee-supplied names into trusted markup.
                self.message_post(body=warning)
        return result

    def _collect_payslip_totals(self, payslips):
        result = super()._collect_payslip_totals(payslips)
        if self._uses_recorded_funds():
            result["recorded_funds"] = self._collect_payslip_fund_bases(payslips)
        return result

    def _uses_recorded_funds(self):
        """Insurance filings, without imposing fund evidence on tax reports."""
        return self._report_code in {"sk_mvp", "sk_vpp", "sk_health", "sk_eldp"}

    def _sum_recorded_fund_bases(self, slips, recorded, mapping):
        """Sum validated records using a wire mapping owned by the country form."""
        if not all(recorded.get(slip.id) for slip in slips):
            return False
        result = {field: Decimal(0) for field in mapping.values()}
        for slip in slips:
            direction_hook = getattr(slip, "_cssk_fund_record_direction", None)
            direction = direction_hook() if direction_hook else 1
            for row in recorded[slip.id]:
                key = row["fund"], row["side"]
                if key in mapping:
                    result[mapping[key]] += direction * Decimal(row["base"])
        return result

    def _effective_fund_payslips(self, slips):
        """Native refund linkage/signs belong to the installed engine bridge."""
        hook = getattr(slips, "_cssk_effective_fund_payslips", None)
        return hook() if hook else slips
