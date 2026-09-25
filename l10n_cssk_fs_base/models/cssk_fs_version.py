import re

from odoo import fields, models


class CSSKFsVersion(models.Model):
    """A versioned financial-statement template (Súvaha / VZS / Rozvaha / VZZ)."""

    _name = "cssk.fs.statement.version"
    _description = "Financial Statement Version"
    _order = "country_id, statement_kind, valid_from desc"

    name = fields.Char(required=True)
    country_id = fields.Many2one("res.country", required=True)
    statement_kind = fields.Selection(
        [
            ("balance_sheet", "Balance sheet"),
            ("profit_loss", "Income statement"),
            ("cash_flow", "Cash flow statement"),
            ("equity_changes", "Statement of changes in equity"),
        ],
        required=True,
        help="Balance sheet evaluates account balances **as of** the period "
        "end (cumulative); P&L, cash flow and changes-in-equity evaluate the "
        "**period** movement (use the accounts_open / accounts_close line kinds "
        "for the opening / closing balances within those statements).",
    )
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    line_def_ids = fields.One2many(
        "cssk.fs.statement.line.def", "version_id"
    )

    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's "
        "statutory XML.")
    xml_schema_data = fields.Binary(attachment=True)
    xml_schema_filename = fields.Char()
    xml_schema_optional = fields.Boolean(
        string="No official XSD exists",
        help="Tick only where the authority publishes NO schema for this "
        "form, so its absence is a fact about the form and not a missing "
        "file. Export then skips validation and says so in the log, instead "
        "of refusing.\n\n"
        "The Czech accounting statements are the case: Rozvaha, Výkaz zisku "
        "a ztráty, Přehled o peněžních tocích and Přehled o změnách vlastního "
        "kapitálu are filed as attachments inside the DPPO envelope, and no "
        "standalone XSD is published for any of them. The Slovak side is the "
        "opposite — Úč POD ships uzpod-2014.xsd — which is why this is a "
        "property of the VERSION and not of the form family.")
    xml_root_element = fields.Char(required=True)

    # ------------------------------------------------------------------
    # Properties of the DEFINITIONS, read by everything that matches an
    # account code against them: the statement that computes the figures and
    # the reverse-drill footprint that says which rows a posting feeds.
    #
    # THE RULE, and it was learned three times in a row: a hook that answers a
    # question about the DEFINITIONS belongs on the version, not on the
    # computed record. All three of `_cssk_claimed_codes`,
    # `_cssk_two_sided_prefixes` and `_cssk_tag_codes` started on
    # `cssk.fs.statement`, where the forward direction could reach them and
    # the reverse direction could not — so the footprint quietly answered a
    # different question from the figures, and a country override reached one
    # of them and not the other.
    #
    # The test for a new hook is therefore: does it decide WHICH ROW an
    # account feeds? If so it goes here. Ordering, diagnostics and rendering
    # stay on the statement — they shape the computation, not the mapping.
    # ------------------------------------------------------------------
    def _cssk_formula_tokens(self):
        """Every account token this version's rows name, both columns."""
        self.ensure_one()
        return [
            tok
            for ldef in self.line_def_ids
            for formula in (ldef.account_formula,
                            ldef.account_formula_correction)
            for tok in (formula or "").split(",")
        ]

    def _cssk_claimed_codes(self):
        """Account codes some row of this version names OUTRIGHT.

        A residual row takes what is left of its group after every named row
        has taken its own, so the set of names is what "left" means. Returns
        ``None`` where the version uses no residual token at all, which turns
        the whole mechanism off and keeps every existing form byte-identical.

        An ``X`` only counts as a residual where it is part of the ACCOUNT
        code: UZPODv14 also writes tag filters (``666&X_1``) whose tag NAMES
        contain an X, and reading those as residuals switched the mechanism on
        for a form that has none — under which a six-digit token ending in 000
        excludes its own account, so ``013000`` matched nothing.
        """
        self.ensure_one()
        codes = [self._cssk_token_code(tok)
                 for tok in self._cssk_formula_tokens()]
        codes = [c for c in codes if c]
        if not any("X" in c for c in codes):
            return None
        return {c for c in codes if "X" not in c}

    def _cssk_two_sided_prefixes(self):
        """Prefixes this version names on BOTH sides of the sheet.

        341-347 are a pohľadávka or a záväzok by the sign of the balance, and
        481000, 316100 and 373100 likewise. Summed ungated the same balance
        lands on both sides at once and nothing objects: the sheet still foots
        and still balances.
        """
        self.ensure_one()
        pos, neg = set(), set()
        for tok in self._cssk_formula_tokens():
            tok = tok.strip()
            if not tok:
                continue
            (neg if tok.startswith("-") else pos).add(
                self._cssk_token_code(tok))
        return {code for code in pos & neg if code}

    def _cssk_tag_codes(self):
        """``{tag: {account codes}}`` for a version whose rows filter by tag.

        Some rows cannot be told apart by account code at all: Úč POD 2 splits
        financial income IX/X/XI and cost N by whether the counterparty is a
        prepojená účtovná jednotka, which lives on an account TAG. The token
        grammar says it as ``665&IX_1`` (only accounts tagged IX_1) and
        ``665!IX_1!IX_2`` (everything else, so the "ostatné" leaf needs no
        setup at all).

        Returning ``None`` — the default — leaves such a token parsed as a
        LITERAL prefix, matching no account and reporting a silent zero. That
        is what every version without tagged rows wants, because a country
        module whose formulas happen to contain ``&`` would otherwise change
        the figures it files.

        On the VERSION, with the statement delegating, because the reverse
        drill needs it too: without it a posting to a 665 account is reported
        as feeding all THREE IX rows, one of them the residual leaf it
        definitively does not reach.
        """
        self.ensure_one()
        return None

    def _cssk_token_code_in(self, ldef, two_sided):
        """Does this row name a two-sided account, so its side is a question?"""
        self.ensure_one()
        if not two_sided:
            return False
        for formula in (ldef.account_formula, ldef.account_formula_correction):
            for tok in (formula or "").split(","):
                if self._cssk_token_code(tok) in two_sided:
                    return True
        return False

    @staticmethod
    def _cssk_token_code(token):
        """The account-code part of a token: ``-666&X_1`` -> ``666``."""
        token = (token or "").strip().lstrip("-").upper()
        return re.split(r"[&!]", token)[0].strip() if token else ""


