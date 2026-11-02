# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Data service behind the interactive general ledger / trial balance.

The OCA reports compute every line up front and render static HTML. Here the
account rows (opening, debit, credit, closing) are aggregated by
``read_group`` and an account's journal items are fetched only when it is
unfolded, a page at a time, so a ledger with hundreds of thousands of items
opens as fast as its trial balance.

Every read goes through the ORM (``read_group`` / ``search_fetch``): access
rights and record rules apply, so the public methods are safe to call over
RPC by any user.

``data`` is the dictionary the OCA wizards prepare for their own reports
(``_prepare_report_general_ledger`` / ``_prepare_report_trial_balance``), so a
module adjusting those (e.g. leaving out year-end closing journals) adjusts
this view too.
"""
import ast

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

PAGE = 80


class AccountFinancialReportInteractive(models.AbstractModel):
    _name = "account.financial.report.interactive"
    _description = "Interactive general ledger / trial balance"

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------
    @api.model
    def _base_domain(self, data):
        domain = Domain([("company_id", "=", data["company_id"]), ("display_type", "not in", ("line_section", "line_note"))])
        if data.get("only_posted_moves"):
            domain &= Domain("parent_state", "=", "posted")
        else:
            domain &= Domain("parent_state", "in", ("posted", "draft"))
        if data.get("account_ids"):
            domain &= Domain("account_id", "in", data["account_ids"])
        if data.get("partner_ids"):
            domain &= Domain("partner_id", "in", data["partner_ids"])
        if data.get("journal_ids"):
            domain &= Domain("journal_id", "in", data["journal_ids"])
        if data.get("cost_center_ids"):
            domain &= Domain("analytic_distribution", "in", data["cost_center_ids"])
        if data.get("domain"):
            domain &= Domain(data["domain"])
        if data.get("extra_domain"):
            domain &= Domain(self._parse_extra_domain(data["extra_domain"]))
        return domain

    @api.model
    def _parse_extra_domain(self, text):
        """The filter built in the view's domain editor, as a literal domain.
        Literal parsing only: the text comes from the browser."""
        if isinstance(text, list):
            return text
        try:
            value = ast.literal_eval(text)
        except (ValueError, SyntaxError) as exc:
            raise UserError(self.env._(
                "This filter cannot be applied: %s", text)) from exc
        if not isinstance(value, list):
            raise UserError(self.env._("This filter cannot be applied: %s", text))
        return value

    @api.model
    def _period_domain(self, data):
        return self._base_domain(data) & Domain([
            ("date", ">=", data["date_from"]), ("date", "<=", data["date_to"])])

    @api.model
    def _fy_start(self, data):
        return data.get("fy_start_date") or data["date_from"]

    @api.model
    def _sum_by_account(self, domain, aggregates=("balance:sum",)):
        return {
            account.id: values
            for account, *values in self.env["account.move.line"]._read_group(
                domain, ["account_id"], list(aggregates))
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Comparison periods
    # ------------------------------------------------------------------
    @api.model
    def _comparison_periods(self, data, comparison):
        """[(label, date_from, date_to)] of the periods to compare with, most
        recent first: ``previous`` steps back by the period's own length (whole
        months when the period is whole months), ``last_year`` by years."""
        if not comparison or comparison.get("mode") not in ("previous", "last_year"):
            return []
        count = max(1, min(int(comparison.get("count") or 1), 12))
        date_from, date_to = data["date_from"], data["date_to"]
        whole_months = date_from.day == 1 and (date_to + relativedelta(days=1)).day == 1
        months = (date_to.year - date_from.year) * 12 + date_to.month - date_from.month + 1
        periods = []
        for k in range(1, count + 1):
            if comparison["mode"] == "last_year":
                start, end = date_from - relativedelta(years=k), date_to - relativedelta(years=k)
            elif whole_months:
                start = date_from - relativedelta(months=months * k)
                end = start + relativedelta(months=months, days=-1)
            else:
                length = (date_to - date_from).days + 1
                start = date_from - relativedelta(days=length * k)
                end = date_to - relativedelta(days=length * k)
            label = "%s - %s" % (fields.Date.to_string(start), fields.Date.to_string(end))
            periods.append((label, start, end))
        return periods

    @api.model
    def shift_period(self, data, step):
        """``data`` moved ``step`` periods back (-1) or forward (+1), by the
        same rule as the comparison: whole months when the period is whole
        months, its length in days otherwise. The fiscal year start follows
        when the period crosses into another fiscal year."""
        data = self._normalize(data)
        date_from, date_to = data["date_from"], data["date_to"]
        whole_months = date_from.day == 1 and (date_to + relativedelta(days=1)).day == 1
        if whole_months:
            months = (date_to.year - date_from.year) * 12 + date_to.month - date_from.month + 1
            start = date_from + relativedelta(months=months * step)
            end = start + relativedelta(months=months, days=-1)
        else:
            length = (date_to - date_from).days + 1
            start = date_from + relativedelta(days=length * step)
            end = date_to + relativedelta(days=length * step)
        company = self.env["res.company"].browse(data["company_id"])
        fy = company.compute_fiscalyear_dates(start)
        result = dict(data, date_from=start, date_to=end, fy_start_date=fy["date_from"])
        return {key: fields.Date.to_string(value) if key in ("date_from", "date_to", "fy_start_date")
                and value else value for key, value in result.items()}

    @api.model
    def _natural_sign(self, account):
        """-1 for accounts whose normal balance is a credit (income,
        liabilities, equity), 1 otherwise: growth is measured on that side, so
        rising revenue reads as a positive figure."""
        prefix = (account.account_type or "").split("_")[0]
        return -1 if prefix in ("income", "liability", "equity") else 1

    @api.model
    def _growth_sense(self, account):
        """1 when growth is good (income), -1 when it is bad (expenses), 0
        where 'better' depends on what the account is for."""
        prefix = (account.account_type or "").split("_")[0]
        return {"income": 1, "expense": -1}.get(prefix, 0)

    @api.model
    def get_accounts(self, data, comparison=None):
        """One row per account: opening, debit, credit and closing balance.

        Opening follows the account's ``include_initial_balance``: balance
        sheet accounts carry everything before the period, profit and loss
        accounts only what lies between the fiscal year start and the period;
        the profit and loss of earlier years is shown on the company's
        unaffected earnings account, so the opening column still balances.
        """
        data = self._normalize(data)
        base = self._base_domain(data)
        date_from = data["date_from"]
        fy_start = self._fy_start(data)
        period = self._sum_by_account(
            self._period_domain(data), ("debit:sum", "credit:sum", "balance:sum"))
        compared = []
        for label, start, end in self._comparison_periods(data, comparison):
            compared.append((label, self._sum_by_account(base & Domain([
                ("date", ">=", start), ("date", "<=", end)]))))
        opening_bs = self._sum_by_account(base & Domain([
            ("date", "<", date_from), ("account_id.include_initial_balance", "=", True)]))
        opening_pl = self._sum_by_account(base & Domain([
            ("date", ">=", fy_start), ("date", "<", date_from),
            ("account_id.include_initial_balance", "=", False)]))
        earlier_pl = sum(
            value[0] for value in self._sum_by_account(base & Domain([
                ("date", "<", fy_start), ("account_id.include_initial_balance", "=", False),
            ])).values())

        Account = self.env["account.account"]
        account_ids = set(period) | set(opening_bs) | set(opening_pl)
        for _label, values in compared:
            account_ids |= set(values)
        unaffected = Account.browse(data.get("unaffected_earnings_account") or [])
        if not unaffected:
            unaffected = Account.search([
                *Account._check_company_domain(data["company_id"]),
                ("account_type", "=", "equity_unaffected")], limit=1)
        currency = self.env["res.company"].browse(data["company_id"]).currency_id
        add_unaffected = unaffected and not currency.is_zero(earlier_pl) and (
            not data.get("account_ids") or unaffected.id in data["account_ids"])
        if add_unaffected:
            account_ids.add(unaffected.id)

        rows = []
        for account in Account.browse(account_ids).sorted(lambda a: (a.code or "", a.id)):
            debit, credit, balance = period.get(account.id, (0.0, 0.0, 0.0))
            opening = (opening_bs.get(account.id) or opening_pl.get(account.id) or [0.0])[0]
            if add_unaffected and account == unaffected:
                opening += earlier_pl
            compare = [currency.round((values.get(account.id) or [0.0])[0]) for _l, values in compared]
            if data.get("hide_account_at_0") and all(
                    currency.is_zero(v) for v in (opening, debit, credit, *compare)):
                continue
            net = currency.round(balance)
            growth = None
            if compare and not currency.is_zero(compare[0]):
                sign = self._natural_sign(account)
                growth = round((net - compare[0]) * sign / abs(compare[0]) * 100, 1)
            rows.append({
                "type": "account",
                "id": account.id,
                "code": account.code,
                "name": account.name,
                "group_id": account.group_id.id,
                "by_partner": self._group_by_partner(data, account),
                "centralized": self._centralized(data, account),
                "opening": currency.round(opening),
                "debit": currency.round(debit),
                "credit": currency.round(credit),
                "closing": currency.round(opening + balance),
                "net": net,
                "compare": compare,
                "growth": growth,
                "growth_sense": self._growth_sense(account),
            })
        if data.get("show_hierarchy"):
            rows = self._with_hierarchy(rows, data, currency)
        return {
            "accounts": rows,
            "statements": bool(self.env.ref(
                "partner_statement.activity_statement_wizard_action", raise_if_not_found=False)),
            "comparison_labels": [label for label, _values in compared],
            "currency_id": currency.id,
            "totals": {
                key: currency.round(sum(row[key] for row in rows if row["type"] == "account"))
                for key in ("opening", "debit", "credit", "closing")
            },
        }

    @api.model
    def get_lines(self, data, account_id, offset=0, start_balance=0.0, limit=PAGE, partner_id=None):
        """A page of the account's journal items in the period, with a running
        balance continuing from ``start_balance`` (the opening balance for the
        first page, the last row's balance for the next ones)."""
        data = self._normalize(data)
        domain = self._period_domain(data) & Domain("account_id", "=", account_id)
        if partner_id is not None:
            # 0 stands for the items without a partner.
            domain &= Domain("partner_id", "=", partner_id or False)
        account = self.env["account.account"].browse(account_id)
        if self._centralized(data, account):
            return self._centralized_lines(data, domain, start_balance)
        company_currency = self.env["res.company"].browse(data["company_id"]).currency_id
        AML = self.env["account.move.line"]
        total = AML.search_count(domain)
        lines = AML.search_fetch(
            domain,
            ["date", "move_id", "move_name", "journal_id", "partner_id", "name", "ref",
             "debit", "credit", "balance", "amount_currency", "currency_id"],
            order="date, move_name, id", offset=offset, limit=limit)
        running = start_balance
        result = []
        for line in lines:
            running += line.balance
            result.append({
                "id": line.id,
                "date": fields.Date.to_string(line.date),
                "move_id": line.move_id.id,
                "move_name": line.move_name or line.move_id.display_name,
                "journal": line.journal_id.code,
                "partner": line.partner_id.display_name or "",
                "partner_id": line.partner_id.id,
                "label": line.name or line.ref or "",
                "debit": line.debit,
                "credit": line.credit,
                "balance": running,
                "amount_currency": line.amount_currency
                if data.get("foreign_currency") and line.currency_id != company_currency else False,
                "currency": line.currency_id.name
                if data.get("foreign_currency") and line.currency_id != company_currency else "",
            })
        return {"lines": result, "total": total, "offset": offset + len(result)}

    # ------------------------------------------------------------------
    # Grouping options of the wizards
    # ------------------------------------------------------------------
    @api.model
    def _group_by_partner(self, data, account):
        """The general ledger's 'Grouped by: Partners' applies to the accounts
        that are kept per partner: receivables and payables."""
        return data.get("grouped_by") == "partners" and account.account_type in (
            "asset_receivable", "liability_payable")

    @api.model
    def _centralized(self, data, account):
        """OCA's 'Activate centralization': accounts flagged centralized show
        one line per month instead of every journal item."""
        return bool(data.get("centralize")) and bool(account.centralized)

    @api.model
    def _with_hierarchy(self, rows, data, currency):
        """Insert account-group subtotal rows (the trial balance's 'Show
        hierarchy'), in display order, each before its accounts. With 'Limit
        hierarchy levels', groups deeper than the chosen level are left out
        and their accounts sit under the deepest shown group."""
        Group = self.env["account.group"]
        limit = data.get("show_hierarchy_level") if data.get("limit_hierarchy_level") else None
        keys = ("opening", "debit", "credit", "closing", "net")
        totals, chains = {}, {}
        for row in rows:
            chain = []
            group = Group.browse(row["group_id"])
            while group:
                chain.insert(0, group)
                group = group.parent_id
            if limit:
                chain = chain[:limit]
            chains[row["id"]] = chain
            for group in chain:
                bucket = totals.setdefault(group.id, dict.fromkeys(keys, 0.0))
                for key in keys:
                    bucket[key] += row.get(key, 0.0)
        result, open_chain = [], []
        for row in rows:
            chain = chains[row["id"]]
            common = 0
            while common < min(len(chain), len(open_chain)) and chain[common] == open_chain[common]:
                common += 1
            for level, group in enumerate(chain[common:], start=common + 1):
                values = {key: currency.round(totals[group.id][key]) for key in keys}
                result.append(dict(values, type="group", id="g%s" % group.id, level=level,
                                   code=group.code_prefix_start or "", name=group.name,
                                   compare=[], growth=None, growth_sense=0))
            open_chain = chain
            result.append(dict(row, level=len(chain) + 1))
        return result

    @api.model
    def get_partners(self, data, account_id):
        """Partner rows of a receivable / payable account: opening, debit,
        credit and closing per partner (items without a partner together)."""
        data = self._normalize(data)
        base = self._base_domain(data) & Domain("account_id", "=", account_id)
        period = self._sum_by_partner(self._period_domain(data) & Domain("account_id", "=", account_id),
                                      ("debit:sum", "credit:sum", "balance:sum"))
        opening = self._sum_by_partner(base & Domain("date", "<", data["date_from"]))
        currency = self.env["res.company"].browse(data["company_id"]).currency_id
        rows = []
        for key in set(period) | set(opening):
            debit, credit, balance = period.get(key, (0.0, 0.0, 0.0))
            start = (opening.get(key) or [0.0])[0]
            if all(currency.is_zero(v) for v in (start, debit, credit, balance)):
                continue
            partner = self.env["res.partner"].browse(key)
            rows.append({
                "id": key, "name": partner.display_name if key else self.env._("No partner"),
                "opening": currency.round(start), "debit": currency.round(debit),
                "credit": currency.round(credit), "closing": currency.round(start + balance),
            })
        return sorted(rows, key=lambda r: (r["id"] == 0, (r["name"] or "").lower()))

    @api.model
    def _sum_by_partner(self, domain, aggregates=("balance:sum",)):
        return {
            partner.id or 0: values
            for partner, *values in self.env["account.move.line"]._read_group(
                domain, ["partner_id"], list(aggregates))
        }

    @api.model
    def _centralized_lines(self, data, domain, start_balance):
        """One line per month for a centralized account."""
        running = start_balance
        result = []
        for month, debit, credit, balance in self.env["account.move.line"]._read_group(
                domain, ["date:month"], ["debit:sum", "credit:sum", "balance:sum"], order="date:month"):
            running += balance
            result.append({
                "id": "m%s" % fields.Date.to_string(month), "date": fields.Date.to_string(month),
                "move_id": False, "move_name": self.env._("Centralized"), "journal": "",
                "partner": "", "partner_id": False,
                "label": month.strftime("%Y-%m"), "debit": debit, "credit": credit,
                "balance": running, "amount_currency": False, "currency": "",
            })
        return {"lines": result, "total": len(result), "offset": len(result)}

    @api.model
    def statement_action(self, data, partner_id):
        """The OCA partner activity statement for the partner and the report's
        period - send it by email, print or export from there. False when
        partner_statement is not installed."""
        action = self.env.ref(
            "partner_statement.activity_statement_wizard_action", raise_if_not_found=False)
        if not action:
            return False
        data = self._normalize(data)
        result = action._get_action_dict()
        result["context"] = {
            "active_model": "res.partner", "active_ids": [partner_id], "active_id": partner_id,
            "default_company_id": data["company_id"],
            "default_date_start": fields.Date.to_string(data["date_from"]),
            "default_date_end": fields.Date.to_string(data["date_to"]),
        }
        return result

    @api.model
    def get_account_domain(self, data, account_id):
        """Domain of the period's items of an account, for 'open in list'."""
        data = self._normalize(data)
        return list(self._period_domain(data) & Domain("account_id", "=", account_id))

    # ------------------------------------------------------------------
    @api.model
    def _normalize(self, data):
        data = dict(data)
        for key in ("date_from", "date_to", "fy_start_date"):
            if data.get(key):
                data[key] = fields.Date.to_date(data[key])
        return data
