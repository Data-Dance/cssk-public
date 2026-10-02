# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The quarterly OSS VAT return, Union scheme (zvláštní režim jednoho správního
místa — režim Unie / osobitná úprava — úprava pre Úniu).

What is aggregated
------------------
Every journal item that carries core ``l10n_eu_oss``'s ``OSS`` tax tag. Core
puts that tag on ALL repartition lines of the destination-rate taxes it
creates, base and tax alike, so the tag alone says "this is an OSS supply".
The BASE lines (``tax_line_id`` empty) are what the return reports; the TAX
lines are only used to check that the VAT computed for the return agrees with
the VAT that was actually booked.

Why not the tag-line engine of ``l10n_cssk_vat_return_base``
-------------------------------------------------------------
That engine evaluates a FIXED list of numbered rows, one tag formula each. The
OSS return has no fixed rows: it has one row per member state of consumption ×
rate × goods/services, an open-ended set that the tags cannot enumerate (one
tag covers every OSS tax). What IS shared is the statutory pipeline around the
figures — kontroly, rendering, XSD validation, retention of the filed copy and
delivery tracking — through the same mixins the VAT return uses.

EUR conversion — the rule and where it comes from
-------------------------------------------------
The return is made out in euro even by a member state of identification
outside the euro area (both CZ and SK forms state amounts in EUR). An amount
invoiced in another currency is converted at the **exchange rate published by
the European Central Bank for the last day of the tax period, or, if none is
published for that day, for the next day of publication**:

* Council Directive 2006/112/EC, **Art. 369h(2)** (Union scheme), as amended
  by Council Directive (EU) 2017/2455;
* CZ: **§ 110ze odst. 2 písm. a)** zákona č. 235/2004 Sb. — and **písm. b)**:
  a correction (dodatečné daňové přiznání) uses the rate used for the
  ORIGINAL supply;
* SK: **§ 68b ods. 17** zákona č. 222/2004 Z. z. — the reference rate
  "určený a vyhlásený Európskou centrálnou bankou alebo Národnou bankou
  Slovenska platný posledný deň príslušného zdaňovacieho obdobia alebo
  nasledujúci deň".

So: an invoice already in EUR is taken as invoiced, never through the
company's books (whose CZK figure was converted at the ČNB rate of the tax
point, a different rate on a different day). Anything else is converted from
the DOCUMENT currency at the period-end rate, and a correction of an earlier
quarter at the period-end rate of THAT quarter.

The rate table of the company is used only to PROPOSE a rate: it may hold ČNB
or a commercial bank's rates rather than the ECB reference rate, and nothing
in it says which. Every proposed rate therefore has to be confirmed as the ECB
reference rate before the return can be exported.

