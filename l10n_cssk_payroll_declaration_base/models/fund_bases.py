# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The declaration-facing protocol; no engine or country storage dependency."""

from decimal import Decimal
import hashlib
import json

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class DeclarationFundBases(models.AbstractModel):
    _inherit = "cssk.payroll.declaration.mixin"

    _fund_confirmation_fields = frozenset(
        {
            "fund_bases_confirmed_by",
            "fund_bases_confirmed_at",
            "fund_bases_confirmation_digest",
        }
    )

    fund_bases_fallback_reason = fields.Text(
        string="Reason for using the original gross-based calculation",
        copy=False,
        help="Explain the reviewed correction of older payroll without recorded fund bases. Confirm it before generating the correction; do not recalculate filed payroll to create historical evidence.",
    )
    fund_bases_confirmed_by = fields.Many2one(
        "res.users", string="Legacy calculation confirmed by", readonly=True, copy=False
    )
    fund_bases_confirmed_at = fields.Datetime(
        string="Legacy calculation confirmed on", readonly=True, copy=False
    )
    fund_bases_confirmation_digest = fields.Char(
        string="Reviewed payroll sources", readonly=True, copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any(
            self.env.context.get("default_" + name)
            for name in self._fund_confirmation_fields
        ) or any(
            values.get(name)
            for values in vals_list
            for name in self._fund_confirmation_fields
        ):
            raise UserError(
                _("Confirm legacy fund calculations through the declaration action.")
            )
        return super().create(vals_list)

    def write(self, values):
        if self._fund_confirmation_fields.intersection(values):
            raise UserError(
                _("Confirm legacy fund calculations through the declaration action.")
            )
        if "fund_bases_fallback_reason" in values and any(
            (record.fund_bases_fallback_reason or "")
            != (values["fund_bases_fallback_reason"] or "")
            for record in self
        ):
            if any(record.state != "draft" for record in self):
                raise UserError(
                    _(
                        "Reset the declaration to draft before changing the legacy calculation reason."
                    )
                )
            values = dict(
                values, **{name: False for name in self._fund_confirmation_fields}
            )
        return super().write(values)

    def _legacy_fund_report_inputs(self):
        """Editable filing inputs, including the form's original-filing link."""
        self.ensure_one()
        names = [
            name
            for name, field in self._fields.items()
            if field.store
            and not field.readonly
            and not field.compute
            and name not in {"state", "submission_reference"}
            and field.type
            in {
                "boolean",
                "integer",
                "float",
                "monetary",
                "selection",
                "char",
                "date",
                "many2one",
            }
        ]
        if "version_id" in self._fields:
            names.append("version_id")
        return self.read(names, load=None)[0]

    def _fund_fallback_digest(self, slips):
        """Bind consent to this filing and the actual sources, never a context flag."""
        self.ensure_one()
        sources = []
        for slip in slips.sorted("id"):
            slip.check_access("read")
            version = self._payslip_version(slip)
            # A write timestamp alone misses two edits within one second.
            # Include stored scalar source facts, independent of country and
            # engine; translated/display fields are not calculation inputs.
            version_fields = (
                [
                    name
                    for name, field in version._fields.items()
                    if field.store
                    and not field.translate
                    and field.type
                    in {
                        "boolean",
                        "integer",
                        "float",
                        "monetary",
                        "selection",
                        "char",
                        "date",
                        "datetime",
                        "many2one",
                    }
                ]
                if version
                else []
            )
            sources.append(
                {
                    "id": slip.id,
                    "employee": slip.employee_id.id,
                    "company": slip.company_id.id,
                    "from": str(slip.date_from),
                    "to": str(slip.date_to),
                    "version": version.id if version else False,
                    "version_changed": str(version.write_date) if version else False,
                    "version_facts": version.read(version_fields, load=None)[0]
                    if version
                    else False,
                    "salary": sorted(
                        [
                            [
                                line.id,
                                line.code,
                                line.amount,
                                line.quantity,
                                line.rate,
                                line.total,
                            ]
                            for line in slip.line_ids
                        ]
                    ),
                }
            )
        value = {
            "model": self._name,
            "filing_inputs": self._legacy_fund_report_inputs(),
            "company": self.company_id.id,
            "from": str(self.date_from),
            "to": str(self.date_to),
            "kind": self.correction_type,
            "reason": (self.fund_bases_fallback_reason or "").strip(),
            "sources": sources,
        }
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, allow_nan=False, default=str).encode()
        ).hexdigest()

    def _legacy_fund_fallback_is_confirmed(self, slips):
        self.ensure_one()
        return bool(
            self.fund_bases_confirmed_by
            and self.fund_bases_confirmed_at
            and (self.fund_bases_fallback_reason or "").strip()
            and self.fund_bases_confirmation_digest == self._fund_fallback_digest(slips)
        )

    def action_confirm_legacy_fund_bases(self):
        self.check_access("write")
        for record in self:
            if record.company_id not in self.env.companies:
                raise AccessError(
                    _(
                        "Use an allowed company when reviewing the declaration's legacy payroll."
                    )
                )
            if record.state != "draft" or not record.is_correction:
                raise UserError(
                    _(
                        "Confirm the legacy calculation on a draft corrective declaration."
                    )
                )
            reason = (record.fund_bases_fallback_reason or "").strip()
            if not reason:
                raise UserError(
                    _(
                        "Record the reviewed reason for using the original gross-based calculation."
                    )
                )
            slips = record._get_period_payslips()
            _records, missing = record._payslip_fund_records(slips)
            if not missing:
                raise UserError(
                    _(
                        "There are no payroll sources without recorded fund bases to confirm."
                    )
                )
            if (
                record.fund_bases_confirmed_by == self.env.user
                and record._legacy_fund_fallback_is_confirmed(slips)
            ):
                continue
            moment = fields.Datetime.now()
            # The action owns the audit fields; the ordinary write chain of
            # every other mixin still runs. RPC cannot supply this confirmation.
            super(DeclarationFundBases, record).write(
                {
                    "fund_bases_confirmed_by": self.env.user.id,
                    "fund_bases_confirmed_at": moment,
                    "fund_bases_confirmation_digest": record._fund_fallback_digest(
                        slips
                    ),
                }
            )
            record.message_post(
                body=_(
                    "Legacy gross-based calculation confirmed by %(user)s at %(when)s for %(slips)s. Reason: %(reason)s",
                    user=self.env.user.display_name,
                    when=str(moment),
                    slips=", ".join(missing.mapped("display_name")),
                    reason=reason,
                )
            )
        return True

    fund_bases_warning = fields.Text(
        string="Unrecorded fund bases",
        readonly=True,
        copy=False,
        help="Payslips for which the declaration used the original gross-based calculation instead of recorded fund bases.",
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
            records = reader() if callable(reader) else False
            result[slip.id] = records or False
            if callable(reader) and not records:
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
        recorded, _without_records = self._payslip_fund_records(slips)
        for slip in slips:
            if slip.company_id != self.company_id:
                raise UserError(_("Use payslips from the declaration company."))
            records = recorded[slip.id]
            if not callable(getattr(slip, "_cssk_recorded_fund_bases", None)):
                # An engine without a recorder keeps its existing behaviour;
                # its missing implementation is not a missing payslip record.
                result[slip.id] = False
                continue
            keys = {(row["fund"], row["side"]) for row in records or []}
            needed = required(slip, records) if callable(required) else required
            if not records or (needed is not None and not set(needed).issubset(keys)):
                missing |= slip
                result[slip.id] = False
            else:
                result[slip.id] = records
        if (
            missing
            and self.is_correction
            and not self._legacy_fund_fallback_is_confirmed(slips)
        ):
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
