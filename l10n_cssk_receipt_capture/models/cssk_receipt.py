# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..tools.amounts import (
    flatten_label, normalize_vat, reconciles, same_rate, split_gross,
)

_logger = logging.getLogger(__name__)


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
    amount_total = fields.Monetary(tracking=True)
    amount_untaxed = fields.Monetary(compute="_compute_amounts", store=True)
    amount_tax = fields.Monetary(compute="_compute_amounts", store=True)
    line_ids = fields.One2many("cssk.receipt.line", "receipt_id")
    tax_summary_ids = fields.One2many("cssk.receipt.tax", "receipt_id")

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
    @api.depends("seller_name", "partner_id.name", "issue_date", "receipt_uid")
    def _compute_name(self):
        for receipt in self:
            seller = receipt.partner_id.name or receipt.seller_name
            if seller and receipt.issue_date:
                receipt.name = "%s · %s" % (
                    seller, fields.Date.to_string(receipt.issue_date.date()))
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
    def _candidate_providers(self):
        """Active providers that could read this receipt, best first."""
        self.ensure_one()
        providers = self.env["cssk.receipt.provider"].search([])
        out = self.env["cssk.receipt.provider"]
        for provider in providers:
            impl = provider._implementation()
            if impl is None:
                continue
            if impl._can_capture(self):
                out |= provider
        return out

    def action_capture(self):
        """Read each receipt through its provider and reconcile the result."""
        for receipt in self:
            provider = receipt.provider_id or receipt._candidate_providers()[:1]
            if not provider:
                raise UserError(_(
                    "No capture provider can read this receipt. Install a "
                    "provider (Slovak eKasa, or the AI reader) or fill the "
                    "lines by hand."))
            impl = provider._get_implementation()
            try:
                vals = impl._capture(receipt)
            except UserError as err:
                receipt.write({
                    "provider_id": provider.id,
                    "state": "error",
                    "review_reason": str(err),
                })
                receipt.message_post(body=_("Capture failed: %s", err))
                continue
            vals.setdefault("provider_id", provider.id)
            vals["captured_on"] = fields.Datetime.now()
            # Replace any previous detail rather than appending to it: a second
            # capture of the same receipt must not double its lines.
            for field_name in ("line_ids", "tax_summary_ids"):
                vals[field_name] = (
                    [fields.Command.clear()] + list(vals.get(field_name) or []))
            receipt.write(vals)
            receipt._post_capture()
        return True

    def _post_capture(self):
        """Resolve the seller, then gate on the arithmetic."""
        self.ensure_one()
        if not self.partner_id:
            self.partner_id = self._find_partner()
        problems = self._check_reconciliation()
        if problems:
            self.write({"state": "review", "review_reason": "\n".join(problems)})
            self.message_post(body=_(
                "Captured but parked for review:<ul>%s</ul>",
                "".join("<li>%s</li>" % p for p in problems)))
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

    def action_force_captured(self):
        """Accept a receipt that failed a gate, on the user's responsibility."""
        for receipt in self.filtered(lambda r: r.state == "review"):
            receipt.message_post(body=_(
                "Review overridden by %(user)s. Reported discrepancy:<br/>%(why)s",
                user=self.env.user.display_name,
                why=(receipt.review_reason or "").replace("\n", "<br/>")))
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
        candidates = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("amount_type", "=", "percent"),
            ("company_id", "=", company.id),
        ])
        for tax in candidates:
            if same_rate(tax.amount, rate):
                return tax
        return self.env["account.tax"]

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
            "invoice_date": self.issue_date and self.issue_date.date(),
            "date": self.issue_date and self.issue_date.date(),
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
