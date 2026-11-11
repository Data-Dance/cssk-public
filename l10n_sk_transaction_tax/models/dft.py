# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Reviewed DFT workpaper on native journal items and the shared filing pipeline."""

import base64
from calendar import monthrange
from collections import defaultdict
from decimal import Decimal
import hashlib
import re

from lxml import etree
from psycopg2 import errors as pg_errors
from odoo import _, Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import file_path
from odoo.addons.l10n_cssk_core.tools import split_street

from .. import wire
from ..deadlines import monthly_deadline

MODEL = "l10n.sk.transaction.tax"


def _check_unreversed_source(line):
    """A reversal is evidence of undoing a payment, not a new taxable debit."""
    move = line.move_id
    if move.reversed_entry_id or move.reversal_move_ids.filtered(
        lambda reversal: reversal.state == "posted"
    ):
        raise UserError(line.env._("Use an unreversed original payment or tax source."))


GENERATED = {
    "state",
    "payload",
    "source_history",
    "xml_attachment_id",
    "submitted_attachment_id",
    "filed_history_ids",
    "submitted_date",
    "legacy",
    "name",
    "currency_id",
    "tax_total",
    "provision_move_id",
    "provision_history_ids",
}
IDENTITY = {
    "company_id",
    "period",
    "period_from",
    "period_to",
    "original_return_id",
    "filing_type",
}
INPUTS = {
    "company_id",
    "period",
    "period_from",
    "period_to",
    "signed_on",
    "filing_on",
    "deadline",
    "deadline_reference",
    "filing_type",
    "discovery_date",
    "original_return_id",
    "grounds_c",
    "grounds_d",
    "grounds_e",
    "representative_kind",
    "representative_first_name",
    "representative_last_name",
    "representative_id",
    "refund_requested",
    "refund_bank_id",
    "refund_date",
    "source_ids",
    "adjustment_ids",
    "provision_journal_id",
    "provision_expense_account_id",
    "provision_payable_account_id",
}


