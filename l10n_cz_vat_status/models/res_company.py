# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The company's VAT status on a date, and what it does to a set of taxes.

**What each status may carry**, from zákon č. 235/2004 Sb.:

* **plátce** — everything the chart offers. Nothing is mapped.
* **neplátce** — no output VAT (only a plátce owes it on its supplies,
  § 108 odst. 1; a non-payer who states VAT on a document owes it anyway,
  § 108 odst. 4 písm. g), which is what this module keeps from happening), and
  **no deduction** (§ 72 odst. 1 gives it to a plátce). A supplier's VAT is
  simply part of the price: it is posted to the cost account of the line.
* **identifikovaná osoba** — the same, except that it **owes** VAT, with no
  deduction, on
  - an intra-Community acquisition of goods, § 108 odst. 2 (§ 16, § 25),
  - a service, goods with installation, or goods through networks received
    from a person not established in CZ, § 108 odst. 3 písm. a),
  and its § 9 odst. 1 services to another member state are reported on the
  souhrnné hlášení, § 102 odst. 3 písm. a), and on DPHDP3 ř. 21.

  It does **not** owe under § 108 odst. 3 písm. b) (other goods from an
  unregistered foreign person), § 108 odst. 4 písm. a) (domestic reverse
  charge) or písm. c) (import self-assessment): all three name a plátce. Import
  VAT is paid to the customs office instead, § 108 odst. 5 písm. a).

**How a tax is recognised** is by the DPHDP3 row its base carries, i.e. by
``l10n_cz``'s tax-report tags. The same mechanism ``l10n_cz_vat_return`` uses
for the ř. 43/44 deduction, and for the same reason: the tag is the tax's own
statement of what it is, so a chart that adds a rate needs no change here.

