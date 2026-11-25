# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

CZ_CLOSING_ACCOUNT_CODE = "702000"  # Konečný účet rozvažný
CZ_OPENING_ACCOUNT_CODE = "701000"  # Počáteční účet rozvažný
CZ_PL_ACCOUNT_CODE = "710000"  # Účet zisků a ztrát
CZ_RESULT_APPROVAL_ACCOUNT_CODE = "431000"  # Výsledek hospodaření ve schvalovacím řízení


class AccountFiscalyearClosingConfig(models.Model):
    _inherit = "account.fiscalyear.closing.config"

    def _l10n_cz_is_cz(self):
        self.ensure_one()
        return self.fyc_id.company_id.chart_template == "cz"

    def _mapping_move_lines_get(self):
        """Mirror every closed account on the závěrkový účet, not just the net.

        The generic engine posts ONE destination line carrying the *net* of all
        source accounts. On a complete balance sheet that net is zero, so 702
        would not appear in the entry at all: the assets would simply be set
        against the liabilities. That balances, but it is not the Czech
        závěrka. ČÚS 002 bod 2.2.3 closes the final balances of the asset
        accounts and of the liability accounts against the *konečný účet
        rozvažný*, so 702 carries the counter-entry of each of them (its own
        total then being zero by the balance equation, not by omission).

        So for CZ each source line is paired with its mirror on the
        destination. The same code as in l10n_sk_fiscal_year_closing, gated on
        the Czech chart; the two cannot share a module because each depends on
        its own chart.
        """
        move_lines = super()._mapping_move_lines_get()
        if not self._l10n_cz_is_cz():
            return move_lines

        dest_ids = {m.dest_account_id.id for m in self.mapping_ids if m.dest_account_id}
        if not dest_ids:
            return move_lines

        # Each mapping has its own destination, so resolve source account ->
        # destination per mapping rather than assuming a single one. Our CZ
        # template does use one destination per config, but a hand-edited
        # closing may not, and mirroring everything onto the first mapping's
        # destination would post a plausible-but-wrong allocation.
        dest_by_source = {}
        for mapping in self.mapping_ids.filtered("dest_account_id"):
            src_accounts = self.env["account.account"].search(
                [
                    ("company_ids", "in", self.fyc_id.company_id.ids),
                    ("code", "=ilike", mapping.src_accounts),
                ]
            )
            for account in src_accounts:
                dest_by_source.setdefault(account.id, mapping.dest_account_id)

        # Drop the engine's netted destination line(s); we re-emit per account.
        source_lines = [line for line in move_lines if line.get("account_id") not in dest_ids]

        mirrored = []
        for line in source_lines:
            mirrored.append(line)
            dest_account = dest_by_source.get(line.get("account_id"))
            if not dest_account:
                # No mapping claims this account: leave the engine's own
                # balancing behaviour alone rather than inventing a counterpart.
                continue
            counter = dict(
                line,
                account_id=dest_account.id,
                debit=line.get("credit") or 0.0,
                credit=line.get("debit") or 0.0,
            )
            # Only carry amount_currency when the source line actually had one.
            # Passing amount_currency=0 on a line with no foreign currency makes
            # Odoo derive the balance FROM it and zero the line, silently
            # unbalancing the entry.
            if line.get("amount_currency"):
                counter["amount_currency"] = -line["amount_currency"]
            else:
                counter.pop("amount_currency", None)
            mirrored.append(counter)
        return mirrored

    def inverse_move_prepare(self):
        """Reopen through 701, and reopen the result on 431, not on 710.

        The engine builds the opening move by plainly reversing the closing one,
        which would leave **702** as the counterpart on both sides and put the
        year's result back on **710**. ČÚS 002 names two accounts of group 70:
        the books close on the *konečný účet rozvažný* (702) and open on the
        *počáteční účet rozvažný* (701, bod 2.1.2), so that counterpart is
        swapped.

        The result is the other half. The closing carries it from 710 to 702
        (bod 2.2.3), and a plain reversal would reopen it on 710, a závěrkový
        účet with no place in the new year. Bod 2.1.3 says where it goes:
        "Zisk, popřípadě ztráta, zaúčtovaný ve prospěch, popřípadě na vrub,
        konečného účtu rozvažného se při otevírání účtů hlavní knihy zaúčtuje
        ve prospěch, případně na vrub, příslušného účtu účtové skupiny 43 –
        Výsledek hospodaření se souvztažným zápisem na vrub, případně ve
        prospěch, počátečního účtu rozvažného." The standard names the group;
        431 is the account of the směrná účtová osnova convention and of the
        l10n_cz chart. Reversing the 710 / 702 pair and swapping both accounts
        gives exactly that, with the sign carried over.
        """
        move_ids = super().inverse_move_prepare()
        if not move_ids or self.move_type != "opening":
            return move_ids
        company = self.fyc_id.company_id
        if company.chart_template != "cz":
            return move_ids

        Account = self.env["account.account"]

        def account(code):
            return Account.search(
                [("company_ids", "in", company.ids), ("code", "=", code)],
                limit=1,
            )

        closing_account = account(CZ_CLOSING_ACCOUNT_CODE)
        opening_account = account(CZ_OPENING_ACCOUNT_CODE)
        moves = self.env["account.move"].browse(move_ids)
        if not (closing_account and opening_account):
            _logger.warning(
                "CZ závěrka: účet %s nebo %s chybí, otevření zůstává na 702.",
                CZ_CLOSING_ACCOUNT_CODE,
                CZ_OPENING_ACCOUNT_CODE,
            )
            # Leave the reversal whole rather than half-converted: a 702 /
            # 431 opening is neither the engine's entry nor the Czech one.
            return move_ids
        lines = moves.line_ids.filtered(
            lambda line: line.account_id == closing_account
        )
        if lines:
            lines.account_id = opening_account

        pl_account = account(CZ_PL_ACCOUNT_CODE)
        result_lines = moves.line_ids.filtered(
            lambda line: pl_account and line.account_id == pl_account
        )
        if result_lines:
            approval_account = account(CZ_RESULT_APPROVAL_ACCOUNT_CODE)
            if approval_account:
                result_lines.account_id = approval_account
            else:
                _logger.warning(
                    "CZ závěrka: účet %s chybí, výsledek hospodaření se "
                    "otevírá na %s.",
                    CZ_RESULT_APPROVAL_ACCOUNT_CODE,
                    CZ_PL_ACCOUNT_CODE,
                )
        return move_ids


