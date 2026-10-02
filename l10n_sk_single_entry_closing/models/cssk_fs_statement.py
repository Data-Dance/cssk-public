# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class CsskFsStatement(models.Model):
    """Evaluate the rows that read the denník.

    Only the new line kind is handled here; everything else — the states, the
    comparison period, the manual overrides, the XSD-validated export, the
    unmapped-amount tracking — is the shared framework's, unchanged.
    """

    _inherit = "cssk.fs.statement"

    cssk_first_zavierka = fields.Boolean(
        string="First závierka in JÚ",
        compute="_compute_cssk_first_zavierka", store=True, readonly=False,
        help="Leaves the preceding-period columns of Úč FO 2-01 empty. "
             "§ 22 ods. 4 opatrenia requires that on the first závierka after "
             "the unit comes into existence, and the vysvetlivky (pt. 16) "
             "require it where the unit kept podvojné účtovníctvo in the "
             "immediately preceding period — which the books cannot tell, so "
             "the guess below is editable.",
    )

    @api.depends("company_id", "date_from")
    def _compute_cssk_first_zavierka(self):
        """Guess it from whether the books reach back before the period.

        No posted entry before the period means there is no preceding period to
        report, which is the § 22 ods. 4 case. The PÚ case cannot be derived at
        all — a company that kept double-entry books last year has entries like
        any other — so the filer corrects it.
        """
        for statement in self:
            earlier = statement.company_id and statement.date_from and self.env[
                "account.move.line"].search_count([
                    ("company_id", "=", statement.company_id.id),
                    ("parent_state", "=", "posted"),
                    ("date", "<", statement.date_from),
                ])
            statement.cssk_first_zavierka = not earlier

    def _cssk_render_context(self):
        """Add what the UZFOv14 template needs beyond the shared context."""
        ctx = super()._cssk_render_context()
        ctx.update({
            "whole": self._cssk_whole_euros,
            "prior_empty": self.cssk_first_zavierka,
        })
        return ctx

    @api.model
    def _cssk_whole_euros(self, value):
        """The figure as the form takes it, or an empty element.

        The tlačivo is headed "(v celých eurách)" and the schema's
        ``emptyStringOrDecimal`` puts no constraint on the fraction, so a whole
        number is both what the form asks for and valid. An absent figure is an
        empty element rather than a zero, the way the eForm leaves a row nobody
        filled.
        """
        if value is None:
            return ""
        return str(int(round(value)))

    def _compute_name(self):
        """Name a JÚ závierka after the form it is, not after a kind label.

        The framework names a statement from its ``statement_kind``, and this
        version has to declare one of the four the framework knows. It declares
        ``profit_loss``, so the filed file came out of the demo instance called
        "Výkaz ziskov a strát — 2026-12-31.xml" — an income statement, which it
        is not. The attachment carries whatever ``name`` says, so this is also
        the filename that reaches the register.
        """
        others = self.browse()
        for statement in self:
            if statement.version_id == self.env.ref(
                "l10n_sk_single_entry_closing.uzfo_v14", raise_if_not_found=False
            ):
                suffix = _(" (opravná)") \
                    if statement.submission_type == "opravna" else ""
                statement.name = "Účtovná závierka v JÚ (Úč FO) — %s%s" % (
                    statement.date_to or "", suffix)
            else:
                others |= statement
        if others:
            super(CsskFsStatement, others)._compute_name()

    def _cssk_record_unmapped(self):
        """Flag only what this form is actually expected to carry.

        The framework's diagnostic is written for the súvaha, where every
        account with a balance must reach a row. Úč FO 2-01 reports **majetok
        and záväzky only**: the result of the year comes from the denník on the
        other half of the document, equity is not reported at all (r. 21 IS the
        owner's equity), and podsúvahové accounts are outside the závierka
        entirely. Run unfiltered on the demo instance it reported 57 unmapped
        accounts, every one of them a class 5/6, equity or 9xx account that the
        form correctly ignores.

        A diagnostic that cries wolf is worthless on the day it is right, so
        those classes are excluded and the check keeps its teeth for what it is
        for: a majetok or záväzok account that no row claims.
        """
        uzfo = self.env.ref("l10n_sk_single_entry_closing.uzfo_v14",
                            raise_if_not_found=False)
        others = self.filtered(lambda s: s.version_id != uzfo)
        if others:
            super(CsskFsStatement, others)._cssk_record_unmapped()
        for statement in self - others:
            super(CsskFsStatement, statement)._cssk_record_unmapped()
            statement._cssk_drop_expected_unmapped()

    def _cssk_drop_expected_unmapped(self):
        """Remove the classes Úč FO 2-01 does not report from the warning."""
        self.ensure_one()
        if not self.unmapped_note:
            return
        kept = []
        for line in self.unmapped_note.splitlines():
            code = line.split()[0] if line.split() else ""
            if not code:
                continue
            account = self.env["account.account"].with_company(
                self.company_id).search([("code", "=", code)], limit=1)
            # Classes 5 and 6 are the result, which Úč FO 1-01 reports from the
            # denník; class 7 and 9 are závierkové and podsúvahové accounts;
            # equity is r. 21 itself.
            if code[:1] in ("5", "6", "7", "9") or account.account_type in (
                "equity", "equity_unaffected", "off_balance",
            ):
                continue
            kept.append(line)
        self.unmapped_count = len(kept)
        self.unmapped_note = "\n".join(kept) or False

    def _compute_period(self, date_from, date_to, overrides=None):
        computed, columns = super()._compute_period(
            date_from, date_to, overrides=overrides)
        cash_lines = self.version_id.line_def_ids.filtered(
            lambda ldef: ldef.kind == "cash_categories")
        if not cash_lines:
            return computed, columns
        totals = self._cssk_cash_category_totals(date_from, date_to)
        overrides = overrides or {}
        for ldef in cash_lines:
            if ldef.code in overrides:
                continue
            computed[ldef.code] = self._cssk_eval_cash_categories(
                ldef.cash_category_formula, totals)
        # Aggregates over those rows have to be recomputed now that the cash
        # rows hold their values: the parent pass evaluated them against zeros.
        #
        # **In DEPENDENCY order, not sequence order.** An aggregate over an
        # aggregate would otherwise read the stale zero its parent pass left:
        # with A = B and B = a cash row, a pass in sequence order computes A
        # from B's zero and only then fixes B, returning a wrong A and no error.
        # The shipped rows happen to be sequenced safely, so this would have sat
        # here until somebody added a row — found by a second opinion from
        # gpt-5.3-codex, and pinned by a test whose aggregates point forward.
        for ldef in self._cssk_eval_order():
            if ldef.kind != "aggregate" or ldef.code in overrides:
                continue
            computed[ldef.code] = self._eval_aggregate(
                ldef.aggregate_formula, computed)
        return computed, columns

    def _cssk_cash_category_totals(self, date_from, date_to):
        """``{category code: amount}`` from the denník for the period.

        **Non-cash rows are left out.** A výkaz o príjmoch a výdavkoch reports
        money received and money paid; the odpis that never touched the bank
        belongs in the income-tax base, not in this statement. It is carried in
        the denník's non-cash part and reaches DPFO tabuľka 1 from there.

        Amounts are taken as the classification carries them, so a storno
        reduces its own category instead of appearing on the other side.
        """
        self.ensure_one()
        rows = self.env["cssk.cash.journal.line"].search([
            ("company_id", "=", self.company_id.id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
            ("non_cash", "=", False),
        ])
        totals = {}
        for row in rows:
            code = row.category_id.code
            if not code:
                continue
            totals[code] = totals.get(code, 0.0) + row.amount_classified
        return totals

    @api.model
    def _cssk_eval_cash_categories(self, formula, totals):
        """Signed sum of the category totals named in ``formula``."""
        value = 0.0
        for token in (formula or "").split(","):
            token = token.strip()
            if not token:
                continue
            sign = -1.0 if token.startswith("-") else 1.0
            value += sign * totals.get(token.lstrip("-"), 0.0)
        return value
