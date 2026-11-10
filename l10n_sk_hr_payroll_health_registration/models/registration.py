# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""601 is an HR-event declaration, using the common filing/archive pipeline."""

import hashlib
import base64
from datetime import timedelta

from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import file_path

from .. import wire601

MODEL = "l10n.sk.health.registration"
GENERATED = frozenset(
    {
        "state",
        "source_snapshot",
        "source_history",
        "xml_attachment_id",
        "submitted_attachment_id",
        "filed_history_ids",
        "submitted_date",
        "name",
        "report_code",
        "date_from",
        "date_to",
        "country_id",
        "currency_id",
        "batch_year",
    }
)
DOCUMENT = frozenset(
    {
        "company_id",
        "year",
        "month",
        "version_id",
        "event_ids",
        "insurer_code",
        "receiver_ico",
        "payer_number",
        "sending_date",
        "batch_sequence",
        "payment_bank_id",
        "responsible_person",
        "phone",
        "correction_type",
        "correction_reference",
        "amends_id",
        "export_format",
        "legal_form",
    }
)


class HealthRegistration(models.Model):
    _name = MODEL
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "Slovak health-insurance registration batch601"
    _check_company_auto = True
    _report_code = "sk_health_registration"
    _country_code = "SK"
    _supported_correction_types = ("regular", "corrective")
    _order = "sending_date desc, id desc"

    state = fields.Selection(copy=False)
    xml_attachment_id = fields.Many2one(copy=False)
    insurer_code = fields.Selection(
        [("24", "Dôvera"), ("25", "VšZP"), ("27", "Union")], required=True
    )
    receiver_ico = fields.Char(string="Insurer recipient IČO", required=True)
    payer_number = fields.Char(string="Assigned insurer payer number", required=True)
    legal_form = fields.Selection(
        [("FO", "Natural person"), ("PO", "Legal entity")], default="PO", required=True
    )
    sending_date = fields.Date(required=True, default=fields.Date.context_today)
    batch_sequence = fields.Integer(required=True, default=1)
    batch_year = fields.Integer(compute="_compute_batch_year", store=True)
    payment_bank_id = fields.Many2one(
        "res.partner.bank", required=True, check_company=True
    )
    responsible_person = fields.Char(required=True)
    phone = fields.Char(required=True)
    export_format = fields.Selection(
        [("xml", "XML (UTF8)"), ("text", "Text (ISO8859-2)")],
        default="xml",
        required=True,
    )
    amends_id = fields.Many2one(
        MODEL,
        string="Original filed batch",
        check_company=True,
        copy=False,
        ondelete="restrict",
    )
    event_ids = fields.One2many(
        "l10n.sk.health.registration.event", "batch_id", copy=True
    )
    source_snapshot = fields.Json(
        string="Generated registration evidence", readonly=True, copy=False
    )
    source_history = fields.Json(
        string="Filed registration source history", readonly=True, copy=False
    )

    _one_original_sequence = models.UniqueIndex(
        "(company_id, insurer_code, batch_year, batch_sequence) WHERE correction_type = 'regular'",
        "This insurer already has an original batch with this number in the sending year.",
    )

    @api.depends("sending_date")
    def _compute_batch_year(self):
        for row in self:
            row.batch_year = row.sending_date.year if row.sending_date else False

    @api.model_create_multi
    def create(self, vals_list):
        if any("default_" + key in self.env.context for key in GENERATED) or any(
            GENERATED & values.keys() for values in vals_list
        ):
            raise UserError(
                _(
                    "Registration generation and filing evidence is created by the workflow."
                )
            )
        return super().create(vals_list)

    def write(self, values):
        if GENERATED & values.keys():
            raise UserError(
                _(
                    "Registration generation and filing evidence is created by the workflow."
                )
            )
        self._lock_for_change()
        if DOCUMENT & values.keys() and any(row.state != "draft" for row in self):
            raise UserError(
                _("Reset the registration batch to draft before changing its inputs.")
            )
        result = super().write(values)
        self.event_ids._check_scope()
        return result

    def _declaration_write(self, values):
        # Private method: RPC cannot call this, and no public context flag
        # permits a caller to forge generated/filed evidence.
        return super(HealthRegistration, self).write(values)

    def _lock_for_change(self):
        self.check_access("write")
        if self:
            self.flush_recordset()
            self.env.cr.execute(
                "SELECT id FROM l10n_sk_health_registration WHERE id = ANY(%s) "
                "ORDER BY id FOR UPDATE",
                [self.ids],
            )
            self.invalidate_recordset()
            self.check_access("write")

    def _version_reference_date(self):
        # A continuous notice uses the interface on its sending date, even
        # when correcting a historical change from an older calendar month.
        return self.sending_date or super()._version_reference_date()

    def _prior_submitted(self):
        self.ensure_one()
        prior = self.amends_id
        if prior and (
            prior.company_id != self.company_id
            or prior.insurer_code != self.insurer_code
            or prior.state != "submitted"
            or prior == self
        ):
            raise UserError(
                _(
                    "Select a filed batch of this company and insurer as the correction source."
                )
            )
        return prior

    def _preflight(self):
        super()._preflight()
        self.event_ids._check_scope()
        if not self.event_ids:
            raise UserError(
                _("Add the reviewed registration events before generating601.")
            )
        if self.payment_bank_id.partner_id != self.company_id.partner_id:
            raise UserError(
                _("The registration payment bank account must belong to this company.")
            )
        if self.correction_type == "regular" and self.amends_id:
            raise UserError(
                _("A regular registration batch cannot amend a prior filing.")
            )
        return True

    def _declaration_source_data(self):
        company = self.company_id
        data = {
            "ident": {
                "characteristic": "O" if self.is_correction else "N",
                "sender": company.company_registry or "",
                "receiver": self.receiver_ico,
                "insurer": self.insurer_code + "00",
                "sent_on": str(self.sending_date),
                "sequence": self.batch_sequence,
            },
            "payer": {
                "payer": self.payer_number,
                "period": "%04d-%02d" % (int(self.year), int(self.month)),
                "name": company.name,
                "ico": company.company_registry or "",
                "tax_id": company.vat or company.l10n_sk_dic or "",
                "legal_form": self.legal_form,
                "town": company.city or "",
                "street": company.street or "",
                "postcode": company.zip or "",
                "country": company.country_id.code or "",
                "phone": self.phone,
                "responsible_person": self.responsible_person,
                "iban": (self.payment_bank_id.acc_number or "").replace(" ", ""),
            },
            "events": [event._wire_values() for event in self.event_ids.sorted("id")],
            "sources": [
                {
                    "event_id": event.id,
                    "reference": event.source_reference,
                    "calendar_id": event.source_calendar_id.id,
                    "employer_notice_reviewed": event.employer_notice_reviewed,
                }
                for event in self.event_ids.sorted("id")
            ],
        }
        try:
            wire601.records(data["ident"], data["payer"], data["events"])
        except ValueError as exc:
            raise UserError(_("Review the registration inputs: %s", str(exc))) from exc
        if not self.is_correction and self.source_history:
            previous = self.source_history[-1]["payload"]
            if any(data[key] != previous[key] for key in ("ident", "payer", "events")):
                raise UserError(
                    _(
                        "A filed original cannot become a different new filing. Create a new batch or an explicit correction."
                    )
                )
        return data

    def _prepare_employee_declarations(self, data):
        # The event rows are the native source; there is no second payslip
        # or per-employee monetary table for a registration notice.
        return True

    def _render_xml(self, data):
        try:
            renderer = (
                wire601.render_text
                if self.export_format == "text"
                else wire601.render_xml
            )
            result = renderer(data["ident"], data["payer"], data["events"])
        except ValueError as exc:
            raise UserError(_("Review the registration inputs: %s", str(exc))) from exc
        self._declaration_write({"source_snapshot": data})
        return result

    def _validate_against_schema(self, content):
        if self.export_format == "text":
            rows = content.decode("iso8859-2").split("\r\n")
            if rows[-1] != "" or len(rows) < 4:
                raise UserError(_("The601 text framing is invalid."))
            rows = rows[:-1]
            if any(not row.endswith("|") for row in rows):
                raise UserError(_("The601 text framing is invalid."))
            counts = [len(row.split("|")) - 1 for row in rows]
            if counts[:2] != [10, 25] or any(count != 9 for count in counts[2:]):
                raise UserError(_("The601 text framing is invalid."))
            if rows[0].split("|")[7] != str(len(rows) - 2):
                raise UserError(_("The601 event count is invalid."))
            return True
        schema_file = file_path(
            "l10n_sk_hr_payroll_health_registration/schemas/davka601-derived-2026.xsd"
        )
        with open(schema_file, "rb") as stream:
            schema_bytes = stream.read()
        if hashlib.sha256(schema_bytes).hexdigest() != wire601.SCHEMA_SHA256:
            raise UserError(_("The pinned601 validation schema changed unexpectedly."))
        schema = etree.XMLSchema(etree.fromstring(schema_bytes))
        try:
            schema.assertValid(etree.fromstring(content))
        except etree.DocumentInvalid as exc:
            if any(event.code == "2S" for event in self.event_ids):
                raise UserError(
                    _(
                        "The published XML check rejects code2S. Use the601 text format when its charset can represent the names."
                    )
                ) from exc
            raise UserError(
                _("The601 XML does not match its pinned validation interface.")
            ) from exc
        return True

    def _declaration_attachment_metadata(self):
        return {
            "name": wire601.filename(
                self.source_snapshot["ident"], xml=self.export_format == "xml"
            ),
            "mimetype": "application/xml"
            if self.export_format == "xml"
            else "text/plain",
        }

    def _declaration_generated_message(self):
        return _(
            "Registration601 generated and checked. Sending to the insurer is a separate action."
        )

    def action_generate(self):
        self._lock_for_change()
        with self.env.cr.savepoint():
            return super().action_generate()

    def action_submit(self):
        self._lock_for_change()
        for row in self:
            if not row.source_snapshot:
                raise UserError(
                    _("Generate the registration evidence before recording submission.")
                )
            if row._declaration_source_data() != row.source_snapshot:
                raise UserError(
                    _(
                        "The registration source changed. Reset and generate the file again before recording submission."
                    )
                )
            attachment = row.xml_attachment_id
            if attachment.res_model != MODEL or attachment.res_id != row.id:
                raise UserError(
                    _("The generated registration file does not belong to this batch.")
                )
        with self.env.cr.savepoint():
            result = super().action_submit()
            for row in self:
                row._declaration_write(
                    {
                        "source_history": (row.source_history or [])
                        + [
                            {
                                "attachment_id": row.submitted_attachment_id.id,
                                "payload": row.source_snapshot,
                            },
                        ]
                    }
                )
            return result

    def action_reset_to_draft(self):
        self._lock_for_change()
        return super().action_reset_to_draft()

    def unlink(self):
        self._lock_for_change()
        if any(row.filed_history_ids for row in self):
            raise UserError(
                _("A registration batch with filed history must be retained.")
            )
        return super().unlink()