**A tax that must change becomes a "twin"**: a copy of it with the same rate
and the same reporting, minus the deduction. Twins point back to their source
(``l10n_cz_vat_status_source_id``), so a document can always be normalised to
the plátce taxes and re-mapped for another status — which is what lets a date
change on a draft move taxes both ways, and lets a user's own tax choice
survive it.
"""

import logging
import re

from odoo import api, fields, models
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

#: DPHDP3 rows (by the ``VAT <n> Base`` tag on the base repartition line).
#: Output a non-payer never charges is everything on a sale tax except what an
#: identifikovaná osoba still reports: ř. 21 (§ 9 odst. 1 services to another
#: member state) and ř. 31 (triangular trade as the middle person, § 17).
IO_SALE_ROWS = {"21", "31"}
#: Self-assessed rows an identifikovaná osoba owes (§ 108 odst. 2, § 108
#: odst. 3 písm. a)): ř. 3/4 acquisition of goods, ř. 5/6 services from an EU
#: person, ř. 12/13 other supplies by a non-established person.
IO_SELFASSESSED_ROWS = {"3", "4", "5", "6", "12", "13"}
#: Domestic reverse charge, § 92a — a plátce-only regime (§ 108 odst. 4
#: písm. a)). A non-payer's supplier charges ordinary VAT instead.
DOMESTIC_RC_ROWS = {"10", "11"}
#: Paid to the customs office by a non-payer (§ 108 odst. 5 písm. a)); the
#: ř. 7/8 self-assessment is for a plátce (§ 108 odst. 4 písm. c)), ř. 32 and
#: ř. 42 only describe a plátce's import.
CUSTOMS_ROWS = {"7", "8", "32", "42"}
#: Ordinary deduction of domestic input VAT.
DEDUCTION_ROWS = {"40", "41"}
#: New means of transport (ř. 9, § 19): a non-payer files it as typ_platce R
#: with its own rules. Deliberately left alone.
UNTOUCHED_ROWS = {"9"}

#: Rows 40–53 are the deduction section of DPHDP3 (nárok na odpočet, krácení,
#: koeficient). A twin must carry none of them.
_TAG_ROW_RE = re.compile(r"^VAT (\d+)\b")


def _tag_rows(tags):
    rows = set()
    for tag in tags:
        match = _TAG_ROW_RE.match(tag.name or "")
        if match:
            rows.add(match.group(1))
    return rows


def _is_deduction_tag(tag):
    match = _TAG_ROW_RE.match(tag.name or "")
    return bool(match) and 40 <= int(match.group(1)) <= 53


#: status -> DPHDP3 VetaD/typ_platce (dphdp3_epo2.xsd: P plátce § 6–6fa,
#: I identifikovaná osoba § 6g–6l, N neplátce dle § 108).
TYP_PLATCE = {"payer": "P", "identified": "I", "non_payer": "N"}


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_vat_status_period_ids = fields.One2many(
        "l10n.cz.vat.status.period", "company_id", string="VAT status history")
    l10n_cz_vat_status_today = fields.Selection(
        [("payer", "Plátce DPH (§ 6–6f)"),
         ("identified", "Identifikovaná osoba (§ 6g–6l)"),
         ("non_payer", "Neplátce")],
        string="VAT status today", compute="_compute_l10n_cz_vat_status_today")
    l10n_cz_vat_status_note_non_payer = fields.Char(
        string="Invoice statement (neplátce)",
        default="Nejsem plátce DPH.",
        help="Printed on an invoice dated while the company is not "
        "registered for VAT. A legal entity may prefer "
        "'Nejsme plátci DPH.'; empty prints nothing.")
    l10n_cz_vat_status_note_identified = fields.Char(
        string="Invoice statement (identifikovaná osoba)",
        default="Nejsem plátce DPH (identifikovaná osoba).",
        help="Printed on an invoice dated while the company is an "
        "identifikovaná osoba.")

    @api.depends("l10n_cz_vat_status_period_ids.date_from",
                 "l10n_cz_vat_status_period_ids.status")
    def _compute_l10n_cz_vat_status_today(self):
        today = fields.Date.context_today(self)
        for company in self:
            company.l10n_cz_vat_status_today = company._l10n_cz_vat_status_on(today)

    # ------------------------------------------------------------------
    # The history
    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_has_history(self):
        """Whether this module has anything to say for the company at all.

        Every effect is gated on this, so a company that never records a
        status is exactly where it was before the module was installed.
        """
        self.ensure_one()
        return bool(self.sudo().l10n_cz_vat_status_period_ids)

    def _l10n_cz_vat_status_on(self, date):
        """``payer`` / ``identified`` / ``non_payer`` on ``date``.

        The row starting on or before ``date`` wins; before the first row, and
        with no history at all, the answer is ``payer`` — which is what every
        Czech company was to this localisation before the module existed.
        """
        self.ensure_one()
        periods = self.sudo().l10n_cz_vat_status_period_ids
        if not date or not periods:
            return "payer"
        date = fields.Date.to_date(date)
        started = periods.filtered(lambda p: p.date_from <= date)
        if not started:
            return "payer"
        return started.sorted("date_from")[-1].status

    def _l10n_cz_vat_status_segments(self, date_from, date_to):
        """``[(first day, last day, status)]`` covering the closed interval."""
        self.ensure_one()
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        cuts = sorted(
            p.date_from for p in self.sudo().l10n_cz_vat_status_period_ids
            if date_from < p.date_from <= date_to)
        segments, start = [], date_from
        for cut in cuts:
            segments.append((start, fields.Date.subtract(cut, days=1),
                             self._l10n_cz_vat_status_on(start)))
            start = cut
        segments.append((start, date_to, self._l10n_cz_vat_status_on(start)))
        return segments

    def _l10n_cz_vat_status_label(self, status):
        return dict(
            self._fields["l10n_cz_vat_status_today"]._description_selection(
                self.env))[status]

    def _l10n_cz_vat_status_describe(self, segments):
        return ", ".join(
            "%s–%s %s" % (format_date(self.env, a), format_date(self.env, b),
                          self._l10n_cz_vat_status_label(s))
            for a, b, s in segments)

    # ------------------------------------------------------------------
    # The hook l10n_cz_statutory leaves for this module
    # ------------------------------------------------------------------
    def _l10n_cz_typ_platce(self, date):
        """DPHDP3 ``VetaD/typ_platce`` on ``date`` (the return's last day).

        P / I / N from the status on that day. No history: the base answer,
        which is P. S (skupina, § 5a) and R / D (nový dopravní prostředek,
        § 19b / § 19c) are not modelled and never returned from here.
        """
        self.ensure_one()
        if not self._l10n_cz_vat_status_has_history():
            return super()._l10n_cz_typ_platce(date)
        return TYP_PLATCE[self._l10n_cz_vat_status_on(date)]

    # ------------------------------------------------------------------
    # Tax classification and mapping
    # ------------------------------------------------------------------
    @api.model
    def _l10n_cz_vat_status_tax_kind(self, tax):
        """What a tax is, as far as a non-payer is concerned.

        Read off the DPHDP3 row its base declares on (``VAT <n> Base``).
        """
        if tax.amount_type == "group":
            return "neutral"
        reps = tax.invoice_repartition_line_ids | tax.refund_repartition_line_ids
        base_rows = _tag_rows(
            reps.filtered(lambda r: r.repartition_type == "base").tag_ids)
        all_tags = reps.tag_ids
        if tax.type_tax_use == "sale":
            if base_rows & IO_SALE_ROWS:
                return "sale_eu_service"
            if not all_tags and not tax.amount:
                return "neutral"
            return "sale_taxed"
        if tax.type_tax_use != "purchase":
            return "neutral"
        if base_rows & UNTOUCHED_ROWS:
            return "neutral"
        if base_rows & CUSTOMS_ROWS:
            return "customs"
        if base_rows & IO_SELFASSESSED_ROWS:
            # The twin is built by redirecting the one positive leg; any other
            # shape is not the Czech chart's and is left for a human (the
            # posting check then refuses rather than guessing).
            return ("io_selfassessed" if self._l10n_cz_vat_status_two_legs(tax)
                    else "io_selfassessed_unsupported")
        if base_rows & DOMESTIC_RC_ROWS:
            return "domestic_rc"
        if base_rows & DEDUCTION_ROWS:
            return "deductible"
        if not all_tags or not tax.amount:
            return "neutral"
        legs = tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax")
        if len(legs) == 1 and legs.factor_percent > 0:
            # Another deduction the chart reports somewhere (ř. 47 fixed
            # assets and the like): single leg, positive, tagged.
            return "deductible"
        return "neutral"

    @api.model
    def _l10n_cz_vat_status_two_legs(self, tax):
        """One +100 and one −100 tax leg on both the invoice and refund side."""
        for reps in (tax.invoice_repartition_line_ids,
                     tax.refund_repartition_line_ids):
            factors = sorted(reps.filtered(
                lambda r: r.repartition_type == "tax").mapped("factor_percent"))
            if factors != [-100.0, 100.0]:
                return False
        return True

    #: kind -> {status: action}; action is "keep", "drop", or a twin kind.
    _L10N_CZ_VAT_STATUS_ACTIONS = {
        "neutral": {"non_payer": "keep", "identified": "keep"},
        "sale_taxed": {"non_payer": "drop", "identified": "drop"},
        "sale_eu_service": {"non_payer": "drop", "identified": "keep"},
        "deductible": {"non_payer": "nondeductible", "identified": "nondeductible"},
        "domestic_rc": {"non_payer": "nondeductible", "identified": "nondeductible"},
        "io_selfassessed": {"non_payer": "drop", "identified": "selfassessed"},
        # No twin is ever built for it, so the identified-person side stays
        # unresolved and blocks posting.
        "io_selfassessed_unsupported": {"non_payer": "drop",
                                        "identified": "selfassessed"},
        "customs": {"non_payer": "drop", "identified": "drop"},
    }

    def _l10n_cz_vat_status_map_taxes(self, taxes, status):
        """The taxes a document of ``status`` carries in place of ``taxes``.

        Taxes are first normalised to their plátce source, so this is
        idempotent and reversible: mapping a non-payer document's taxes for
        ``payer`` gives the original ones back.
        """
        return self._l10n_cz_vat_status_map_taxes_ex(taxes, status)[0]

    def _l10n_cz_vat_status_map_taxes_ex(self, taxes, status):
        """``(taxes, unresolved)`` — ``unresolved`` are sources that need a
        twin which does not exist.

        An unresolved source is kept in the result so a draft stays editable,
        but it is REPORTED: comparing the result with the line would find them
        equal and let the source through silently, which is exactly the
        failure a status check exists to prevent (raised by a GPT-5.3-Codex
        review). The posting check refuses on it.
        """
        self.ensure_one()
        Tax = self.env["account.tax"]
        if not taxes:
            return taxes, Tax
        # ``_origin``: inside an onchange the taxes are NewId copies, which no
        # search for their twins would ever match.
        taxes = taxes._origin
        normal = Tax.browse(list(dict.fromkeys(
            (t.l10n_cz_vat_status_source_id or t).id for t in taxes)))
        if status == "payer":
            return normal, Tax
        twins = self._l10n_cz_vat_status_twins(normal)
        result, unresolved = [], Tax
        for tax in normal:
            action = self._L10N_CZ_VAT_STATUS_ACTIONS[
                self._l10n_cz_vat_status_tax_kind(tax)][status]
            if action == "keep":
                result.append(tax.id)
            elif action != "drop":
                twin = twins.get((tax.id, action))
                if twin:
                    result.append(twin.id)
                else:
                    result.append(tax.id)
                    unresolved |= tax
        return Tax.browse(list(dict.fromkeys(result))), unresolved

    def _l10n_cz_vat_status_twins(self, sources):
        """``{(source id, kind): twin}`` for ``sources``, archived included."""
        twins = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", self.id),
            ("l10n_cz_vat_status_source_id", "in", sources.ids),
        ])
        return {(t.l10n_cz_vat_status_source_id.id, t.l10n_cz_vat_status_kind): t
                for t in twins}

    # ------------------------------------------------------------------
    # Twin generation
    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_ensure_taxes(self):
        """Create every twin this company's history can need. Idempotent.

        Only runs for a company that records a non-payer period, so a company
        that stays a plátce never sees a tax it did not have. Archived taxes
        (the historical rates of ``l10n_cssk_vat_return_base``) get twins too:
        a 2023 bill at 15 % dated in a non-payer period needs one.
        """
        Tax = self.env["account.tax"].with_context(active_test=False)
        created = Tax.browse()
        for company in self:
            statuses = set(company.sudo().l10n_cz_vat_status_period_ids.mapped("status"))
            needed = {"non_payer": {"nondeductible"},
                      "identified": {"nondeductible", "selfassessed"}}
            kinds_needed = set()
            for status in statuses:
                kinds_needed |= needed.get(status, set())
            if not kinds_needed:
                continue
            sources = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                ("l10n_cz_vat_status_source_id", "=", False),
            ])
            existing = company._l10n_cz_vat_status_twins(sources)
            for source in sources:
                kind = company._l10n_cz_vat_status_tax_kind(source)
                for status in statuses:
                    action = self._L10N_CZ_VAT_STATUS_ACTIONS[kind].get(status)
                    if action not in ("nondeductible", "selfassessed"):
                        continue
                    if kind == "io_selfassessed_unsupported":
                        _logger.warning(
                            "l10n_cz_vat_status: %s has no +100/-100 tax legs; "
                            "no identified-person twin built", source.name)
                        continue
                    if (source.id, action) in existing:
                        continue
                    twin = company._l10n_cz_vat_status_make_twin(source, action)
                    existing[(source.id, action)] = twin
                    created |= twin
        if created:
            _logger.info("l10n_cz_vat_status: %s tax twin(s) created: %s",
                         len(created), ", ".join(created.mapped("name")))
        return created

    _L10N_CZ_VAT_STATUS_TWIN_SUFFIX = {
        "nondeductible": " (no deduction)",
        "selfassessed": " (identified person)",
    }

    def _l10n_cz_vat_status_make_twin(self, source, kind):
        """Copy ``source`` into a tax a non-payer may carry.

        ``nondeductible`` — one tax leg per document type, **no account and no
        tags**: Odoo posts a leg without an account onto the base line's own
        account (``account.tax._prepare_tax_lines``), so the supplier's VAT
        becomes part of the cost, and nothing reaches the return.

        ``selfassessed`` — the source's legs and output tags unchanged, except
        that the positive leg (the deduction side: on the Czech chart it sits
        on the input account 343 1xx while the liability leg sits on 343 2xx)
        loses its account, so it lands on the cost, and every deduction-section
        tag (ř. 40–53) is removed. The liability and ř. 3–13 stay exactly as
        the plátce tax reports them.
        """
        self.ensure_one()
        vals = {
            "name": source.name + self._L10N_CZ_VAT_STATUS_TWIN_SUFFIX[kind],
            "l10n_cz_vat_status_source_id": source.id,
            "l10n_cz_vat_status_kind": kind,
            "fiscal_position_ids": [(5, 0, 0)],
            "original_tax_ids": [(5, 0, 0)],
            # A KH hint the source carries would still classify our lines;
            # the resolver is gated anyway, but a twin should state nothing.
            "cssk_control_section_default": False,
            "cssk_control_is_reverse_charge": False,
            "cssk_historic_source_tax_id": False,
        }
        vals = {k: v for k, v in vals.items() if k in source._fields}
        if kind == "nondeductible":
            for field in ("invoice_repartition_line_ids",
                          "refund_repartition_line_ids"):
                doc = "invoice" if field.startswith("invoice") else "refund"
                vals[field] = [(5, 0, 0),
                               (0, 0, {"repartition_type": "base",
                                       "document_type": doc,
                                       "factor_percent": 100.0}),
                               (0, 0, {"repartition_type": "tax",
                                       "document_type": doc,
                                       "factor_percent": 100.0,
                                       "account_id": False,
                                       "use_in_tax_closing": False})]
        twin = source.copy(vals)
        if kind == "selfassessed":
            for rep in twin.invoice_repartition_line_ids | twin.refund_repartition_line_ids:
                write = {}
                deduction_tags = rep.tag_ids.filtered(_is_deduction_tag)
                if deduction_tags:
                    write["tag_ids"] = [(3, t.id) for t in deduction_tags]
                if rep.repartition_type == "tax" and rep.factor_percent > 0:
                    write.update({"account_id": False,
                                  "use_in_tax_closing": False})
                if write:
                    rep.write(write)
        twin.active = source.active
        return twin

    def _l10n_cz_vat_status_strip_twin_deductions(self):
        """Remove ř. 40–53 tags a chart-wide pass put onto our twins."""
        reps = self.env["account.tax.repartition.line"].search([
            ("tax_id.company_id", "in", self.ids),
            ("tax_id.l10n_cz_vat_status_source_id", "!=", False),
        ])
        for rep in reps:
            bad = rep.tag_ids.filtered(_is_deduction_tag)
            if bad:
                rep.tag_ids = [(3, t.id) for t in bad]

    # ------------------------------------------------------------------
    # Other modules' chart-wide passes must leave twins alone
    # ------------------------------------------------------------------
    def _cz_tag_selfassessed_deduction(self):
        """``l10n_cz_vat_return`` tags the ř. 43/44 deduction onto EVERY
        two-legged Czech purchase tax. An identifikovaná osoba has no
        deduction (§ 72 odst. 1), so on its self-assessment twins those tags
        would report a deduction that does not exist. Undone right after."""
        res = super()._cz_tag_selfassessed_deduction()
        self._l10n_cz_vat_status_strip_twin_deductions()
        return res

    def _cssk_tax_is_superseded(self, tax):
        """Never clone a twin into a historical rate: the historical rates get
        twins of their own, from the rate clone."""
        return bool(tax.l10n_cz_vat_status_source_id) or super()._cssk_tax_is_superseded(tax)

    # ------------------------------------------------------------------
    def _l10n_cz_vat_status_history_changed(self, since=None, ignored_before=None):
        """``since``: the earliest day whose status may have changed.

        The KH section of a posted line is stored, and which lines belong to a
        plátce period has just changed under it. Only documents whose DUZP (or
        accounting date, where there is none) falls on or after ``since`` can
        be affected: a credit note takes the status of the invoice it
        corrects, which is never later than its own DUZP.

        ``ignored_before``: the ids ``_l10n_cz_vat_status_ignored_move_ids``
        returned before the change. A declared later period applies only to
        a plátce's documents (``account.move.
        _l10n_cz_vat_status_ignores_declared_date``), so the documents that
        moved in or out of that set have their VAT-deferral entries
        (``l10n_cssk_core``) withdrawn or created. Only those: a plátce
        document without entries for another reason — posted before the
        deferral account was set, say — is not the status history's business.

        Filings need nothing: they read the status live whenever they are
        computed. One already filed is not changed — that takes a dodatečné
        přiznání, as any correction of a filed period does.
        """
        self._l10n_cz_vat_status_ensure_taxes()
        MoveLine = self.env["account.move.line"]
        for company in self:
            domain = [("company_id", "=", company.id),
                      ("parent_state", "=", "posted")]
            if since:
                domain += ["|", ("move_id.taxable_supply_date", ">=", since),
                           "&", ("move_id.taxable_supply_date", "=", False),
                           ("move_id.date", ">=", since)]
            MoveLine.search(domain)._cssk_recompute_section_codes()
        if ignored_before is not None:
            Move = self.env["account.move"]
            before = set(Move.browse(ignored_before).exists().filtered(
                lambda m: m.company_id in self).ids)
            flipped = before ^ set(self._l10n_cz_vat_status_ignored_move_ids())
            Move.browse(sorted(flipped))._l10n_cz_vat_status_resync_deferral()

    def _l10n_cz_vat_status_ignored_move_ids(self):
        """Posted documents whose declared VAT period is ignored today.

        Snapshot taken before and after a history change, so that only the
        documents whose answer changed are touched. Scans only documents that
        record a declared period at all, which is the exception.
        """
        moves = self.env["account.move"].search([
            ("company_id", "in", self.ids), ("state", "=", "posted"),
            ("cssk_vat_deduction_date", "!=", False),
            ("cssk_vat_deferral_origin_id", "=", False)])
        return [m.id for m in moves
                if m._l10n_cz_vat_status_ignores_declared_date()]

    def action_l10n_cz_vat_status_ensure_taxes(self):
        self._l10n_cz_vat_status_ensure_taxes()
        return True
