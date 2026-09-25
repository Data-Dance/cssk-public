from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    # --- § 53b oprava odpočítanej dane pri nevymožiteľnej pohľadávke ---------
    l10n_sk_par53b_origin_id = fields.Many2one(
        "account.move", string="Original invoice (§ 53b)", copy=False, index=True,
        help="Prijatá faktúra, ktorej odpočítaná daň sa opravuje podľa § 53b.")
    l10n_sk_par53b_correction_ids = fields.One2many(
        "account.move", "l10n_sk_par53b_origin_id", string="Opravy § 53b")
    l10n_sk_par53b_state = fields.Selection(
        [("none", "—"), ("corrected", "Corrected (§ 53b)"),
         ("reclaimed", "Reclaimed")],
        compute="_compute_l10n_sk_par53b_state", store=True,
        string="Stav § 53b", default="none")

    @api.depends("l10n_sk_par53b_correction_ids.state",
                 "l10n_sk_par53b_correction_ids.l10n_sk_par53b_is_reclaim")
    def _compute_l10n_sk_par53b_state(self):
        for move in self:
            posted = move.l10n_sk_par53b_correction_ids.filtered(
                lambda c: c.state == "posted")
            if not posted:
                move.l10n_sk_par53b_state = "none"
            elif posted.filtered("l10n_sk_par53b_is_reclaim"):
                move.l10n_sk_par53b_state = "reclaimed"
            else:
                move.l10n_sk_par53b_state = "corrected"

    l10n_sk_par53b_is_reclaim = fields.Boolean(
        string="§ 53b — znovu uplatnenie", copy=False,
        help="Interná oprava, ktorá po zaplatení vracia odpočet späť.")

    def _par53b_deducted_vat(self):
        """Total input VAT this purchase bill deducted (debit balance)."""
        self.ensure_one()
        tax_lines = self.line_ids.filtered(
            lambda l: l.tax_line_id
            and l.tax_line_id.type_tax_use == "purchase")
        return sum(tax_lines.mapped("balance")), tax_lines.account_id[:1]

    def _par53b_unpaid_fraction(self):
        self.ensure_one()
        if not self.amount_total:
            return 1.0
        return min(1.0, max(0.0, abs(self.amount_residual) / abs(self.amount_total)))

    def _par53b_paid_fraction(self):
        self.ensure_one()
        return 1.0 - self._par53b_unpaid_fraction()

    def _par53b_posted_53b_vat(self, reclaim):
        """Σ VAT of this bill's posted § 53b moves of one kind.

        Corrections credit the input-VAT (343) account, re-claims debit it, so
        the r29-tagged line's credit/debit is the move's § 53b VAT amount.
        """
        self.ensure_one()
        moves = self.l10n_sk_par53b_correction_ids.filtered(
            lambda c: c.state == "posted"
            and c.l10n_sk_par53b_is_reclaim == reclaim)
        lines = moves.line_ids.filtered("tax_tag_ids")
        return sum(lines.mapped("debit" if reclaim else "credit"))

    def _par53b_make_move(self, date, journal, account, tag, reclaim=False):
        """Create (unposted) the § 53b correction / re-claim journal entry.

        The VAT-account line carries the r29 tag so the DPH return picks it up.
        Correction: credit input-VAT account, debit the cost account → r29 +,
        scaled by the *unpaid* fraction (only the unpaid share is corrected).
        Re-claim (§ 53b ods. 6, after payment): the mirror → r29 −, based on
        the posted corrections' VAT × the bill's *paid* fraction, minus what
        was already re-claimed — cumulative re-claims can never exceed what
        the corrections un-deducted.
        """
        self.ensure_one()
        currency = self.company_id.currency_id
        vat, vat_account = self._par53b_deducted_vat()
        if reclaim:
            corrected = self._par53b_posted_53b_vat(reclaim=False)
            reclaimed = self._par53b_posted_53b_vat(reclaim=True)
            target = min(corrected, corrected * self._par53b_paid_fraction())
            vat = currency.round(target - reclaimed)
            if vat <= 0:
                raise UserError(_(
                    "Faktúra %s nemá čo znovu uplatniť podľa § 53b ods. 6 — "
                    "buď nebola (ďalej) zaplatená, alebo už bola opravená "
                    "daň znovu uplatnená v plnej výške zaplatenia.")
                    % (self.name or ""))
        else:
            vat = currency.round(vat * self._par53b_unpaid_fraction())
            if vat <= 0:
                raise UserError(_("Faktúra %s nemá odpočítanú daň na opravu.")
                                % (self.name or ""))
        vat_account = vat_account or account
        # correction un-deducts (credit 343); re-claim re-deducts (debit 343)
        vat_dr, vat_cr = (vat, 0.0) if reclaim else (0.0, vat)
        cost_dr, cost_cr = (0.0, vat) if reclaim else (vat, 0.0)
        label = (_("§ 53b — znovu uplatnenie odpočítanej dane")
                 if reclaim else _("§ 53b — oprava odpočítanej dane"))
        return self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": journal.id,
            "date": date,
            "ref": "%s — %s" % (label, self.name or ""),
            "partner_id": self.commercial_partner_id.id,
            "l10n_sk_par53b_origin_id": self.id,
            "l10n_sk_par53b_is_reclaim": reclaim,
            "line_ids": [
                (0, 0, {
                    "name": label,
                    "account_id": vat_account.id,
                    "debit": vat_dr, "credit": vat_cr,
                    "tax_tag_ids": [(6, 0, tag.ids)],
                }),
                (0, 0, {
                    "name": label,
                    "account_id": account.id,
                    "debit": cost_dr, "credit": cost_cr,
                }),
            ],
        })

    def action_par53b_reclaim(self):
        """Re-deduct § 53b VAT once the bill is (partly) paid again."""
        for bill in self:
            corr = bill.l10n_sk_par53b_correction_ids.filtered(
                lambda c: c.state == "posted"
                and not c.l10n_sk_par53b_is_reclaim)
            if not corr:
                raise UserError(_("Faktúra %s nebola opravená podľa § 53b.")
                                % (bill.name or ""))
            tag = corr[:1].line_ids.tax_tag_ids
            cost = corr[:1].line_ids.filtered(
                lambda l: not l.tax_tag_ids).account_id[:1]
            move = bill._par53b_make_move(
                fields.Date.context_today(bill), corr[:1].journal_id,
                cost, tag, reclaim=True)
            move.action_post()
        return True


