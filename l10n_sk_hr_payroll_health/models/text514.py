# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Published 2023+ TXT output through the common declaration lifecycle."""

from decimal import Decimal

from odoo import _, fields, models
from odoo.exceptions import UserError

from .. import text514 as wire
from .l10n_sk_health import INSURER_CODE_4


class HealthText514(models.Model):
    _inherit = "l10n.sk.health"

    # Keep existing API callers' XML choice. The menu explicitly opens the
    # published text format; the selected format is retained on each filing.
    export_format = fields.Selection(
        [("xml", "Legacy XML"), ("text2023", "Published 514 text (2023+)")],
        default="xml",
        required=True,
        help="The text layout is pinned to the insurer-published 2023 interface. "
        "Legacy XML is only structurally checked, not authority-XSD validated.",
    )
    batch_sequence = fields.Integer(string="Batch sequence", default=1)
    sending_date = fields.Date(string="Sending date", default=fields.Date.context_today)
    text_payer_number = fields.Char(
        string="Payer number at selected insurer",
        default=lambda self: self.env.company.l10n_sk_health_payer_number,
    )
    registered_count = fields.Integer(
        string="Registered at this insurer",
        default=-1,
        help="Reviewed registration count, including employees with no premium for a whole-month benefit period.",
    )
    registered_all_insurers_count = fields.Integer(
        string="Registered at all insurers", default=-1
    )
    payer_legal_form = fields.Selection(
        [("PO", "Legal entity"), ("FO", "Natural person")], default="PO"
    )
    payment_bank_id = fields.Many2one(
        "res.partner.bank", string="Employer payment bank account"
    )
    employer_partner_id = fields.Many2one(related="company_id.partner_id")

    _supported_correction_types = ("regular", "corrective")

    def _health_payer_number(self):
        if self.export_format == "text2023":
            return self.text_payer_number
        return super()._health_payer_number()

    def write(self, vals):
        inputs = {
            "export_format",
            "batch_sequence",
            "sending_date",
            "text_payer_number",
            "registered_count",
            "registered_all_insurers_count",
            "payer_legal_form",
            "payment_bank_id",
            "company_id",
            "insurer_code",
            "year",
            "month",
            "payment_date",
            "version_id",
            "correction_type",
        }
        if inputs.intersection(vals) and any(
            rec.state != "draft" and rec.export_format == "text2023" for rec in self
        ):
            raise UserError(
                _(
                    "Reset the text declaration to draft before changing its inputs; the filed copy is preserved."
                )
            )
        return super().write(vals)

    def _text514_rows(self, data):
        rows = []
        insured_identifiers = set()
        for employee, bucket in sorted(
            data["per_employee"].items(), key=lambda item: item[0].id
        ):
            slips = bucket["payslips"]
            if len(slips) != 1:
                raise UserError(
                    _(
                        "This health statement needs one consolidated payroll source per employee. Review the payroll correction sources."
                    )
                )
            slip = slips[0]
            if slip.date_from < self.date_from or slip.date_to > self.date_to:
                raise UserError(
                    _(
                        "Allocate the health payroll source to its calendar month before generating text 514."
                    )
                )
            getter = getattr(slip, "_l10n_sk_health_assessment_facts", None)
            if getter is None:
                raise UserError(
                    _(
                        "The installed payroll engine has no retained health-assessment adapter for the text 514."
                    )
                )
            facts = getter()
            if facts["birth_number"] in insured_identifiers:
                raise UserError(
                    _(
                        "Consolidate health payroll sources sharing one insured-person identifier before generating this statement."
                    )
                )
            insured_identifiers.add(facts["birth_number"])
            current_calendar = self.env["l10n.sk.health.calendar"].search(
                [
                    ("company_id", "=", slip.company_id.id),
                    ("employee_id", "=", employee.id),
                    ("month", "=", slip.date_from.replace(day=1)),
                    ("state", "!=", "superseded"),
                ]
            )
            retained_id = facts.get("calendar_id")
            if (
                current_calendar
                and (
                    current_calendar.id != retained_id
                    or current_calendar.state != "reviewed"
                )
            ) or (retained_id and not current_calendar):
                raise UserError(
                    _(
                        "The health calendar changed after payroll calculation. Review the payroll correction before generating a new statement."
                    )
                )
            if facts["insurer"] != self.insurer_code:
                raise UserError(
                    _("The retained health insurer does not match this statement.")
                )
            if facts["exempt"]:
                raise UserError(
                    _(
                        "An exempt health-income source must not be included in this statement."
                    )
                )
            assessed = any(
                Decimal(str(facts[key])) != 0
                for key in ("income", "employee", "employer", "topup", "op")
            )
            rows.append(
                {
                    "employee_id": employee.id,
                    "birth_number": facts["birth_number"],
                    "days": facts["insured_days"] if assessed else 0,
                    "disabled": facts["disabled"],
                    "premium_assessed": assessed,
                    "rate_employer": facts["rate_employer"],
                    "rate_employee": facts["rate_employee"],
                    "income": facts["income"],
                    "base": facts["base"],
                    "employer": facts["employer"],
                    "employee": facts["employee"],
                    "topup": facts["topup"],
                    "total": sum(
                        Decimal(str(facts[key]))
                        for key in ("employee", "employer", "topup")
                    ),
                    "op_income": facts["op_income"],
                    "other_income": facts["other_income"],
                    "op": facts["op"],
                    "exempt_income": 0,
                    "shorttime_base": None,
                    "minimum_opt_out": facts["minimum_opt_out"],
                }
            )
        return rows

    def _text514_payload(self, data):
        self.ensure_one()
        if self.correction_type not in ("regular", "corrective"):
            raise UserError(
                _(
                    "The text adapter supports full original and corrective filings; additive differences require their own reviewed source."
                )
            )
        if (
            self.registered_count < 0
            or self.registered_all_insurers_count < self.registered_count
        ):
            raise UserError(
                _(
                    "Enter the reviewed health-registration counts for this insurer and for all insurers."
                )
            )
        if not self.sending_date or not self.payment_date:
            raise UserError(
                _("Set the sending date and payment date before generating text 514.")
            )
        if (
            not self.payment_bank_id
            or self.payment_bank_id.partner_id != self.company_id.partner_id
            or (
                self.payment_bank_id.company_id
                and self.payment_bank_id.company_id != self.company_id
            )
        ):
            raise UserError(
                _("Select a bank account belonging to the payroll employer.")
            )
        rows = self._text514_rows(data)
        company = self.company_id
        ident = {
            "characteristic": "O" if self.correction_type == "corrective" else "N",
            "ico": self._company_ico(company),
            "payer": self.text_payer_number,
            "insurer": INSURER_CODE_4[self.insurer_code],
            "sent_on": str(self.sending_date),
            "sequence": self.batch_sequence,
        }
        employer = {
            "period": "%04d%02d" % (int(self.year), int(self.month)),
            "payment_day": self.payment_date.day,
            "name": company.name,
            "dic": self._digits(company.l10n_sk_dic),
            "iban": (self.payment_bank_id.acc_number or "").replace(" ", ""),
            "legal_form": self.payer_legal_form,
        }
        summary = wire.aggregate(
            rows, self.registered_count, self.registered_all_insurers_count
        )
        return ident, employer, summary, rows

    def _prepare_employee_declarations(self, data):
        result = super()._prepare_employee_declarations(data)
        if self.export_format == "text2023":
            facts = {row["employee_id"]: row for row in self._text514_rows(data)}
            for line in self._sheet_lines():
                row = facts[line.employee_id.id]
                line.write({"vz_base": float(row["base"]), "insured_days": row["days"]})
        return result

    def _render_xml(self, data):
        if self.export_format != "text2023":
            return super()._render_xml(data)
        try:
            return wire.render(*self._text514_payload(data))
        except (ValueError, KeyError) as exc:
            raise UserError(
                _("The 514 text fields failed validation: %s", str(exc))
            ) from exc

    def _validate_against_schema(self, content):
        if self.export_format != "text2023":
            return super()._validate_against_schema(content)
        # The codec validates the published field lengths, dates, identities,
        # precision and totals before serialization. This stage checks the
        # actual emitted record framing, rather than pretending TXT is XSD.
        records = content.decode("utf-8").split("\r\n")
        if records[-1] != "" or len(records) < 4:
            raise UserError(_("The 514 text record framing is invalid."))
        records = records[:-1]
        if any(not row.endswith("|") for row in records):
            raise UserError(_("The 514 text record framing is invalid."))
        lengths = [len(row.split("|")) - 1 for row in records]
        if lengths[:3] != [10, 13, 20] or any(length != 17 for length in lengths[3:]):
            raise UserError(_("The 514 text record framing is invalid."))
        if records[0].split("|")[7] != str(len(records) - 3):
            raise UserError(_("The 514 text employee count is invalid."))
        return True

    def _declaration_attachment_metadata(self):
        if self.export_format != "text2023":
            return super()._declaration_attachment_metadata()
        characteristic = "O" if self.correction_type == "corrective" else "N"
        return {
            "name": wire.filename(
                characteristic,
                "%04d%02d" % (int(self.year), int(self.month)),
                self.batch_sequence,
            ),
            "mimetype": "text/plain",
        }

    def _declaration_generated_message(self):
        if self.export_format == "text2023":
            return _(
                "Declaration generated in the published 514 text layout; field and total checks passed."
            )
        return _(
            "Legacy 514 XML generated and structurally checked; authority XSD acceptance is not established."
        )