class HealthRegistrationEvent(models.Model):
    _name = "l10n.sk.health.registration.event"
    _description = "Reviewed health-insurance registration event"
    _check_company_auto = True
    _order = "id"

    batch_id = fields.Many2one(
        MODEL, required=True, ondelete="cascade", check_company=True
    )
    company_id = fields.Many2one(related="batch_id.company_id", store=True)
    employee_id = fields.Many2one(
        "hr.employee", required=True, check_company=True, ondelete="restrict"
    )
    source_calendar_id = fields.Many2one(
        "l10n.sk.health.calendar", check_company=True, ondelete="restrict"
    )
    source_reference = fields.Char(required=True)
    employer_notice_reviewed = fields.Boolean(
        string="Employer notice obligation reviewed",
        help="Confirm that this change must be reported by the employer. Facts already communicated by an authority, such as the relevant ePN data, must not be filed again.",
    )
    code = fields.Char(
        required=True,
        help="Reviewed statutory code, such as2,2D,2Y,2N,2P,2S or the relevant1x category.",
    )
    validity = fields.Selection(
        [("Z", "Start"), ("K", "End"), ("X", "Cancel row")], required=True
    )
    changed_on = fields.Date(required=True)
    first_name = fields.Char(required=True)
    last_name = fields.Char(required=True)
    title = fields.Char()
    birth_number = fields.Char()
    insurer_identifier = fields.Char(
        help="BIČ assigned by the authority; never generated by this module."
    )

    @api.onchange("employee_id")
    def _onchange_employee_identity(self):
        for event in self:
            if event.employee_id:
                event.first_name, event.last_name = event.batch_id._split_person_name(
                    event.employee_id
                )
                event.birth_number = (
                    (event.employee_id.identification_id or "")
                    .replace("/", "")
                    .replace(" ", "")
                )
                # Prefill identity only. A name or RC does not establish
                # the employer's notice duty or an assigned BIČ.
                event.insurer_identifier = False
                event.employer_notice_reviewed = False

    @api.constrains("batch_id", "employee_id", "source_calendar_id")
    def _check_scope(self):
        for event in self:
            if event.employee_id.company_id != event.batch_id.company_id:
                raise ValidationError(
                    _(
                        "The registration event and employee must belong to the same company."
                    )
                )
            calendar = event.source_calendar_id
            if calendar and (
                calendar.employee_id != event.employee_id
                or calendar.company_id != event.batch_id.company_id
            ):
                raise ValidationError(
                    _(
                        "The registration calendar must belong to this employee and company."
                    )
                )

    def _wire_values(self):
        self.ensure_one()
        if not (self.source_reference or "").strip():
            raise UserError(
                _("Retain the source reference for each registration event.")
            )
        if not self.employer_notice_reviewed:
            raise UserError(
                _(
                    "Review the employer's notice obligation before including this event."
                )
            )
        # The optional country payroll module owns the dated exemption fact.
        # A later/current HR card must not reclassify a historical notice.
        # K remains valid on the date a worker becomes exempt (VšZP guidance);
        # X must also remain available to cancel an erroneous old registration.
        if self.code == "2D" and self.validity == "Z":
            version = (
                self.env["hr.version"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", self.employee_id.id),
                        ("company_id", "=", self.batch_id.company_id.id),
                        ("date_version", "<=", self.changed_on),
                    ],
                    order="date_version desc, id desc",
                    limit=1,
                )
            )
            # Only consume an existing eligibility fact. HR-only installations
            # still require the explicit employer-notice review above. sudo is
            # limited to this company-scoped boolean; payroll-only fields are
            # not disclosed to the HR user or copied into the notice.
            if (
                version
                and "l10n_sk_health_exempt" in version._fields
                and version.l10n_sk_health_exempt
            ):
                raise UserError(
                    _("Do not start2D coverage for a health-exempt agreement worker.")
                )
        calendar = self.source_calendar_id
        if calendar:
            accepted = (
                {"reviewed", "superseded"} if self.validity == "X" else {"reviewed"}
            )
            if calendar.state not in accepted:
                raise UserError(
                    _("Review the registration event's source calendar first.")
                )
            if self.code in {"2", "2D", "2Y", "2N"}:
                covered = set()
                for span in calendar.interval_ids.filtered(
                    lambda line: line.kind == self.code
                ):
                    covered.update(
                        span.date_start + timedelta(days=n)
                        for n in range((span.date_end - span.date_start).days + 1)
                    )
                change = self.changed_on
                if (
                    change not in covered
                    or self.validity == "Z"
                    and change - timedelta(days=1) in covered
                    or self.validity == "K"
                    and change + timedelta(days=1) in covered
                ):
                    raise UserError(
                        _(
                            "The registration endpoint disagrees with its reviewed calendar source."
                        )
                    )
                if (
                    self.code == "2D"
                    and self.validity != "X"
                    and any(
                        row.kind == "2" and row.date_start <= change <= row.date_end
                        for row in calendar.interval_ids
                    )
                ):
                    raise UserError(
                        _(
                            "Do not report2D while the same employer already records employment on this day."
                        )
                    )
        return {
            "birth_number": self.birth_number or "",
            "insurer_identifier": self.insurer_identifier or "",
            "first_name": self.first_name,
            "last_name": self.last_name,
            "title": self.title or "",
            "code": self.code,
            "validity": self.validity,
            "changed_on": str(self.changed_on),
        }

    def _draft_parents(self, parents):
        parents._lock_for_change()
        if any(row.state != "draft" for row in parents):
            raise UserError(
                _("Reset the registration batch to draft before changing its events.")
            )

    @api.model_create_multi
    def create(self, vals_list):
        default = self.default_get(["batch_id"]).get("batch_id")
        parents = self.env[MODEL].browse(
            [
                v.get("batch_id", default)
                for v in vals_list
                if v.get("batch_id", default)
            ]
        )
        self._draft_parents(parents)
        return super().create(vals_list)

    def write(self, values):
        parents = self.batch_id
        if values.get("batch_id"):
            parents |= self.env[MODEL].browse(values["batch_id"])
        self._draft_parents(parents)
        return super().write(values)

    def unlink(self):
        self._draft_parents(self.batch_id)
        return super().unlink()


