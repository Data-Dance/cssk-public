from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CsskStatementAccountMap(models.Model):
    """Report an account of THIS company's chart under another account code.

    Every statutory statement reads ledger balances by account-code prefix,
    and the forms name the standard chart's codes: Úč POD puts dlhodobé
    bankové úvery on 461100 and bežné on 461200. A chart carried over from
    another system keeps its own analytics — 461001 for the long-term loan,
    461002 for the short-term one — and those match no row at all. The money
    is in the ledger and not on the form, and the sheet stops balancing.

    Renaming the accounts would rewrite the client's chart to suit a form.
    This keeps the chart and says, per company, which code an account is
    REPORTED under. The substitution happens where the balances are read
    (``_cssk_balances_by_account_code``), so the preview, the filed XML, the
    unmapped check and the drill-down all see the same thing.

    ``balance_side`` handles the account whose row depends on the sign of its
    balance at the period end — the overdrawn bank account that must be shown
    as a krátkodobý bankový úver. A debit- or credit-only mapping applies to
    the cumulative as-of balance only (the balance sheet); a period movement
    has no side in that sense, so those windows read the account under its
    own code.
    """

    _name = "cssk.statement.account.map"
    _description = "Statement account mapping"
    _order = "company_id, reported_code, id"

    company_id = fields.Many2one(
        "res.company", required=True, ondelete="cascade", index=True,
        default=lambda self: self.env.company)
    account_id = fields.Many2one(
        "account.account", required=True, ondelete="cascade",
        domain="[('company_ids', 'in', company_id)]")
    reported_code = fields.Char(
        required=True,
        help="The account code the statutory statements read this account "
        "as — a code the form's rows name, e.g. 461200 for a short-term bank "
        "loan on the Slovak Úč POD.")
    balance_side = fields.Selection(
        [("any", "Any balance"),
         ("debit", "Debit balance only"),
         ("credit", "Credit balance only")],
        required=True, default="any",
        help="Any balance: always reported under the code.\n"
        "Debit / credit balance only: reported under the code only when the "
        "account's balance at the period end has that sign (an overdrawn "
        "bank account reported as a bank loan); otherwise it keeps its own "
        "code. Applies to balance-sheet balances only.")
    note = fields.Char()

    _company_account_side_uniq = models.Constraint(
        "UNIQUE (company_id, account_id, balance_side)",
        "An account can be mapped only once per balance side.")

    @api.constrains("reported_code")
    def _check_reported_code(self):
        for rec in self:
            code = (rec.reported_code or "").strip()
            if not code or any(ch in code for ch in ", -&!"):
                raise ValidationError(_(
                    "The reported code must be a plain account code, without "
                    "spaces, commas, signs or tag operators."))

    @api.constrains("account_id", "company_id", "balance_side")
    def _check_sides(self):
        for rec in self:
            sides = self.search([
                ("company_id", "=", rec.company_id.id),
                ("account_id", "=", rec.account_id.id),
            ]).mapped("balance_side")
            if "any" in sides and len(sides) > 1:
                raise ValidationError(_(
                    "Account %s is mapped for any balance AND for one side. "
                    "Use either one 'any balance' mapping, or a debit and/or "
                    "a credit mapping.", rec.account_id.display_name))

    @api.model
    def _cssk_map_for(self, company):
        """``{account_id: {side: reported_code}}`` for ``company``."""
        if not company:
            return {}
        result = {}
        # sudo: the mapping is configuration that decides the figures, so a
        # user who may compute or read a statement of ``company`` must get
        # the same figures as the manager who configured it — not fewer rows
        # because they lack read access to the configuration. Only that one
        # company's mappings are read, and only to produce its own figures.
        for rec in self.sudo().search([("company_id", "=", company.id)]):
            result.setdefault(rec.account_id.id, {})[rec.balance_side] = (
                rec.reported_code.strip())
        return result

    @api.model
    def _cssk_reported_code(self, mapping, account_id, own_code, balance,
                            as_of):
        """The code ``account_id`` is reported under, given its balance."""
        sides = mapping.get(account_id)
        if not sides:
            return own_code
        if "any" in sides:
            return sides["any"]
        if as_of and balance:
            side = "credit" if balance < 0 else "debit"
            return sides.get(side, own_code)
        return own_code
