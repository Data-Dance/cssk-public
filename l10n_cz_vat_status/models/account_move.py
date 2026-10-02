# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which status a document falls under, and keeping its taxes consistent.

**The deciding date is the DUZP** (``taxable_supply_date``), falling back to
the invoice date, then the accounting date. The status matters for exactly
two questions and both are anchored on the tax point:

* whether output VAT arises — the obligation arises on the day of the taxable
  supply (§ 20a odst. 1) and falls on whoever is a plátce *then* (§ 108
  odst. 1);
* whether input VAT is deductible — the right "vzniká plátci okamžikem, kdy
  nastaly skutečnosti zakládající povinnost tuto daň přiznat" (§ 72 odst. 5),
  i.e. again at the supplier's tax point, not the day the bill is booked or
  received; and § 72 odst. 1 gives it only to a plátce.

The invoice date is only the day the document was issued (§ 29 odst. 1 lists
it separately as písm. g), the DUZP as písm. h)), and the accounting date is a
bookkeeping choice; neither decides who owed the tax. ``l10n_cz`` already fills the DUZP on every Czech
invoice, so the fallbacks are for documents that arrive without one.

**Boundary days** are inclusive on the new status: a document whose DUZP is
the first day of a status row falls under that row, and one dated the day
before falls under the previous one. The row's first day is the day the Act
says the status begins or ends (see ``l10n.cz.vat.status.period``).