class CSSKFsLineDef(models.Model):
    """A financial-statement line definition.

    ``accounts``  → value = signed sum of move-line balances on accounts whose
                    code matches the formula (comma-separated prefixes; a
                    leading '-' on a token negates it).
    ``aggregate`` → value = formula over other line codes.
    ``manual``    → entered by the user.
    """

    _name = "cssk.fs.statement.line.def"
    _description = "Financial Statement Line Definition"
    _order = "version_id, sequence, code"

    version_id = fields.Many2one(
        "cssk.fs.statement.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    level = fields.Integer(
        default=0, help="Indentation level for display (0 = top)."
    )
    kind = fields.Selection(
        [
            ("accounts", "Account codes"),
            ("accounts_open", "Account balances — period start (cash flow)"),
            ("accounts_close", "Account balances — period end (cash flow)"),
            ("aggregate", "Aggregate of other lines"),
            ("manual", "Manual"),
        ],
        required=True,
        default="accounts",
        help="``accounts`` = period movement (P&L / cash flow) or as-of balance "
        "(balance sheet). ``accounts_open`` / ``accounts_close`` = cumulative "
        "balance at the start / end of the period — for the opening / closing "
        "cash rows of a cash-flow statement.",
    )
    basis = fields.Selection(
        [
            ("version", "From the statement kind"),
            ("as_of", "Cumulative balance as of the period end"),
            ("movement", "Movement within the period"),
        ],
        required=True, default="version",
        help="Which balance a ``kind=accounts`` line reads. Left at 'From the "
        "statement kind' it follows the version — as-of for a balance sheet, "
        "movement for a P&L, cash flow or changes in equity — which is what "
        "every statement filed as its own document wants.\n\n"
        "Set it explicitly only where ONE document carries rows of both "
        "bases. The Slovak účtovná závierka is exactly that: UZPODv14 is a "
        "single ``dokument`` whose ``telo`` holds ``ucPod1Suvaha`` (as-of) "
        "beside ``ucPod2VykazZS`` (movement), so a version modelling it cannot "
        "have one basis for all its lines.",
    )
    account_formula = fields.Char(
        help="Account-code prefixes for kind=accounts, e.g. '012,013,-072' "
        "(leading '-' negates the token). Where a correction formula is also "
        "set this is the GROSS side (brutto).",
    )
    account_formula_correction = fields.Char(
        string="Correction formula",
        help="Accounts of the row's correction column (korekcia) — "
        "accumulated depreciation and impairment. Set only on a form filed in "
        "brutto / korekcia / netto columns, which the Slovak Súvaha is: the "
        "tlačivo states both groups per row, e.g. r005 Softvér is "
        "'(013) - /073, 091A/', so account_formula='013' and "
        "account_formula_correction='073,091'. Netto is derived as gross minus "
        "correction; leave empty and the row reports a single net figure as "
        "before.",
    )

    def _cssk_reads_movement(self):
        """Whether this line reads the period movement rather than the as-of
        balance. The version's ``statement_kind`` is the default and stays the
        answer for every statement that is filed on its own."""
        self.ensure_one()
        if self.basis != "version":
            return self.basis == "movement"
        return self.version_id.statement_kind in (
            "profit_loss", "cash_flow", "equity_changes")
    aggregate_formula = fields.Char(
        help="Formula over line codes for kind=aggregate, e.g. 'a_i + a_ii'.",
    )
