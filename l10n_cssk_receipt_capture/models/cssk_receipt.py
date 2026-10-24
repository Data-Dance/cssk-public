# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging
import time
from datetime import timedelta

import pytz
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools.amounts import (
    flatten_label, normalize_vat, reconciles, same_rate, split_gross,
)
from ..tools.errors import CaptureFailed, ProviderUnavailable
from ..tools.qr import decode_qr_payloads, decoder_available

_logger = logging.getLogger(__name__)

#: Delays before each automatic retry of a TRANSIENT failure. A refusal, an
#: unregistered receipt or a photograph the model cannot read is never retried
#: on a timer: the same request would get the same answer and cost the same.
AUTO_RETRY_DELAYS = (timedelta(minutes=15), timedelta(hours=1), timedelta(hours=4))

#: The amount up to which a till receipt is itself a simplified tax document,
#: and so enough to deduct its VAT. Above it the buyer needs a full invoice.
#: Both verified against the consolidated texts in force 1. 1.–31. 12. 2026.
SIMPLIFIED_INVOICE_LIMITS = {
    # zákon č. 222/2004 Z. z.: § 74 ods. 3 písm. b) makes a receipt from a
    # pokladnica e-kasa klient a zjednodušená faktúra "ak cena tovaru alebo
    # služby vrátane dane nie je viac ako 400 eur"; § 51 ods. 1 písm. a) makes
    # the deduction depend on having a faktúra.
    "SK": (400.0, "EUR",
           "§ 74 ods. 3 písm. b) a § 51 ods. 1 písm. a) zákona č. 222/2004 Z. z."),
    # zákon č. 235/2004 Sb.: § 30 odst. 1 — a zjednodušený daňový doklad only
    # "pokud celková částka za plnění na daňovém dokladu není vyšší než 10000 Kč".
    "CZ": (10000.0, "CZK", "§ 30 odst. 1 zákona č. 235/2004 Sb."),
}


