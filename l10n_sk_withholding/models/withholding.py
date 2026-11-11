# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A filing workpaper referencing the native ledger, never another ledger."""

from calendar import monthrange
from collections import defaultdict
from decimal import Decimal
import hashlib
import base64

from lxml import etree
from psycopg2 import errors as pg_errors
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import file_path

from odoo.addons.l10n_cssk_core.tools import split_street

from .. import wire4311
from ..deadline4311 import regular_deadline

MODEL = "l10n.sk.withholding"


def _settlement_key(facts):
    credits = facts.get("credit_line_ids", facts.get("receivable_line_ids", []))
    return "%s:%s" % (
        facts["kind"],
        ",".join(str(identifier) for identifier in sorted(credits)),
    )


GENERATED = {
    "state",
    "payload",
    "source_history",
    "xml_attachment_id",
    "name",
    "submitted_attachment_id",
    "filed_history_ids",
    "submitted_date",
    "legacy",
    "currency_id",
    "date_from",
    "date_to",
}
EVENT_DERIVED = {
    "company_id",
    "currency_id",
    "tax_rate",
    "tax_amount",
    "net_amount",
    "remitted",
    "remitted_on",
    "remittance_reviewed",
}
INPUTS = {
    "company_id",
    "period",
    "prepared_on",
    "filing_on",
    "prepared_by",
    "phone",
    "dividend_account_id",
    "tax_account_id",
    "event_ids",
    "original_return_id",
    "original_filing_date",
    "original_date_reviewed",
    "correction_source_reference",
    "resident_scope_reviewed",
    "authority_deadline",
    "authority_deadline_reference",
}


