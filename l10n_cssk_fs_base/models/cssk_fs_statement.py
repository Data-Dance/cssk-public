import logging
import re

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_lt = LazyTranslate(__name__)

_logger = logging.getLogger(__name__)


class CSSKFsStatement(models.Model):
    """Financial statement (Súvaha / VZS / Rozvaha / VZZ).

    A hierarchical line tree computed from account-code balances + aggregates,
    for a current period and a comparison (prior) period. CE-clean: reads
    ``account.move.line`` balances directly, no ``account_reports``.
    """

    _name = "cssk.fs.statement"
    _description = "Financial Statement"
    # Two mixins, two concerns, both wanted: the statutory one retains the
    # filed copy, the submittable one tracks whether it arrived and holds what
    # came back. Neither substitutes for the other — a daňová kontrola asks for
    # the doručenka, which only the second can produce.
    _inherit = ["mail.thread", "mail.activity.mixin",
                "cssk.statutory.submission.mixin",
                "cssk.submittable.mixin"]
    _order = "date_to desc, id desc"

    # Not stored: rendered in the reader's language (so the name never mixes
    # languages and localises on a Czech vs. Slovak server).
    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    country_id = fields.Many2one(
        related="company_id.account_fiscal_country_id", store=True
    )

    version_id = fields.Many2one(
        "cssk.fs.statement.version",
        required=True,
        domain="[('country_id', '=', country_id),"
        " ('valid_from', '<=', date_to),"
        " '|', ('valid_to', '=', False), ('valid_to', '>=', date_from)]",
        # The dropdown must offer an ARCHIVED vintage too. The domain
        # above already scopes by period, so a 2026 filing never sees
        # the 2014 vzor anyway — archiving is a way of tidying the
        # configuration list, and it must not quietly make an old
        # period unenterable or a historical filing un-repointable.
        context={'active_test': False},
    )
    statement_kind = fields.Selection(related="version_id.statement_kind")

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    # copy=True so an opravná závěrka inherits the original's manual overrides
    # (recompute then re-reads them); see action_create_amendment.
    line_ids = fields.One2many(
        "cssk.fs.statement.line", "statement_id", copy=True)

    # Health roll-up: how many drillable leaves don't tie to their journal items.
    unreconciled_count = fields.Integer(compute="_compute_unreconciled_count")

    # The other way a statement can be wrong while looking perfect: an account
    # whose code no row's formula covers contributes to nothing at all. The
    # sheet still foots and still balances — a balanced ledger says nothing
    # about whether every account reached a row — so this has to be reported
    # rather than inferred. Recorded at compute time, when the balances are in
    # hand.
    unmapped_count = fields.Integer(readonly=True, copy=False)
    unmapped_note = fields.Text(
        readonly=True, copy=False, string="Accounts on no row",
        help="Accounts carrying a balance that no row of this statement "
             "claims. Their money is in the ledger and not on the form.")

    @api.depends("line_ids.has_source", "line_ids.source_reconciles")
    def _compute_unreconciled_count(self):
        for stmt in self:
            stmt.unreconciled_count = len(stmt.line_ids.filtered(
                lambda ln: ln.has_source and not ln.source_reconciles))

    def action_view_unreconciled(self):
        self.ensure_one()
        bad = self.line_ids.filtered(
            lambda ln: ln.has_source and not ln.source_reconciles)
        return {
            "type": "ir.actions.act_window",
            "name": _("Unreconciled rows"),
            "res_model": "cssk.fs.statement.line",
            "view_mode": "list",
            "domain": [("id", "in", bad.ids)],
            "context": {"create": False, "delete": False},
        }

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("exported", "Exported"),
            ("submitted", "Submitted"),
            ("cancelled", "Cancelled"),
            # Terminal, and off the workflow rather than at the end of it. A
            # historical filing was completed and submitted years ago by
            # whoever ran the previous system; it is a RECORD of a filing, not
            # a filing in progress, so no transition leads into or out of it.
            # Set automatically whenever ``legacy`` is set — see
            # ``cssk.statutory.submission.mixin``, which owns that rule so the
            # importer cannot set one without the other.
            ("legacy", "Historical filing"),
        ],
        default="draft",
        tracking=True,
    )
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)

    # Amendment (opravná účetní / účtovná závierka) — a corrective re-filing of
    # an already-submitted FS. Unlike the tax returns there are no difference
    # rows: the amended statement is a full restatement of the same period,
    # flagged Opravná and linked back to the original filed copy.
    submission_type = fields.Selection(
        [("radna", "Regular"), ("opravna", "Corrective")],
        default="radna", copy=False, tracking=True, required=True,
        help="Regular = original filing; Corrective = a corrective financial "
             "statement that supersedes an already-submitted one for the same "
             "period.")
    original_return_id = fields.Many2one(
        "cssk.fs.statement", string="Amends", readonly=True, copy=False,
        help="The originally-filed statement this corrective statement corrects.")
    amendment_ids = fields.One2many(
        "cssk.fs.statement", "original_return_id", string="Amendments")

    _KIND_LABELS = {
        "balance_sheet": "Balance sheet",
        "profit_loss": "Income statement",
        "cash_flow": "Cash flow statement",
        "equity_changes": "Statement of changes in equity",
    }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # FS statements are annual — default to the previous calendar year so the
        # version domain (which depends on the period) resolves on a new record.
        today = fields.Date.context_today(self)
        res.setdefault(
            "date_from", today.replace(year=today.year - 1, month=1, day=1))
        res.setdefault(
            "date_to", today.replace(year=today.year - 1, month=12, day=31))
        # The per-kind menus pass ``fs_create_kind`` so New lands on the right
        # statement type with its current version preselected.
        kind = self.env.context.get("fs_create_kind")
        if kind and not res.get("version_id"):
            country = self.env.company.account_fiscal_country_id
            # ``active_test=False``: a historical vintage is exactly the kind
            # an administrator archives once it is superseded, and without this
            # New on an old period would find no version, leave the required
            # field empty, and offer nothing in the dropdown either — the field
            # domain filters the same way. Archiving has to stay a presentation
            # decision, not one that makes old periods unenterable.
            ver = self.env["cssk.fs.statement.version"].with_context(
                active_test=False).search([
                ("statement_kind", "=", kind),
                ("country_id", "=", country.id),
                ("valid_from", "<=", res["date_to"]),
                "|", ("valid_to", "=", False),
                ("valid_to", ">=", res["date_from"]),
            ], order="valid_from desc", limit=1)
            if ver:
                res["version_id"] = ver.id
        return res

    @api.depends("statement_kind", "date_to", "submission_type")
    def _compute_name(self):
        for st in self:
            suffix = _("(corrective)") if st.submission_type == "opravna" else ""
            st.name = "%s — %s%s" % (
                _(self._KIND_LABELS.get(st.statement_kind, "FS")),
                st.date_to or "",
                (" " + suffix) if suffix else "",
            )

    def _prior_dates(self):
        self.ensure_one()
        pf = self.date_from - relativedelta(years=1) if self.date_from else False
        pt = self.date_to - relativedelta(years=1) if self.date_to else False
        return pf, pt

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only draft statements can be recomputed."))
        overrides = {
            line.code: line.manual_value
            for line in self.line_ids
            if line.is_overridden
        }
        self.line_ids.unlink()

        current, columns = self._compute_period(
            self.date_from, self.date_to, overrides)
        prior_from, prior_to = self._prior_dates()
        prior, _prior_columns = self._compute_period(prior_from, prior_to)

        vals = []
        for ldef in self.version_id.line_def_ids.sorted("sequence"):
            vals.append(
                {
                    "statement_id": self.id,
                    "code": ldef.code,
                    "name": ldef.name,
                    "sequence": ldef.sequence,
                    "level": ldef.level,
                    "kind": ldef.kind,
                    "current_value": current.get(ldef.code, 0.0),
                    "prior_value": prior.get(ldef.code, 0.0),
                    "gross_value": columns.get(ldef.code, (0.0, 0.0))[0],
                    "correction_value": columns.get(ldef.code, (0.0, 0.0))[1],
                    "is_overridden": ldef.code in overrides,
                    "manual_value": overrides.get(ldef.code, 0.0),
                }
            )
        created = self.env["cssk.fs.statement.line"].create(vals)
        self._fs_build_tree_and_sources(created)
        self._cssk_record_unmapped()
        self.state = "preview"

    def action_view_unmapped(self):
        """Name them. A count tells nobody which account to go and look at."""
        self.ensure_one()
        raise UserError(_(
            "%(count)s account(s) carry a balance that no row of this "
            "statement claims, so their money is in the ledger and not on the "
            "form:\n\n%(codes)s\n\nEither the chart uses codes this form's "
            "mapping does not name, or a row is missing them.",
            count=self.unmapped_count, codes=self.unmapped_note or ""))

    def _cssk_record_unmapped(self):
        """Report the accounts that reached no row of this statement."""
        self.ensure_one()
        balances = self._cssk_account_balance_map(None, self.date_to)
        cells = [
            (formula, [])
            for ldef in self.version_id.line_def_ids
            for formula in (ldef.account_formula,
                            ldef.account_formula_correction)
        ]
        unmapped = self._cssk_unmapped_codes(
            balances, cells, claimed=self._cssk_claimed_codes(),
            tag_codes=self._cssk_tag_codes())
        # Rounding dust is not a mapping error and naming it buries the ones
        # that are.
        unmapped = [(code, bal) for code, bal in unmapped if abs(bal) >= 1.0]
        self.unmapped_count = len(unmapped)
        self.unmapped_note = "\n".join(
            "%s  %.2f" % (code, bal) for code, bal in unmapped[:50]) or False
        if unmapped:
            _logger.warning(
                "%s: %d account(s) carry a balance that no row claims: %s",
                self.display_name, len(unmapped),
                ", ".join("%s %.0f" % (c, b) for c, b in unmapped[:10]))

    def _fs_build_tree_and_sources(self, lines):
        """Link the foldable hierarchy (parent_id, from each aggregate's formula)
        and, for leaf lines, the exact journal items behind the value."""
        by_code = {ln.code: ln for ln in lines}
        for ldef in self.version_id.line_def_ids:
            line = by_code.get(ldef.code)
            if not line:
                continue
            if ldef.kind == "aggregate" and ldef.aggregate_formula:
                for child_code in re.findall(
                        r"[A-Za-z_][A-Za-z0-9_]*", ldef.aggregate_formula):
                    child = by_code.get(child_code)
                    if child and child != line and not child.parent_id:
                        child.parent_id = line.id
            elif line.is_leaf and ldef.account_formula:
                line.source_domain = repr(self._fs_source_domain(ldef))

    def _fs_source_domain(self, ldef):
        """A small, serialisable account.move.line domain for the leaf's source
        journal items (re-queried on drill-down instead of storing the ids — a
        balance-sheet leaf can span a year of postings)."""
        codes = sorted(set(re.findall(r"[0-9]+", ldef.account_formula or "")))
        if not codes:
            return []
        acc_dom = ["|"] * (len(codes) - 1) + [
            ("account_id.code", "=like", c + "%") for c in codes]
        if ldef.kind == "accounts_open":
            date_dom = [("date", "<", str(self.date_from))]
        elif ldef.kind == "accounts_close":
            date_dom = [("date", "<=", str(self.date_to))]
        else:  # P&L movement
            date_dom = [("date", ">=", str(self.date_from)),
                        ("date", "<=", str(self.date_to))]
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id)] + date_dom + acc_dom

    def _cssk_eval_order(self):
        """Line definitions in DEPENDENCY order, not sequence order.

        A statutory form numbers its totals ABOVE the rows they add up:
        UZPODv14 opens with ``r001 = r. 02 + r. 33 + r. 74`` and only then
        lists r002 onwards. Evaluating by ``sequence`` therefore asks for
        ``s002`` before anything has computed it, and ``safe_eval`` raises
        ``NameError`` on the first row of the form.

        Non-aggregate rows keep their sequence order and come first; aggregates
        follow, each after the rows its formula names. A cycle cannot be
        ordered and is emitted last in sequence order, so a bad formula fails
        as a NameError naming the code rather than looping here.
        """
        self.ensure_one()
        defs = self.version_id.line_def_ids.sorted("sequence")
        aggs = [d for d in defs if d.kind == "aggregate"]
        plain = [d for d in defs if d.kind != "aggregate"]
        by_code = {d.code: d for d in aggs}
        ordered, seen, guard = list(plain), {d.code for d in plain}, set()

        def visit(d):
            if d.code in seen or d.code in guard:
                return
            guard.add(d.code)
            for ref in re.findall(r"[A-Za-z_]\w*", d.aggregate_formula or ""):
                dep = by_code.get(ref)
                if dep is not None:
                    visit(dep)
            guard.discard(d.code)
            if d.code not in seen:
                seen.add(d.code)
                ordered.append(d)

        for d in aggs:
            visit(d)
        for d in aggs:                      # anything a cycle left behind
            if d.code not in seen:
                ordered.append(d)
        return ordered

    def _compute_period(self, date_from, date_to, overrides=None):
        """Return ``{code: value}`` for the given period (overrides applied so
        dependent aggregates see them)."""
        self.ensure_one()
        overrides = overrides or {}
        computed = {}
        #: {code: (gross, correction)} for rows the form files in three
        #: columns; absent for every other row, which reports one figure.
        columns = {}
        # P&L and cash flow read the period **movement**; the balance sheet
        # reads the cumulative as-of balance (movement = pass a lower date
        # bound). Decided PER LINE rather than per statement, because one
        # document can carry both: UZPODv14 holds ucPod1Suvaha (as-of) beside
        # ucPod2VykazZS (movement) in a single telo. A line left on the default
        # follows the version's statement_kind exactly as before.
        opening = (date_from - relativedelta(days=1)) if date_from else date_to
        # ONE grouped query per distinct date window per period (instead of
        # one search per code prefix per line): the prefix matching happens
        # in Python in _eval_accounts. At most three windows exist (period
        # movement, opening cumulative, closing cumulative).
        window_maps = {}

        def balances(win_from, win_to):
            key = (win_from, win_to)
            if key not in window_maps:
                window_maps[key] = self._cssk_account_balance_map(
                    win_from, win_to)
            return window_maps[key]

        for ldef in self._cssk_eval_order():
            if ldef.code in overrides:
                value = overrides[ldef.code]
            elif ldef.kind == "accounts":
                window = balances(
                    date_from if ldef._cssk_reads_movement() else None, date_to)
                value = self._eval_accounts(ldef.account_formula, window)
                if ldef.account_formula_correction:
                    # Brutto / korekcia / netto. The korekcia accounts carry
                    # credit balances (oprávky, opravné položky), so their sum
                    # is negative; the form prints the column POSITIVE and
                    # nets it off the gross, which is what the tlačivo's
                    # "(013) - /073, 091A/" says in words.
                    correction = -self._eval_accounts(
                        ldef.account_formula_correction, window)
                    columns[ldef.code] = (value, correction)
                    value = value - correction
            elif ldef.kind == "accounts_open":
                # cumulative balance the day before the period (stav PP na začiatku)
                value = self._eval_accounts(
                    ldef.account_formula, balances(None, opening))
            elif ldef.kind == "accounts_close":
                # cumulative balance at period end (stav PP na konci)
                value = self._eval_accounts(
                    ldef.account_formula, balances(None, date_to))
            elif ldef.kind == "aggregate":
                value = self._eval_aggregate(ldef.aggregate_formula, computed)
            else:
                value = 0.0
            computed[ldef.code] = value
        return computed, columns

    def _eval_accounts(self, formula, balances):
        """Signed sum of the pre-fetched account-code balances matching the
        formula's comma-separated code prefixes.

        ``balances`` is the window's ``{account_code: balance}`` map
        (``_cssk_account_balance_map`` — one grouped query per date window
        per period instead of one search per prefix per line). The token
        semantics are IDENTICAL to the historical per-prefix search: a
        leading '-' negates the prefix's contribution, and an account
        matched by two tokens contributes once PER TOKEN.

        Delegates to the shared matcher in ``l10n_cssk_core`` so the figures
        previewed here and the figures written into a country module's filed
        XML come out of ONE implementation.

        ``claimed`` is passed ONLY when this version actually uses a residual
        token (``02X`` = "any other account of group 02 that no row names").
        The synthetic-absorb rule stays off otherwise, because CZ row
        definitions use 6-digit tokens (343000 beside 343001/343112) where
        absorbing would change filed figures — so a form that never writes a
        residual is evaluated exactly as before."""
        self.ensure_one()
        if not (formula or "").strip() or not balances:
            return 0.0
        return self._cssk_eval_formula(
            formula, balances, default_sign=1.0,
            claimed=self._cssk_claimed_codes(),
            two_sided=self._cssk_two_sided_prefixes(),
            tag_codes=self._cssk_tag_codes())

    def _cssk_tag_codes(self):
        """Delegated to the version; see ``_cssk_two_sided_prefixes``."""
        self.ensure_one()
        return self.version_id._cssk_tag_codes()

    def _cssk_two_sided_prefixes(self):
        """Delegated to the version — a property of its definitions, and read
        by the reverse-drill footprint as well as by this computation. One
        answer, so the two directions cannot drift."""
        self.ensure_one()
        return self.version_id._cssk_two_sided_prefixes()

    def _cssk_claimed_codes(self):
        """Delegated to the version; see ``_cssk_two_sided_prefixes``."""
        self.ensure_one()
        return self.version_id._cssk_claimed_codes()

    def _eval_aggregate(self, formula, computed):
        if not formula:
            return 0.0
        return float(safe_eval(formula, dict(computed)) or 0.0)

    # ------------------------------------------------------------------
    # Export — the pipeline lives in cssk.statutory.submission.mixin;
    # only the form-specific hooks are parameterized here. The FS thereby
    # also gains the ``_cssk_check_kontroly`` stage (a no-op until a country
    # module supplies FS kontrolné pravidlá; the SK UZPOD export has its own
    # dedicated pipeline in ``l10n.sk.uzpod``).
    # ------------------------------------------------------------------
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("financial statement")
    _cssk_xml_name_fallback = "financial_statement"

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx.update({
            "lines": self.line_ids,
            "current": {l.code: l.current_value for l in self.line_ids},
            "prior": {l.code: l.prior_value for l in self.line_ids},
        })
        return ctx

    # ------------------------------------------------------------------
    # Amendment
    # ------------------------------------------------------------------
    def action_create_amendment(self):
        """Opravná účetní/účtovná závierka. The shared mixin copies the original
        into a fresh draft (carrying the manual overrides via line_ids copy=True
        and linking original_return_id); here we additionally flag the copy as
        Opravná. There are no difference rows — the accountant corrects the
        accounting and recomputes the full statement."""
        action = super().action_create_amendment()
        amendment = (
            self.browse(action.get("res_id"))
            if isinstance(action, dict) else self.browse()
        )
        if amendment and amendment.exists():
            amendment.submission_type = "opravna"
        return action


