from odoo import Command, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_invoice_journal_id = fields.Many2one(
        "account.journal",
        string="Advance Invoices Journal",
        # The advance tax documents are out_invoice moves kept in a dedicated
        # journal (typically a general journal, code TDADV) so they are separated
        # from ordinary customer invoices; the move-type check is relaxed for it.
        domain="[('company_id', '=', id), ('type', 'in', ('sale', 'general'))]",
        check_company=True,
        # No default / not required: a cross-company env.ref default breaks the
        # creation of additional companies (check_company error).  The journal is
        # populated by the install hook, by the localization modules, or manually.
    )
    advance_received_account_id = fields.Many2one(
        "account.account",
        string="Advance Clearing Account",
        domain="[('reconcile', '=', True)]",
        check_company=True,
        help="Reconcilable clearing/transit account used to match the advance "
        "payment against its tax document. Both the payment and the receivable "
        "side of the tax document are posted here and reconciled together.",
    )
    advance_tax_doc_account_id = fields.Many2one(
        "account.account",
        string="Received Advance Account (short-term)",
        check_company=True,
        help="Account carrying the net (ex-VAT) received advance until it is "
        "settled on the final invoice. Used on the tax-document income line and "
        "on the settlement deduction line. Short-term received advances.",
    )
    advance_tax_doc_account_lt_id = fields.Many2one(
        "account.account",
        string="Received Advance Account (long-term)",
        check_company=True,
        help="As the short-term received-advance account, but for advances that "
        "are settled after more than one year (long-term received advances).",
    )

    # ------------------------------------------------------------------
    # Localization spec application (see ``tools.apply_advance_invoice_spec``)
    # ------------------------------------------------------------------
    def _resolve_advance_account(self, code):
        """Resolve a statutory account ``code`` to a record for this company."""
        self.ensure_one()
        if not code:
            return self.env["account.account"]
        return self.env["account.account"].with_company(self).search(
            [("code", "=", code), ("company_ids", "in", self.id)], limit=1
        )

    def _apply_advance_invoice_setup(self, spec):
        """Fill empty advance-invoice config fields from a localization ``spec``.

        Idempotent and non-destructive: only fields that are currently unset are
        written, so a hand-configured deployment is preserved on upgrade.
        """
        field_by_role = {
            "received_clearing": "advance_received_account_id",
            "tax_doc_st": "advance_tax_doc_account_id",
            "tax_doc_lt": "advance_tax_doc_account_lt_id",
        }
        accounts_spec = spec.get("accounts", {})
        for company in self:
            created = company._ensure_advance_accounts(spec)
            vals = {}
            for role, field in field_by_role.items():
                if field not in company._fields or company[field]:
                    continue
                code = accounts_spec.get(role)
                # Prefer an account we just created/looked up by code (avoids a
                # company-dependent code search resolving to the wrong account
                # before the new account's code is flushed).
                account = created.get(code) or company._resolve_advance_account(code)
                if account:
                    vals[field] = account.id

            if not company.advance_invoice_journal_id:
                journal = company._get_or_create_advance_invoice_journal(spec)
                if journal:
                    vals["advance_invoice_journal_id"] = journal.id

            if vals:
                company.write(vals)

    def _ensure_advance_accounts(self, spec):
        """Create localization-specific accounts that the standard chart lacks.

        ``spec['create_accounts']`` is a list of dicts with at least ``code`` and
        ``name``; ``account_type`` defaults to ``asset_receivable`` (the clearing
        account is used as the receivable side of the tax document and reconciled
        against the payment) and ``reconcile`` to ``True``. Skipped if the code
        already exists for the company.
        """
        self.ensure_one()
        Account = self.env["account.account"]
        created = {}
        for acc in spec.get("create_accounts", []):
            existing = self._resolve_advance_account(acc["code"])
            if existing:
                created[acc["code"]] = existing
                continue
            created[acc["code"]] = Account.with_company(self).create({
                "name": acc.get("name", acc["code"]),
                "code": acc["code"],
                "account_type": acc.get("account_type", "asset_receivable"),
                "reconcile": acc.get("reconcile", True),
                "company_ids": [Command.link(self.id)],
            })
        # Flush so subsequent company-dependent code searches see the new accounts.
        self.env.flush_all()
        return created

    def _get_or_create_advance_invoice_journal(self, spec):
        """Return a dedicated journal for advance tax documents, creating it if
        the company does not have one yet (journal codes are unique per company)."""
        self.ensure_one()
        code = spec.get("journal_code", "TDADV")
        Journal = self.env["account.journal"]
        journal = Journal.search(
            [("company_id", "=", self.id), ("code", "=", code)], limit=1
        )
        if journal:
            return journal
        return Journal.create({
            "name": spec.get("journal_name", "Tax Documents for Advance Invoices"),
            "code": code,
            "type": "general",
            "company_id": self.id,
        })