class Withholding(models.Model):
    _name = MODEL
    _inherit = [
        "cssk.statutory.submission.mixin",
        "cssk.submittable.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "Slovak withholding notice 4311"
    _check_company_auto = True
    _order = "period desc, id desc"

    def _xml_country_name(self, country):
        # Installing a reporting module must not require an active Slovak UI
        # language. The reviewed domestic adapter has a stable statutory label.
        return (
            "Slovensko"
            if country.code == "SK"
            else country.with_context(lang=None).name
        )

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    period = fields.Date(
        required=True, help="First day of the reported calendar month."
    )
    date_from = fields.Date(related="period", string="Period start")
    date_to = fields.Date(compute="_compute_date_to")
    name = fields.Char(compute="_compute_name", store=True)
    state = fields.Selection(
        [
            (s, s.title())
            for s in ("draft", "preview", "exported", "submitted", "legacy")
        ],
        default="draft",
        required=True,
        copy=False,
    )
    prepared_on = fields.Date(required=True, default=fields.Date.context_today)
    filing_on = fields.Date(
        required=True,
        default=fields.Date.context_today,
        string="Filing date / remittance cutoff",
        help="Actual filing date, or the intended date before sending. Reconcile it to the actual filing day. The printed preparation date is a separate fact.",
    )
    prepared_by = fields.Char(required=True)
    phone = fields.Char()
    resident_scope_reviewed = fields.Boolean(
        string="Reviewed: no other resident withholding titles this month",
        help="Row 01 must include all resident withholding. This adapter currently supports dividends and author income only; other section 43 titles require a complete notice outside this adapter.",
    )
    authority_deadline = fields.Date(
        string="Different deadline granted by the authority"
    )
    authority_deadline_reference = fields.Char(
        help="Retain the authority's decision under section 43(11); an intended filing date does not extend the deadline."
    )
    dividend_account_id = fields.Many2one(
        "account.account",
        check_company=True,
        string="Dividend account (optional restriction)",
    )
    tax_account_id = fields.Many2one(
        "account.account", required=True, check_company=True
    )
    original_return_id = fields.Many2one(
        MODEL, check_company=True, copy=False, ondelete="restrict"
    )
    original_filing_date = fields.Date(string="Actual previous filing date", copy=False)
    original_date_reviewed = fields.Boolean(copy=False)
    correction_source_reference = fields.Char(copy=False)
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True, copy=False)
    payload = fields.Json(readonly=True, copy=False)
    source_history = fields.Json(readonly=True, copy=False)
    event_ids = fields.One2many("l10n.sk.withholding.event", "notice_id", copy=True)

    _one_filed_original = models.UniqueIndex(
        "(company_id, period) WHERE original_return_id IS NULL AND state = 'submitted'",
        "There is already a filed original withholding notice for this company and month.",
    )

    @api.depends("period")
    def _compute_name(self):
        for rec in self:
            rec.name = "OZN4311v26-%s" % (
                rec.period.strftime("%Y-%m") if rec.period else "draft"
            )

    @api.depends("period")
    def _compute_date_to(self):
        for rec in self:
            rec.date_to = (
                rec.period.replace(day=monthrange(rec.period.year, rec.period.month)[1])
                if rec.period
                else False
            )

    @api.constrains("period", "company_id", "original_return_id")
    def _check_scope(self):
        for rec in self:
            seen, ancestor = rec, rec.original_return_id
            while ancestor:
                if ancestor in seen:
                    raise ValidationError(
                        _("A withholding correction chain cannot contain a cycle.")
                    )
                seen |= ancestor
                ancestor = ancestor.original_return_id
            if rec.period and rec.period.day != 1:
                raise ValidationError(
                    _("Select the first day of the withholding month.")
                )
            if rec.original_return_id and (
                rec.original_return_id == rec
                or rec.original_return_id.company_id != rec.company_id
                or rec.original_return_id.period != rec.period
            ):
                raise ValidationError(
                    _("The original notice must belong to the same company and month.")
                )

    @api.model_create_multi
    def create(self, values_list):
        defaults = {
            key[8:]: value
            for key, value in self.env.context.items()
            if key.startswith("default_")
        }
        for values in values_list:
            supplied = dict(defaults, **values)
            if (
                any(supplied.get(key) for key in GENERATED - {"state"})
                or supplied.get("state", "draft") != "draft"
            ):
                raise UserError(
                    _("The withholding workflow creates export and filing evidence.")
                )
        # Acquire the correction chain before inserting its deferred FK.
        prior_ids = {
            v.get("original_return_id", defaults.get("original_return_id"))
            for v in values_list
        }
        company_ids = {
            values.get("company_id", defaults.get("company_id") or self.env.company.id)
            for values in values_list
        }
        self.browse([identifier for identifier in prior_ids if identifier])._lock(
            extra_companies=self.env["res.company"].browse(list(company_ids))
        )
        return super().create(values_list)

    def _lock(self, extra_companies=None):
        self.check_access("write")
        targets, frontier = self, self
        while frontier:
            frontier = frontier.original_return_id - targets
            targets |= frontier
        companies = targets.company_id | (
            extra_companies if extra_companies is not None else self.env["res.company"]
        )
        if companies:
            companies.check_access("read")
            # Serialize allocations across different months. NO KEY UPDATE
            # remains compatible with native accounting's deferred company FKs.
            try:
                with self.env.cr.savepoint(flush=False):
                    self.env.cr.execute(
                        "SELECT id FROM res_company WHERE id = ANY(%s) ORDER BY id FOR NO KEY UPDATE NOWAIT",
                        [companies.ids],
                        log_exceptions=False,
                    )
                    self.env.cr.execute(
                        "UPDATE res_company SET l10n_sk_withholding_epoch = clock_timestamp() WHERE id = ANY(%s)",
                        [companies.ids],
                        log_exceptions=False,
                    )
            except pg_errors.LockNotAvailable as exc:
                raise UserError(
                    _(
                        "Another process is allocating this company's withholding sources. Reload and retry."
                    )
                ) from exc
            companies.invalidate_recordset(["l10n_sk_withholding_epoch"])
        if targets:
            targets.check_access("write")
            targets.flush_recordset()
            try:
                with self.env.cr.savepoint(flush=False):
                    self.env.cr.execute(
                        "SELECT id FROM l10n_sk_withholding WHERE id = ANY(%s) ORDER BY id FOR UPDATE NOWAIT",
                        [targets.ids],
                        log_exceptions=False,
                    )
                    self.env.cr.execute(
                        "UPDATE l10n_sk_withholding SET write_date = clock_timestamp() WHERE id = ANY(%s)",
                        [targets.ids],
                        log_exceptions=False,
                    )
            except pg_errors.LockNotAvailable as exc:
                raise UserError(
                    _(
                        "Another process is changing this withholding notice or its correction chain. Reload and retry."
                    )
                ) from exc
            targets.invalidate_recordset()
            targets.check_access("write")

    def write(self, values):
        if GENERATED & values.keys():
            raise UserError(
                _("The withholding workflow creates export and filing evidence.")
            )
        targets = self
        if values.get("original_return_id"):
            targets |= self.browse(values["original_return_id"])
        targets._lock(
            extra_companies=self.env["res.company"].browse(
                [values["company_id"]] if values.get("company_id") else []
            )
        )
        identity = {
            "company_id",
            "period",
            "filing_on",
            "original_return_id",
            "original_filing_date",
        }
        if identity & values.keys():
            for rec in self.filtered("filed_history_ids"):
                for key in identity & values.keys():
                    current = rec[key]
                    current = (
                        current
                        if key in {"period", "filing_on", "original_filing_date"}
                        else current.id
                    )
                    supplied = (
                        fields.Date.to_date(values[key])
                        if key in {"period", "filing_on", "original_filing_date"}
                        else values[key]
                    )
                    if supplied != current:
                        raise UserError(
                            _(
                                "A filed withholding notice retains its company, period and correction identity after reset."
                            )
                        )
        if INPUTS & values.keys() and any(rec.state != "draft" for rec in self):
            raise UserError(_("Reset the notice to draft before changing its inputs."))
        if {
            "original_return_id",
            "original_filing_date",
            "correction_source_reference",
        } & values.keys():
            values = {"original_date_reviewed": False, **values}
        result = super().write(values)
        if "filing_on" in values:
            self.event_ids.write({"remittance_reporting_reviewed": False})
        return result

    def _cssk_workflow_write(self, values):
        return super(Withholding, self).write(values)

    def _filed_leaf(self):
        self.ensure_one()
        filed = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("period", "=", self.period),
                ("filed_history_ids", "!=", False),
            ]
        )
        filed = filed.filtered(
            lambda rec: rec.submission_state not in {"rejected", "cancelled"}
        )
        leaves = filed - filed.original_return_id
        if len(leaves) > 1:
            raise UserError(
                _(
                    "Reconcile competing filed notices before preparing another correction."
                )
            )
        return leaves

    def _sources(self):
        self.ensure_one()
        if not self.resident_scope_reviewed:
            raise UserError(
                _(
                    "Confirm that no other resident withholding titles are missing from row 01. This adapter covers dividends and author income only."
                )
            )
        if (
            self.authority_deadline
            and not (self.authority_deadline_reference or "").strip()
        ):
            raise UserError(
                _(
                    "A different withholding deadline requires the authority's actual decision and retained reference."
                )
            )
        if self.company_id.country_id.code != "SK" or self.currency_id.name != "EUR":
            raise UserError(
                _(
                    "This notice adapter requires a Slovak corporate payer with EUR ledger amounts."
                )
            )
        prior = self.original_return_id
        latest = self._filed_leaf()
        if latest and latest != self and latest != prior:
            raise UserError(
                _(
                    "Base the complete correction on the immediately previous filed notice."
                )
            )
        if prior and not prior.filed_history_ids:
            raise UserError(
                _(
                    "Select an actually filed original notice before preparing its correction."
                )
            )
        if prior and not (
            self.original_filing_date
            and self.original_date_reviewed
            and (self.correction_source_reference or "").strip()
        ):
            raise UserError(
                _(
                    "Review the actual previous filing date against its filing receipt before preparing a correction."
                )
            )
        if not self.event_ids:
            raise UserError(_("Add the reviewed actual dividend payments."))
        if not self.tax_account_id.code.startswith("342"):
            raise UserError(
                _(
                    "Use the Slovak dividend 364 and withholding 342 accounts, including their analytical subaccounts."
                )
            )
        street, number = split_street(self.company_id)
        data = {
            "payer": {
                "dic": self.company_id.l10n_sk_dic or "",
                "ico": self.company_id.company_registry or "",
                "name": self.company_id.name,
                "street": street,
                "number": number,
                "zip": self.company_id.zip or "",
                "city": self.company_id.city or "",
                "country_name": self._xml_country_name(self.company_id.country_id),
                "prepared_by": self.prepared_by,
                "phone": self.phone or "",
            },
            "period": self.period.strftime("%Y-%m"),
            "resident_scope_reviewed": self.resident_scope_reviewed,
            "deadline": str(self.authority_deadline or regular_deadline(self.period)),
            "authority_deadline_reference": self.authority_deadline_reference or "",
            "prepared_on": str(self.prepared_on),
            "filing_on": str(self.filing_on),
            "original_filed_on": str(self.original_filing_date) if prior else None,
            "correction_source_reference": self.correction_source_reference
            if prior
            else None,
            "events": [],
            "sources": [],
        }
        allocated = defaultdict(float)
        settlement_allocated = defaultdict(float)
        reserved = self._allocated_elsewhere()
        for event in self.event_ids.sorted("id"):
            if not event.payment_reviewed or not (event.source_reference or "").strip():
                raise UserError(
                    _(
                        "Review the actual dividend payment and retain its source reference."
                    )
                )
            if event.company_id != self.company_id:
                raise UserError(
                    _("Every dividend source must belong to the notice company.")
                )
            if (
                not event.decision_on
                or not event.paid_on
                or event.decision_on > event.paid_on
            ):
                raise UserError(
                    _(
                        "Review the completed profit period, distribution decision and actual payment dates."
                    )
                )
            liability = event.distribution_line_id.account_id
            if event.income_kind == "dividend":
                if (
                    not event.profit_period_start
                    or not event.profit_period_end
                    or not event.profit_period_end < event.decision_on
                ):
                    raise UserError(
                        _(
                            "Review the completed profit period before reporting a dividend."
                        )
                    )
                if (
                    not liability.code.startswith("364")
                    or self.dividend_account_id
                    and liability != self.dividend_account_id
                ):
                    raise UserError(
                        _("Select the actual dividend 364 liability source.")
                    )
            elif event.income_kind == "author":
                if event.no_withholding_agreement:
                    raise UserError(
                        _(
                            "Report the author's no-withholding agreement separately under section 43(14), not as deducted tax here."
                        )
                    )
                if not liability.code.startswith(("321", "379")):
                    raise UserError(
                        _(
                            "Select the posted supplier or other payable for the resident author income."
                        )
                    )
            try:
                rate, tax = wire4311.income_tax(
                    event.gross, event.income_kind, event.profit_period_start
                )
            except ValueError as exc:
                raise UserError(
                    _("Review dividend tax inputs: %s", self.env._(exc.args[0]))
                ) from exc
            tax = float(tax)
            net = event.gross - tax
            sources = [
                (
                    "income",
                    event.distribution_line_id,
                    event.gross,
                    liability,
                    -1,
                ),
                ("payment", event.payment_line_id, net, liability, 1),
            ]
            if tax:
                sources.append(
                    (
                        "withholding",
                        event.withholding_line_id,
                        tax,
                        self.tax_account_id,
                        -1,
                    )
                )
            elif event.withholding_line_id:
                raise UserError(
                    _("Do not attach a nonzero tax entry to a zero-tax dividend.")
                )
            receipts, remitted, remitted_on, reviewed = event._remittance_facts()
            if receipts and not reviewed:
                raise UserError(
                    _(
                        "Review each actual remittance and retain its source reference before reporting tax as paid."
                    )
                )
            if remitted and not remitted_on:
                raise UserError(
                    _(
                        "The form accepts one remittance date per income. Select and review the reported date from the actual allocated payments."
                    )
                )
            for receipt in receipts:
                if receipt.amount <= 0:
                    raise UserError(
                        _(
                            "A remittance allocation must be a positive actual payment amount."
                        )
                    )
                sources.append(
                    (
                        "remittance"
                        if receipt.source_kind == "bank"
                        else "authority_remittance",
                        receipt.line_id,
                        receipt.amount,
                        self.tax_account_id,
                        1,
                    )
                )
            source = {
                "event_id": event.id,
                "reference": event.source_reference,
                "payment_reviewed": event.payment_reviewed,
                "remittance_reviewed": reviewed,
                "decision_on": str(event.decision_on),
                "payment_form": event.payment_form,
                "remittances": [
                    {
                        "id": row.id,
                        "line_id": row.line_id.id,
                        "actual_on": str(row.actual_on),
                        "amount": row.amount,
                        "reference": row.source_reference,
                        "reviewed": row.reviewed,
                        "source_kind": row.source_kind,
                    }
                    for row in receipts
                ],
                "lines": [],
            }
            for kind, line, value, account, sign in sources:
                if (
                    not line
                    or line.company_id != self.company_id
                    or line.move_id.state != "posted"
                    or line.account_id != account
                    or line.balance * sign <= 0
                ):
                    raise UserError(
                        _(
                            "Use posted source lines of the correct company, account and direction."
                        )
                    )
                if (
                    line.move_id.reversed_entry_id
                    or line.move_id.reversal_move_ids.filtered(
                        lambda move: move.state == "posted"
                    )
                ):
                    raise UserError(
                        _(
                            "Use unreversed original withholding sources, not reversed payments or reversal entries."
                        )
                    )
                if (
                    kind in {"income", "payment"}
                    and line.partner_id != event.partner_id
                    or kind == "withholding"
                    and line.partner_id
                    and line.partner_id != event.partner_id
                ):
                    raise UserError(
                        _(
                            "The dividend recipient disagrees with the native ledger counterparty."
                        )
                    )
                settlement = (
                    event._check_payment_source(kind, line)
                    if kind in {"payment", "remittance"}
                    else None
                )
                allocated[line.id] += value
                if (
                    self.currency_id.compare_amounts(
                        allocated[line.id], abs(line.balance)
                    )
                    > 0
                ):
                    raise UserError(
                        _("Notice allocations exceed the actual posted source line.")
                    )
                if (
                    self.currency_id.compare_amounts(
                        allocated[line.id] + reserved[line.id], abs(line.balance)
                    )
                    > 0
                ):
                    raise UserError(
                        _(
                            "This source is already allocated in another live notice. Use only its remaining amount."
                        )
                    )
                if settlement:
                    self._claim_settlement(
                        settlement, value, settlement_allocated, reserved
                    )
                source["lines"].append(
                    {
                        "kind": kind,
                        "id": line.id,
                        "move_id": line.move_id.id,
                        "account_id": line.account_id.id,
                        "date": str(line.date),
                        "balance": line.balance,
                        "allocated": value,
                        "settlement": settlement,
                    }
                )
            person = event.partner_id
            person_street, person_number = split_street(person)
            data["events"].append(
                {
                    "person_type": "PO" if person.is_company else "FO",
                    "tax_residence": event.tax_residence,
                    "kind": event.income_kind,
                    "no_withholding_agreement": event.no_withholding_agreement,
                    "profit_period_start": str(event.profit_period_start)
                    if event.profit_period_start
                    else None,
                    "profit_period_end": str(event.profit_period_end)
                    if event.profit_period_end
                    else None,
                    "gross": event.gross,
                    "paid_on": str(event.paid_on),
                    "withheld": tax,
                    "remitted": remitted,
                    "remitted_on": str(remitted_on) if remitted else None,
                    "recipient": {
                        "first_name": event.first_name,
                        "last_name": event.last_name,
                        "birth_number": event.birth_number or "",
                        "birth_date": str(event.birth_date)
                        if event.birth_date
                        else None,
                        "street": person_street,
                        "number": person_number,
                        "zip": person.zip or "",
                        "city": person.city or "",
                        "country_name": self._xml_country_name(person.country_id) or "",
                        "country_code": person.country_id.code or "",
                    },
                }
            )
            data["sources"].append(source)
        try:
            wire4311.render(
                data["payer"],
                data["period"],
                data["prepared_on"],
                data["events"],
                original_filed_on=data["original_filed_on"],
                filing_on=data["filing_on"],
            )
        except ValueError as exc:
            raise UserError(
                _("Review withholding notice inputs: %s", self.env._(exc.args[0]))
            ) from exc
        return data

    def action_compute_lines(self):
        self._lock()
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Reset the notice before recomputing its sources."))
            rec._cssk_workflow_write({"payload": rec._sources(), "state": "preview"})
            if not rec.original_return_id and rec.filing_on > (
                rec.authority_deadline or regular_deadline(rec.period)
            ):
                rec.message_post(
                    body=_(
                        "The intended regular withholding filing is after its applicable deadline. Review actual filing and any authority-granted different deadline."
                    )
                )
        return True

    def _cssk_preflight_export(self):
        # This income-tax form requires DIC, including a non-VAT payer;
        # the generic core's VAT-number requirement is not this form's rule.
        if self._sources() != self.payload:
            raise UserError(
                _(
                    "The notice sources changed. Reset and recompute before export or filing."
                )
            )
        if self.source_history:
            previous = self.source_history[-1]["payload"]
            previous_xml = wire4311.render(
                previous["payer"],
                previous["period"],
                previous["prepared_on"],
                previous["events"],
                original_filed_on=previous["original_filed_on"],
                filing_on=previous["filing_on"],
            )
            if self._render_xml() != previous_xml:
                raise UserError(
                    _(
                        "Create an explicit correction instead of replacing the contents of a filed original notice."
                    )
                )
        return True

    def _render_xml(self):
        data = self.payload
        return wire4311.render(
            data["payer"],
            data["period"],
            data["prepared_on"],
            data["events"],
            original_filed_on=data["original_filed_on"],
            filing_on=data["filing_on"],
        )

    def _validate_against_schema(self, content):
        with open(
            file_path("l10n_sk_withholding/data/ozn4311_2026.xsd"), "rb"
        ) as stream:
            schema = stream.read()
        if hashlib.sha256(schema).hexdigest() != wire4311.SCHEMA_SHA256:
            raise UserError(_("The pinned withholding schema changed unexpectedly."))
        etree.XMLSchema(etree.fromstring(schema)).assertValid(etree.fromstring(content))
        return True

    def action_export_xml(self):
        self._lock()
        with self.env.cr.savepoint():
            return super().action_export_xml()

    def action_submit(self):
        self._lock()
        with self.env.cr.savepoint():
            for rec in self:
                rec._check_retained_export()
                rec._check_retained_allocations()
                try:
                    drift = rec._sources() != rec.payload
                except AccessError:
                    raise
                except UserError:
                    drift = True
                if drift:
                    rec.message_post(
                        body=_(
                            "Current withholding sources differ from the retained export. Review a separate correction; the exported copy is unchanged."
                        )
                    )
                if (
                    rec.xml_attachment_id.res_model != MODEL
                    or rec.xml_attachment_id.res_id != rec.id
                ):
                    raise UserError(
                        _(
                            "The exported file does not belong to this withholding notice."
                        )
                    )
            result = super().action_submit()
            for rec in self:
                rec._cssk_workflow_write(
                    {
                        "source_history": (rec.source_history or [])
                        + [
                            {
                                "attachment_id": rec.submitted_attachment_id.id,
                                "payload": rec.payload,
                            }
                        ]
                    }
                )
            return result

    def _check_retained_export(self):
        self.ensure_one()
        if not self.payload or not self._cssk_has_retained_xml_attachment():
            raise UserError(
                _(
                    "The retained withholding payload must match its exported attachment."
                )
            )

    def _check_retained_allocations(self):
        self.ensure_one()
        latest = self._filed_leaf()
        if latest and latest not in (self, self.original_return_id):
            raise UserError(
                _(
                    "Base the complete correction on the immediately previous filed notice."
                )
            )
        other, claimed = (
            self._allocated_elsewhere(retained_only=True),
            defaultdict(float),
        )
        for source in self.payload["sources"]:
            for line in source["lines"]:
                claimed[line["id"]] += line["allocated"]
                if (
                    self.currency_id.compare_amounts(
                        claimed[line["id"]] + other[line["id"]], abs(line["balance"])
                    )
                    > 0
                ):
                    raise UserError(
                        _(
                            "This source is already allocated in another live notice. Use only its remaining amount."
                        )
                    )
                settlement = line.get("settlement")
                if settlement:
                    self._claim_settlement(
                        settlement, line["allocated"], claimed, other
                    )

    def _claim_settlement(self, facts, amount, claimed, other):
        """One physical credit pool may back several counterpart allocations."""
        key = _settlement_key(facts)
        credits = set(key.partition(":")[2].split(","))
        for retained, value in other.items():
            if (
                value
                and isinstance(retained, str)
                and retained != key
                and credits.intersection(retained.partition(":")[2].split(","))
            ):
                raise UserError(
                    _(
                        "A live notice retains a different settlement-credit set. Review the changed native source and its correction before reusing those credits."
                    )
                )
        claimed[key] += amount
        if (
            self.currency_id.compare_amounts(
                claimed[key] + other[key], facts["capacity"]
            )
            > 0
        ):
            raise UserError(
                _(
                    "The reported payments exceed the actual settlement credits, including amounts reserved by other live notices."
                )
            )

    def _reserved_lines(self, *, retained_only=False):
        """Working reservations and retained claims, with filing precedence.

        A file already sent cannot lose priority to another notice's later
        draft. Filing checks only retained claims; computation still includes
        every working reservation before producing another export.
        """
        self.ensure_one()
        claimed = defaultdict(float)
        if self.source_history:
            for source in self.source_history[-1]["payload"]["sources"]:
                for line in source["lines"]:
                    claimed[line["id"]] += line["allocated"]
                    if line.get("settlement"):
                        claimed[_settlement_key(line["settlement"])] += line[
                            "allocated"
                        ]
            if self.state == "submitted":
                return claimed
        if self.state == "exported" and self.payload:
            exported = defaultdict(float)
            for source in self.payload["sources"]:
                for line in source["lines"]:
                    exported[line["id"]] += line["allocated"]
                    if line.get("settlement"):
                        exported[_settlement_key(line["settlement"])] += line[
                            "allocated"
                        ]
            for key, value in exported.items():
                claimed[key] = max(claimed[key], value)
        if retained_only:
            return claimed
        working = defaultdict(float)
        for event in self.event_ids:
            for line, amount in (
                (event.distribution_line_id, event.gross),
                (event.payment_line_id, event.net_amount),
                (event.withholding_line_id, event.tax_amount),
            ):
                if line:
                    working[line.id] += max(amount, 0)
            for receipt in event.remittance_ids.filtered(
                lambda row: row.actual_on <= self.filing_on
            ):
                working[receipt.line_id.id] += max(receipt.amount, 0)
            settlements = [("payment", event.payment_line_id, event.net_amount)]
            settlements += [
                ("remittance", receipt.line_id, receipt.amount)
                for receipt in event.remittance_ids
                if receipt.source_kind == "bank" and receipt.actual_on <= self.filing_on
            ]
            for kind, line, amount in settlements:
                if not line:
                    continue
                try:
                    facts = event._check_payment_source(kind, line)
                except AccessError:
                    raise
                except UserError:
                    # Incomplete drafts retain their counterpart reservation;
                    # they cannot yet establish a physical settlement pool.
                    continue
                working[_settlement_key(facts)] += max(amount, 0)
        for key, value in working.items():
            claimed[key] = max(claimed[key], value)
        return claimed

    def _allocated_elsewhere(self, *, retained_only=False):
        """Full replacements share a reservation; unrelated notices add up.

        A working correction cannot release its still-filed ancestor's amount
        for another notice. The current correction itself may replace ancestors.
        The company coordinator serialises this read with every source mutation.
        """
        self.ensure_one()
        ignored, ancestor = self, self.original_return_id
        while ancestor:
            ignored |= ancestor
            ancestor = ancestor.original_return_id
        live = self.search(
            [("company_id", "=", self.company_id.id), ("id", "not in", ignored.ids)]
        )
        live = live.filtered(
            lambda rec: rec.submission_state not in {"rejected", "cancelled"}
        )
        filed = live.filtered("filed_history_ids")
        superseded = filed.original_return_id
        groups = defaultdict(lambda: defaultdict(float))
        for notice in live - superseded:
            root = notice
            while root.original_return_id:
                root = root.original_return_id
            for key, value in notice._reserved_lines(
                retained_only=retained_only
            ).items():
                groups[root.id][key] = max(groups[root.id][key], value)
        result = defaultdict(float)
        for group in groups.values():
            for key, value in group.items():
                result[key] += value
        return result

    def action_reset_to_draft(self):
        self._lock()
        # Ordinary accountants may fix an unfiled draft/preview/export.
        # Reopening an actual filed history retains the shared manager gate.
        if not any(rec.filed_history_ids for rec in self):
            self._cssk_workflow_write({"state": "draft"})
            return True
        return super().action_reset_to_draft()

    def action_create_amendment(self):
        self.ensure_one()
        self._lock()
        latest = self._filed_leaf()
        if latest and latest != self:
            return latest.action_create_amendment()
        if not self.filed_history_ids:
            raise UserError(
                _(
                    "Select an actually filed original notice before preparing its correction."
                )
            )
        action = super().action_create_amendment()
        self.env[MODEL].browse(action["res_id"]).write(
            {
                "prepared_on": fields.Date.context_today(self),
                "filing_on": fields.Date.context_today(self),
                "original_filing_date": False,
                "original_date_reviewed": False,
                "correction_source_reference": False,
            }
        )
        return action

    def unlink(self):
        self._lock()
        if any(rec.filed_history_ids for rec in self):
            raise UserError(_("Retain a withholding notice with filed history."))
        return super().unlink()


