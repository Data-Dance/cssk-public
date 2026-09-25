import logging

from odoo import _, api, fields, models
from odoo.tools import float_compare
from odoo.addons.l10n_cssk_core.tools import normalize_vat


_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_statutory_footprint(self):
        res = super()._cssk_statutory_footprint()
        if self.cssk_control_section_code:
            res.append({
                "form": _("VAT control statement"),
                "code": self.cssk_control_section_code,
                "name": _("VAT control statement (KV / KH)"),
                "res_model": "cssk.control.statement"})
        return res

    cssk_control_section_code = fields.Char(
        compute="_compute_cssk_control_section_code",
        store=True,
        index=True,
        help="Control-statement section (KV DPH / KH DPH) assigned to this "
        "line. Computed by a country-specific resolver.",
    )
    cssk_control_partner_vat_override = fields.Char(
        help="If set, used instead of the partner VAT for control-statement "
        "classification (supports multi-VAT foreign branches; SK 'entry_vat').",
    )
    cssk_control_rate_declared = fields.Float(
        string="VAT rate declared",
        digits=(16, 4),
        help="The VAT rate the source document states, for a line that carries "
        "the return tags without carrying the tax.\n\n"
        "Some statutory lines never named a rate — the CZ/SK reverse-charge "
        "band was one line for every rate until the vzor of 1. 7. 2025 — so "
        "their tag cannot say which rate applied and no amount of data will "
        "make it. Where the producer of the document knows, it says so here.\n\n"
        "It SELECTS among the taxes the tag already reaches; it never computes. "
        "A rate matching none of them is a mapping error and is refused, not "
        "applied. Ignored where the line carries a real tax.",
    )

    # NB: deliberately NOT depending on company_id.account_fiscal_country_id —
    # that would recompute this stored field on every move line whenever a
    # company address changes (Odoo guards this in
    # test_no_recompute_when_company_address_changes). The resolver still reads
    # the fiscal country at compute time; a country change is rare and handled
    # by ``_cssk_recompute_section_codes`` below.
    #
    # ⚠️ THE SAME APPLIES TO A CODE CHANGE, and that is the case people meet.
    # The dependencies below are all DATA — none of them changes when the
    # resolver's Python does. So after fixing a resolver, every stored value is
    # stale and a comparison re-run returns byte-identical numbers: the code is
    # right and the measurement is of the old code. It cost the i6 extractor a
    # near-miss — a correct fix measured as having done nothing, caught only by
    # calling the resolver directly on a document the statement still
    # contained. **Fix a resolver, then run the recompute.**
    @api.depends(
        "move_id.move_type",
        "parent_state",
        "tax_ids",
        "tax_ids.cssk_control_section_default",
        "tax_ids.cssk_control_is_reverse_charge",
        "tax_ids.tax_exigibility",
        "tax_ids.children_tax_ids.tax_exigibility",
        "move_id.always_tax_exigible",
        "move_id.tax_cash_basis_origin_move_id",
        "tax_tag_ids",
        "partner_id",
        "journal_id.cssk_control_section_override",
    )
    def _compute_cssk_control_section_code(self):
        for line in self:
            line.cssk_control_section_code = (
                line._cssk_resolve_section_code() or False
            )

    def _cssk_resolve_section_code(self):
        """Resolve the control-statement section for this line.

        Base behaviour: honour an explicit journal override, otherwise return
        ``False``. Country modules override and call ``super()`` to chain.
        The reverse-charge flag must be checked **first** in country
        implementations (see the design note).
        """
        self.ensure_one()
        if self.journal_id.cssk_control_section_override:
            return self.journal_id.cssk_control_section_override
        return False

    # -- snapshot helpers used by concrete section _populate_for_statement --

    def _cssk_partner_vat_for_statement(self):
        self.ensure_one()
        return self.cssk_control_partner_vat_override or (
            self.partner_id.vat
            or self.move_id._cssk_vat_document().partner_id.vat or ""
        )

    def _cssk_partner_vat_stripped(self):
        self.ensure_one()
        # One shared normaliser (l10n_cssk_core.tools.normalize_vat):
        # uppercase, drop ALL whitespace (inner included) and strip the
        # leading 2-letter country prefix — same prefix semantics as before;
        # the whitespace/uppercase cleanup is the normalisation fix.
        return normalize_vat(self._cssk_partner_vat_for_statement())

    def _cssk_direction_sign(self):
        """+1 for inbound (purchases), -1 for outbound (sales).

        Move-line ``balance`` is credit-negative, so outbound supplies (income,
        credit) and inbound (expense, debit) both become **positive** for a
        normal document and **negative** for its refund/correction — which is
        exactly the sign convention the control statement and VAT return use.

        ⚠️ The direction comes from ``move_type`` on purpose. Deriving it from
        the line's own taxes instead looks like an improvement — it would give
        a journal entry carrying VAT a direction, which ``move_type`` cannot —
        and it does not work. Tried twice while reconciling an imported month
        against the filed returns: both times section A5 came out right and A4
        went from exact to +78 730.40. An entry-shaped invoice and an
        entry-shaped credit note have identically signed revenue lines, so no
        function of the line separates them.

        ⚠️ The JOURNAL is not a safe substitute either, though it looks like
        one — it is a property of the document rather than of the line, which
        is exactly the objection above. Tried 2026-08-15: taking the direction
        from ``journal_id.type`` for a move whose ``move_type`` is ``entry``
        moved section A4 from 26 periods agreeing to 9, and A5 from 42 to 2,
        measured across 59 filed control statements. It flips a majority that
        was already right in order to correct a minority that was not.

        The fix belongs upstream, in whatever produced a directionless move:
        give the document its direction back rather than guessing it here.
        Three attempts have now failed the same way, and the fourth is not an
        attempt at all — ``cssk_vat_direction`` lets the document declare it.
        """
        self.ensure_one()
        # A declared direction wins, and is the answer to everything above: the
        # document that knows its own side says so instead of leaving the
        # statement to work it out from evidence that cannot carry it.
        #
        # A cash-basis entry answers for its invoice: the entry itself is an
        # ``entry`` and would read as purchase-side whatever it settled.
        document = self.move_id._cssk_vat_document()
        declared = document.cssk_vat_direction
        if declared:
            return -1.0 if declared == "sale" else 1.0
        out = document.move_type in (
            "out_invoice",
            "out_refund",
            "out_receipt",
        )
        return -1.0 if out else 1.0

    def _cssk_taxes(self):
        """The taxes applying to this line — from ``tax_ids``, or from its tags.

        A line can legitimately carry the VAT-return tags without carrying the
        tax itself, and an importer does it deliberately: Odoo has no way to
        say "report this supply but do not post the tax", because a tax on a
        line always posts. Where a source reported VAT that its own ledger does
        not contain — an advance settlement reports the whole supply to the tax
        office while booking only the remainder — the tags are the only honest
        representation, and the control statement must still see the line.

        Only BASE repartition tags are followed. A tax line carries tags too,
        and treating one as a base line would report the supply twice.
        """
        self.ensure_one()
        if self.tax_ids:
            # Exigibility is a property of each LEAF tax, and Odoo decides it
            # per child of a group (it tags each child separately), so a group
            # may be partly due. Keep a group whole when all of it is due,
            # drop it when none is, and keep only its due children otherwise.
            due_taxes = self.env["account.tax"]
            for tax in self.tax_ids:
                flat = tax.flatten_taxes_hierarchy()
                due = flat.filtered(lambda t: not self._cssk_tax_is_deferred(t))
                due_taxes |= tax if due == flat else due
            return due_taxes
        if not self.tax_tag_ids or self.tax_repartition_line_id:
            return self.tax_ids
        # ⚠️ Company-scoped. Without it this picks up the identically-named
        # taxes of every other company in the database — which is why a line
        # resolved to twelve taxes with six distinct names.
        reps = self.env["account.tax.repartition.line"].with_context(
            active_test=False
        ).search([
            ("tag_ids", "in", self.tax_tag_ids.ids),
            ("repartition_type", "=", "base"),
            ("company_id", "=", self.company_id.id),
        ])
        return reps.tax_id

    def _cssk_tax_is_deferred(self, tax):
        """Whether ``tax`` is not yet due on this line (cash basis, unpaid).

        A tax "Based on Payment" is not due when the invoice is posted: Odoo
        parks it on the tax's transition account and reports it only from the
        cash-basis entry it posts on payment. Its own tax report does that
        through ``_get_tax_exigible_domain``, and this is the same rule, so
        the control statement and Odoo agree on what is due:

        * a move with no receivable or payable line is always exigible
          (``always_tax_exigible``) — there is no payment to wait for;
        * a cash-basis entry is exigible by definition — it IS the payment;
        * otherwise a tax is deferred if it is "Based on Payment". Called on
          LEAF taxes; ``_cssk_taxes`` flattens groups first.

        The TAGS already obey this — Odoo writes no tags for a deferred tax on
        the invoice, which is why the tag-driven VAT return never reported an
        unpaid one. The control statement classifies from ``tax_ids``, which
        Odoo writes regardless, and so reported the invoice when it was
        posted AND its cash-basis entry when it was paid.
        """
        move = self.move_id
        if move.always_tax_exigible or move.tax_cash_basis_origin_move_id:
            return False
        return tax.tax_exigibility == "on_payment"

    def _cssk_taxes_for_amounts(self):
        """The taxes to COMPUTE with, which is not the same set as above.

        Classification can use every candidate — 23 %, 23 % S, 23 % M and
        their 20 % historic clones all classify a domestic supply into A.1, so
        the ambiguity does not matter there. Computing is different: the caller
        hands the set to ``compute_all``, which applies them **cumulatively**.

        ⚠️ A TAG DOES NOT IDENTIFY A TAX, and passing every candidate is not a
        conservative over-estimate — it is a multiplication. Measured on a real
        filing: a base line of 1 995.00 carrying tag '03' resolved to twelve
        taxes summing to 258 %, and the KV row reported **5 147.10 of VAT
        against an actual 399.00** — schema-valid, plausible on its face, and
        12.9x the truth. A 23 % rate on an August 2024 supply is also
        impossible; that rate did not exist until 2025.

        Where the candidates AGREE on a rate, the choice between them does not
        matter: 20 %, 20 % S and 20 % M compute the same tax on the same base,
        so one representative is taken.

        Where they DISAGREE, two things can still settle it, in this order,
        and neither of them guesses:

        1. **The document says so.** ``cssk_control_rate_declared`` carries the
           rate the source recorded, and it SELECTS among the candidates the
           tag already reaches. Declared beats derived — the same reasoning as
           ``cssk_vat_direction`` and ``cssk_vat_correction`` on the move — so
           it is applied to the full candidate set, before any inference of
           ours narrows it: a document whose accounting date sits on the wrong
           side of a rate change is not second-guessed. A declared rate
           matching no candidate is a mapping error in whatever declared it,
           and is refused rather than computed: the field must never become a
           channel for a number with nothing behind it.

           It does NOT override the calendar, though. A rate the tag can reach
           but that was not in force when the document was taxed is not a tie
           broken, it is two pieces of evidence contradicting each other — a
           2020 Czech document declaring 12 %, a band that did not exist until
           2024 — and which of the two is wrong is exactly what we do not know.
           So the declaration is intersected with the rates in force, and a
           contradiction refuses. Where no window is known the intersection is
           a no-op, so nothing is lost by not knowing.
        2. **The date rules the rest out.** A rate has a period in which it was
           in force, and candidates from another era are not candidates at all.
           This is not a nicety: adding the 23 % rate in 2025 gave every
           standard-rate tag a second candidate and thereby stopped EVERY
           earlier period computing, retroactively. See
           :meth:`_cssk_taxes_in_force`.

        **None of this touches a line that carries a tax.** The method returns
        on ``tax_ids`` before any of it, so neither the date filter nor the
        declaration can reach an explicitly-set tax — including one whose rate
        the document's own date says was not in force, which a history import
        produces in quantity when it maps a source code to a tax by name and
        rate. Those lines compute from what the document says, as they always
        have. Said plainly because the fallback in
        :meth:`_cssk_taxes_in_force` reads like a safety net, and would be
        load-bearing for a whole imported decade if the filter were ever
        extended to ``tax_ids``. It should not be: an explicit tax is a
        statement, not a candidate.

        Where neither settles it the rate is simply not in the data. That
        happens for real and not only in imports: a tag whose rivals were all
        in force at once — SK 5/10/20 before 2025, CZ 15 and 10 both reduced —
        names a line that did not distinguish them. This then returns nothing,
        so the row keeps its BASE and reports no tax: visibly incomplete, and
        caught by the kontroly rather than filed. Guessing would produce a
        plausible wrong number, which is the worst outcome available here.
        """
        self.ensure_one()
        taxes = self._cssk_taxes()
        if self.tax_ids:
            return taxes  # the document says which; no inference involved
        if not taxes:
            return taxes
        declared = self.cssk_control_rate_declared
        if declared:
            # 0.0 is "not declared", not "zero-rated" — a zero-rated line has
            # no tax to report either way, so nothing is lost by the collision.
            match = taxes.filtered(
                lambda t: t.amount_type == "percent"
                and not float_compare(t.amount, declared, precision_digits=4)
            )
            # Several taxes can share a rate — "23 %", "23 % S", "23 % M" —
            # and which one is taken does not matter: they compute the same
            # tax on the same base, and the line's tags already decide which
            # row it reports on. Same reasoning as the agreement case below.
            return (match & self._cssk_taxes_in_force(taxes))[:1]
        taxes = self._cssk_taxes_in_force(taxes)
        # Rounded to the precision the declaration is matched at, so a rate
        # stored as 20.000000001 by hand does not read as a second rate.
        if len({round(rate, 4) for rate in taxes.mapped("amount")}) > 1:
            return self.env["account.tax"]
        return taxes[:1]

    def _cssk_taxes_in_force(self, taxes):
        """Drop the candidates whose rate was not in force when this was taxed.

        The rate date is the tax point, not the period (see
        ``account.move._cssk_rate_date``) — a December supply claimed in
        January is rated in December.

        Guarded on the field rather than declared as a dependency: the windows
        live on the historical-rate family in ``l10n_cssk_vat_return_base``,
        and the control statement must install without it. Uninstalled, this is
        a no-op and the agreement test decides exactly as it did before.

        An empty result means the chart has no rate for that date at all —
        SK ships no 19 % standard clone for 2004-2010, by an explicit decision
        in ``SK_HISTORIC_VAT_RATES`` — so the unfiltered set is kept. The
        filter may only ever remove ambiguity; it must not create a refusal
        that did not exist before it.

        ⚠️ Only ever called with candidates DERIVED FROM TAGS. A line carrying
        ``tax_ids`` never gets here, and must not: see the note in
        :meth:`_cssk_taxes_for_amounts`.
        """
        self.ensure_one()
        if "cssk_historic_valid_from" not in self.env["account.tax"]._fields:
            return taxes
        in_force = taxes._cssk_in_force_on(self.move_id._cssk_rate_date())
        return in_force or taxes

    def _cssk_recompute_section_codes(self):
        """Recompute the stored section code, and say how many changed.

        ``cssk_control_section_code`` is stored and depends on **data**. A
        change to the resolver's Python is therefore invisible to Odoo's
        invalidation: the values on disk stay as the previous version left
        them, and every statement built from them stays wrong while the code is
        right. There is no dependency that could express "the algorithm
        changed", so this has to be explicit.

        Returns the number of lines whose section actually moved, because that
        is the number worth reporting — "recomputed 40 000 lines" says nothing,
        "97 lines left C.1" says whether the fix did what was expected.

        Call it after any change to a ``_cssk_resolve_section_code``
        implementation, and after a company's fiscal country changes.
        """
        before = {line.id: line.cssk_control_section_code for line in self}
        # ``modified()`` is not enough: it tells Odoo the field's DEPENDENCIES
        # changed, and none of them did — the value is then re-read from the
        # database, which is the stale value we are trying to replace.
        # ``add_to_compute`` marks the field itself as needing computation,
        # which is the only thing that reruns the resolver.
        self.env.add_to_compute(
            self._fields["cssk_control_section_code"], self)
        self.flush_recordset(["cssk_control_section_code"])
        self.invalidate_recordset(["cssk_control_section_code"])
        changed = sum(
            1 for line in self
            if line.cssk_control_section_code != before.get(line.id)
        )
        if changed:
            _logger.info(
                "cssk: %s of %s line(s) changed control section on recompute",
                changed, len(self),
            )
        return changed

    @api.model
    def _cssk_recompute_company_section_codes(self, company):
        """Recompute every posted line of ``company`` that could carry a section.

        The convenience form, since the answer to "which lines?" after a
        resolver change is always "all of them".
        """
        lines = self.search([
            ("company_id", "=", company.id),
            ("parent_state", "=", "posted"),
        ])
        return lines._cssk_recompute_section_codes()

    @api.model
    def _cssk_recompute_cash_basis_section_codes(self, country_code):
        """Recompute the section of every line that cash basis touches.

        Until 19.0.2.1.5 the section was assigned from ``tax_ids`` without
        asking whether the tax was due yet, so an unpaid invoice carrying a
        tax "Based on Payment" held a section it must not have, and the
        cash-basis entries of its payments held one resolved as if they had no
        partner. Neither changes on its own — the stored value depends on data,
        not on the resolver's code — so an upgrade has to recompute them.

        Narrowed to exactly those two populations, because a full recompute is
        an hour on a large agenda and every other line is unaffected.

        Called from the COUNTRY module's migration, not from this module's:
        a migration here runs before the country resolver is loaded, and would
        recompute every line with the base resolver, which returns nothing.
        """
        companies = self.env["res.company"].sudo().with_context(
            active_test=False).search(
            [("account_fiscal_country_id.code", "=", country_code)])
        changed = 0
        for company in companies:
            aml = self.sudo().with_company(company).with_context(
                allowed_company_ids=[company.id])
            lines = aml.search([
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                "|", "|",
                ("move_id.tax_cash_basis_origin_move_id", "!=", False),
                ("tax_ids.tax_exigibility", "=", "on_payment"),
                # a group carrying an on-payment child
                ("tax_ids.children_tax_ids.tax_exigibility", "=", "on_payment"),
            ])
            changed += lines._cssk_recompute_section_codes()
        return changed

    def _cssk_base_and_tax_amounts(self):
        """Return ``(base, tax)`` in **company currency** for this base line,
        signed per :meth:`_cssk_direction_sign`.

        Uses Odoo's own ``tax.compute_all`` so multi-rate and price-included
        taxes are handled correctly rather than approximated.
        """
        self.ensure_one()
        sign = self._cssk_direction_sign()
        taxes = self._cssk_taxes_for_amounts()
        if not taxes:
            # The line still belongs in the statement — it was classified from
            # the full candidate set — so its BASE is reported and its tax is
            # not. A row with a base and no tax is visibly incomplete and the
            # kontroly names it; a row with a base and a guessed tax is not.
            if self._cssk_taxes():
                return sign * self.balance, 0.0
            return 0.0, 0.0
        # ``balance`` on a posted base line is ALWAYS tax-exclusive — even for
        # price-included taxes (the tax part was split off at posting time).
        # ``handle_price_include=False`` (Odoo 19: special_mode
        # ``'total_excluded'``) makes compute_all treat the input as the net
        # base for every tax, instead of re-extracting an included tax from an
        # amount that no longer contains it.
        res = taxes.compute_all(
            self.balance,
            currency=self.company_id.currency_id,
            quantity=1.0,
            partner=self.partner_id,
            handle_price_include=False,
        )
        # Reverse charge / self-assessment: the bill posts BOTH the self-assessed
        # output (tag 19/09b) and its deduction (tag 10b) on the same line, so
        # compute_all nets those taxes to ~0. The control statement wants the
        # GROSS self-assessed tax (the output leg) — recover it from base × rate,
        # but ONLY for the RC-flagged taxes: a normal tax sharing the line keeps
        # its computed amount.
        # The flag alone is not the right question here — see
        # ``account.tax._cssk_self_assesses``. It marks the DOMESTIC reverse
        # charge for the section resolver, and the country modules keep
        # intra-EU acquisitions out of it on purpose; but an EU acquisition
        # nets its legs the same way and needs the same recovery. Union rather
        # than replacement, so a flagged GROUP tax still contributes its
        # children (a group carries no repartition of its own and so can never
        # be detected structurally).
        rc_flat = taxes.filtered(
            "cssk_control_is_reverse_charge"
        ).flatten_taxes_hierarchy() | taxes.flatten_taxes_hierarchy().filtered(
            lambda t: t.with_context(
                cssk_refund=self.move_id.move_type
            )._cssk_self_assesses()
        )
        # Only the taxes actually RECOVERED below are removed from the computed
        # sum. Excluding every rc_flat member and re-adding only the percent
        # ones silently DROPPED a fixed-amount tax that carried the flag: it
        # left the first sum and never reached the second. Reachable through
        # the flag alone, and it under-reports rather than over-reports, which
        # is the direction that goes unnoticed.
        recovered = rc_flat.filtered(lambda t: t.amount_type == "percent")
        tax = sum(
            t["amount"] for t in res["taxes"] if t["id"] not in recovered.ids
        )
        tax += sum(self.balance * t.amount / 100.0 for t in recovered)
        # A rate-bearing tax that POSTED NOTHING reports nothing.
        #
        # On an invoice Odoo raises itself the two can never differ, so this
        # only bites on an imported ledger, where the source may have booked a
        # document at a rate but with no tax at all. Keeping compute_all's
        # answer there reports VAT the company never booked — and it does more
        # than misstate a figure: base+tax decides the over/under-threshold
        # split, so 2 100 of tax that does not exist moved a 10 000 document
        # out of the aggregate section and into the detail one.
        #
        # The decisive argument is agreement between the two statements. The
        # VAT return reads TAGS, and the tag sits on the zero tax line, so the
        # return already reports nothing for these. A control statement that
        # reports 2 100 against a return that reports 0 is wrong whichever
        # figure is right.
        #
        # Deliberately narrow: only where the posted tax is EXACTLY zero, and
        # never for a self-assessed tax (whose legs net to zero by design and
        # whose recovery is the whole point of the block above). Anything
        # partially posted is left alone rather than guessed at, because
        # attributing a document's tax lines back to one base line is not
        # something this method can do correctly.
        charged = (taxes.flatten_taxes_hierarchy() - rc_flat).filtered(
            lambda t: t.amount_type == "percent" and t.amount
        )
        if charged:
            # The document must actually HAVE a tax line for these taxes that
            # posts nothing. "No tax line at all" is a different case and must
            # keep its computed tax: a tags-only line — a journal entry
            # carrying tax_tag_ids and no tax_ids, which is how an imported
            # ledger records VAT it booked itself — has no tax line by
            # construction, and zeroing it would silently empty every such row.
            # Caught by the SK suite, which had a test for exactly that shape.
            tax_lines = self.move_id.line_ids.filtered(
                lambda x: x.tax_line_id in charged
            )
            # EVERY one of them must post nothing, not merely their sum. A
            # document can carry a charge and its reversal for the same tax —
            # then the sum is zero while real VAT was booked, and testing the
            # sum would drop a figure that exists. Per-line attribution back to
            # one base line is not possible on this data path, so the test is
            # deliberately the conservative one: unanimity, or leave it alone.
            currency = self.company_id.currency_id
            if tax_lines and all(
                currency.is_zero(bal) for bal in tax_lines.mapped("balance")
            ):
                tax -= sum(
                    part["amount"] for part in res["taxes"]
                    if part["id"] in charged.ids
                )
        # THE TAX A DOCUMENT CHARGED IS A FACT; A TAX WE DERIVE IS NOT.
        #
        # Everything above computes the tax from this line's base. That is the
        # right machinery for ALLOCATING a base to its rates and for the
        # self-assessment recovery, and it is the wrong source for the figure
        # itself: § 78a reports the tax as invoiced. The two differ, and not
        # only by a rounding direction — measured against a real agenda, ten
        # pokladničné doklady summed to a filed 152.98 where the tax derived
        # from their summed base is 152.96, and one of them charged 1.27 on a
        # base of 6.32 where base × 20 % is 1.264. No rounding of a derived
        # figure reaches 1.27; only reading the document does.
        #
        # So where the document POSTED a tax for these taxes, that posted
        # figure is what gets reported, apportioned across the base lines that
        # share it so the lines still sum to what the document charged.
        # `charged` is REUSED rather than recomputed, and that is what makes
        # the zero-posted rule above and the read below mutually exclusive by
        # construction instead of by coincidence: the rule fires only when
        # every tax line of this same set posts zero, and the read refuses a
        # zero total. Two independently-written but equal sets would drift,
        # and the drift would double-subtract — the derived amount removed by
        # the rule and again by the swap — which under-reports silently.
        posted = self._cssk_posted_tax_amount(charged)
        if posted is not None:
            # SWAP only what was read, rather than replacing the whole figure.
            # A line can carry a fixed-amount tax beside a percent one, and a
            # fixed amount is never read here — replacing `tax` outright
            # dropped it silently, which under-reports and so goes unnoticed.
            derived = sum(part["amount"] for part in res["taxes"]
                          if part["id"] in charged.ids)
            tax = tax - derived + posted
        return sign * self.balance, sign * tax

    def _cssk_posted_tax_amount(self, taxes):
        """This line's share of the tax the DOCUMENT actually posted, or None.

        ``None`` means "cannot be read here, keep the derived figure", and it
        is returned generously — a wrong reading is worse than a derived one:

        * no tax line for these taxes at all. A tags-only line (an imported
          ledger recording VAT it booked itself) has none by construction, and
          so does a document whose tax was never posted separately.
        * a tax line that posts nothing. That case is already handled above,
          deliberately and narrowly, and must not be second-guessed here.

        Where the same tax is spread over several base lines the posted amount
        is apportioned by BASE SHARE, which is the allocation the document
        itself used. The shares sum back to the posted total exactly, so a
        row aggregating them reports what the document charged rather than a
        re-derivation of it.

        ``taxes`` must already be FLATTENED and narrowed to the percent taxes
        that are to be read — the caller does that, because it needs the same
        set to subtract the derived figure it is replacing.
        """
        self.ensure_one()
        flat = taxes
        if not flat:
            return None
        tax_lines = self.move_id.line_ids.filtered(
            lambda x: x.tax_line_id in flat)
        if not tax_lines:
            return None
        currency = self.company_id.currency_id
        posted = sum(tax_lines.mapped("balance"))
        if currency.is_zero(posted):
            # Left to the zero-posted rule above, which knows the difference
            # between "posted nothing" and "a charge and its reversal".
            return None
        # FLATTEN THE SIBLING'S OWN TAXES BEFORE TESTING MEMBERSHIP. `flat` is
        # flattened and a base line may carry the GROUP, so a raw intersection
        # misses a genuine sibling — which shrinks the denominator and hands
        # this line more than its share of the document's tax.
        siblings = self.move_id.line_ids.filtered(
            lambda x: not x.tax_line_id
            and (x.tax_ids.flatten_taxes_hierarchy() & flat))
        balances = siblings.mapped("balance")
        total_base = sum(balances)
        if currency.is_zero(total_base):
            return None
        # APPORTION ONLY WHERE IT IS STABLE. Splitting by base share assumes
        # the tax follows the base proportionally. It does not when a document
        # mixes signs for one tax — goods and a return line, or an invoice
        # with a discount — because the net can be a rounding artefact of two
        # large opposite numbers, and the share of a line then swings wildly.
        # The shares would still sum to the posted total, so a row over the
        # whole document stays right; a document whose lines land in DIFFERENT
        # sections would not. Refuse and keep the derived figure, which is
        # stable if less faithful.
        nonzero = [b for b in balances if not currency.is_zero(b)]
        if len(nonzero) > 1 and not (
                all(b > 0 for b in nonzero) or all(b < 0 for b in nonzero)):
            return None
        return posted * (self.balance / total_base)

    def _cssk_tax_rate(self):
        """Percentage of the applied VAT tax (the grouping key for KV/KH rows).
        Returns the first percent tax's rate; multi-rate lines are split by the
        populate routine, so a single rate per group is the norm.

        ⚠️ Taken from the SAME narrowed set the amount is computed from. Taking
        it from the full classification set instead produced a row that
        declared a rate the amount logic had explicitly refused to trust: an
        exported A.1 row read ``D='0.00' S='23' Z='1995.00'`` — a taxable
        supply of 1 995.00 at 23 % carrying no tax, XSD-valid and false on its
        face. 23 % was also impossible for that period; the rate did not exist
        until 2025.

        A row whose rate cannot be determined therefore reports **no rate**,
        matching its zero tax, and the kontroly refuses the export rather than
        filing a description of a supply we cannot describe.
        """
        self.ensure_one()
        rates = self._cssk_taxes_for_amounts().filtered(
            lambda t: t.amount_type == "percent")
        return rates[:1].amount if rates else 0.0