**A credit note** follows the document it corrects. A § 42 correction adjusts
the base of the original supply, so the regime of the original supply is the
one applied, even when the credit note is issued after a status change. (How
a former plátce corrects after deregistration is an open question for the
accountant — see the README.)
"""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_cz_vat_status = fields.Selection(
        [("payer", "Plátce DPH (§ 6–6f)"),
         ("identified", "Identifikovaná osoba (§ 6g–6l)"),
         ("non_payer", "Neplátce")],
        string="Company VAT status", compute="_compute_l10n_cz_vat_status",
        help="The company's VAT status on this document's DUZP. Empty when "
        "the company records no VAT-status history.")
    l10n_cz_vat_status_warning = fields.Text(
        string="VAT status warning", compute="_compute_l10n_cz_vat_status")
    l10n_cz_vat_status_print_note = fields.Char(
        string="VAT status statement", compute="_compute_l10n_cz_vat_status")
    l10n_cz_vat_status_declared_date_note = fields.Char(
        string="VAT period declared: not applied",
        compute="_compute_l10n_cz_vat_status_declared_date_note",
        help="Set when the document records a VAT period declared that is "
        "ignored because the company was not a plátce on the document's "
        "deciding date.")
    l10n_cz_vat_status_is_tax_document = fields.Boolean(
        string="Daňový doklad", compute="_compute_l10n_cz_vat_status",
        help="False when the document must not be presented as a daňový "
        "doklad because the company was not a plátce on its DUZP.")

    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_date(self):
        self.ensure_one()
        move = self
        if move.move_type in ("out_refund", "in_refund") and move.reversed_entry_id:
            move = move.reversed_entry_id
        return (move.taxable_supply_date or move.invoice_date or move.date
                or fields.Date.context_today(move))

    def _l10n_cz_vat_status_applies(self):
        self.ensure_one()
        company = self.company_id
        return bool(
            company
            and self.is_invoice(include_receipts=True)
            and company.account_fiscal_country_id.code == "CZ"
            and company._l10n_cz_vat_status_has_history())

    def _l10n_cz_vat_status_current(self):
        """The status on the document's date, or False when not applicable."""
        self.ensure_one()
        if not self._l10n_cz_vat_status_applies():
            return False
        return self.company_id._l10n_cz_vat_status_on(
            self._l10n_cz_vat_status_date())

    def _l10n_cz_vat_status_mismatched_lines(self):
        """``[(line, expected taxes)]`` for lines whose taxes do not fit.

        A line whose tax needs a twin that does not exist is a mismatch too,
        even though its expected taxes equal its own: see
        ``res.company._l10n_cz_vat_status_map_taxes_ex``.
        """
        self.ensure_one()
        status = self._l10n_cz_vat_status_current()
        if not status:
            return []
        company = self.company_id
        out = []
        for line in self.invoice_line_ids.filtered(
                lambda l: l.display_type == "product"):
            expected, unresolved = company._l10n_cz_vat_status_map_taxes_ex(
                line.tax_ids, status)
            if unresolved or set(expected.ids) != set(line.tax_ids._origin.ids):
                out.append((line, expected))
        return out

    @api.depends(
        "move_type", "company_id", "taxable_supply_date", "invoice_date", "date",
        "reversed_entry_id", "invoice_line_ids.tax_ids",
        "company_id.l10n_cz_vat_status_period_ids.date_from",
        "company_id.l10n_cz_vat_status_period_ids.status",
    )
    def _compute_l10n_cz_vat_status(self):
        for move in self:
            status = move._l10n_cz_vat_status_current()
            move.l10n_cz_vat_status = status
            move.l10n_cz_vat_status_warning = False
            move.l10n_cz_vat_status_print_note = False
            move.l10n_cz_vat_status_is_tax_document = True
            if not status or status == "payer":
                continue
            company = move.company_id
            label = company._l10n_cz_vat_status_label(status)
            bad = move._l10n_cz_vat_status_mismatched_lines()
            if bad:
                move.l10n_cz_vat_status_warning = _(
                    "On %(date)s the company is “%(status)s”, and %(n)d line(s) "
                    "carry taxes that status does not allow. Use “Apply VAT "
                    "status taxes” to replace them.",
                    date=fields.Date.to_string(move._l10n_cz_vat_status_date()),
                    status=label, n=len(bad))
            if move.is_sale_document(include_receipts=True):
                move.l10n_cz_vat_status_print_note = (
                    company.l10n_cz_vat_status_note_non_payer
                    if status == "non_payer"
                    else company.l10n_cz_vat_status_note_identified) or False
                # An identifikovaná osoba issues a daňový doklad for a § 9
                # odst. 1 service to another member state (§ 28 odst. 3 písm.
                # a) bod 1) — the one sale it still reports. Anything else it
                # or a neplátce issues is not a daňový doklad.
                reports = any(
                    t.invoice_repartition_line_ids.tag_ids
                    for t in move.invoice_line_ids.tax_ids)
                move.l10n_cz_vat_status_is_tax_document = (
                    status == "identified" and reports)

    # ------------------------------------------------------------------
    # The declared VAT period (l10n_cssk_core ``cssk_vat_deduction_date``)
    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_ignores_declared_date(self):
        """Whether this document's ``cssk_vat_deduction_date`` must be ignored.

        That date moves a document onto a later return, and — with the
        company's deferral account — its VAT off 343 until then. Both exist
        for the **right to deduct**, which § 73 lets a plátce exercise later
        than it arose. A neplátce or an identifikovaná osoba has no such right
        (§ 72 odst. 1 gives it to a plátce only), so there is nothing to
        defer. What such a company does carry on 343 is a **liability** — an
        identifikovaná osoba's self-assessment on an intra-Community
        acquisition (§ 108 odst. 2, tax point § 25) or on a service from
        abroad (§ 108 odst. 3 písm. a), tax point § 24) — and a liability is
        declared for the period of its tax point, § 101 odst. 1 with § 20a.
        A declared later period cannot move it.

        So the status on the document's deciding date
        (``_l10n_cz_vat_status_date``: the DUZP; a credit note follows the
        document it corrects) decides: anything but ``payer`` ignores the
        date, for the ledger and for every filing alike. Entries count too:
        a hand-booked self-assessment is the same liability.

        With no status history this is always False — exactly as before.
        """
        self.ensure_one()
        company = self.company_id
        return bool(
            self.cssk_vat_deduction_date
            and company
            and company.account_fiscal_country_id.code == "CZ"
            and company._l10n_cz_vat_status_has_history()
            and company._l10n_cz_vat_status_on(
                self._l10n_cz_vat_status_date()) != "payer")

    @api.depends(
        "cssk_vat_deduction_date", "move_type", "company_id",
        "taxable_supply_date", "invoice_date", "date", "reversed_entry_id",
        "company_id.l10n_cz_vat_status_period_ids.date_from",
        "company_id.l10n_cz_vat_status_period_ids.status",
    )
    def _compute_l10n_cz_vat_status_declared_date_note(self):
        for move in self:
            note = False
            if move._l10n_cz_vat_status_ignores_declared_date():
                company = move.company_id
                note = _(
                    "The VAT period declared (%(declared)s) is not applied: "
                    "on %(date)s the company is “%(status)s”, which has no "
                    "deduction to claim later (§ 72 odst. 1 zákona o DPH). "
                    "The document is reported, and its VAT stays on its "
                    "account, in the period of its tax point.",
                    declared=fields.Date.to_string(move.cssk_vat_deduction_date),
                    date=fields.Date.to_string(move._l10n_cz_vat_status_date()),
                    status=company._l10n_cz_vat_status_label(
                        company._l10n_cz_vat_status_on(
                            move._l10n_cz_vat_status_date())))
            move.l10n_cz_vat_status_declared_date_note = note

    def _cssk_vat_deferral_needed(self):
        """No deferral off 343 for a document whose declared date is ignored:
        see ``_l10n_cz_vat_status_ignores_declared_date``."""
        if self._l10n_cz_vat_status_ignores_declared_date():
            return False
        return super()._cssk_vat_deferral_needed()

    def _l10n_cz_vat_status_resync_deferral(self):
        """Bring posted documents' deferral entries in line with the status.

        Called when the status history changes. A document that was a
        plátce's when posted may now fall in a non-payer period (its entries
        are withdrawn), and the other way round (they are created). Each
        document is handled on its own savepoint: an entry in a locked period
        cannot be withdrawn or created, and that must not make the status
        history itself impossible to record. Such a document says so in its
        chatter, and the entries are left for the accountant to correct.

        Returns the documents that could not be brought in line.
        """
        failed = self.browse()
        for move in self:
            live = move.cssk_vat_deferral_move_ids.filtered(
                lambda m: m.state != "cancel")
            ignored = move._l10n_cz_vat_status_ignores_declared_date()
            if ignored and live:
                action = move._cssk_cancel_vat_deferral
            elif not ignored and not live and move._cssk_vat_deferral_needed():
                action = move._cssk_create_vat_deferral
            else:
                continue
            try:
                with self.env.cr.savepoint():
                    action()
            except (UserError, ValidationError) as e:
                failed |= move
                _logger.warning(
                    "VAT status change: deferral of %s not brought in line: %s",
                    move.display_name, e)
                move.message_post(body=_(
                    "The company's VAT status history changed, and this "
                    "document's VAT-deferral entries should now be "
                    "%(what)s, but that failed: %(error)s. Correct them by "
                    "hand (or reset and repost the document once the period "
                    "is open).",
                    what=_("withdrawn") if ignored else _("created"),
                    error=str(e)))
        return failed

    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_remap(self):
        """Replace every line's taxes by the ones its status allows."""
        for move in self:
            status = move._l10n_cz_vat_status_current()
            if not status:
                continue
            for line, expected in move._l10n_cz_vat_status_mismatched_lines():
                line.tax_ids = expected

    @api.onchange("taxable_supply_date", "invoice_date")
    def _onchange_l10n_cz_vat_status_date(self):
        # Normalise-then-map, so a change back across a boundary restores the
        # plátce taxes and a user's own choice of tax survives both ways.
        self._l10n_cz_vat_status_remap()

    def action_l10n_cz_vat_status_apply_taxes(self):
        self.company_id._l10n_cz_vat_status_ensure_taxes()
        for move in self:
            if move.state != "draft":
                raise UserError(_("Only a draft document's taxes can be changed."))
        self._l10n_cz_vat_status_remap()
        return True

    def _post(self, soft=True):
        """Refuse to post a document whose taxes contradict the status.

        Blocking rather than warning, unlike the partner-side registration
        check: this is the company's own status, recorded by the company, and
        a neplátce's invoice showing VAT creates the very liability (§ 108
        odst. 4 písm. g)) the status says it does not have. Imports that must
        reproduce a historical document as it was can pass the context key
        ``l10n_cz_vat_status_skip_check``.
        """
        if not self.env.context.get("l10n_cz_vat_status_skip_check"):
            to_check = self.filtered(lambda m: m._l10n_cz_vat_status_applies())
            to_check.company_id._l10n_cz_vat_status_ensure_taxes()
            problems = []
            for move in to_check:
                bad = move._l10n_cz_vat_status_mismatched_lines()
                if bad:
                    status = move.company_id._l10n_cz_vat_status_label(
                        move._l10n_cz_vat_status_current())
                    problems.append(_(
                        "%(move)s (%(status)s on %(date)s): %(lines)s",
                        move=move.display_name, status=status,
                        date=fields.Date.to_string(move._l10n_cz_vat_status_date()),
                        lines="; ".join(
                            "%s: %s → %s" % (
                                line.name or line.product_id.display_name or "",
                                ", ".join(line.tax_ids.mapped("name")) or "–",
                                ", ".join(exp.mapped("name")) or "–")
                            if set(exp.ids) != set(line.tax_ids.ids) else
                            _("%(line)s: no non-payer variant of %(taxes)s "
                              "could be generated — its repartition is not "
                              "the Czech chart's shape; set the tax by hand",
                              line=line.name or line.product_id.display_name or "",
                              taxes=", ".join(line.tax_ids.mapped("name")))
                            for line, exp in bad)))
            if problems:
                raise UserError(_(
                    "These documents carry taxes the company's VAT status does "
                    "not allow on their DUZP. Use “Apply VAT status taxes” on "
                    "each, or correct the status history:\n%s",
                    "\n".join("• " + p for p in problems)))
        return super()._post(soft=soft)