class WithholdingEvent(models.Model):
    _name = "l10n.sk.withholding.event"
    _description = "Reviewed dividend income backed by native ledger sources"
    _check_company_auto = True

    notice_id = fields.Many2one(
        MODEL, required=True, check_company=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="notice_id.company_id", store=True)
    currency_id = fields.Many2one(related="notice_id.currency_id")
    partner_id = fields.Many2one("res.partner", required=True, check_company=True)
    tax_residence = fields.Char(required=True, default="SK")
    first_name = fields.Char(required=True)
    last_name = fields.Char(required=True)
    birth_number = fields.Char()
    birth_date = fields.Date()
    income_kind = fields.Selection(
        [
            ("dividend", "Resident individual dividend"),
            ("author", "Resident author income"),
        ],
        required=True,
        default="dividend",
    )
    no_withholding_agreement = fields.Boolean(
        string="Author agreement not to withhold tax"
    )
    profit_period_start = fields.Date()
    profit_period_end = fields.Date()
    gross = fields.Monetary(
        required=True,
        string="Taxable income (excluding VAT)",
        help="For author income, enter the income excluding VAT less any actually withheld art-fund contribution under section 43(5)(b). Do not deduct a contribution that was not actually withheld. The payment amount is this taxable income less withholding tax.",
    )
    decision_on = fields.Date(required=True, string="Decision or source agreement date")
    paid_on = fields.Date(required=True)
    remitted_on = fields.Date(compute="_compute_remittances")
    tax_rate = fields.Float(compute="_compute_preview_amounts")
    tax_amount = fields.Monetary(compute="_compute_preview_amounts")
    net_amount = fields.Monetary(
        compute="_compute_preview_amounts",
        string="Income after withholding (excluding VAT)",
    )
    distribution_line_id = fields.Many2one(
        "account.move.line",
        required=True,
        check_company=True,
        ondelete="restrict",
        string="Income liability source line",
    )
    withholding_line_id = fields.Many2one(
        "account.move.line", check_company=True, ondelete="restrict"
    )
    payment_line_id = fields.Many2one(
        "account.move.line", required=True, check_company=True, ondelete="restrict"
    )
    payment_form = fields.Selection(
        [
            ("disbursement", "Bank or cash payment"),
            ("setoff", "Set-off of mutual claims"),
        ],
        required=True,
        default="disbursement",
        help="A registered payment through its native outstanding account still needs actual payment evidence. A set-off needs reviewed legal evidence and a reconciled receivable of the same recipient.",
    )
    remittance_ids = fields.One2many(
        "l10n.sk.withholding.remittance", "event_id", copy=True
    )
    remitted = fields.Monetary(compute="_compute_remittances")
    reported_remitted_on = fields.Date(string="Reviewed remittance date for the form")
    remittance_reporting_reviewed = fields.Boolean(
        string="Single-date presentation reviewed"
    )
    source_reference = fields.Char(required=True)
    payment_reviewed = fields.Boolean()
    remittance_reviewed = fields.Boolean(
        compute="_compute_remittances", string="All receipt evidence reviewed"
    )

    def _check_payment_source(self, kind, line):
        """Accept native settlement evidence without treating any asset as cash."""
        self.ensure_one()
        credits = line.move_id.line_ids.filtered(lambda row: row.balance < 0)
        if kind == "payment" and self.payment_form == "setoff":
            receivables = credits.filtered(
                lambda row: row.account_id.account_type == "asset_receivable"
                and row.partner_id == self.partner_id
                and row.reconciled
            )
            if not receivables:
                raise UserError(
                    _(
                        "A set-off requires a reconciled mutual receivable of the same recipient covering the paid source line and retained legal evidence."
                    )
                )
            return {
                "kind": "setoff",
                "move_id": line.move_id.id,
                "receivable_line_ids": sorted(receivables.ids),
                "claim_line_ids": sorted(
                    receivables.matched_debit_ids.debit_move_id.ids
                ),
                "capacity": -sum(receivables.mapped("balance")),
            }
        cash = credits.filtered(lambda row: row.account_id.account_type == "asset_cash")
        if cash:
            return {
                "kind": "disbursement",
                "move_id": line.move_id.id,
                "credit_line_ids": sorted(cash.ids),
                "capacity": -sum(cash.mapped("balance")),
            }
        payment = line.move_id.origin_payment_id
        if (
            payment
            and payment.move_id == line.move_id
            and payment.payment_type == "outbound"
            and payment.state in {"in_process", "paid"}
            and payment.company_id == self.company_id
            and credits.filtered(
                lambda row: row.account_id == payment.outstanding_account_id
            )
        ):
            return {
                "kind": "registered_payment",
                "move_id": line.move_id.id,
                "payment_id": payment.id,
                "outstanding_account_id": payment.outstanding_account_id.id,
                "capacity": -sum(
                    credits.filtered(
                        lambda row: row.account_id == payment.outstanding_account_id
                    ).mapped("balance")
                ),
                "credit_line_ids": sorted(
                    credits.filtered(
                        lambda row: row.account_id == payment.outstanding_account_id
                    ).ids
                ),
            }
        raise UserError(
            _(
                "The reviewed payment must reference a posted bank or cash disbursement, a native registered outbound payment, or an evidenced income set-off."
            )
        )

    @api.onchange("payment_form")
    def _onchange_payment_form(self):
        self.payment_reviewed = False

    @api.onchange("payment_line_id")
    def _onchange_payment_source(self):
        for event in self:
            event.paid_on = event.payment_line_id.date
            event.payment_reviewed = False

    @api.onchange("distribution_line_id")
    def _onchange_distribution_source(self):
        for event in self:
            event.decision_on = event.distribution_line_id.date
            event.payment_reviewed = False

    def _remittance_facts(self):
        self.ensure_one()
        cutoff = self.notice_id.filing_on
        rows = self.remittance_ids.filtered(
            lambda row: cutoff and row.actual_on and row.actual_on <= cutoff
        )
        try:
            total = float(
                sum((wire4311.amount(row.amount) for row in rows), Decimal(0))
            )
        except ValueError as exc:
            raise UserError(
                _("Enter actual remittance amounts as nonnegative finite cent amounts.")
            ) from exc
        dates = set(rows.mapped("actual_on"))
        reported = next(iter(dates)) if len(dates) == 1 else False
        if (
            len(dates) > 1
            and self.remittance_reporting_reviewed
            and self.reported_remitted_on in dates
        ):
            reported = self.reported_remitted_on
        reviewed = bool(rows) and all(
            row.reviewed and (row.source_reference or "").strip() for row in rows
        )
        return rows, total, reported, reviewed

    @api.depends(
        "remittance_ids.amount",
        "remittance_ids.actual_on",
        "remittance_ids.reviewed",
        "remittance_ids.source_reference",
        "notice_id.filing_on",
        "reported_remitted_on",
        "remittance_reporting_reviewed",
    )
    def _compute_remittances(self):
        for event in self:
            _, event.remitted, event.remitted_on, event.remittance_reviewed = (
                event._remittance_facts()
            )

    @api.depends(
        "gross", "profit_period_start", "income_kind", "no_withholding_agreement"
    )
    def _compute_preview_amounts(self):
        for event in self:
            rate, tax = 0, 0
            if (
                (event.profit_period_start or event.income_kind == "author")
                and event.gross >= 0
                and not (
                    event.income_kind == "author" and event.no_withholding_agreement
                )
            ):
                try:
                    rate, tax = wire4311.income_tax(
                        event.gross, event.income_kind, event.profit_period_start
                    )
                except ValueError:
                    # An incomplete/unsupported draft is still editable;
                    # the source preflight provides the actual blocking error.
                    pass
            event.tax_rate = float(rate)
            event.tax_amount = float(tax)
            event.net_amount = event.gross - float(tax)

    def _draft_parents(self, parents):
        parents._lock()
        if any(rec.state != "draft" for rec in parents):
            raise UserError(_("Reset the notice before changing its income sources."))

    @api.model_create_multi
    def create(self, values_list):
        if any("default_" + key in self.env.context for key in EVENT_DERIVED) or any(
            EVENT_DERIVED & values.keys() for values in values_list
        ):
            raise UserError(
                _(
                    "Income tax and remittance totals are derived from their reviewed source rows."
                )
            )
        default = self.default_get(["notice_id"]).get("notice_id")
        parents = self.env[MODEL].browse(
            [
                v.get("notice_id", default)
                for v in values_list
                if v.get("notice_id", default)
            ]
        )
        self._draft_parents(parents)
        return super().create(values_list)

    def write(self, values):
        if EVENT_DERIVED & values.keys():
            raise UserError(
                _(
                    "Income tax and remittance totals are derived from their reviewed source rows."
                )
            )
        parents = self.notice_id
        if values.get("notice_id"):
            parents |= self.env[MODEL].browse(values["notice_id"])
        self._draft_parents(parents)
        if {
            "partner_id",
            "income_kind",
            "no_withholding_agreement",
            "tax_residence",
            "first_name",
            "last_name",
            "birth_number",
            "birth_date",
            "profit_period_start",
            "profit_period_end",
            "gross",
            "distribution_line_id",
            "withholding_line_id",
            "payment_line_id",
            "payment_form",
            "paid_on",
            "decision_on",
            "source_reference",
        } & values.keys():
            values = {"payment_reviewed": False, **values}
        if "reported_remitted_on" in values:
            values = {"remittance_reporting_reviewed": False, **values}
        return super().write(values)

    def unlink(self):
        self._draft_parents(self.notice_id)
        return super().unlink()


