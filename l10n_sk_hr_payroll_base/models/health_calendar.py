# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Reviewed monthly insurance facts, independent of either payroll engine.

This is a factual HR source, not evidence that a 601 notice was submitted.
Keeping revisions preserves the source of a previously calculated payslip.
"""

from calendar import monthrange

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..health_calendar import month_context


class HealthCalendar(models.Model):
    _name = "l10n.sk.health.calendar"
    _description = "Slovak monthly health-insurance calendar"
    _order = "month desc, id desc"
    _rec_name = "employee_id"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        check_company=True,
        ondelete="restrict",
    )
    month = fields.Date(required=True, help="First day of the insurance month.")
    evidence = fields.Char(
        string="Source reference",
        help="Retained work dates, employee notice or insurer decision supporting these facts.",
    )
    complete = fields.Boolean(
        string="Entire month reviewed",
        help="The intervals describe the whole month, including days without insurance and all known minimum exceptions. An empty reviewed calendar explicitly means no insured days.",
    )
    interval_ids = fields.One2many(
        "l10n.sk.health.calendar.interval",
        "calendar_id",
        copy=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("reviewed", "Reviewed"), ("superseded", "Superseded")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
    )
    reviewed_by = fields.Many2one("res.users", readonly=True, copy=False)
    reviewed_at = fields.Datetime(readonly=True, copy=False)
    supersedes_id = fields.Many2one(
        "l10n.sk.health.calendar",
        readonly=True,
        copy=False,
        ondelete="restrict",
    )

    _one_current_month = models.UniqueIndex(
        "(company_id, employee_id, month) WHERE state != 'superseded'",
        "There is already a current health calendar for this employee and month.",
    )

    @api.constrains("month", "employee_id", "company_id")
    def _check_month_company(self):
        for row in self:
            if row.month.day != 1:
                raise ValidationError(
                    _("The insurance month must start on its first day.")
                )
            if row.employee_id.company_id != row.company_id:
                raise ValidationError(
                    _(
                        "The health calendar and employee must belong to the same company."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        protected = {"state", "reviewed_by", "reviewed_at", "supersedes_id"}
        if any("default_" + key in self.env.context for key in protected) or any(
            protected & values.keys() for values in vals_list
        ):
            raise UserError(_("Use the health-calendar review and revision actions."))
        return super().create(vals_list)

    def write(self, values):
        self._lock_for_change()
        if {"state", "reviewed_by", "reviewed_at", "supersedes_id"} & values.keys():
            raise UserError(_("Use the health-calendar review and revision actions."))
        if any(row.state != "draft" for row in self):
            raise UserError(
                _("Reviewed health-calendar facts are immutable. Create a revision.")
            )
        result = super().write(values)
        # Parent changes must recheck existing children as well as new rows.
        self.interval_ids._check_interval()
        return result

    def unlink(self):
        self._lock_for_change()
        if any(row.state != "draft" for row in self):
            raise UserError(
                _("Reviewed health-calendar facts are immutable. Create a revision.")
            )
        return super().unlink()

    def action_review(self):
        self._lock_for_change()
        for row in self:
            if row.state == "reviewed":
                continue
            if row.state != "draft":
                raise UserError(_("Only a draft health calendar can be reviewed."))
            if not row.complete or not (row.evidence or "").strip():
                raise UserError(
                    _("Review the entire month and retain a source reference first.")
                )
            row.interval_ids._check_interval()
            row._calendar_context()
            super(HealthCalendar, row).write(
                {
                    "state": "reviewed",
                    "reviewed_by": self.env.user.id,
                    "reviewed_at": fields.Datetime.now(),
                }
            )
        return True

    def action_create_revision(self):
        """Keep old rows and review identity; a new draft is not yet effective."""
        self.ensure_one()
        self._lock_for_change()
        if self.state != "reviewed":
            raise UserError(_("Create a revision of a reviewed health calendar."))
        with self.env.cr.savepoint():
            super(HealthCalendar, self).write({"state": "superseded"})
            # Force the indexed state out before inserting the replacement.
            self.flush_recordset(["state"])
            revision = self.copy({"complete": False})
            super(HealthCalendar, revision).write({"supersedes_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": revision.id,
            "view_mode": "form",
            "target": "current",
        }

    def _lock_for_change(self):
        """Serialize review/revision and child changes on the same parent."""
        self.check_access("write")
        if self:
            self.flush_recordset()
            self.env.cr.execute(
                "SELECT id FROM l10n_sk_health_calendar WHERE id = ANY(%s) "
                "ORDER BY id FOR UPDATE",
                [self.ids],
            )
            # Child-only writes must advance a non-key parent version. Row
            # locking/cache invalidation alone preserves a stale RR snapshot.
            self.env.cr.execute(
                "UPDATE l10n_sk_health_calendar SET write_date = clock_timestamp() "
                "WHERE id = ANY(%s)",
                [self.ids],
            )
            # A writer may have changed the month/company while we waited.
            # Recheck both constraints and access against the committed row.
            self.invalidate_recordset()
            self.check_access("write")

    def _calendar_context(self):
        self.ensure_one()
        result = month_context(
            [
                {"kind": row.kind, "start": row.date_start, "end": row.date_end}
                for row in self.interval_ids
            ],
            self.month,
        )
        result["calendar_id"] = self.id
        result["source_reference"] = self.evidence or False
        return result


class HealthCalendarInterval(models.Model):
    _name = "l10n.sk.health.calendar.interval"
    _description = "Slovak health-insurance calendar interval"
    _order = "date_start, id"
    _check_company_auto = True

    calendar_id = fields.Many2one(
        "l10n.sk.health.calendar",
        required=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(related="calendar_id.company_id", store=True)
    kind = fields.Selection(
        [
            ("2", "Employment (2)"),
            ("2D", "Agreement work/rest days (2D)"),
            ("2Y", "Single irregular-income day (2Y)"),
            ("2N", "No-income employment exclusion (2N)"),
            ("benefit", "Benefit / income-compensation days"),
            ("state", "State-insured status"),
            ("disabled", "Health disability"),
            ("self_employed", "Self-employed status"),
            ("missing", "Declared missing"),
            ("other_employment", "Employment with another employer"),
        ],
        required=True,
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    @api.constrains("calendar_id", "kind", "date_start", "date_end")
    def _check_interval(self):
        for row in self:
            month = row.calendar_id.month
            last = month.replace(day=monthrange(month.year, month.month)[1])
            if not month <= row.date_start <= row.date_end <= last:
                raise ValidationError(
                    _("Health-calendar intervals must stay inside their month.")
                )
            if row.kind == "2Y" and row.date_start != row.date_end:
                raise ValidationError(_("A 2Y source must identify one calendar day."))

    def _check_draft_parent(self):
        if any(row.calendar_id.state != "draft" for row in self):
            raise UserError(
                _("Reviewed health-calendar facts are immutable. Create a revision.")
            )

    @api.model_create_multi
    def create(self, vals_list):
        # Use effective defaults too; a child may be created from a nested form.
        default = self.default_get(["calendar_id"]).get("calendar_id")
        parents = self.env["l10n.sk.health.calendar"].browse(
            [
                values.get("calendar_id", default)
                for values in vals_list
                if values.get("calendar_id", default)
            ]
        )
        parents._lock_for_change()
        if any(row.state != "draft" for row in parents):
            raise UserError(
                _("Reviewed health-calendar facts are immutable. Create a revision.")
            )
        return super().create(vals_list)

    def write(self, values):
        parents = self.calendar_id
        if values.get("calendar_id"):
            parents |= self.env["l10n.sk.health.calendar"].browse(values["calendar_id"])
        parents._lock_for_change()
        self._check_draft_parent()
        if "calendar_id" in values:
            parent = self.env["l10n.sk.health.calendar"].browse(values["calendar_id"])
            parent.check_access("write")
            if parent.state != "draft":
                raise UserError(
                    _(
                        "Reviewed health-calendar facts are immutable. Create a revision."
                    )
                )
        return super().write(values)

    def unlink(self):
        self.calendar_id._lock_for_change()
        self._check_draft_parent()
        return super().unlink()


class HealthCalendarEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_sk_health_calendar_ids = fields.One2many(
        "l10n.sk.health.calendar",
        "employee_id",
        string="Health calendars",
        groups="hr.group_hr_manager",
    )