class Par53bWizard(models.TransientModel):
    _name = "l10n.sk.par53b.wizard"
    _description = "Oprava odpočítanej dane pri nevymožiteľnej pohľadávke (§ 53b)"

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company)
    date = fields.Date(
        string="As of date", required=True, default=fields.Date.context_today,
        help="K tomuto dňu sa posudzuje 100-dňová lehota; opravná interná "
             "faktúra dostane tento dátum.")
    threshold_days = fields.Integer(
        string="Days overdue", default=100, required=True,
        help="§ 53b: oprava ak je faktúra nezaplatená viac ako 100 dní po "
             "splatnosti.")
    journal_id = fields.Many2one(
        "account.journal", string="Denník opráv", required=True,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")
    correction_account_id = fields.Many2one(
        "account.account", string="Protiúčet (náklad)", required=True,
        domain="[('company_ids', 'in', company_id)]",
        help="Účet, na ktorý sa preúčtuje opravená (neodpočítateľná) daň — "
             "zvyčajne 548.")
    bill_ids = fields.Many2many("account.move", compute="_compute_bills")
    bill_count = fields.Integer(compute="_compute_bills")

    @api.depends("company_id", "date", "threshold_days")
    def _compute_bills(self):
        for wiz in self:
            bills = wiz._qualifying_bills()
            wiz.bill_ids = bills
            wiz.bill_count = len(bills)

    def _qualifying_bills(self):
        self.ensure_one()
        if not self.date:
            return self.env["account.move"]
        cutoff = self.date - timedelta(days=self.threshold_days or 0)
        bills = self.env["account.move"].search([
            ("company_id", "=", self.company_id.id),
            ("move_type", "=", "in_invoice"),
            ("state", "=", "posted"),
            # correction candidates only: in_payment/paid bills have nothing
            # unpaid to correct (the reclaim path, action_par53b_reclaim,
            # deliberately accepts them — § 53b ods. 6 applies AFTER payment)
            ("payment_state", "in", ("not_paid", "partial")),
            ("invoice_date_due", "!=", False),
            # 100 days elapsed ON the 100th day after due date, hence <=
            ("invoice_date_due", "<=", cutoff),
        ])
        return bills.filtered(
            lambda b: b.l10n_sk_par53b_state == "none"
            and b._par53b_deducted_vat()[0] > 0)

    def _r29_tag(self):
        tag = self.env["account.account.tag"]._get_tax_tags(
            "29", self.company_id.account_fiscal_country_id.id)
        if not tag:
            raise UserError(_("Chýba daňová značka r29 (§ 53b) pre SK."))
        return tag

    def action_generate(self):
        self.ensure_one()
        bills = self._qualifying_bills()
        if not bills:
            raise UserError(_("Žiadne faktúry nespĺňajú podmienky § 53b "
                              "k %s.") % self.date)
        tag = self._r29_tag()
        moves = self.env["account.move"]
        for bill in bills:
            moves |= bill._par53b_make_move(
                self.date, self.journal_id, self.correction_account_id, tag)
        moves.action_post()
        return {
            "type": "ir.actions.act_window",
            "name": _("Opravy § 53b"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("id", "in", moves.ids)],
        }