class WithholdingRemittance(models.Model):
    _name = "l10n.sk.withholding.remittance"
    _description = "Actual tax remittance allocated to reported income"
    _check_company_auto = True

    event_id = fields.Many2one(
        "l10n.sk.withholding.event",
        required=True,
        check_company=True,
        ondelete="cascade",
    )
    company_id = fields.Many2one(related="event_id.company_id", store=True)
    currency_id = fields.Many2one(related="event_id.currency_id")
    line_id = fields.Many2one(
        "account.move.line", required=True, check_company=True, ondelete="restrict"
    )
    actual_on = fields.Date(required=True)
    amount = fields.Monetary(required=True)
    source_reference = fields.Char(required=True)
    source_kind = fields.Selection(
        [("bank", "Bank/cash payment"), ("authority", "Actual authority allocation")],
        default="bank",
        required=True,
        help="An authority allocation requires the actual decision or verified tax-account settlement, not an application for a transfer.",
    )
    reviewed = fields.Boolean()

    @api.onchange("line_id")
    def _onchange_line(self):
        for row in self:
            row.actual_on = row.line_id.date
            row.reviewed = False

    @api.constrains("amount")
    def _check_amount(self):
        for row in self:
            try:
                if wire4311.amount(row.amount) <= 0:
                    raise ValueError("nonpositive allocation")
            except ValueError as exc:
                raise ValidationError(
                    _("Allocate a positive actual remittance amount in cents.")
                ) from exc

    def _draft_events(self, events):
        events._draft_parents(events.notice_id)

    @api.model_create_multi
    def create(self, values_list):
        if any(
            "default_" + key in self.env.context
            for key in ("company_id", "currency_id")
        ) or any(
            {"company_id", "currency_id"} & values.keys() for values in values_list
        ):
            raise UserError(
                _("Remittance ownership and currency follow its income source.")
            )
        default = self.default_get(["event_id"]).get("event_id")
        events = self.env["l10n.sk.withholding.event"].browse(
            [
                v.get("event_id", default)
                for v in values_list
                if v.get("event_id", default)
            ]
        )
        self._draft_events(events)
        result = super().create(values_list)
        result.event_id.write({"remittance_reporting_reviewed": False})
        return result

    def write(self, values):
        if {"company_id", "currency_id"} & values.keys():
            raise UserError(
                _("Remittance ownership and currency follow its income source.")
            )
        events = self.event_id
        if values.get("event_id"):
            events |= self.env["l10n.sk.withholding.event"].browse(values["event_id"])
        self._draft_events(events)
        if {
            "line_id",
            "actual_on",
            "amount",
            "source_reference",
            "source_kind",
        } & values.keys():
            values = {"reviewed": False, **values}
        result = super().write(values)
        events.write({"remittance_reporting_reviewed": False})
        return result

    def unlink(self):
        events = self.event_id
        self._draft_events(events)
        result = super().unlink()
        events.write({"remittance_reporting_reviewed": False})
        return result


class WithholdingAttachment(models.Model):
    _inherit = "ir.attachment"

    def _check_withholding_archive(self, values=None):
        for attachment in self.filtered(
            lambda row: row.res_model == MODEL and row.res_id
        ):
            notice = self.env[MODEL].browse(attachment.res_id).exists()
            if not notice or not (
                attachment in notice.filed_history_ids
                or attachment == notice.xml_attachment_id
                and notice.state == "exported"
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
                    _("The exported or filed withholding file is immutable.")
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
            self._check_withholding_archive(values)
        return super().write(values)

    def unlink(self):
        self._check_withholding_archive()
        return super().unlink()


class WithholdingCompanyCoordinator(models.Model):
    _inherit = "res.company"

    l10n_sk_withholding_epoch = fields.Datetime(
        readonly=True,
        copy=False,
        help="Internal non-key concurrency marker for withholding source allocations; not an accounting fact.",
    )