class CSSKReceipt(models.Model):
    """A captured cash-register receipt.

    The lifecycle is: ``new`` (we hold a photo and/or a QR payload) → a provider
    reads it → ``captured`` when everything reconciles, ``review`` when it does
    not, ``error`` when the source refused → ``done`` once a document exists.
    """

    _name = "cssk.receipt"
    _description = "Captured Fiscal Receipt"
    _inherit = ["mail.thread"]
    _order = "issue_date desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company, index=True)
    currency_id = fields.Many2one(
        "res.currency", required=True,
        default=lambda s: s.env.company.currency_id)
    state = fields.Selection(
        [
            ("new", "New"),
            ("captured", "Captured"),
            ("review", "Needs Review"),
            ("error", "Error"),
            ("done", "Posted"),
        ],
        default="new", required=True, tracking=True, index=True)

    # --- acquisition ---------------------------------------------------
    provider_id = fields.Many2one(
        "cssk.receipt.provider", string="Capture provider", tracking=True)
    qr_raw = fields.Char(
        string="QR payload",
        help="The literal string decoded from the receipt's QR code.")
    attachment_id = fields.Many2one(
        "ir.attachment", string="Source image", ondelete="set null")
    payload_raw = fields.Text(
        string="Provider payload", readonly=True, copy=False,
        help="Verbatim response from the capture source, kept for audit.")
    captured_on = fields.Datetime(readonly=True, copy=False)
    review_reason = fields.Text(readonly=True, copy=False)
    qr_source = fields.Selection(
        [
            ("manual", "Entered by hand"),
            ("decoded", "Read from the photograph"),
            ("scanned", "Scanned with the camera"),
            ("printed", "Rebuilt from identifiers printed on the receipt"),
        ],
        string="QR origin", readonly=True, copy=False)
    qr_detected = fields.Text(
        string="Codes on the photograph", readonly=True, copy=False,
        help="Every QR code found on the photograph, and which one was used. A "
             "receipt can carry several — a loyalty link above the fiscal code.")
    printed_identifiers = fields.Text(
        readonly=True, copy=False,
        help="Fiscal identifiers an AI reading found printed on the receipt "
             "(JSON). Used to look the receipt up when its QR will not decode.")

    # --- attempts ------------------------------------------------------
    attempt_ids = fields.One2many(
        "cssk.receipt.attempt", "receipt_id", string="Attempts", readonly=True)
    attempt_count = fields.Integer(compute="_compute_attempt_stats")
    total_cost = fields.Float(
        compute="_compute_attempt_stats", digits=(16, 6),
        help="What every attempt on this receipt cost, failed ones included.")
    next_attempt_at = fields.Datetime(
        readonly=True, copy=False, index=True,
        help="When a transient failure will be retried automatically.")

    # ``receipt_uid`` is the deduplication key and must come from the source,
    # never from the QR string: an off-line Slovak receipt is printed without an
    # identifier but acquires one as soon as the till catches up, so the same
    # purchase has two possible QR payloads and exactly one identifier.
    receipt_uid = fields.Char(
        string="Receipt identifier", index=True, copy=False, tracking=True)

    # --- seller --------------------------------------------------------
    partner_id = fields.Many2one(
        "res.partner", string="Seller", tracking=True,
        domain="[('is_company', '=', True)]")
    seller_name = fields.Char(tracking=True)
    seller_vat = fields.Char(
        string="VAT number",
        help="The VAT identification number as printed (IČ DPH / DIČ). Not "
             "derivable from the tax number: a member of a VAT group files "
             "under the group's number, which is unrelated to its own.")
    seller_tax_id = fields.Char(
        string="Tax number", help="DIČ / daňové identifikační číslo.")
    seller_reg_id = fields.Char(string="Company ID", help="IČO.")
    seller_vat_payer = fields.Boolean(string="Seller is VAT-registered")
    premises_note = fields.Char(
        string="Premises",
        help="Where the receipt was issued, which is usually not the seller's "
             "registered address — a motorway service station, a branch. Kept "
             "as a note so it never lands on the partner.")

    # --- money ---------------------------------------------------------
    issue_date = fields.Datetime(tracking=True)
    issue_tz = fields.Char(
        readonly=True, copy=False,
        help="The time zone the receipt's printed time was in. The issue date "
             "is stored in UTC like every Odoo datetime; this is what turns it "
             "back into the date on the paper.")
    amount_total = fields.Monetary(tracking=True)
    amount_untaxed = fields.Monetary(compute="_compute_amounts", store=True)
    amount_tax = fields.Monetary(compute="_compute_amounts", store=True)
    line_ids = fields.One2many("cssk.receipt.line", "receipt_id")
    tax_summary_ids = fields.One2many("cssk.receipt.tax", "receipt_id")
    vat_full_invoice = fields.Boolean(
        string="Full invoice held", tracking=True, copy=False,
        help="Tick when a full invoice for this purchase is in hand: its VAT is "
             "then deductible whatever the receipt's amount. A separate field "
             "rather than an editable computed one, because a recompute would "
             "silently undo an edit to that.")
    vat_deductible = fields.Boolean(
        string="VAT deductible", compute="_compute_vat_deductible", store=True,
        help="Whether the VAT on this receipt is deducted. Off when the receipt "
             "is above the amount up to which a till receipt is a simplified "
             "invoice and no full invoice is held: the purchase is then booked at "
             "its gross amount with the VAT as part of the cost.")
    vat_deductible_note = fields.Text(
        compute="_compute_vat_deductible_note", store=True, readonly=True)

    # --- outcome -------------------------------------------------------
    move_id = fields.Many2one(
        "account.move", string="Vendor bill", readonly=True, copy=False)

    _uid_company_uniq = models.Constraint(
        "unique(company_id, receipt_uid)",
        "This receipt has already been captured for this company.",
    )

    # ------------------------------------------------------------------
    # compute
    # ------------------------------------------------------------------
    @api.depends("seller_name", "partner_id.name", "issue_date", "issue_tz",
                 "receipt_uid")
    def _compute_name(self):
        for receipt in self:
            seller = receipt.partner_id.name or receipt.seller_name
            if seller and receipt.issue_date:
                receipt.name = "%s · %s" % (
                    seller, fields.Date.to_string(receipt._issue_local_date()))
            elif seller:
                receipt.name = seller
            else:
                receipt.name = receipt.receipt_uid or _("Receipt (uncaptured)")

    def _round(self, amount):
        """Round to the receipt's currency, so float drift never decides a gate."""
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        return currency.round(amount) if currency else round(amount, 2)

    @api.depends("tax_summary_ids.amount_untaxed", "tax_summary_ids.amount_tax",
                 "line_ids.amount_untaxed", "line_ids.amount_tax")
    def _compute_amounts(self):
        """Totals come from the recap when there is one, the lines otherwise.

        The recap is the authority: it is the figure the seller reported and the
        figure a tax audit compares against. Summing the lines instead can
        differ by a cent per rate once each line is rounded on its own.
        """
        for receipt in self:
            source = receipt.tax_summary_ids or receipt.line_ids
            receipt.amount_untaxed = receipt._round(
                sum(source.mapped("amount_untaxed")))
            receipt.amount_tax = receipt._round(sum(source.mapped("amount_tax")))

    # ------------------------------------------------------------------
    # capture
    # ------------------------------------------------------------------
    @api.depends("attempt_ids.cost")
    def _compute_attempt_stats(self):
        for receipt in self:
            receipt.attempt_count = len(receipt.attempt_ids)
            receipt.total_cost = sum(receipt.attempt_ids.mapped("cost"))

    # ------------------------------------------------------------------
    # time
    # ------------------------------------------------------------------
    def _default_issue_tz(self):
        self.ensure_one()
        return (self.env.user.tz or self.company_id.partner_id.tz
                or "Europe/Bratislava")

    @api.model
    def _local_to_utc(self, naive, tzname):
        """A naive time read off the paper, as the naive UTC Odoo stores."""
        if not naive:
            return naive
        try:
            tz = pytz.timezone(tzname)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone("Europe/Bratislava")
        # is_dst=False: during the autumn hour that happens twice, take the
        # later one rather than refuse a receipt printed in it.
        return tz.localize(naive, is_dst=False).astimezone(pytz.utc).replace(
            tzinfo=None)

    def _issue_local_date(self):
        """The date printed on the receipt.

        Not ``issue_date.date()``: that is the UTC date, a day early for every
        receipt printed between midnight and 01:00 or 02:00 local time.
        """
        self.ensure_one()
        if not self.issue_date:
            return False
        tz = pytz.timezone(self.issue_tz or self._default_issue_tz())
        return pytz.utc.localize(self.issue_date).astimezone(tz).date()

    # ------------------------------------------------------------------
    # capture
    # ------------------------------------------------------------------
    def _candidate_providers(self):
        """Active providers that could read this receipt now, best first.

        Asked afresh on every capture, never taken from ``provider_id``: that
        field says who read the receipt LAST. A receipt the AI reader failed on
        and that the user then scanned has a QR now, and must go to the code
        reader, not back to the model.
        """
        self.ensure_one()
        out = self.env["cssk.receipt.provider"]
        for provider in self.env["cssk.receipt.provider"].search([]):
            impl = provider._implementation()
            if impl is not None and impl._can_capture(self):
                out |= provider
        return out

    @api.model
    def _provider_accepting(self, payload, include_archived=False):
        """The first provider that can look a receipt up by this QR payload.

        ``include_archived`` asks only so that a fiscal code nobody is enabled
        to read is not reported as "not a receipt verification code".
        """
        Provider = self.env["cssk.receipt.provider"]
        if include_archived:
            Provider = Provider.with_context(active_test=False)
        for provider in Provider.search([]):
            impl = provider._implementation()
            if impl is not None and impl._accepts_qr(payload):
                return provider
        return self.env["cssk.receipt.provider"]

    def _prepare_qr(self):
        """Read the QR codes off the photograph, if no payload is known yet.

        Every code is decoded and offered to the providers; the first one a
        provider recognises is used. A loyalty link printed above the fiscal
        code is ignored, and said so in ``qr_detected``.
        """
        self.ensure_one()
        attachment = self.attachment_id
        if self.qr_raw or not attachment:
            return
        if not (attachment.mimetype or "").startswith("image/"):
            return
        if not decoder_available():
            self.qr_detected = _(
                "The QR code on the photograph was not read: no QR decoder is "
                "installed on this server (the Python package zxing-cpp).")
            return
        payloads, unreadable = decode_qr_payloads(attachment.raw or b"")
        chosen = False
        lines = []
        for payload in payloads:
            provider = self._provider_accepting(payload)
            if provider and not chosen:
                chosen = payload
                lines.append(_("Used (%(reader)s): %(code)s",
                               reader=provider.name, code=payload))
            elif provider:
                lines.append(_("Ignored, a further verification code: %s",
                               payload[:120]))
            elif archived := self._provider_accepting(payload, include_archived=True):
                lines.append(_(
                    "Not used — %(reader)s reads this code but is archived: %(code)s",
                    reader=archived.name, code=payload[:120]))
            else:
                lines.append(_("Ignored, not a receipt verification code: %s",
                               payload[:120]))
        if unreadable and not chosen:
            lines.append(_(
                "A QR code is on the photograph but could not be read — printed "
                "too densely, or damaged. Scan it with the camera instead."))
        elif not payloads and not unreadable:
            lines.append(_("No QR code found on the photograph."))
        vals = {"qr_detected": "\n".join(lines)}
        if chosen:
            vals.update(qr_raw=chosen, qr_source="decoded")
        self.write(vals)

    def action_capture(self):
        """Read each receipt and reconcile the result. Never raises for one
        receipt's failure: the reason is stored on it, and shown."""
        for receipt in self:
            receipt._capture_once()
        return True

    def _capture_once(self):
        self.ensure_one()
        if self.qr_raw and not self.qr_source:
            self.qr_source = "manual"
        self._prepare_qr()
        providers = self._candidate_providers()
        if not providers:
            self._fail(self._why_nothing_can_read())
            return
        unavailable = []
        for provider in providers:
            impl = provider._get_implementation()
            started, started_at = time.monotonic(), fields.Datetime.now()
            try:
                vals = impl._capture(self)
                usage = vals.pop("_usage", None) or {}
                self._apply_capture(provider, impl, vals)
            except ProviderUnavailable as err:
                self._log_attempt(provider, "unavailable", started, started_at,
                                  message=str(err))
                unavailable.append("%s: %s" % (provider.name, err))
                continue
            except CaptureFailed as err:
                self._log_attempt(provider, "error", started, started_at,
                                  message=str(err), usage=err.usage,
                                  transient=err.transient)
                self._fail(str(err), provider=provider,
                           transient=err.transient, retry_after=err.retry_after)
                return
            except UserError as err:
                self._log_attempt(provider, "error", started, started_at,
                                  message=str(err))
                self._fail(str(err), provider=provider)
                return
            self._log_attempt(provider, self.state, started, started_at,
                              message=self.review_reason or False, usage=usage)
            self._verify_printed_identifiers()
            return
        self._fail("\n".join(unavailable))

    def _apply_capture(self, provider, impl, vals):
        """Write a provider's reading onto the receipt, then gate it."""
        self.ensure_one()
        # Not called ``uid``: when the environment carries no language — a
        # cron, a sudo or test environment — Odoo 19's ``_()`` reads ``cr`` and
        # ``uid`` out of this frame's locals to find one, and a receipt
        # identifier there is taken for a user id.
        identifier = vals.get("receipt_uid")
        if identifier:
            duplicate = self.search([
                ("company_id", "=", self.company_id.id),
                ("receipt_uid", "=", identifier),
                ("id", "!=", self.id),
            ], limit=1)
            if duplicate:
                # Caught here rather than by the unique constraint, which would
                # surface as a database error and abort the whole upload.
                raise CaptureFailed(_(
                    "This receipt has already been captured as %(name)s "
                    "(identifier %(identifier)s).",
                    name=duplicate.display_name, identifier=identifier))
        if vals.get("issue_date"):
            tzname = impl._issue_timezone(self) or self._default_issue_tz()
            vals["issue_date"] = self._local_to_utc(vals["issue_date"], tzname)
            vals["issue_tz"] = tzname
        vals.setdefault("provider_id", provider.id)
        vals["captured_on"] = fields.Datetime.now()
        vals["next_attempt_at"] = False
        # Replace any previous detail rather than appending to it: a second
        # capture of the same receipt must not double its lines.
        for field_name in ("line_ids", "tax_summary_ids"):
            vals[field_name] = (
                [fields.Command.clear()] + list(vals.get(field_name) or []))
        self.write(vals)
        self._post_capture()

    def _log_attempt(self, provider, outcome, started, started_at,
                     message=False, usage=None, transient=False):
        usage = usage or {}
        if outcome not in ("captured", "review", "error", "unavailable"):
            outcome = "captured"
        self.env["cssk.receipt.attempt"].create({
            "receipt_id": self.id,
            "provider_id": provider.id if provider else False,
            "started_at": started_at,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "outcome": outcome,
            "message": message or False,
            "transient": transient,
            "model_label": usage.get("model") or False,
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "cost": float(usage.get("cost") or 0.0),
            "confidence": float(usage.get("confidence") or 0.0),
        })

    def _fail(self, message, provider=None, transient=False, retry_after=None):
        """Park the receipt in ``error`` with a reason a person can act on."""
        self.ensure_one()
        vals = {"state": "error", "review_reason": message,
                "next_attempt_at": False}
        if provider:
            vals["provider_id"] = provider.id
        retry_note = ""
        # Counted in the database: the attempt that just failed was created a
        # moment ago and need not be in this record's cached one2many yet.
        retries_used = self.env["cssk.receipt.attempt"].search_count([
            ("receipt_id", "=", self.id), ("transient", "=", True)]) - 1
        if transient and retries_used < len(AUTO_RETRY_DELAYS):
            delay = AUTO_RETRY_DELAYS[max(retries_used, 0)]
            if retry_after:
                delay = max(delay, timedelta(seconds=int(retry_after)))
            vals["next_attempt_at"] = fields.Datetime.now() + delay
            retry_note = _("It will be retried automatically.")
        self.write(vals)
        body = Markup("<p>%s</p><p>%s</p>") % (_("Capture failed."), message)
        if retry_note:
            body += Markup("<p>%s</p>") % retry_note
        self.message_post(body=body)

    def _why_nothing_can_read(self):
        reasons = []
        if self.qr_detected:
            reasons.append(self.qr_detected)
        if self.attachment_id and not self.qr_raw:
            reasons.append(_(
                "No reader for photographs is available. Configure the AI "
                "reader, or scan the receipt's QR code with the camera."))
        if not self.attachment_id and not self.qr_raw:
            reasons.append(_(
                "There is neither a photograph nor a QR code to read."))
        return "\n".join(reasons) or _("No capture provider can read this receipt.")

    @api.model
    def _cron_retry_transient(self, limit=20):
        """Retry receipts whose last failure was transient and whose time came."""
        due = self.search([
            ("state", "=", "error"),
            ("next_attempt_at", "!=", False),
            ("next_attempt_at", "<=", fields.Datetime.now()),
        ], limit=limit, order="next_attempt_at")
        for receipt in due:
            try:
                # A savepoint per receipt: after a database error the
                # transaction is aborted, and without one the write below — and
                # every receipt after this one — would fail with it.
                with self.env.cr.savepoint():
                    receipt._capture_once()
            except Exception:  # noqa: BLE001 - one receipt must not stop the rest
                _logger.exception("Retrying receipt %s failed", receipt.id)
                receipt.next_attempt_at = False

    # ------------------------------------------------------------------
    # identifiers printed on the paper
    # ------------------------------------------------------------------
    def _verify_printed_identifiers(self):
        """Look the receipt up by the identifiers an AI reading found on it.

        When the QR will not decode — a dense off-line code on a thermal
        printer defeated every decoder tried — the same identifiers are usually
        printed as text beside it. A provider that can look the receipt up by
        them turns them into payloads; the authority's answer replaces the
        model's reading if it finds the receipt, and parks the receipt for
        review if it does not. A misread identifier therefore costs a lookup,
        never a wrong entry.
        """
        self.ensure_one()
        if not self.printed_identifiers or self.qr_source in ("decoded", "scanned",
                                                             "printed"):
            return
        try:
            identifiers = json.loads(self.printed_identifiers)
        except ValueError:
            return
        for provider in self.env["cssk.receipt.provider"].search([]):
            impl = provider._implementation()
            if impl is None or provider == self.provider_id:
                continue
            candidates = impl._qr_from_printed(identifiers) or []
            if not candidates:
                continue
            tried = []
            for payload in candidates[:3]:
                started, started_at = time.monotonic(), fields.Datetime.now()
                previous = {"qr_raw": self.qr_raw, "qr_source": self.qr_source}
                self.write({"qr_raw": payload, "qr_source": "printed"})
                try:
                    vals = impl._capture(self)
                    vals.pop("_usage", None)
                    # Defence in depth: a misread key should simply find
                    # nothing, but if it ever finds a DIFFERENT receipt, its
                    # total will not be the one on the photograph.
                    if self.amount_total and not reconciles(
                            vals.get("amount_total"), self.amount_total):
                        raise CaptureFailed(_(
                            "The registered receipt for these identifiers totals "
                            "%(theirs).2f, not %(ours).2f as on the photograph.",
                            theirs=vals.get("amount_total") or 0.0,
                            ours=self.amount_total))
                    self._apply_capture(provider, impl, vals)
                except ProviderUnavailable as err:
                    self._log_attempt(provider, "unavailable", started,
                                      started_at, message=str(err))
                    self.write(previous)
                    self.message_post(body=_(
                        "The identifiers printed on the receipt could not be "
                        "checked with %(reader)s: %(why)s",
                        reader=provider.name, why=err))
                    return
                except UserError as err:
                    self._log_attempt(provider, "error", started, started_at,
                                      message=str(err))
                    self.write(previous)
                    if isinstance(err, CaptureFailed) and err.transient:
                        return
                    tried.append(payload)
                    continue
                self._log_attempt(provider, self.state, started, started_at,
                                  message=self.review_reason or False)
                self.message_post(body=_(
                    "Confirmed by %s from the identifiers printed on the "
                    "receipt; its figures replace the photograph reading.",
                    provider.name))
                return
            problem = _(
                "The identifiers printed on this receipt did not match a "
                "registered receipt at %(reader)s (tried %(n)s), so the "
                "figures are a reading of the photograph only.",
                reader=provider.name, n=len(tried))
            self.write({
                "state": "review",
                "review_reason": "\n".join(
                    p for p in (self.review_reason, problem) if p),
            })
            return

    # ------------------------------------------------------------------
    # camera scan
    # ------------------------------------------------------------------
    @api.model
    def _scan_hints(self):
        hints = []
        for provider in self.env["cssk.receipt.provider"].search([]):
            impl = provider._implementation()
            hint = impl._scan_hint() if impl is not None else None
            if hint:
                hints.append(hint)
        return " ".join(hints)

    @api.model
    def action_capture_from_scan(self, text):
        """Capture a receipt from a QR code scanned with the camera.

        Returns ``{"retry": True, "message": ...}`` when the code is not one any
        provider can look up — the loyalty link printed above the fiscal code
        is the usual case — so the scanner can stay open; otherwise the action
        that shows the result.
        """
        text = (text or "").strip()
        if not text or not self._provider_accepting(text):
            return {
                "retry": True,
                "message": " ".join(filter(None, [
                    _("That is not a receipt verification code (it reads "
                      "\u201c%s\u201d).", text[:80]),
                    self._scan_hints(),
                ])),
            }
        receipt = self.search([
            ("company_id", "=", self.env.company.id), ("qr_raw", "=", text),
        ], limit=1)
        if not receipt:
            receipt = self.create({"qr_raw": text, "qr_source": "scanned"})
        if receipt.state in ("new", "error"):
            receipt.action_capture()
        return {"retry": False, "action": receipt._scan_result_action()}

    def action_open_attempts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Capture attempts"),
            "res_model": "cssk.receipt.attempt",
            "view_mode": "list,form",
            "domain": [("receipt_id", "=", self.id)],
        }

    def _scan_result_action(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "cssk.receipt",
            "res_id": self.id,
            "views": [[False, "form"]],
            "target": "current",
        }

    def _post_capture(self):
        """Resolve the seller, then gate on the arithmetic."""
        self.ensure_one()
        if not self.partner_id:
            self.partner_id = self._find_partner()
        problems = self._check_reconciliation()
        if problems:
            self.write({"state": "review", "review_reason": "\n".join(problems)})
            self.message_post(body=Markup("<p>%s</p><ul>%s</ul>") % (
                _("Captured but parked for review:"),
                Markup().join(Markup("<li>%s</li>") % p for p in problems)))
        else:
            self.write({"state": "captured", "review_reason": False})
            self.message_post(body=_("Captured and reconciled."))

    # ------------------------------------------------------------------
    # reconciliation gates
    # ------------------------------------------------------------------
    def _check_reconciliation(self):
        """Return a list of human-readable problems; empty means it adds up."""
        self.ensure_one()
        problems = []
        if not self.amount_total:
            problems.append(_("The receipt total is missing."))
            return problems

        if not reconciles(self.amount_untaxed + self.amount_tax, self.amount_total):
            problems.append(_(
                "Base plus VAT (%(sum).2f) does not equal the receipt total "
                "(%(total).2f).",
                sum=self.amount_untaxed + self.amount_tax,
                total=self.amount_total))

        if self.line_ids:
            line_sum = self._round(sum(self.line_ids.mapped("amount_total")))
            if not reconciles(line_sum, self.amount_total):
                problems.append(_(
                    "The lines sum to %(lines).2f but the receipt total is "
                    "%(total).2f.", lines=line_sum, total=self.amount_total))

        # A refund or correction item. The sign convention is undocumented and
        # we have never had a sample, so it is never guessed: an unsigned
        # negative item would otherwise reconcile perfectly while pointing the
        # money the wrong way.
        negatives = self.line_ids.filtered("is_negative")
        if negatives:
            problems.append(_(
                "%(count)s item(s) are marked as returns or corrections. "
                "Receipts carrying them are not posted automatically — check "
                "the signs against the paper before accepting.",
                count=len(negatives)))

        # Each bucket's own arithmetic. Without this a recap that shifts value
        # between base and tax still foots against the items, so VAT could be
        # overstated at an otherwise-correct total.
        for row in self.tax_summary_ids:
            base, tax = split_gross(
                row.amount_untaxed + row.amount_tax, row.vat_rate,
                (self.currency_id or self.company_id.currency_id).rounding or 0.01)
            if not reconciles(base, row.amount_untaxed) or \
                    not reconciles(tax, row.amount_tax):
                problems.append(_(
                    "The %(rate)g%% bucket states %(base).2f + %(tax).2f, but "
                    "%(gross).2f at %(rate)g%% is %(want_base).2f + "
                    "%(want_tax).2f.",
                    rate=row.vat_rate, base=row.amount_untaxed,
                    tax=row.amount_tax,
                    gross=row.amount_untaxed + row.amount_tax,
                    want_base=base, want_tax=tax))

        # Each recap bucket must match the lines assigned to its rate. This is
        # the check that catches a provider reading the wrong rate label.
        if self.line_ids and self.tax_summary_ids:
            for row in self.tax_summary_ids:
                lines = self.line_ids.filtered(
                    lambda l, r=row.vat_rate: same_rate(l.vat_rate, r))
                gross = self._round(sum(lines.mapped("amount_total")))
                if not reconciles(gross, row.amount_untaxed + row.amount_tax):
                    problems.append(_(
                        "At %(rate)s%%, the items total %(gross).2f but the "
                        "receipt's VAT recap says %(recap).2f.",
                        rate=row.vat_rate, gross=gross,
                        recap=row.amount_untaxed + row.amount_tax))
            recap_rates = self.tax_summary_ids.mapped("vat_rate")
            orphans = self.line_ids.filtered(
                lambda l: not any(same_rate(l.vat_rate, r) for r in recap_rates))
            if orphans:
                problems.append(_(
                    "%(count)s item(s) carry a VAT rate the recap does not "
                    "mention (%(rates)s).",
                    count=len(orphans),
                    rates=", ".join(
                        "%g%%" % r for r in sorted(set(orphans.mapped("vat_rate"))))))
        return problems

    def _seller_country_code(self):
        self.ensure_one()
        prefix = normalize_vat(self.seller_vat)[:2]
        if len(prefix) == 2 and prefix.isalpha():
            return "GR" if prefix == "EL" else prefix
        country = (self.company_id.account_fiscal_country_id
                   or self.company_id.country_id)
        return country.code or False

    @api.depends("amount_total", "amount_tax", "currency_id", "seller_vat",
                 "issue_date", "company_id", "vat_full_invoice")
    def _compute_vat_deductible(self):
        """Whether this receipt alone supports deducting its VAT.

        A till receipt is a simplified tax document only up to a statutory
        amount. Above it the receipt is still a perfectly good accounting
        document — there is no cap on issuing one, and the purchase is booked
        in full — but the VAT on it may not be deducted without a full invoice,
        so it becomes part of the cost. Editable: tick it back when a full
        invoice for the purchase is in hand.
        """
        for receipt in self:
            receipt.vat_deductible = (receipt.vat_full_invoice
                                      or not receipt._simplified_invoice_note())

    @api.depends("amount_total", "amount_tax", "currency_id", "seller_vat",
                 "issue_date", "company_id")
    def _compute_vat_deductible_note(self):
        for receipt in self:
            receipt.vat_deductible_note = receipt._simplified_invoice_note() or False

    def _simplified_invoice_note(self):
        """Why the VAT is not deductible from this receipt, or False."""
        self.ensure_one()
        if not self.amount_tax or not self.amount_total:
            return False
        rule = SIMPLIFIED_INVOICE_LIMITS.get(self._seller_country_code())
        if not rule:
            return False
        limit, limit_currency_code, reference = rule
        limit_currency = self.env["res.currency"].with_context(
            active_test=False).search([("name", "=", limit_currency_code)], limit=1)
        if not limit_currency:
            return False
        amount = self.amount_total
        if self.currency_id and self.currency_id != limit_currency:
            amount = self.currency_id._convert(
                amount, limit_currency, self.company_id,
                self._issue_local_date() or fields.Date.context_today(self))
        if limit_currency.compare_amounts(amount, limit) <= 0:
            return False
        return _(
            "This receipt totals %(amount)s %(cur)s including VAT, above the "
            "%(limit)s %(cur)s up to which a till receipt counts as a simplified "
            "invoice (%(ref)s). The purchase is booked in full, but its VAT is "
            "not deductible from the receipt and is part of the cost. Tick "
            "\u201cFull invoice held\u201d if you have one for it.",
            # A plain figure: format() would add the symbol beside the code.
            amount="%.2f" % amount, cur=limit_currency_code,
            limit="%g" % limit, ref=reference)

    def action_force_captured(self):
        """Accept a receipt that failed a gate, on the user's responsibility."""
        for receipt in self.filtered(lambda r: r.state == "review"):
            receipt.message_post(body=Markup("<p>%s</p><ul>%s</ul>") % (
                _("Review overridden by %s. Reported discrepancy:",
                  self.env.user.display_name),
                Markup().join(Markup("<li>%s</li>") % line for line in
                              (receipt.review_reason or "").splitlines() if line)))
            receipt.state = "captured"
        return True

    # ------------------------------------------------------------------
    # seller resolution
    # ------------------------------------------------------------------
    def _find_partner(self):
        """Match the seller on VAT, then tax number, then company id.

        Never on name: two Slovak sole traders can share one, and the whole
        point of capture is that the identifiers are machine-read.
        """
        self.ensure_one()
        Partner = self.env["res.partner"]
        allowed = ["|", ("company_id", "=", False),
                   ("company_id", "=", self.company_id.id)]

        # VAT first, compared normalized. "SK 7199 000 006" and "SK7199000006"
        # are the same number, and no LIKE pattern matches both, so the
        # normalization happens in SQL. The resulting ids are then re-read
        # through the ORM so record rules still apply.
        if self.seller_vat:
            found = self._search_partner_by_normalized("vat", self.seller_vat)
            if found:
                return found

        # IČO is the strongest key on a Czech or Slovak document: exact, stable,
        # and unaffected by VAT-group registration.
        if self.seller_reg_id:
            found = Partner.search(
                [("company_registry", "=", self.seller_reg_id)] + allowed, limit=1)
            if found:
                return found

        if self.seller_tax_id:
            found = self._search_partner_by_normalized(
                "vat", self.seller_tax_id, allow_prefix=True)
            if found:
                return found
        return Partner

    # Columns this method may normalize. The column name is interpolated into
    # SQL, so it is whitelisted rather than trusted — the current callers pass
    # constants, and this keeps that true for the next one.
    _NORMALIZED_SEARCH_FIELDS = ("vat",)

    def _search_partner_by_normalized(self, field, value, allow_prefix=False):
        """Find a partner whose ``field`` equals ``value`` ignoring punctuation.

        Normalizing in SQL rather than in Python because the alternative is
        reading every partner that has a VAT number: no LIKE pattern matches
        both "SK 7199 000 006" and "SK7199000006".

        ``allow_prefix`` additionally accepts a stored value that is the wanted
        one behind a two-letter country prefix, so a tax number matches a VAT
        number built from it. It is deliberately *not* a suffix match: "…0372640"
        would otherwise collide with any longer number ending the same way.
        """
        self.ensure_one()
        if field not in self._NORMALIZED_SEARCH_FIELDS:
            raise ValueError("Refusing to normalize-search on %r" % field)
        wanted = normalize_vat(value)
        if not wanted:
            return self.env["res.partner"]
        patterns = [wanted]
        if allow_prefix:
            # Two placeholders, both parameterised: 'SK' || wanted etc.
            patterns.append("__" + wanted)
        expression = (
            "upper(regexp_replace(%s, '[^A-Za-z0-9]', '', 'g'))" % field)
        self.env.cr.execute(
            """
                SELECT id FROM res_partner
                 WHERE {field} IS NOT NULL
                   AND {expression} LIKE ANY(%s)
                   AND (company_id IS NULL OR company_id = %s)
                 ORDER BY id
                 LIMIT 20
            """.format(field=field, expression=expression),
            (patterns, self.company_id.id),
        )
        ids = [row[0] for row in self.env.cr.fetchall()]
        if not ids:
            return self.env["res.partner"]
        # Back through the ORM so access rules and multi-company rules apply.
        candidates = self.env["res.partner"].search([("id", "in", ids)])
        for candidate in candidates:
            normalized = normalize_vat(candidate.vat)
            if normalized == wanted:
                return candidate
            if allow_prefix and normalized[2:] == wanted \
                    and normalized[:2].isalpha():
                return candidate
        return self.env["res.partner"]

    def _prepare_partner_vals(self):
        """Values for a partner created from the receipt's seller block.

        Only the seller's own registered identity goes in. The premises where
        the receipt was issued is a different address and belongs nowhere near
        the partner record.
        """
        self.ensure_one()
        return {
            "name": self.seller_name or self.seller_vat or _("Unknown seller"),
            "is_company": True,
            "vat": self.seller_vat or False,
            "company_registry": self.seller_reg_id or False,
            "supplier_rank": 1,
        }

    def action_create_partner(self):
        for receipt in self.filtered(lambda r: not r.partner_id):
            receipt.partner_id = self.env["res.partner"].create(
                receipt._prepare_partner_vals())
        return True

    # ------------------------------------------------------------------
    # tax resolution
    # ------------------------------------------------------------------
    def _checked_tax_for_rate(self, rate):
        """``_tax_for_rate``, refusing a tax whose percentage is not that rate.

        A company's rate map is hand-filled, so it can point 19 % at a 23 %
        tax. Caught here rather than downstream because two buckets with equal
        bases and swapped taxes post exactly the amounts the receipt reports —
        every aggregate agrees while each line reports the wrong base on the
        VAT return.
        """
        self.ensure_one()
        tax = self._tax_for_rate(rate)
        if tax and tax.amount_type == "percent" \
                and not same_rate(tax.amount, rate):
            raise UserError(_(
                "%(tax)s is mapped to %(rate)g%% but is a %(actual)g%% tax. "
                "Fix the company's VAT-rate mapping — posting it would report "
                "the wrong base at both rates.",
                tax=tax.display_name, rate=rate, actual=tax.amount))
        return tax

    def _tax_for_rate(self, rate):
        """The company's domestic input tax for a VAT rate.

        Prefers the map that ``account_invoice_ai_extract`` already asks the
        user to fill, so a database that captures both invoices and receipts
        configures its rates once. Falls back to a search when that module is
        not installed.
        """
        self.ensure_one()
        company = self.company_id
        if hasattr(company, "_ai_extract_tax_for_rate"):
            tax = company._ai_extract_tax_for_rate(rate)
            if tax:
                return tax
        default = company.account_purchase_tax_id
        if default and default.amount_type == "percent" \
                and same_rate(default.amount, rate):
            return default
        candidates = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("amount_type", "=", "percent"),
            ("company_id", "=", company.id),
        ]).filtered(lambda tax: same_rate(tax.amount, rate))
        # A stock SK chart has seven 5 % purchase taxes; the EU, reverse-charge
        # and customs ones net their VAT out through a negative repartition
        # line and are never what a till receipt carries.
        domestic = candidates.filtered(lambda tax: not any(
            line.factor_percent < 0
            for line in tax.invoice_repartition_line_ids
            if line.repartition_type == "tax"))
        return (domestic or candidates)[:1]

    # ------------------------------------------------------------------
    # vendor-bill sink
    # ------------------------------------------------------------------
    def _bill_journal(self):
        self.ensure_one()
        journal = self.company_id.cssk_receipt_journal_id
        if not journal:
            journal = self.env["account.journal"].search([
                ("type", "=", "purchase"),
                ("company_id", "=", self.company_id.id),
            ], limit=1)
        if not journal:
            raise UserError(_(
                "No purchase journal is configured for %s.",
                self.company_id.display_name))
        return journal

    def _bill_expense_account(self):
        self.ensure_one()
        account = self.company_id.cssk_receipt_expense_account_id
        if not account:
            raise UserError(_(
                "Set the default receipt expense account in Settings ▸ "
                "Accounting ▸ Fiscal Receipt Capture before posting receipts."))
        return account

    def _prepare_bill_line_vals(self):
        """Bill lines: one per VAT rate, or one per item, per company setting.

        Per rate is the default because it is the only shape that cannot drift:
        the base posted is the base the seller reported. Per item is friendlier
        to read and is offered for those who want it, with the same
        reconciliation check applied to the result.
        """
        self.ensure_one()
        account = self._bill_expense_account()
        vals = []
        if not self.vat_deductible:
            # Booked in full, VAT and all, as cost: nothing is claimed, so no
            # tax is applied and nothing reaches the VAT return.
            source = (self.line_ids
                      if self.company_id.cssk_receipt_bill_detail == "lines"
                      else self.tax_summary_ids)
            for item in source:
                label = (flatten_label(item.name, limit=180)
                         if item._name == "cssk.receipt.line"
                         else _("Receipt items at %g%% VAT", item.vat_rate))
                vals.append(fields.Command.create({
                    "name": _("%s (VAT not deductible)", label),
                    "quantity": 1.0,
                    "price_unit": item.amount_total,
                    "account_id": account.id,
                    "tax_ids": [fields.Command.clear()],
                }))
            if not vals:
                raise UserError(_(
                    "This receipt has neither a VAT recap nor any items, so "
                    "there is nothing to post."))
            return vals
        if self.company_id.cssk_receipt_bill_detail == "lines":
            for line in self.line_ids:
                tax = self._checked_tax_for_rate(line.vat_rate)
                label = flatten_label(line.name, limit=180)
                if line.quantity and line.quantity != 1.0:
                    label = "%s (%g %s)" % (
                        label, line.quantity, line.uom_label or "")
                vals.append(fields.Command.create({
                    "name": label.strip(),
                    # Quantity 1 on purpose: see cssk.receipt.line.
                    "quantity": 1.0,
                    "price_unit": line.amount_untaxed,
                    "account_id": account.id,
                    "tax_ids": [fields.Command.set(tax.ids)],
                }))
        else:
            for row in self.tax_summary_ids:
                tax = self._checked_tax_for_rate(row.vat_rate)
                vals.append(fields.Command.create({
                    "name": _("Receipt items at %g%% VAT", row.vat_rate),
                    "quantity": 1.0,
                    "price_unit": row.amount_untaxed,
                    "account_id": account.id,
                    "tax_ids": [fields.Command.set(tax.ids)],
                }))
        if not vals:
            raise UserError(_(
                "This receipt has neither a VAT recap nor any items, so there "
                "is nothing to post."))
        return vals

    def _prepare_bill_vals(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_(
                "Set the seller on %s before posting it.", self.display_name))
        ref = self.receipt_uid or self.qr_raw or ""
        return {
            # in_receipt is Odoo's own type for an over-the-counter purchase.
            "move_type": "in_receipt",
            "journal_id": self._bill_journal().id,
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            # A receipt entered by hand may have no issue date; a bill must.
            "invoice_date": self._issue_local_date() or fields.Date.context_today(self),
            "date": self._issue_local_date() or fields.Date.context_today(self),
            "ref": ref[:64] or False,
            "invoice_line_ids": self._prepare_bill_line_vals(),
        }

    def action_create_bill(self):
        """Create a DRAFT vendor receipt and verify it against the source."""
        moves = self.env["account.move"]
        for receipt in self:
            if receipt.state not in ("captured",):
                raise UserError(_(
                    "Only a captured, reconciled receipt can be posted. %s is "
                    "%s.", receipt.display_name, receipt.state))
            if receipt.move_id:
                raise UserError(_(
                    "%s already has the vendor bill %s.",
                    receipt.display_name, receipt.move_id.display_name))
            move = self.env["account.move"].create(receipt._prepare_bill_vals())
            receipt._verify_move(move)
            if receipt.attachment_id:
                receipt.attachment_id.copy({
                    "res_model": "account.move", "res_id": move.id})
            receipt.write({"move_id": move.id, "state": "done"})
            receipt.message_post(body=_(
                "Vendor receipt %s created (draft).", move.display_name))
            moves |= move
        return moves

    def _verify_move(self, move):
        """Refuse a document whose tax does not equal the receipt's own.

        Odoo computes tax from the lines it was given; the receipt states what
        the seller actually reported. When those disagree the document is
        wrong — most often because a VAT rate has no tax mapped, so the line
        silently posts untaxed.
        """
        self.ensure_one()
        if not self.vat_deductible:
            if not reconciles(move.amount_total, self.amount_total, tolerance=0.02):
                raise UserError(_(
                    "The document totals %(move).2f but the receipt totals "
                    "%(receipt).2f. Nothing was posted.",
                    move=move.amount_total, receipt=self.amount_total))
            if not reconciles(move.amount_tax, 0.0, tolerance=0.001):
                raise UserError(_(
                    "The VAT on this receipt is not deductible, yet the document "
                    "carries %.2f of VAT. Nothing was posted.", move.amount_tax))
            return
        missing = set()
        included = self.env["account.tax"]
        rates = (self.tax_summary_ids.mapped("vat_rate")
                 if self.company_id.cssk_receipt_bill_detail != "lines"
                 else self.line_ids.mapped("vat_rate"))
        for rate in set(rates):
            if not rate:
                continue
            tax = self._tax_for_rate(rate)
            if not tax:
                missing.add(rate)
            elif tax.price_include:
                included |= tax
        if missing:
            raise UserError(_(
                "No purchase tax is mapped for %(rates)s. Add it to the "
                "company's VAT-rate mapping — without it the receipt would "
                "post without VAT and the deduction would be lost.",
                rates=", ".join("%g%%" % r for r in sorted(missing))))
        if included:
            # A bill line carries the NET amount, so a tax-included tax would
            # read it as a gross and understate the whole document. The totals
            # check below would catch it, but with a number nobody can act on.
            raise UserError(_(
                "The purchase tax %(tax)s is tax-included, but a vendor-bill "
                "line carries the net amount, so the document would come out "
                "lower than the receipt. Map a tax-excluded purchase tax for "
                "this rate, or create the receipt as employee expenses, which "
                "need the tax-included kind.",
                tax=", ".join(included.mapped("display_name"))))
        if not reconciles(move.amount_total, self.amount_total, tolerance=0.02):
            raise UserError(_(
                "The document totals %(move).2f but the receipt totals "
                "%(receipt).2f. Nothing was posted.",
                move=move.amount_total, receipt=self.amount_total))
        if not reconciles(move.amount_tax, self.amount_tax, tolerance=0.02):
            raise UserError(_(
                "The document's VAT is %(move).2f but the receipt reports "
                "%(receipt).2f. Nothing was posted.",
                move=move.amount_tax, receipt=self.amount_tax))
        self._verify_move_per_rate(move)

    def _verify_move_per_rate(self, move):
        """Check each rate's tax separately, not just the document total.

        Two rates can be wrong in opposite directions and still foot: posting
        23 % where the receipt says 19 % and 19 % where it says 23 % leaves
        every aggregate intact while reporting the wrong tax on the VAT return.
        """
        self.ensure_one()
        if not self.tax_summary_ids:
            return
        posted = {}
        for tax_line in move.line_ids.filtered("tax_line_id"):
            tax = tax_line.tax_line_id
            if tax.amount_type != "percent":
                continue
            # A vendor bill's tax line is a credit, hence the sign flip.
            posted[tax.amount] = posted.get(tax.amount, 0.0) + (
                tax_line.credit - tax_line.debit)
        for row in self.tax_summary_ids:
            if not row.amount_tax:
                continue
            got = next((amount for rate, amount in posted.items()
                        if same_rate(rate, row.vat_rate)), 0.0)
            if not reconciles(abs(got), row.amount_tax, tolerance=0.02):
                raise UserError(_(
                    "The document posts %(got).2f of VAT at %(rate)g%% but the "
                    "receipt reports %(want).2f. Nothing was posted.",
                    got=abs(got), rate=row.vat_rate, want=row.amount_tax))

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _store_payload(self, payload):
        """Pretty-print a provider payload for the audit field."""
        try:
            return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        except (TypeError, ValueError):
            return str(payload)

    @api.model
    def _create_from_attachment(self, attachment, vals=None):
        """Create one uncaptured receipt per attachment."""
        return self.create(dict(
            vals or {},
            attachment_id=attachment.id,
            company_id=(vals or {}).get("company_id") or self.env.company.id,
        ))