class CSSKFsStatementLine(models.Model):
    _name = "cssk.fs.statement.line"
    _description = "Financial Statement Line"
    _order = "statement_id, sequence, code"

    statement_id = fields.Many2one(
        "cssk.fs.statement", required=True, ondelete="cascade", index=True
    )
    company_currency_id = fields.Many2one(related="statement_id.currency_id")
    code = fields.Char(required=True)
    name = fields.Char()
    sequence = fields.Integer(default=10)
    level = fields.Integer(default=0)
    kind = fields.Selection(
        [("accounts", "Account codes"),
         ("accounts_open", "Account balances — period start"),
         ("accounts_close", "Account balances — period end"),
         ("aggregate", "Aggregate"),
         ("manual", "Manual")]
    )
    current_value = fields.Monetary(
        currency_field="company_currency_id",
        help="The row's reported figure. On a form filed in three columns "
             "this is the NETTO — gross minus correction.")
    prior_value = fields.Monetary(currency_field="company_currency_id")
    gross_value = fields.Monetary(
        currency_field="company_currency_id", string="Brutto",
        help="Gross column, where the form has one. The Slovak Súvaha is "
             "filed as brutto / korekcia / netto and its schema requires all "
             "three per row (tRiadok14 s1/s2/s3), so a net figure alone "
             "cannot be filed.")
    correction_value = fields.Monetary(
        currency_field="company_currency_id", string="Korekcia",
        help="Correction column — accumulated depreciation and impairment. "
             "Reported as a positive number, as the form does.")
    is_overridden = fields.Boolean(
        string="Override",
        help="Tick to enter a manual value for the current period (preserved "
        "across recompute and fed into dependent lines).",
    )
    manual_value = fields.Monetary(currency_field="company_currency_id")

    # --- hierarchy + drill-down (foldable statement tree -> journal items) ---
    parent_id = fields.Many2one(
        "cssk.fs.statement.line", ondelete="set null", index=True)
    child_ids = fields.One2many(
        "cssk.fs.statement.line", "parent_id")
    is_leaf = fields.Boolean(compute="_compute_is_leaf", store=True)
    tree_label = fields.Char(compute="_compute_tree_label")
    # Drill-down: a small serialised account.move.line domain (re-queried on
    # click) — a leaf can span a year of postings, so we store the criteria, not
    # the ids. Empty/false for aggregate & derived rows (no single line set).
    source_domain = fields.Char()
    has_source = fields.Boolean(compute="_compute_has_source")
    source_reconciles = fields.Boolean(
        compute="_compute_source_reconciles",
        help="The source lines' sum equals the line value in magnitude.")

    @api.depends("source_domain")
    def _compute_has_source(self):
        for line in self:
            line.has_source = bool(line.source_domain
                                   and line.source_domain not in ("[]", "False"))

    @api.depends("kind")
    def _compute_is_leaf(self):
        for line in self:
            line.is_leaf = line.kind in (
                "accounts", "accounts_open", "accounts_close")

    @api.depends("name", "code", "level")
    def _compute_tree_label(self):
        for line in self:
            line.tree_label = ("    " * max(line.level or 0, 0)) \
                + (line.name or line.code or "")

    @api.depends("source_domain", "current_value")
    def _compute_source_reconciles(self):
        # Batched: ONE grouped query per statement per date window (instead
        # of one _read_group per line on every form load). Leaf domains share
        # the company/date base and differ only in their account-code
        # prefixes, so the prefix matching happens in Python on a
        # {account_code: balance} map.
        for stmt, lines in self.grouped("statement_id").items():
            maps = {}
            for line in lines:
                if not line.has_source:
                    line.source_reconciles = False
                    continue
                domain = safe_eval(line.source_domain)
                prefixes = [
                    term[2][:-1] for term in domain
                    if isinstance(term, (list, tuple))
                    and term[0] == "account_id.code" and term[1] == "=like"]
                base = [
                    list(term) for term in domain
                    if isinstance(term, (list, tuple))
                    and term[0] != "account_id.code"]
                key = repr(base)
                if key not in maps:
                    maps[key] = stmt._cssk_balances_by_account_code(
                        base, company=stmt.company_id)
                s = sum(
                    balance for code, balance in maps[key].items()
                    if any(code.startswith(p) for p in prefixes))
                line.source_reconciles = (
                    abs(abs(s) - abs(line.current_value)) < 0.5)

    def action_view_source_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "l10n_cssk_fs_base.view_move_line_fs_audit", raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": _("Source documents — %s %s") % (self.code or "", self.name or ""),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": [(view.id if view else False, "list"), (False, "form")],
            "domain": safe_eval(self.source_domain or "[]"),
            "context": {"create": False, "delete": False,
                        "group_by": ["move_id"]},
        }

    @api.onchange("is_overridden", "manual_value")
    def _onchange_override(self):
        for line in self:
            if line.is_overridden:
                line.current_value = line.manual_value