class HealthRegistrationAttachment(models.Model):
    _inherit = "ir.attachment"

    def _check_health_registration_archive(self, values=None):
        for attachment in self.filtered(
            lambda row: row.res_model == MODEL and row.res_id
        ):
            batch = self.env[MODEL].browse(attachment.res_id).exists()
            if not batch or not (
                attachment in batch.filed_history_ids
                or attachment == batch.xml_attachment_id
                and batch.state == "generated"
            ):
                continue
            unchanged = values is not None
            if values is not None:
                for key in ("res_model", "res_id", "name", "mimetype", "company_id"):
                    if key in values:
                        current = attachment[key]
                        current = current.id if key == "company_id" else current
                        unchanged = unchanged and values[key] == current
                for key in ("raw", "datas"):
                    if key in values:
                        content = values[key] or b""
                        if isinstance(content, str):
                            content = content.encode()
                        if key == "datas":
                            content = base64.b64decode(content)
                        unchanged = (
                            unchanged
                            and hashlib.sha1(content).hexdigest() == attachment.checksum
                        )
                if {"db_datas", "store_fname"} & values.keys() and not {
                    "raw",
                    "datas",
                } & values.keys():
                    unchanged = False
            if not unchanged:
                raise UserError(
                    _("The generated or filed registration file is immutable.")
                )

    def write(self, values):
        if {
            "datas",
            "raw",
            "db_datas",
            "store_fname",
            "res_model",
            "res_id",
            "name",
            "mimetype",
            "company_id",
        } & values.keys():
            self._check_health_registration_archive(values)
        return super().write(values)

    def unlink(self):
        self._check_health_registration_archive()
        return super().unlink()
