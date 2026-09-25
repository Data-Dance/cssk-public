# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields, models


class AccountTax(models.Model):
    """Marks a tax as a *historical* rate — one no longer in force.

    A chart template ships the rates in force today. A history import does not
    need those: it needs the rate that applied when the document was issued, and
    a Czech or Slovak agenda of any age crosses at least one rate change. Mapping
    a 2024 Slovak supply onto today's 23 % is not a mapping decision, it is a
    restatement — the base is the line amount, so only the tax figure moves, and
    it moves silently.

    The fields here are what makes such a tax identifiable afterwards. Without
    them a historical rate is indistinguishable from a rate somebody created by
    hand, which is exactly how both reference companies ended up with partial,
    active, undocumented sets of them.
    """

    _inherit = "account.tax"

    cssk_historic_valid_from = fields.Date(
        string="Rate In Force From",
        help="First day this rate applied. Set only on taxes generated for a "
        "rate that is no longer current.",
    )
    cssk_historic_valid_to = fields.Date(
        string="Rate In Force Until",
        help="Last day this rate applied.",
    )
    cssk_historic_source_tax_id = fields.Many2one(
        "account.tax",
        string="Derived From",
        ondelete="set null",
        help="The current-rate tax this one was cloned from. Kept because the "
        "clone's repartition and tags come from it: if the statutory form ever "
        "stops treating rate slots as interchangeable, this is the list of "
        "taxes that assumption was applied to.",
    )

    def _cssk_rate_starts(self):
        """``{tax id: derived start}`` for the CURRENT rates in ``self``.

        One query for the whole recordset. ``_cssk_rate_window`` would
        otherwise issue one per current-rate tax, and it is called once per
        line of a mass compute — thousands of lines times a few candidates.

        Only rates carrying no window of their own are looked up: a historical
        clone states its own dates and needs nothing.
        """
        current = self.filtered(
            lambda t: not t.cssk_historic_valid_from and not t.cssk_historic_valid_to
        )
        if not current:
            return {}
        starts = {}
        clones = self.with_context(active_test=False).search([
            ("cssk_historic_source_tax_id", "in", current.ids),
            ("cssk_historic_valid_to", "!=", False),
        ])
        for clone in clones:
            source = clone.cssk_historic_source_tax_id.id
            end = clone.cssk_historic_valid_to
            if source not in starts or end > starts[source]:
                starts[source] = end
        return {k: v + timedelta(days=1) for k, v in starts.items()}

    def _cssk_rate_window(self):
        """``(first day, last day)`` this rate was in force. ``False`` = open.

        A HISTORICAL rate states its own window, because the generator stamped
        it. A CURRENT rate carries none — it is the rate in force now — but its
        START is derivable from the same data: a historical clone pointing at
        it ran until the day the current rate took over. SK 23 % has a 20 %
        clone ending 2024-12-31, so 23 % began 2025-01-01, and the same for
        19 % over its 10 % clone.

        Where SEVERAL clones point at one current rate the latest of them wins,
        which is what a merger of rate bands means: CZ 12 % is cloned from by
        15 % (to 2023-12-31), 14 %, 10 % (to 2023-12-31), 9 % and 5 %, and
        12 % duly starts 2024-01-01, the day the two reduced bands became one.

        A current rate that no clone points at stays unbounded, because nothing
        in the data says when it started. SK 5 % is exactly that: § 27 ods. 2
        písm. b) **added** it on 2023-01-01 rather than replacing a predecessor,
        so it has no clone to be bounded by and remains a candidate for every
        earlier date. ``cssk_historic_valid_from`` is a plain field on every
        tax, not only on clones — setting it on such a rate by hand is truthful
        and this method will then prefer it.
        """
        self.ensure_one()
        if self.cssk_historic_valid_from or self.cssk_historic_valid_to:
            return self.cssk_historic_valid_from, self.cssk_historic_valid_to
        # Archived on purpose: every clone is inactive, so the default
        # active_test would find none of them and every current rate would look
        # unbounded.
        clones = self.with_context(active_test=False).search([
            ("cssk_historic_source_tax_id", "=", self.id),
            ("cssk_historic_valid_to", "!=", False),
        ])
        if not clones:
            return False, False
        return max(clones.mapped("cssk_historic_valid_to")) + timedelta(days=1), False

    def _cssk_in_force_on(self, date):
        """The subset of ``self`` whose rate was in force on ``date``.

        An unbounded rate matches every date — "we do not know when this began"
        must not silently exclude it.
        """
        if not date:
            return self
        derived = self._cssk_rate_starts()
        kept = self.browse()
        for tax in self:
            start = tax.cssk_historic_valid_from or derived.get(tax.id)
            end = tax.cssk_historic_valid_to
            if start and date < start:
                continue
            if end and date > end:
                continue
            kept |= tax
        return kept