class AccountFiscalyearClosing(models.Model):
    _inherit = "account.fiscalyear.closing"

    l10n_cz_pre_close_warning = fields.Text(
        string="Before closing the year",
        compute="_compute_l10n_cz_pre_close_warning",
    )

    @api.depends("company_id", "date_start", "date_end", "state")
    def _compute_l10n_cz_pre_close_warning(self):
        for closing in self:
            issues = (
                closing._l10n_cz_pre_close_issues()
                if closing.state in ("draft", "calculated")
                and closing.date_start
                and closing.date_end
                and closing.company_id.account_fiscal_country_id.code == "CZ"
                else []
            )
            closing.l10n_cz_pre_close_warning = "\n".join(issues) or False

    def _l10n_cz_pre_close_issues(self):
        """What an accountant has to look at before the year is closed.

        Advisory only: each item can have a legitimate explanation. Modules
        that may be absent are looked up by name, so the check runs on every
        combination of Community, OCA and Enterprise.
        """
        self.ensure_one()
        env = self.env
        company = self.company_id
        period = [
            ("company_id", "=", company.id),
            ("date", ">=", self.date_start),
            ("date", "<=", self.date_end),
        ]
        issues = []
        Move = env["account.move"].sudo()
        draft = Move.search_count(period + [("state", "=", "draft")])
        if draft:
            issues.append(_("%(count)s draft journal entries.", count=draft))
        gaps = Move.search_count(
            period + [("state", "=", "posted"), ("made_sequence_gap", "=", True)]
        )
        if gaps:
            issues.append(_("%(count)s gaps in document numbering.", count=gaps))
        for prefix, label in (
            ("431", _("profit or loss awaiting approval")),
            ("395", _("internal settlement")),
            ("261", _("cash in transit")),
        ):
            accounts = env["account.account"].sudo().with_company(company).search(
                [("company_ids", "in", company.id), ("code", "=like", prefix + "%")]
            )
            balance = sum(
                env["account.move.line"].sudo().search([
                    ("account_id", "in", accounts.ids),
                    ("company_id", "=", company.id),
                    ("parent_state", "=", "posted"),
                    ("date", "<=", self.date_end),
                ]).mapped("balance")
            )
            if not company.currency_id.is_zero(balance):
                issues.append(_(
                    "Account %(prefix)s (%(label)s) has a balance of %(balance).2f.",
                    prefix=prefix, label=label, balance=balance,
                ))
        if "hr.payslip" in env:
            payslips = env["hr.payslip"].sudo().search_count([
                ("company_id", "=", company.id),
                ("state", "=", "draft"),
                ("date_to", ">=", self.date_start),
                ("date_to", "<=", self.date_end),
            ])
            if payslips:
                issues.append(_("%(count)s draft payslips.", count=payslips))
        if "account.asset.line" in env:
            depreciation = env["account.asset.line"].sudo().search_count([
                ("company_id", "=", company.id),
                ("type", "=", "depreciate"),
                ("init_entry", "=", False),
                ("move_id", "=", False),
                ("line_date", ">=", self.date_start),
                ("line_date", "<=", self.date_end),
                ("asset_id.state", "=", "open"),
            ])
            if depreciation:
                issues.append(
                    _("%(count)s depreciation lines not posted.", count=depreciation)
                )
        if "cssk.vat.return" in env:
            Return = env["cssk.vat.return"].sudo()
            year_returns = Return.search([
                ("company_id", "=", company.id),
                ("date_to", ">=", self.date_start),
                ("date_to", "<=", self.date_end),
            ])
            if year_returns and not year_returns.filtered(
                lambda r: r.date_to == self.date_end
                and r.state in ("exported", "submitted")
            ):
                issues.append(_("The VAT return for the last period is not filed."))
        return issues