class TransactionTax(models.Model):
    _name = MODEL
    _inherit = [
        "cssk.statutory.submission.mixin",
        "cssk.submittable.mixin",
        "mail.thread",
        "mail.activity.mixin",
    ]
    _description = "Slovak financial transaction tax notice"
    _check_company_auto = True
    _order = "period desc, id desc"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    name = fields.Char(compute="_compute_name", store=True)
    period = fields.Date(
        required=True, help="First day of the reported calendar month."
    )
    period_from = fields.Date(
        string="Exact period from",
        help="Optional partial-month start; retain the reported month as well.",
    )
    period_to = fields.Date(
        string="Exact period to",
        help="Optional partial-month end; complete both dates using the actual taxpayer period.",
    )
    signed_on = fields.Date(required=True, default=fields.Date.context_today)
    filing_on = fields.Date(required=True, default=fields.Date.context_today)
    deadline = fields.Date(
        compute="_compute_deadline", store=True, string="Statutory filing deadline"
    )
    deadline_reference = fields.Char(
        help="Optional reference to the official tax calendar. This does not extend the computed statutory deadline.",
    )

    @api.depends("period")
    def _compute_deadline(self):
        for rec in self:
            rec.deadline = monthly_deadline(rec.period) if rec.period else False

    filing_type = fields.Selection(
        [
            ("regular", "Regular"),
            ("corrective", "Corrective"),
            ("additional", "Additional"),
        ],
        default="regular",
        required=True,
    )
    discovery_date = fields.Date(copy=False)
    original_return_id = fields.Many2one(
        MODEL, check_company=True, ondelete="restrict", copy=False
    )
    grounds_c = fields.Boolean(string="Foreign payment-services provider")
    grounds_d = fields.Boolean(string="Recharged costs")
    grounds_e = fields.Boolean(string="Other/special account self-assessment")
    representative_kind = fields.Selection(
        [
            (key, label)
            for key, label in (
                ("statutarnyZastupcaPO", "Statutory representative"),
                ("zastupca", "Representative"),
                ("spravcaVkonkurznomKonani", "Bankruptcy administrator"),
                ("likvidator", "Liquidator"),
                ("pravnyNastupca", "Legal successor"),
            )
        ],
        required=True,
    )
    representative_first_name = fields.Char()
    representative_last_name = fields.Char()
    representative_id = fields.Many2one(
        "res.partner", required=True, check_company=True
    )
    refund_requested = fields.Boolean()
    refund_bank_id = fields.Many2one("res.partner.bank", check_company=True)
    refund_date = fields.Date()
    state = fields.Selection(
        [
            (key, key.title())
            for key in ("draft", "preview", "exported", "submitted", "legacy")
        ],
        default="draft",
        required=True,
        copy=False,
    )
    source_ids = fields.One2many(
        "l10n.sk.transaction.tax.source", "notice_id", copy=True
    )
    adjustment_ids = fields.One2many(
        "l10n.sk.transaction.tax.adjustment", "notice_id", copy=True
    )
    payload = fields.Json(copy=False, readonly=True)
    source_history = fields.Json(copy=False, readonly=True)
    xml_attachment_id = fields.Many2one("ir.attachment", copy=False, readonly=True)
    tax_total = fields.Monetary(compute="_compute_totals")
    provision_journal_id = fields.Many2one("account.journal", check_company=True)
    provision_expense_account_id = fields.Many2one(
        "account.account", check_company=True
    )
    provision_payable_account_id = fields.Many2one(
        "account.account", check_company=True
    )
    provision_move_id = fields.Many2one(
        "account.move", copy=False, readonly=True, check_company=True
    )
    provision_history_ids = fields.Many2many(
        "account.move",
        "l10n_sk_dft_provision_history_rel",
        "notice_id",
        "move_id",
        copy=False,
        readonly=True,
        check_company=True,
    )

    _one_filed_original = models.UniqueIndex(
        "(company_id, period) WHERE filing_type = 'regular' AND state = 'submitted'",
        "There is already a filed regular DFT notice for this company and month.",
    )

    @api.depends("period")
    def _compute_name(self):
        for rec in self:
            rec.name = "OZNDFTv26-%s" % (
                rec.period.strftime("%Y-%m") if rec.period else "draft"
            )

    @api.depends("payload")
    def _compute_totals(self):
        for rec in self:
            rec.tax_total = float((rec.payload or {}).get("total", 0))

    @api.constrains(
        "period",
        "period_from",
        "period_to",
        "original_return_id",
        "company_id",
        "filing_type",
    )
    def _check_scope(self):
        for rec in self:
            if rec.period.day != 1:
                raise ValidationError(_("Select the first day of the DFT month."))
            try:
                wire.period_bounds(
                    rec.period.strftime("%Y-%m"), rec.period_from, rec.period_to
                )
            except ValueError as error:
                raise ValidationError(
                    _(
                        "Review the exact partial-month DFT dates: %s",
                        self.env._(error.args[0]),
                    )
                ) from error
            seen, prior = rec, rec.original_return_id
            while prior:
                if (
                    prior in seen
                    or prior.company_id != rec.company_id
                    or prior.period != rec.period
                ):
                    raise ValidationError(
                        _(
                            "A DFT correction must have an acyclic chain within the same company and month."
                        )
                    )
                seen |= prior
                prior = prior.original_return_id

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
                    _(
                        "The DFT workflow creates export, accounting and filing evidence."
                    )
                )
        prior = {
            values.get("original_return_id", defaults.get("original_return_id"))
            for values in values_list
        }
        company_ids = {
            values.get("company_id", defaults.get("company_id", self.env.company.id))
            for values in values_list
        }
        self.browse([identifier for identifier in prior if identifier])._lock(
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
                        "UPDATE res_company SET l10n_sk_dft_epoch = clock_timestamp() WHERE id = ANY(%s)",
                        [companies.ids],
                        log_exceptions=False,
                    )
            except pg_errors.LockNotAvailable as exc:
                raise UserError(
                    _(
                        "Another process is allocating this company's DFT sources. Reload and retry."
                    )
                ) from exc
            companies.invalidate_recordset(["l10n_sk_dft_epoch"])
        if targets:
            targets.check_access("write")
            targets.flush_recordset()
            try:
                with self.env.cr.savepoint(flush=False):
                    self.env.cr.execute(
                        "SELECT id FROM l10n_sk_transaction_tax WHERE id = ANY(%s) ORDER BY id FOR UPDATE NOWAIT",
                        [targets.ids],
                        log_exceptions=False,
                    )
                    self.env.cr.execute(
                        "UPDATE l10n_sk_transaction_tax SET write_date = clock_timestamp() WHERE id = ANY(%s)",
                        [targets.ids],
                        log_exceptions=False,
                    )
            except pg_errors.LockNotAvailable as exc:
                raise UserError(
                    _(
                        "Another process is changing this DFT notice or its correction chain. Reload and retry."
                    )
                ) from exc
            targets.invalidate_recordset()
            targets.check_access("write")

    def write(self, values):
        if GENERATED & values.keys():
            raise UserError(
                _("The DFT workflow creates export, accounting and filing evidence.")
            )
        targets = self | self.browse(values.get("original_return_id") or [])
        targets._lock(
            extra_companies=self.env["res.company"].browse(
                [values["company_id"]] if values.get("company_id") else []
            )
        )
        if INPUTS & values.keys() and any(rec.state != "draft" for rec in self):
            raise UserError(
                _("Reset the DFT notice to draft before changing its inputs.")
            )
        for rec in self.filtered(
            lambda row: row.filed_history_ids or row.provision_history_ids
        ):
            for key in IDENTITY & values.keys():
                current = (
                    rec[key].id
                    if key in {"company_id", "original_return_id"}
                    else rec[key]
                )
                supplied = (
                    fields.Date.to_date(values[key])
                    if key in {"period", "period_from", "period_to"}
                    else values[key]
                )
                if supplied != current:
                    raise UserError(
                        _(
                            "A filed DFT notice retains its company, period and correction identity after reset."
                        )
                    )
        return super().write(values)

    def _cssk_workflow_write(self, values):
        return super(TransactionTax, self).write(values)

    def _latest_filed(self):
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
                    "Reconcile competing filed DFT notices before preparing another correction."
                )
            )
        return leaves

    def _other_effective_filed_periods(self):
        """Full filed replacements supersede their ancestors, not other months."""
        self.ensure_one()
        filed = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("filed_history_ids", "!=", False),
            ]
        )
        filed = filed.filtered(
            lambda rec: rec.submission_state not in {"rejected", "cancelled"}
        )
        effective = filed - filed.original_return_id
        return effective.filtered(lambda rec: rec.period != self.period)

    def _allocated_credits(self):
        """Only effective filed replacements; working drafts consume no credit."""
        claimed = defaultdict(Decimal)
        for notice in self._other_effective_filed_periods():
            for adjustment in notice.source_history[-1]["payload"]["adjustments"]:
                claimed[adjustment["line_id"]] += abs(Decimal(adjustment["amount"]))
        return claimed

    def _allocated_native_sources(self):
        """Monetary allocations already reported in other effective months.

        The company coordinator covers every month, so a concurrent filing
        forces a stale calculation to retry before it can reuse this balance.
        Annual card usage is a count, not an allocation of the evidence debit.
        """
        allocated = defaultdict(Decimal)
        for notice in self._other_effective_filed_periods():
            payload = notice.source_history[-1]["payload"]
            for row, facts in zip(payload["rows"], payload["source_facts"]):
                if row["kind"] != "card":
                    allocated[facts["line_id"]] += Decimal(
                        facts["allocated_source_amount"]
                    )
        return allocated

    def _earlier_recharge_history(self, rows):
        """Exact earlier filed tax for the currently identified original transfers.

        Unversioned archives need a reviewed amendment; reconstructing a
        per-transfer tax from an aggregate total would guess at consumed caps.
        """
        keys = {
            row["transaction_key"]
            for row in rows
            if row["kind"].startswith("recharge_")
        }
        result = []
        for notice in (
            self._other_effective_filed_periods()
            .filtered(lambda rec: rec.period < self.period)
            .sorted("period")
        ):
            data = notice.source_history[-1]["payload"]
            if not any(row["transaction_key"] in keys for row in data["rows"]):
                continue
            if "computed_recharges" not in data:
                raise UserError(
                    _(
                        "Review the earlier filed recharge allocation through an amendment before applying its remaining transaction cap."
                    )
                )
            for row in data["computed_recharges"]:
                if row["transaction_key"] in keys:
                    result.append(
                        {
                            key: row[key]
                            for key in ("transaction_key", "kind", "base_eur", "tax")
                        }
                    )
        return result

    def action_check_recharge_dependencies(self):
        """Detect a later notice needing amendment after an earlier filed change."""
        self._lock()
        for notice in self:
            if not notice.filed_history_ids:
                continue
            retained = notice.source_history[-1]["payload"]
            if notice._earlier_recharge_history(retained["rows"]) != retained.get(
                "recharge_history", []
            ):
                raise UserError(
                    _(
                        "An earlier identified recharge source changed. Prepare an amendment of this later notice; retain its original filed XML."
                    )
                )
        return True

    def _sources(self):
        self.ensure_one()
        if self.company_id.country_id.code != "SK" or self.currency_id.name != "EUR":
            raise UserError(
                _("This DFT adapter requires a Slovak corporate EUR ledger.")
            )
        end = self.period.replace(
            day=monthrange(self.period.year, self.period.month)[1]
        )
        if self.deadline != monthly_deadline(self.period):
            raise UserError(
                _(
                    "Review the computed statutory deadline, including days of rest. An arbitrary date cannot extend the filing deadline."
                )
            )
        if self.signed_on > self.filing_on or self.filing_on <= end:
            raise UserError(
                _(
                    "The monthly DFT notice is filed after the month, with a preparation date no later than filing."
                )
            )
        latest, prior = self._latest_filed(), self.original_return_id
        if latest and latest != self and latest != prior:
            raise UserError(
                _("Base a DFT correction on the immediately previous filed notice.")
            )
        if (
            self.filing_type == "regular"
            and prior
            or self.filing_type != "regular"
            and not prior
        ):
            raise UserError(
                _(
                    "A regular DFT notice has no original; a correction must reference a filed notice."
                )
            )
        if prior and not prior.source_history:
            raise UserError(
                _(
                    "Select an actually filed DFT notice before preparing its correction."
                )
            )
        if (
            self.filing_type == "corrective"
            and self.filing_on > self.deadline
            or self.filing_type == "additional"
            and self.filing_on <= self.deadline
        ):
            raise UserError(
                _(
                    "Use a corrective notice through the deadline and an additional notice after it."
                )
            )
        street, number = split_street(self.company_id)
        person_street, person_number = split_street(self.representative_id)

        def country(rec):
            return (
                "Slovensko"
                if rec.country_id.code == "SK"
                else rec.country_id.with_context(lang=None).name or ""
            )

        rows, source_facts, allocations = [], [], defaultdict(Decimal)
        previously_allocated = self._allocated_native_sources()
        for source in self.source_ids.sorted("id"):
            try:
                row, facts = source._source_values()
            except ValueError as exc:
                raise UserError(
                    _("Review DFT source inputs: %s", self.env._(exc.args[0]))
                ) from exc
            if source.kind != "card":
                allocations[source.move_line_id.id] += Decimal(
                    facts["allocated_source_amount"]
                )
            if (
                allocations[source.move_line_id.id] > Decimal(facts["source_amount"])
                and source.kind != "card"
            ):
                raise UserError(
                    _("DFT source allocations exceed the actual native transaction.")
                )
            if source.kind != "card" and (
                allocations[source.move_line_id.id]
                + previously_allocated[source.move_line_id.id]
                > Decimal(facts["source_amount"])
            ):
                raise UserError(
                    _(
                        "This native transaction source is already allocated in another filed DFT month. Use only its remaining amount."
                    )
                )
            rows.append(row)
            source_facts.append(facts)
        for line in self.source_ids.move_line_id:
            parts = self.source_ids.filtered(lambda source: source.move_line_id == line)
            if any(parts.mapped("bank_batch")):
                if not all(parts.mapped("bank_batch")) or any(
                    part.kind not in {"transfer", "cash", "excluded", "bank_collected"}
                    for part in parts
                ):
                    raise UserError(
                        _(
                            "Identify every individual payment of a bank batch in the same notice."
                        )
                    )
                facts = next(
                    fact for fact in source_facts if fact["line_id"] == line.id
                )
                if allocations[line.id] != Decimal(facts["source_amount"]):
                    raise UserError(
                        _(
                            "The reviewed individual bank payments must sum to the whole native bank line."
                        )
                    )
        adjustments = [row._source_values() for row in self.adjustment_ids.sorted("id")]
        credits = defaultdict(Decimal)
        previously_claimed = self._allocated_credits()
        for adjustment in adjustments:
            credits[adjustment["line_id"]] += abs(Decimal(adjustment["amount"]))
            if credits[adjustment["line_id"]] > abs(
                Decimal(str(adjustment["balance"]))
            ):
                raise UserError(
                    _("DFT adjustments exceed the actual posted tax source.")
                )
            if credits[adjustment["line_id"]] + previously_claimed[
                adjustment["line_id"]
            ] > abs(Decimal(str(adjustment["balance"]))):
                raise UserError(
                    _(
                        "This actual tax source is already allocated in another filed DFT month. Use only its remaining amount."
                    )
                )
        data = {
            "payer": {
                "ico": self.company_id.company_registry or "",
                "dic": self.company_id.l10n_sk_dic or "",
                "name": self.company_id.name,
                "street": street,
                "number": number,
                "zip": self.company_id.zip or "",
                "city": self.company_id.city or "",
                "country_name": country(self.company_id),
                "phone": self.company_id.phone or "",
                "email": self.company_id.email or "",
            },
            "representative": {
                "kind": self.representative_kind,
                "first_name": self.representative_first_name or "",
                "last_name": self.representative_last_name or "",
                "company_name": self.representative_id.name
                if self.representative_id.is_company
                else "",
                "street": person_street,
                "number": person_number,
                "zip": self.representative_id.zip or "",
                "city": self.representative_id.city or "",
                "country_name": country(self.representative_id),
                "phone": self.representative_id.phone or "",
                "email": self.representative_id.email or "",
            },
            "period": self.period.strftime("%Y-%m"),
            "signed_on": str(self.signed_on),
            "filing_on": str(self.filing_on),
            "deadline": str(self.deadline),
            "deadline_reference": self.deadline_reference,
            "grounds": [key for key in "cde" if self["grounds_" + key]],
            "filing_type": self.filing_type,
            "discovered_on": str(self.discovery_date)
            if self.filing_type == "additional" and self.discovery_date
            else None,
            "previous_tax": prior.source_history[-1]["payload"]["total"]
            if self.filing_type == "additional"
            else None,
            "rows": rows,
            "source_facts": source_facts,
            "adjustments": adjustments,
            "refund": {"requested": self.refund_requested},
        }
        if self.period_from or self.period_to:
            data.update(
                period_from=str(self.period_from), period_to=str(self.period_to)
            )
        recharges = any(row["kind"].startswith("recharge_") for row in rows)
        history = self._earlier_recharge_history(rows) if recharges else []
        if recharges:
            data["recharge_history"] = history
        if self.refund_requested:
            if (
                self.refund_bank_id.partner_id != self.company_id.partner_id
                or not self.refund_date
            ):
                raise UserError(
                    _(
                        "Use the company's actual refund bank account and reviewed request date."
                    )
                )
            data["refund"].update(self._refund_destination())
            data["refund"]["date"] = str(self.refund_date)
        try:
            totals, computed_facts = wire.calculate(
                rows, data["period"], adjustments, history
            )
            if recharges:
                data["computed_recharges"] = [
                    row for row in computed_facts if row["kind"].startswith("recharge_")
                ]
            data["total"] = wire.money(totals["r7"])
            self._render_payload(data)
        except ValueError as exc:
            raise UserError(
                _("Review DFT source inputs: %s", self.env._(exc.args[0]))
            ) from exc
        return data

    def _refund_destination(self):
        """Use the native bank master, including the form's non-IBAN alternative.

        OZNDFTv26 section V requires account number, SWIFT/BIC, bank name,
        city and country for an account abroad that is not in IBAN format.
        base_iban validates accounts classified as IBAN; never put an arbitrary
        foreign account number into the XML's IBAN element.
        """
        self.ensure_one()
        account = self.refund_bank_id
        if account.acc_type == "iban":
            return {"iban": account.sanitized_acc_number}
        bank = account.bank_id
        bic = (bank.bic or "").replace(" ", "").upper()
        if (
            not account.sanitized_acc_number
            or not bank
            or not bank.country
            or bank.country.code == "SK"
            or not all((value or "").strip() for value in (bank.name, bic, bank.city))
            or not re.fullmatch(r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?", bic)
        ):
            raise UserError(
                _(
                    "A non-IBAN refund needs the company's foreign account number and the bank's SWIFT/BIC, name, city and country."
                )
            )
        return {
            "foreign_account_details": (
                "Account: %s; SWIFT/BIC: %s; Bank: %s; City: %s; Country: %s"
                % (
                    account.sanitized_acc_number,
                    bic,
                    bank.name,
                    bank.city,
                    bank.country.with_context(lang=None).name,
                )
            )
        }

    def _render_payload(self, data):
        return wire.render(
            data["payer"],
            data["period"],
            data["rows"],
            data["signed_on"],
            period_from=data.get("period_from"),
            period_to=data.get("period_to"),
            recharge_history=data.get("recharge_history", []),
            **{
                key: data[key]
                for key in (
                    "grounds",
                    "filing_type",
                    "discovered_on",
                    "previous_tax",
                    "adjustments",
                    "representative",
                    "refund",
                )
            },
        )

    def action_compute_lines(self):
        self._lock()
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Reset the DFT notice before recomputing."))
            rec._cssk_workflow_write({"payload": rec._sources(), "state": "preview"})
            rec._warn_domestic_bank_self_assessment()
        return True

    def _warn_domestic_bank_self_assessment(self):
        self.ensure_one()
        if not self.grounds_c or self.grounds_d or self.grounds_e:
            return
        accounts = self.source_ids.filtered(
            lambda source: source.kind in {"transfer", "cash", "card"}
        ).mapped("move_line_id.journal_id.bank_account_id")
        if any((bank.sanitized_acc_number or "").startswith("SK") for bank in accounts):
            self.message_post(
                body=_(
                    "A selected bank journal has a Slovak account, but only foreign-provider payer grounds are selected. Verify whether the domestic bank already collected this tax. Special-account grounds can legitimately concern a domestic account; this warning does not change the calculated amount."
                )
            )

    def _cssk_preflight_export(self):
        if self._sources() != self.payload:
            raise UserError(
                _("DFT sources changed. Reset and recompute before export or filing.")
            )
        if (
            self.source_history
            and self._render_payload(self.source_history[-1]["payload"])
            != self._render_xml()
        ):
            raise UserError(
                _(
                    "Create a separate correction instead of replacing a filed DFT notice."
                )
            )
        return True

    def _render_xml(self):
        return self._render_payload(self.payload)

    def _validate_against_schema(self, content):
        with open(
            file_path("l10n_sk_transaction_tax/data/ozndft_2026.xsd"), "rb"
        ) as stream:
            schema = stream.read()
        if hashlib.sha256(schema).hexdigest() != wire.SCHEMA_SHA256:
            raise UserError(_("The pinned DFT schema changed unexpectedly."))
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
                rec._check_exported_payload()
                rec._check_frozen_allocations()
                rec._warn_current_source_drift()
                rec._warn_recorded_filing_date()
                if (
                    rec.xml_attachment_id.res_model != MODEL
                    or rec.xml_attachment_id.res_id != rec.id
                ):
                    raise UserError(
                        _("The exported attachment does not belong to this DFT notice.")
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

    def _warn_recorded_filing_date(self):
        """A later local entry cannot establish an earlier actual portal filing.

        Keep legitimate retrospective recording possible and retain the exact
        export. Its actual filing date still decides corrective/additional;
        the current recording date independently triggers receipt verification.
        """
        self.ensure_one()
        period = fields.Date.to_date(self.payload["period"] + "-01")
        deadline = monthly_deadline(period)
        declared = fields.Date.to_date(self.payload["filing_on"])
        recorded = fields.Date.context_today(self)
        if declared <= deadline < recorded:
            self.message_post(
                body=_(
                    "This filing is being recorded after its statutory deadline. Verify the declared actual filing date %(filed)s against the portal receipt; the local recording date is %(recorded)s. If a corrective notice was actually filed after %(deadline)s, use an additional notice instead. The retained XML is unchanged.",
                    filed=str(declared),
                    recorded=str(recorded),
                    deadline=str(deadline),
                )
            )

    def _check_exported_payload(self):
        """Filing attests the exported bytes, never today's regenerated master."""
        self.ensure_one()
        if not self.payload or not self._cssk_has_retained_xml_attachment():
            raise UserError(
                _("The retained DFT payload must match its exported attachment.")
            )

    def _check_frozen_allocations(self):
        """Serialised filing still consumes the retained source amounts once."""
        self.ensure_one()
        latest = self._latest_filed()
        if latest and latest not in (self, self.original_return_id):
            raise UserError(
                _("Base a DFT correction on the immediately previous filed notice.")
            )
        previous = self._allocated_native_sources()
        allocated = defaultdict(Decimal)
        for row, facts in zip(self.payload["rows"], self.payload["source_facts"]):
            if row["kind"] == "card":
                continue
            key = facts["line_id"]
            allocated[key] += Decimal(facts["allocated_source_amount"])
            if allocated[key] + previous[key] > Decimal(facts["source_amount"]):
                raise UserError(
                    _(
                        "This native transaction source is already allocated in another filed DFT month. Use only its remaining amount."
                    )
                )
        previous = self._allocated_credits()
        allocated = defaultdict(Decimal)
        for row in self.payload["adjustments"]:
            key = row["line_id"]
            allocated[key] += abs(Decimal(row["amount"]))
            if allocated[key] + previous[key] > abs(Decimal(str(row["balance"]))):
                raise UserError(
                    _(
                        "This actual tax source is already allocated in another filed DFT month. Use only its remaining amount."
                    )
                )

    def _warn_current_source_drift(self):
        """Drift needs a reviewed correction; it cannot rewrite a filed copy."""
        self.ensure_one()
        try:
            changed = self._sources() != self.payload
        except AccessError:
            raise
        except UserError:
            changed = True
        if changed:
            self.message_post(
                body=_(
                    "Current DFT sources differ from the retained export. Review whether a separate correction is required; the exported or filed copy is unchanged."
                )
            )

        if self.filing_type == "regular" and self.filing_on > monthly_deadline(
            self.period
        ):
            self.message_post(
                body=_("This regular DFT notice is filed after its statutory deadline.")
            )
        if not self.grounds_d and any(
            Decimal(row["amount"]) < 0 for row in self.payload["adjustments"]
        ):
            self.message_post(
                body=_(
                    "Review negative DFT reductions without recharged-cost payer grounds; section 10(5) applies to those grounds."
                )
            )

    def action_reset_to_draft(self):
        self._lock()
        if not any(rec.filed_history_ids for rec in self):
            self._cssk_workflow_write({"state": "draft"})
            return True
        return super().action_reset_to_draft()

    def action_create_amendment(self):
        self.ensure_one()
        self._lock()
        prior = self._latest_filed()
        if not prior:
            raise UserError(
                _(
                    "Select an actually filed DFT notice before preparing its correction."
                )
            )
        if prior != self:
            return prior.action_create_amendment()
        action = super().action_create_amendment()
        today = fields.Date.context_today(self)
        deadline = monthly_deadline(self.period)
        self.browse(action["res_id"]).write(
            {
                "signed_on": today,
                "filing_on": today,
                "filing_type": "corrective" if today <= deadline else "additional",
                "discovery_date": today if today > deadline else False,
            }
        )
        return action

    def action_post_provision(self):
        self.ensure_one()
        self._lock()
        if self.state == "draft":
            raise UserError(_("Compute the DFT notice before posting its tax."))
        if self.state == "submitted":
            self._check_exported_payload()
            if (
                not self.source_history
                or self.source_history[-1]["payload"] != self.payload
            ):
                raise UserError(
                    _("Post the DFT liability from the retained filed payload.")
                )
            self._warn_current_source_drift()
        else:
            self._cssk_preflight_export()
        exp, pay, journal = (
            self.provision_expense_account_id,
            self.provision_payable_account_id,
            self.provision_journal_id,
        )
        if (
            not exp.code.startswith("538")
            or not pay.code.startswith("345")
            or journal.type != "general"
        ):
            raise UserError(_("Select the general journal and DFT accounts 538/345."))
        chain, prior = self, self.original_return_id
        while prior:
            chain |= prior
            prior = prior.original_return_id
        moves = chain.provision_history_ids
        # Native reversal links keep independently reversed provisions visible.
        frontier = moves
        while frontier:
            frontier = frontier.reversal_move_ids - moves
            moves |= frontier
        booked = -sum(
            moves.filtered(lambda move: move.state == "posted")
            .line_ids.filtered(lambda line: line.account_id.code.startswith("345"))
            .mapped("balance")
        )
        amount = self.currency_id.round(float(self.payload["total"]) - booked)
        if self.provision_move_id and amount:
            raise UserError(
                _(
                    "Reverse the existing unfiled provision or create a separate filed correction before changing the booked DFT amount."
                )
            )
        if not amount:
            return True
        with self.env.cr.savepoint():
            move = self.env["account.move"].create(
                {
                    "company_id": self.company_id.id,
                    "journal_id": journal.id,
                    "date": self.period.replace(
                        day=monthrange(self.period.year, self.period.month)[1]
                    )
                    if not self.original_return_id
                    else self.signed_on,
                    "ref": self.name,
                    "line_ids": [
                        Command.create(
                            {
                                "name": self.name,
                                "account_id": exp.id,
                                "debit": max(amount, 0),
                                "credit": max(-amount, 0),
                            }
                        ),
                        Command.create(
                            {
                                "name": self.name,
                                "account_id": pay.id,
                                "debit": max(-amount, 0),
                                "credit": max(amount, 0),
                            }
                        ),
                    ],
                }
            )
            move.action_post()
            self._cssk_workflow_write(
                {
                    "provision_move_id": move.id,
                    "provision_history_ids": [Command.link(move.id)],
                }
            )
        return True

    def action_reverse_provision(self):
        self.ensure_one()
        self._lock()
        if self.filed_history_ids:
            raise UserError(
                _("Correct filed DFT through a separate correction notice.")
            )
        move = self.provision_move_id
        if not move:
            return True
        with self.env.cr.savepoint():
            existing = move.reversal_move_ids.filtered(
                lambda row: row.state == "posted"
            )
            if existing:
                self._cssk_workflow_write(
                    {
                        "provision_history_ids": [
                            Command.link(row.id) for row in existing
                        ]
                    }
                )
            elif move.state == "posted":
                reversals = move._reverse_moves(
                    [{"date": move.date, "ref": _("Reversal of %s", move.name)}],
                    cancel=True,
                )
                self._cssk_workflow_write(
                    {
                        "provision_history_ids": [
                            Command.link(row.id) for row in reversals
                        ]
                    }
                )
            elif move.state == "draft":
                raise UserError(
                    _(
                        "Post or remove the unposted native provision before reversing it."
                    )
                )
            self._cssk_workflow_write({"provision_move_id": False})
        return True

    def unlink(self):
        self._lock()
        if any(rec.filed_history_ids or rec.provision_history_ids for rec in self):
            raise UserError(_("Retain DFT notices with filing or accounting evidence."))
        return super().unlink()


class DftEditableSource(models.AbstractModel):
    _name = "l10n.sk.dft.editable.source.mixin"
    _description = "Shared DFT draft-source editing lifecycle"

    def _draft_parents(self, parents):
        parents._lock()
        if any(rec.state != "draft" for rec in parents):
            raise UserError(_("Reset the DFT notice before changing its source rows."))

    @api.model_create_multi
    def create(self, values_list):
        if "default_company_id" in self.env.context or any(
            "company_id" in values for values in values_list
        ):
            raise UserError(_("DFT source ownership follows its notice."))
        default = self.default_get(["notice_id"]).get("notice_id")
        self._draft_parents(
            self.env[MODEL].browse(
                [
                    values.get("notice_id", default)
                    for values in values_list
                    if values.get("notice_id", default)
                ]
            )
        )
        return super().create(values_list)

    def write(self, values):
        if "company_id" in values:
            raise UserError(_("DFT source ownership follows its notice."))
        self._draft_parents(
            self.notice_id | self.env[MODEL].browse(values.get("notice_id") or [])
        )
        return super().write({"reviewed": False, **values})

    def unlink(self):
        self._draft_parents(self.notice_id)
        return super().unlink()


class DftSource(models.Model):
    _name = "l10n.sk.transaction.tax.source"
    _inherit = "l10n.sk.dft.editable.source.mixin"
    _description = "Reviewed native DFT transaction source"
    _check_company_auto = True

    notice_id = fields.Many2one(
        MODEL, required=True, check_company=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="notice_id.company_id", store=True)
    move_line_id = fields.Many2one(
        "account.move.line", required=True, check_company=True, ondelete="restrict"
    )
    kind = fields.Selection(
        [
            (key, label)
            for key, label in (
                ("transfer", "Transfer"),
                ("cash", "Cash withdrawal"),
                ("card", "Annual used card"),
                ("recharge_unknown", "Unidentified recharged transaction"),
                ("recharge_known", "Identified recharged transaction"),
                ("recharge_excluded", "Excluded recharged transaction"),
                ("bank_collected", "Collected by bank"),
                ("excluded", "Excluded from tax"),
            )
        ],
        required=True,
    )
    actual_on = fields.Date(required=True)
    source_reference = fields.Char(required=True)
    classification_reference = fields.Char()
    transaction_reference = fields.Char(
        help="Identified original third-party transaction, or unique individual bank-batch payment reference."
    )
    bank_batch = fields.Boolean(
        help="The bank ledger line aggregates several payments. Enter every reviewed individual payment with a unique transaction reference and its actual amount."
    )
    reviewed = fields.Boolean()
    source_amount = fields.Char(
        help="Allocation in the native line currency. Empty uses the full transaction."
    )
    euro_quote = fields.Char(
        default="1",
        help="Official quote: units of source currency for one euro. Do not round the converted base.",
    )
    exchange_reference = fields.Char(
        help="Official ECB/NBS rate valid on the transaction date."
    )
    card_reference = fields.Char(
        help="Stable card reference, never a full card number."
    )

    def _source_values(self):
        self.ensure_one()
        line = self.move_line_id
        if line.move_id.state != "posted" or line.company_id != self.company_id:
            raise UserError(_("Use posted native source lines of the same company."))
        _check_unreversed_source(line)
        recharged = self.kind.startswith("recharge_")
        if recharged and not (self.transaction_reference or "").strip():
            raise UserError(
                _(
                    "Retain the original third-party transaction or cost reference for each recharged source."
                )
            )
        if not recharged and (
            line.account_id.account_type != "asset_cash"
            or line.balance >= 0
            or line.journal_id.type != "bank"
            or line.account_id != line.journal_id.default_account_id
        ):
            raise UserError(
                _(
                    "A bank transaction must reference the posted credit of a bank journal's payment account."
                )
            )
        if recharged and line.balance <= 0:
            raise UserError(
                _(
                    "Recharged costs need the actual liability settlement, including a reviewed offset."
                )
            )
        currency = line.currency_id or line.company_currency_id
        original = (
            abs(wire.number(line.amount_currency, signed=True))
            if currency != self.company_id.currency_id
            else abs(wire.number(line.balance, signed=True))
        )
        allocated = wire.number(self.source_amount) if self.source_amount else original
        quote = wire.number(self.euro_quote)
        if allocated > original or not quote:
            raise UserError(
                _(
                    "Review the native transaction allocation and positive exchange quote."
                )
            )
        if self.bank_batch and (
            self.kind == "card"
            or recharged
            or not (self.transaction_reference or "").strip()
            or not self.source_amount
        ):
            raise UserError(
                _(
                    "A bank batch needs an explicit amount and unique reference for every individual payment."
                )
            )
        if not recharged and not self.bank_batch and allocated != original:
            raise UserError(
                _(
                    "A resident payer's bank transfer or cash withdrawal uses the whole actual debit, not an arbitrary cost allocation."
                )
            )
        if allocated != Decimal(str(currency.round(float(allocated)))):
            raise UserError(
                _(
                    "Allocate whole monetary units of the source currency; do not round the converted EUR tax base."
                )
            )
        if (
            currency.name == "EUR"
            and quote != 1
            or currency.name != "EUR"
            and not (self.exchange_reference or "").strip()
        ):
            raise UserError(
                _(
                    "A foreign-currency DFT source needs the official dated exchange quote; EUR uses one."
                )
            )
        row = {
            "transaction_key": (
                "card:"
                + str(self.notice_id.period.year)
                + ":"
                + (self.card_reference or "")
            )
            if self.kind == "card"
            else "recharge:" + self.transaction_reference
            if recharged
            else "bank:%s:%s" % (line.id, self.transaction_reference.strip())
            if self.bank_batch
            else str(line.id),
            "kind": self.kind,
            "base_eur": str(allocated / quote),
            "actual_on": str(self.actual_on),
            "source_reference": self.source_reference,
            "reviewed": self.reviewed,
            "classification_reference": self.classification_reference,
            "card_reference": self.card_reference,
        }
        return row, {
            "line_id": line.id,
            "move_id": line.move_id.id,
            "account_id": line.account_id.id,
            "date": str(line.date),
            "balance": line.balance,
            "currency_id": currency.id,
            "source_amount": str(original),
            "allocated_source_amount": str(allocated),
            "quote": str(quote),
            "exchange_reference": self.exchange_reference or "",
            "transaction_reference": self.transaction_reference or "",
            "bank_batch": self.bank_batch,
        }


class DftAdjustment(models.Model):
    _name = "l10n.sk.transaction.tax.adjustment"
    _description = "Reviewed DFT reduction or correction evidence"
    _inherit = "l10n.sk.dft.editable.source.mixin"
    _check_company_auto = True

    notice_id = fields.Many2one(
        MODEL, required=True, check_company=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="notice_id.company_id", store=True)
    move_line_id = fields.Many2one(
        "account.move.line", required=True, check_company=True, ondelete="restrict"
    )
    source_reference = fields.Char(required=True)
    reviewed = fields.Boolean()

    amount = fields.Float(required=True, digits=(16, 2))

    def _source_values(self):
        self.ensure_one()
        line = self.move_line_id
        _check_unreversed_source(line)
        root = line.move_id
        while root.reversed_entry_id:
            root = root.reversed_entry_id
        if self.env[MODEL].search_count([("provision_history_ids", "in", root.ids)]):
            raise UserError(
                _(
                    "The module's own provision is not an actual tax payment or reduction source."
                )
            )
        if (
            line.company_id != self.company_id
            or line.move_id.state != "posted"
            or not line.account_id.code.startswith(("538", "345"))
            or line.date > self.notice_id.filing_on
        ):
            raise UserError(
                _(
                    "A DFT adjustment needs its actual posted tax source and retained legal allocation evidence."
                )
            )
        if abs(wire.number(self.amount, signed=True)) > abs(
            wire.number(line.balance, signed=True)
        ):
            raise UserError(
                _("A DFT adjustment cannot exceed its actual posted tax source.")
            )
        return {
            "amount": str(self.amount),
            "reviewed": self.reviewed,
            "source_reference": self.source_reference,
            "line_id": line.id,
            "move_id": line.move_id.id,
            "balance": line.balance,
            "date": str(line.date),
        }


class DftAttachment(models.Model):
    _inherit = "ir.attachment"

    def _check_dft_archive(self, values=None):
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
                        current = (
                            attachment[key].id
                            if key == "company_id"
                            else attachment[key]
                        )
                        unchanged = unchanged and values[key] == current
                for key in ("raw", "datas"):
                    if key in values:
                        content = values[key] or b""
                        content = (
                            content.encode() if isinstance(content, str) else content
                        )
                        content = (
                            base64.b64decode(content) if key == "datas" else content
                        )
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
                raise UserError(_("The exported or filed DFT XML is immutable."))

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
            self._check_dft_archive(values)
        return super().write(values)

    def unlink(self):
        self._check_dft_archive()
        return super().unlink()


class DftCompanyCoordinator(models.Model):
    _inherit = "res.company"

    l10n_sk_dft_epoch = fields.Datetime(
        string="DFT source coordination timestamp",
        readonly=True,
        copy=False,
        help="Internal non-key concurrency marker for DFT allocations across periods; not a tax or accounting fact.",
    )
