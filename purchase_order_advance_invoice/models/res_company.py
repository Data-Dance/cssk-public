from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Received Advance Tax Documents Journal",
        domain="[('type', '=', 'purchase')]",
        check_company=True,
        help="Purchase journal for the suppliers' tax documents on sent "
        "advance payments (e.g. PDADV).",
    )
    advance_paid_clearing_account_id = fields.Many2one(
        "account.account",
        string="Paid Advances Clearing Account",
        check_company=True,
        help="Reconcilable clearing account (e.g. 314001) carrying both "
        "the advance payment and the tax document's payable leg. Must "
        "be of payable type: it is the payment-term leg of the vendor "
        "bill.",
    )
    advance_paid_account_id = fields.Many2one(
        "account.account",
        string="Paid Advances Account",
        check_company=True,
        help="Net paid advances (e.g. 314000 — poskytnuté zálohy / "
        "preddavky).",
    )
    advance_paid_account_lt_id = fields.Many2one(
        "account.account",
        string="Paid Advances Account (Long-term)",
        check_company=True,
        help="Optional long-term variant; falls back to the short-term "
        "account when empty.",
    )

    # ------------------------------------------------------------------
    # Localization spec application (mirror of the sale-side pattern)
    # ------------------------------------------------------------------
    def _resolve_purchase_advance_account(self, code):
        self.ensure_one()
        return self.env["account.account"].with_company(self).search(
            [
                ("code", "=", code),
                ("company_ids", "in", self.id),
            ],
            limit=1,
        )

    def _apply_purchase_advance_setup(self, spec):
        """Idempotent: creates missing accounts/journal and fills only the
        EMPTY company fields, never clobbering manual configuration."""
        self.ensure_one()
        Account = self.env["account.account"]
        for acc in spec.get("create_accounts", []):
            if self._resolve_purchase_advance_account(acc["code"]):
                continue
            Account.with_company(self).create({
                "code": acc["code"],
                "name": acc["name"],
                "account_type": acc.get("account_type", "liability_payable"),
                "reconcile": acc.get("reconcile", True),
            })
        role_fields = {
            "paid_clearing": "advance_paid_clearing_account_id",
            "paid_st": "advance_paid_account_id",
            "paid_lt": "advance_paid_account_lt_id",
        }
        for role, field_name in role_fields.items():
            code = spec.get("accounts", {}).get(role)
            if not code or self[field_name]:
                continue
            account = self._resolve_purchase_advance_account(code)
            if account:
                self[field_name] = account
        if not self.advance_purchase_journal_id:
            Journal = self.env["account.journal"]
            journal = Journal.with_company(self).search(
                [
                    ("code", "=", spec["journal_code"]),
                    ("company_id", "=", self.id),
                ],
                limit=1,
            )
            if not journal:
                journal = Journal.with_company(self).create({
                    "name": spec["journal_name"],
                    "code": spec["journal_code"],
                    "type": "purchase",
                    "company_id": self.id,
                })
            self.advance_purchase_journal_id = journal