Corrections of earlier quarters
-------------------------------
Corrections are made in a later return, identifying the quarter and member
state, within three years (Implementing Regulation (EU) No 282/2011, Art. 61,
as amended by (EU) 2019/2026; CZ § 110zd; SK § 68b). A credit note (or debit
note) whose original invoice lies in an earlier quarter is therefore not a
negative row of this quarter — neither form accepts one — but a correction of
the original quarter, converted at the original quarter's rate.
"""

from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round
from odoo.tools.translate import LazyTranslate

from .eu_rates import OSS_UNION_SCHEME_START, oss_country_code, rate_type

_lt = LazyTranslate(__name__)

QUARTERS = [("1", "Q1"), ("2", "Q2"), ("3", "Q3"), ("4", "Q4")]


def quarter_bounds(year, quarter):
    start = date(year, 3 * (int(quarter) - 1) + 1, 1)
    return start, start + relativedelta(months=3, days=-1)


def quarter_of(day):
    return day.year, (day.month - 1) // 3 + 1


class CsskOssReturn(models.Model):
    _name = "cssk.oss.return"
    _description = "OSS VAT Return (Union scheme)"
    _inherit = ["mail.thread", "mail.activity.mixin",
                "cssk.statutory.submission.mixin",
                "cssk.submittable.mixin"]
    _order = "date_from desc, id desc"

    _cssk_form_label = _lt("OSS VAT return")
    _cssk_xml_name_fallback = "oss_return"

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    eur_currency_id = fields.Many2one(
        "res.currency", default=lambda s: s.env.ref("base.EUR"),
        required=True, readonly=True)
    country_id = fields.Many2one(
        related="company_id.account_fiscal_country_id", store=True,
        string="Member state of identification")
    version_id = fields.Many2one(
        "cssk.oss.return.version", required=True,
        domain="[('country_id', '=', country_id),"
               " ('valid_from', '<=', date_to),"
               " '|', ('valid_to', '=', False), ('valid_to', '>=', date_from)]",
        context={"active_test": False})
    year = fields.Integer(
        required=True, default=lambda s: fields.Date.context_today(s).year)
    quarter = fields.Selection(QUARTERS, required=True, default="1")
    date_from = fields.Date(compute="_compute_dates", store=True)
    date_to = fields.Date(compute="_compute_dates", store=True)
    partial_date_from = fields.Date(
        string="Registered from",
        help="Only when the registration began during the quarter (or the "
             "member state of identification changed): the first day the "
             "return covers. Emitted as the form's period start date.")
    partial_date_to = fields.Date(
        string="Registered until",
        help="Only when the registration ended during the quarter: the last "
             "day the return covers.")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("exported", "Exported"),
            ("submitted", "Submitted"),
            ("cancelled", "Cancelled"),
            ("legacy", "Historical filing"),
        ],
        default="draft", tracking=True, copy=False)
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True,
                                        copy=False)

    line_ids = fields.One2many("cssk.oss.return.line", "return_id",
                               string="Supplies")
    correction_ids = fields.One2many("cssk.oss.return.correction",
                                     "return_id", string="Corrections")
    rate_ids = fields.One2many("cssk.oss.return.rate", "return_id",
                               string="Exchange rates")

    total_vat = fields.Monetary(
        compute="_compute_totals", currency_field="eur_currency_id",
        string="VAT on supplies (EUR)")
    total_corrections = fields.Monetary(
        compute="_compute_totals", currency_field="eur_currency_id",
        string="Corrections (EUR)")
    total_due = fields.Monetary(
        compute="_compute_totals", currency_field="eur_currency_id",
        string="VAT due (EUR)",
        help="Sum of the POSITIVE per-member-state balances. A member state "
             "whose corrections exceed this quarter's VAT ends negative; that "
             "amount is refunded by that state and is not netted against the "
             "others — the EU return structure's 'Total VAT amount due' and "
             "the Finančná správa eForm both sum the positive balances only.")
    booked_vat = fields.Monetary(
        currency_field="eur_currency_id", readonly=True, copy=False,
        string="VAT booked (EUR)",
        help="The OSS VAT actually posted on the documents in scope, converted "
             "the same way. Checked against the computed VAT by a kontrola.")
    is_nil = fields.Boolean(compute="_compute_totals", string="Nil return")

    @api.depends("year", "quarter")
    def _compute_dates(self):
        for ret in self:
            if ret.year and ret.quarter:
                ret.date_from, ret.date_to = quarter_bounds(ret.year,
                                                            ret.quarter)
            else:
                ret.date_from = ret.date_to = False

    @api.depends("year", "quarter")
    def _compute_name(self):
        for ret in self:
            ret.name = "OSS %s Q%s" % (ret.year or "", ret.quarter or "")

    @api.depends("line_ids.vat_amount", "correction_ids.vat_amount")
    def _compute_totals(self):
        for ret in self:
            ret.total_vat = sum(ret.line_ids.mapped("vat_amount"))
            ret.total_corrections = sum(
                ret.correction_ids.mapped("vat_amount"))
            ret.total_due = sum(v for v in ret._cssk_oss_balances().values()
                                if v > 0)
            ret.is_nil = not ret.line_ids and not ret.correction_ids

    def _cssk_oss_balances(self):
        """``{res.country: EUR}`` — this quarter's VAT plus corrections.

        The EU schema's ``Balances`` section; negative balances stay negative
        and are left out of the total due.
        """
        self.ensure_one()
        out = defaultdict(float)
        for line in self.line_ids:
            out[line.member_state_id] += line.vat_amount
        for corr in self.correction_ids:
            out[corr.member_state_id] += corr.vat_amount
        return {k: float_round(v, 2) for k, v in out.items()}

    # ------------------------------------------------------------------
    # Selection of the documents
    # ------------------------------------------------------------------
    @api.model
    def _cssk_oss_move_date(self, move):
        """The date that puts a document in a quarter.

        A supply belongs to the quarter of its tax point (``taxable_supply_date``
        when recorded, else the invoice date). A credit note belongs to the
        quarter in which it is ISSUED, not to the quarter of the supply it
        corrects: that is the quarter in which the change became known and in
        whose return the correction is declared (CZ § 110zd odst. 1). Taking
        the credit note's tax point would file it back into a quarter whose
        return may already have been submitted, where nothing ever picks it up.
        """
        if move.move_type == "out_refund":
            return move.invoice_date or move.date
        return move.taxable_supply_date or move.invoice_date or move.date

    def _cssk_oss_period_moves(self):
        self.ensure_one()
        Move = self.env["account.move"]
        base = [("company_id", "=", self.company_id.id),
                ("state", "=", "posted")]
        start, end = self.date_from, self.date_to
        refunds = Move.search(base + [
            ("move_type", "=", "out_refund"),
            "|",
            "&", ("invoice_date", "!=", False),
            "&", ("invoice_date", ">=", start), ("invoice_date", "<=", end),
            "&", ("invoice_date", "=", False),
            "&", ("date", ">=", start), ("date", "<=", end),
        ])
        others = Move.search(base + [
            ("move_type", "!=", "out_refund"),
            "|", "|",
            "&", ("taxable_supply_date", "!=", False),
            "&", ("taxable_supply_date", ">=", start),
            ("taxable_supply_date", "<=", end),
            "&", "&", ("taxable_supply_date", "=", False),
            ("invoice_date", "!=", False),
            "&", ("invoice_date", ">=", start), ("invoice_date", "<=", end),
            "&", "&", ("taxable_supply_date", "=", False),
            ("invoice_date", "=", False),
            "&", ("date", ">=", start), ("date", "<=", end),
        ])
        return refunds | others

    def _cssk_oss_origin_move(self, move):
        """The document a credit/debit note corrects, if it names one."""
        origin = move.reversed_entry_id
        if not origin and "debit_origin_id" in move._fields:
            origin = move.debit_origin_id
        return origin

    # ------------------------------------------------------------------
    # Classification of one journal item
    # ------------------------------------------------------------------
    def _cssk_oss_is_oss_tax(self, tax):
        tag = self.env.ref("l10n_eu_oss.tag_oss")
        return bool((tax.invoice_repartition_line_ids.tag_ids
                     | tax.refund_repartition_line_ids.tag_ids) & tag)

    def _cssk_oss_line_tax(self, line):
        """The OSS tax behind a journal item, or a UserError naming it.

        A base line knows its taxes through ``tax_ids``; a tax line through
        ``tax_line_id``. More than one OSS tax on one line cannot be split
        between rows, and a tagged line with no OSS tax at all is a manual
        entry whose rate nobody can know — both are data errors to fix on the
        document, not something to guess.
        """
        # The tax line is checked too: the OSS tag on a journal item is
        # editable, and a hand-tagged domestic tax line would otherwise pass
        # its rate straight into the booked-VAT check.
        taxes = (line.tax_line_id or line.tax_ids).filtered(
            self._cssk_oss_is_oss_tax)
        if len(taxes) != 1:
            raise UserError(_(
                "%(move)s, line '%(line)s', carries the OSS tag but %(n)s OSS "
                "taxes, so its member state and rate cannot be determined. "
                "Correct the document (one OSS tax per line) and compute "
                "again.",
                move=line.move_id.display_name, line=line.name or line.id,
                n=len(taxes)))
        return taxes

    def _cssk_oss_member_state(self, line, tax):
        """Member state of consumption.

        Core creates each OSS tax for ONE destination and links it to that
        destination's fiscal position, so the tax is the most reliable answer
        and does not depend on the document still carrying the position. The
        document's fiscal position and then the delivery address are the
        fallbacks for a tax shared between positions by hand.
        """
        countries = tax.fiscal_position_ids.country_id
        if len(countries) == 1:
            return countries
        fpos_country = line.move_id.fiscal_position_id.country_id
        if fpos_country:
            return fpos_country
        partner = (line.move_id.partner_shipping_id
                   or line.move_id.partner_id)
        if partner.country_id:
            return partner.country_id
        raise UserError(_(
            "%(move)s: the member state of consumption of its OSS supply "
            "cannot be determined (tax %(tax)s belongs to no single OSS fiscal "
            "position, and the document has neither a fiscal position with a "
            "country nor a customer country).",
            move=line.move_id.display_name, tax=tax.display_name))

    def _cssk_oss_supply_type(self, line):
        """``goods`` or ``services`` — both forms split every row by it.

        Read from the product. A line without a product is taken as goods:
        since 1. 7. 2021 the Union scheme is dominated by distance sales of
        goods, and ancillary charges such as shipping follow the principal
        supply of goods. A seller of e-services should put products on its
        lines.
        """
        return "services" if line.product_id.type == "service" else "goods"

    def _cssk_oss_origin(self, line):
        """Member state the supply is made FROM, as ``(res.country, vat)``.

        The member state of identification by default. Goods dispatched from a
        warehouse in another member state, or services supplied from a fixed
        establishment elsewhere, are reported per that state (CZ VetaR
        ``country``; the EU schema's ``MSESTSupplies``). Nothing in a standard
        Odoo invoice records the dispatch state reliably, so such rows are
        entered by hand (manual rows survive a recompute) or supplied by
        overriding this hook.
        """
        return self.company_id.account_fiscal_country_id, False

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only a draft return can be recomputed."))
        if self.date_from < OSS_UNION_SCHEME_START:
            raise UserError(_(
                "The Union scheme OSS return exists from the third quarter of "
                "2021; earlier quarters were filed on the MOSS return."))
        tag = self.env.ref("l10n_eu_oss.tag_oss")
        moves = self._cssk_oss_period_moves()
        aml = self.env["account.move.line"].search([
            ("move_id", "in", moves.ids),
            ("tax_tag_ids", "in", tag.ids),
            ("display_type", "not in", ("line_section", "line_note")),
        ]) if moves else self.env["account.move.line"]

        # key -> {(currency, reference date): amount in document currency}
        supplies = defaultdict(lambda: defaultdict(float))
        supply_amls = defaultdict(lambda: self.env["account.move.line"])
        corrections = defaultdict(lambda: defaultdict(float))
        correction_amls = defaultdict(lambda: self.env["account.move.line"])
        booked = defaultdict(float)
        this_quarter = (self.year, int(self.quarter))

        for line in aml:
            tax = self._cssk_oss_line_tax(line)
            member_state = self._cssk_oss_member_state(line, tax)
            # rounded, so that one statutory rate is one dictionary key
            vat_rate = float_round(tax.amount, 4)
            ref_date = self.date_to
            correction_of = None
            origin = self._cssk_oss_origin_move(line.move_id)
            if origin:
                origin_q = quarter_of(self._cssk_oss_move_date(origin))
                if origin_q < this_quarter:
                    correction_of = origin_q
                    ref_date = quarter_bounds(*origin_q)[1]
            amount = -line.amount_currency
            money_key = (line.currency_id, ref_date)
            if line.tax_line_id:
                booked[money_key] += amount
                continue
            if correction_of:
                key = (correction_of, member_state, vat_rate)
                corrections[key][money_key] += amount
                correction_amls[key] |= line
            else:
                origin_country, origin_vat = self._cssk_oss_origin(line)
                key = (member_state, origin_country, origin_vat or "",
                       self._cssk_oss_supply_type(line), vat_rate)
                supplies[key][money_key] += amount
                supply_amls[key] |= line

        needed = set()
        for buckets in (supplies, corrections):
            for amounts in buckets.values():
                needed.update(amounts)
        needed.update(booked)
        rates = self._cssk_oss_sync_rates(needed)

        def to_eur(amounts):
            total = 0.0
            for (currency, ref_date), amount in amounts.items():
                if currency == self.eur_currency_id:
                    total += amount
                    continue
                rate = rates.get((currency, ref_date))
                if rate:
                    total += amount / rate
            return float_round(total, 2)

        self.line_ids.filtered(lambda ln: not ln.is_manual).unlink()
        self.correction_ids.filtered(lambda c: not c.is_manual).unlink()

        line_vals = []
        for key, amounts in supplies.items():
            member_state, origin_country, origin_vat, supply, rate = key
            base = to_eur(amounts)
            line_vals.append({
                "return_id": self.id,
                "member_state_id": member_state.id,
                "origin_country_id": origin_country.id,
                "origin_vat": origin_vat or False,
                "supply_type": supply,
                "vat_rate": rate,
                "rate_type": rate_type(member_state.code, rate,
                                       self.date_to) or False,
                "taxable_amount": base,
                "vat_amount": float_round(base * rate / 100.0, 2),
                "move_line_ids": [(6, 0, supply_amls[key].ids)],
            })
        self.env["cssk.oss.return.line"].create(line_vals)

        grouped = defaultdict(lambda: {"base": 0.0, "vat": 0.0,
                                       "amls": self.env["account.move.line"]})
        for key, amounts in corrections.items():
            (year, quarter), member_state, rate = key
            base = to_eur(amounts)
            slot = grouped[(year, quarter, member_state)]
            slot["base"] += base
            slot["vat"] += float_round(base * rate / 100.0, 2)
            slot["amls"] |= correction_amls[key]
        self.env["cssk.oss.return.correction"].create([{
            "return_id": self.id,
            "year": year,
            "quarter": str(quarter),
            "member_state_id": member_state.id,
            "taxable_amount": float_round(slot["base"], 2),
            "vat_amount": float_round(slot["vat"], 2),
            "move_line_ids": [(6, 0, slot["amls"].ids)],
        } for (year, quarter, member_state), slot in grouped.items()])

        self.booked_vat = to_eur(booked)
        self.state = "preview"
        return True

    # ------------------------------------------------------------------
    # Exchange rates
    # ------------------------------------------------------------------
    def _cssk_oss_sync_rates(self, needed):
        """Keep one rate row per (currency, reference date) the figures need.

        A row the accountant already confirmed or typed is kept as it is — a
        recompute must never silently replace an entered ECB rate with the
        company table's proposal. Rows no longer needed are dropped. Returns
        ``{(currency, reference date): units of currency per 1 EUR}``, with
        missing rates left out.
        """
        self.ensure_one()
        eur = self.eur_currency_id
        wanted = {(cur, ref) for cur, ref in needed if cur != eur}
        existing = {(r.currency_id, r.reference_date): r for r in self.rate_ids}
        for key, row in existing.items():
            if key not in wanted:
                row.unlink()
        for currency, ref_date in wanted:
            if (currency, ref_date) in existing:
                continue
            fixing_date, rate = self._cssk_oss_proposed_rate(currency,
                                                             ref_date)
            self.env["cssk.oss.return.rate"].create({
                "return_id": self.id,
                "currency_id": currency.id,
                "reference_date": ref_date,
                "fixing_date": fixing_date,
                "rate": rate,
                "source": "table",
            })
        return {(r.currency_id, r.reference_date): r.rate
                for r in self.rate_ids if r.rate > 0}

    def _cssk_oss_proposed_rate(self, currency, ref_date):
        """Propose ``(fixing date, units of currency per EUR)`` from the books.

        The first rate ON OR AFTER the period's last day, because the law
        falls FORWARD to the next day of publication when the last day has
        none (a quarter ending on a Sunday takes Monday's fixing). Odoo's own
        conversion falls BACKWARD to the latest earlier rate, which is the
        wrong day, so it is not used to pick the date.
        """
        company = self.company_id
        eur = self.eur_currency_id
        probe = eur if currency == company.currency_id else currency
        Rate = self.env["res.currency.rate"].sudo()
        rec = Rate.search([
            ("currency_id", "=", probe.id),
            ("name", ">=", ref_date),
            ("company_id", "in", (False, company.root_id.id)),
        ], order="name asc", limit=1)
        if not rec:
            return False, 0.0
        rate = self.env["res.currency"]._get_conversion_rate(
            eur, currency, company, rec.name)
        return rec.name, rate

    def action_confirm_ecb_rates(self):
        """Record that every rate on the return IS the ECB reference rate."""
        for ret in self:
            ret._ensure_not_submitted()
            missing = ret.rate_ids.filtered(lambda r: r.rate <= 0)
            if missing:
                raise UserError(_(
                    "Enter the ECB rate for %s first.",
                    ", ".join(missing.mapped("currency_id.name"))))
            ret.rate_ids.write({"source": "ecb"})
        return True

    # ------------------------------------------------------------------
    # Kontroly
    # ------------------------------------------------------------------
    def check_kontroly(self):
        """``[{code, severity, desc, detail}]`` — the checks no XSD makes."""
        self.ensure_one()
        out = []
        eu = self.env.ref("base.europe").country_ids
        for rate in self.rate_ids:
            if rate.rate <= 0:
                out.append({
                    "code": "OSS_RATE_MISSING", "severity": "error",
                    "desc": _("No exchange rate for %s", rate.currency_id.name),
                    "detail": _("Enter the ECB reference rate for %s.",
                                rate.reference_date)})
            elif rate.source != "ecb":
                out.append({
                    "code": "OSS_RATE_UNCONFIRMED", "severity": "error",
                    "desc": _("%s rate not confirmed as the ECB reference rate",
                              rate.currency_id.name),
                    "detail": _(
                        "%(rate)s from the company rate table (fixing "
                        "%(day)s). The OSS return must use the ECB rate for "
                        "the last day of the period — check it and confirm.",
                        rate=rate.rate, day=rate.fixing_date or "—")})
        for line in self.line_ids:
            label = "%s %s %s%%" % (line.member_state_id.code,
                                    line.supply_type, line.vat_rate)
            if line.taxable_amount < 0 or line.vat_amount < 0:
                out.append({
                    "code": "OSS_NEGATIVE", "severity": "error",
                    "desc": _("Negative row %s", label),
                    "detail": _(
                        "A row cannot be negative. A credit note that "
                        "corrects an earlier quarter must name its original "
                        "invoice (it then becomes a correction of that "
                        "quarter); otherwise enter the correction by hand.")})
            if line.member_state_id not in eu:
                out.append({
                    "code": "OSS_NOT_EU", "severity": "error",
                    "desc": _("%s is not an EU member state", label),
                    "detail": ""})
            if line.member_state_id == line.origin_country_id:
                out.append({
                    "code": "OSS_OWN_STATE", "severity": "error",
                    "desc": _("Supply %s to the state it is made from", label),
                    "detail": _(
                        "A supply consumed in the member state it is made "
                        "from belongs on that state's domestic return, not "
                        "on the OSS return.")})
            if not line.rate_type:
                out.append({
                    "code": "OSS_RATE_TYPE", "severity": "error",
                    "desc": _("Rate type unknown for %s", label),
                    "detail": _("Set standard / reduced on the row.")})
        this_quarter = (self.year, int(self.quarter))
        first = quarter_of(OSS_UNION_SCHEME_START)
        for corr in self.correction_ids:
            period = (corr.year, int(corr.quarter))
            label = "%s Q%s %s" % (corr.year, corr.quarter,
                                   corr.member_state_id.code)
            if not first <= period < this_quarter:
                out.append({
                    "code": "OSS_CORRECTION_PERIOD", "severity": "error",
                    "desc": _("Correction %s", label),
                    "detail": _(
                        "A correction must concern a quarter from Q3 2021 "
                        "up to the one before this return.")})
                continue
            # Three years from the ORIGINAL return's filing deadline — the
            # end of the month after its quarter (CZ § 110zd odst. 3). This
            # return cannot be filed before its own quarter ends, so a
            # deadline inside the quarter is certainly missed; one between
            # the quarter's end and this return's own due date is met only by
            # filing early, which is worth a warning, not a refusal.
            deadline = self._cssk_oss_due_date(*period) + relativedelta(
                years=3)
            if self.date_to >= deadline:
                out.append({
                    "code": "OSS_CORRECTION_LATE", "severity": "error",
                    "desc": _("Correction %s is out of time", label),
                    "detail": _(
                        "The three years for correcting the original return "
                        "ran out on %s. The correction goes to the member "
                        "state of consumption directly.", deadline)})
            elif self._cssk_oss_due_date(*this_quarter) > deadline:
                out.append({
                    "code": "OSS_CORRECTION_LATE", "severity": "warning",
                    "desc": _("Correction %s must be filed by %s", label,
                              deadline),
                    "detail": _(
                        "The three-year correction period ends before this "
                        "return is due; file it no later than %s.",
                        deadline)})
        computed = self.total_vat + self.total_corrections
        n_docs = len((self.line_ids.move_line_ids
                      | self.correction_ids.move_line_ids).move_id)
        tolerance = 0.01 * max(n_docs, 1) + 0.005
        if self.booked_vat and abs(computed - self.booked_vat) > tolerance:
            out.append({
                "code": "OSS_BOOKED_VAT", "severity": "warning",
                "desc": _("Computed VAT differs from the VAT booked"),
                "detail": _(
                    "computed %(c).2f EUR, booked %(b).2f EUR — check for OSS "
                    "tax lines edited by hand or taxes with a wrong rate.",
                    c=computed, b=self.booked_vat)})
        return out

    @staticmethod
    def _cssk_oss_due_date(year, quarter):
        """Filing deadline of a quarter's return: the end of the next month
        (Art. 369f of the Directive; CZ § 110zc odst. 1)."""
        # Day after the quarter, one month on, one day back — in three steps,
        # because relativedelta applies months BEFORE days within one object
        # (30. 9. + (1 day, 1 month) is 31. 10., minus a day is 30. 10.).
        next_month_start = (quarter_bounds(year, quarter)[1]
                            + relativedelta(days=1) + relativedelta(months=1))
        return next_month_start - relativedelta(days=1)

    def _cssk_check_kontroly(self):
        self.ensure_one()
        self._cssk_enforce_kontroly()
        return True

    def _cssk_export_draft_error(self):
        return _("Compute the OSS return before exporting.")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        rows = self.line_ids.sorted(lambda ln: (
            ln.origin_country_id != self.country_id,
            oss_country_code(ln.member_state_id.code), ln.supply_type,
            ln.vat_rate))
        balances = sorted(
            ((oss_country_code(c.code), v)
             for c, v in self._cssk_oss_balances().items()),
            key=lambda kv: kv[0])
        ctx.update({
            "rows": rows,
            "msid_rows": rows.filtered(
                lambda ln: ln.origin_country_id == self.country_id),
            "mest_rows": rows.filtered(
                lambda ln: ln.origin_country_id != self.country_id),
            "corrections": self.correction_ids.sorted(lambda c: (
                c.year, c.quarter, oss_country_code(c.member_state_id.code))),
            "balances": balances,
            "oss_code": oss_country_code,
            "fmt": lambda value: "%.2f" % (value or 0.0),
            "fmt_rate": lambda value: "%.2f" % (value or 0.0),
            "total_due": self.total_due,
        })
        return ctx


class CsskOssReturnLine(models.Model):
    """One row: member state × origin × supply type × rate."""

    _name = "cssk.oss.return.line"
    _description = "OSS VAT Return Supply Row"
    _order = "return_id, member_state_id, supply_type, vat_rate"

    return_id = fields.Many2one("cssk.oss.return", required=True,
                                ondelete="cascade", index=True)
    eur_currency_id = fields.Many2one(related="return_id.eur_currency_id")
    member_state_id = fields.Many2one(
        "res.country", required=True, string="Member state of consumption")
    origin_country_id = fields.Many2one(
        "res.country", required=True, string="Supplied from",
        help="Member state of identification, or the member state of a fixed "
             "establishment / from which the goods were dispatched.")
    origin_vat = fields.Char(
        string="VAT no. there",
        help="VAT or tax reference number assigned by the 'supplied from' "
             "state, when that is not the member state of identification.")
    supply_type = fields.Selection(
        [("goods", "Goods"), ("services", "Services")], required=True)
    vat_rate = fields.Float(required=True, digits=(5, 2))
    rate_type = fields.Selection(
        [("standard", "Standard"), ("reduced", "Reduced")])
    taxable_amount = fields.Monetary(currency_field="eur_currency_id",
                                     string="Taxable amount (EUR)")
    vat_amount = fields.Monetary(currency_field="eur_currency_id",
                                 string="VAT (EUR)")
    is_manual = fields.Boolean(
        string="Manual",
        help="Entered by hand; kept when the return is recomputed.")
    move_line_ids = fields.Many2many("account.move.line",
                                     string="Journal items")

    def action_view_move_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("OSS journal items"),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "domain": [("id", "in", self.move_line_ids.ids)],
            "context": {"create": False},
        }


class CsskOssReturnCorrection(models.Model):
    """A correction of an earlier quarter, per member state (VAT only)."""

    _name = "cssk.oss.return.correction"
    _description = "OSS VAT Return Correction"
    _order = "return_id, year, quarter, member_state_id"

    return_id = fields.Many2one("cssk.oss.return", required=True,
                                ondelete="cascade", index=True)
    eur_currency_id = fields.Many2one(related="return_id.eur_currency_id")
    year = fields.Integer(required=True)
    quarter = fields.Selection(QUARTERS, required=True)
    member_state_id = fields.Many2one(
        "res.country", required=True, string="Member state of consumption")
    taxable_amount = fields.Monetary(
        currency_field="eur_currency_id", string="Base change (EUR)",
        help="Informational: neither form asks for the base of a correction.")
    vat_amount = fields.Monetary(currency_field="eur_currency_id",
                                 string="VAT correction (EUR)")
    is_manual = fields.Boolean(
        string="Manual",
        help="Entered by hand; kept when the return is recomputed.")
    move_line_ids = fields.Many2many("account.move.line",
                                     string="Journal items")

    def action_view_move_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("OSS journal items"),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "domain": [("id", "in", self.move_line_ids.ids)],
            "context": {"create": False},
        }


class CsskOssReturnRate(models.Model):
    """An exchange rate the return used, and whether it is the ECB's."""

    _name = "cssk.oss.return.rate"
    _description = "OSS VAT Return Exchange Rate"
    _order = "return_id, reference_date, currency_id"

    return_id = fields.Many2one("cssk.oss.return", required=True,
                                ondelete="cascade", index=True)
    currency_id = fields.Many2one("res.currency", required=True)
    reference_date = fields.Date(
        required=True,
        help="Last day of the quarter the converted amounts belong to — this "
             "return's, or the corrected quarter's.")
    fixing_date = fields.Date(
        help="Day of the ECB fixing used: the reference date, or the next "
             "day of publication when none was published for it.")
    rate = fields.Float(
        digits=(16, 6), string="Units per 1 EUR",
        help="How many units of the currency one euro buys.")
    source = fields.Selection(
        [("table", "Company rate table (to confirm)"),
         ("ecb", "ECB reference rate")],
        required=True, default="ecb")
