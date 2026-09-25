# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re

from odoo import _, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Generate the VAT rates that used to be in force, for history imports.

    **Country-agnostic on purpose: this module holds no rates.** The mechanism
    is the same for both countries and the rate history is not, so the tables
    live in ``l10n_cz_vat_return`` and ``l10n_sk_vat_return``, which are also
    the modules that depend on the official charts being cloned from.

    Rates are **cloned from the current-rate taxes rather than declared**, which
    is the whole design and deserves its justification:

    * A rate is not one tax. The Slovak chart carries twelve taxes at 23 % —
      plain, reverse charge, EU acquisition, triangulation, import, customs,
      unpaid, and the sale-side variants — and each needs a historical twin.
      Declaring them in CSV would restate every repartition line and every tag
      of the official localisation, and would then drift from it.
    * **The statutory form's rate slots are interchangeable.** Measured on the
      customer's own filed Slovak returns: the 2024-11 return reports its 20 %
      supplies on r03/r04 and the 2025-01 return reports 23 % supplies on the
      *same* r03/r04; likewise r07/r08 for EU acquisitions and r09/r10 for
      § 69(3) services. So the current tax's tags are the correct tags for the
      historical rate wherever the form has not moved the line. That is
      measured from filings rather than reasoned from the statute.
    * **Except where a later form SPLIT a line**, which the same evidence did
      not cover and a later measurement found: the reverse-charge band was one
      line ``r09``/``r10`` until mid-2025 and three afterwards, so a 20 % clone
      of today's 23 % inherits ``09b`` — a line that did not exist while 20 %
      was in force. ``tag_remap`` on the rate table is how a country says so.

    Everything generated is **archived**. A historical rate must not appear when
    somebody raises today's invoice; it only has to exist, be correct, and be
    reachable by an importer that already knows which tax it wants.
    """

    _inherit = "res.company"

    def _cssk_historic_vat_rates(self):
        """Rates that used to be in force, as ``(rate, source_rate, from, to)``
        or ``(rate, source_rate, from, to, tag_remap)``.

        ``source_rate`` names the *current* rate whose taxes are cloned, and so
        decides which statutory slots the historical rate reports in: clone a
        standard rate from the standard rate, a reduced one from a reduced one.

        ``tag_remap`` is an optional ``{old_tag_name: new_tag_name}`` applied to
        the clone's repartition tags. It exists because **cloning the tags is
        right only while the form has not moved the line**.

        That was measured before being relied on — a Slovak return files 20 %
        and 23 % supplies on the same r03/r04, so the domestic bands are
        interchangeable and the clone is correct for them. It is **not** correct
        where a later vzor SPLIT a line: the pre-July-2025 form has a single
        reverse-charge band ``r09``/``r10`` (confirmed against dph2021.xsd),
        and the 2025 form split it into ``r09``/``r09a``/``r09b`` by rate. A
        20 % reverse charge cloned from today's 23 % therefore inherits tag
        ``09b`` — a line that did not exist when 20 % was in force — and files
        on it.

        Found by the MRP extractor comparing a filed FY2024 return: the engine
        reported 804.03 of base and 160.81 of tax on r09b where the filed
        return uses r09.
        """
        self.ensure_one()
        return ()

    #: How core marks a tax the chart has replaced. From
    #: ``account/models/chart_template.py``, where a reload that finds a tax
    #: too different from its template recreates it and renames the old one::
    #:
    #:     tax_to_rename.name = f"[old{n if n > 1 else ''}] {tax_to_rename.name}"
    #:
    #: ⚠️ **Numbered on repeat renames** — ``[old]``, ``[old1]``, ``[old2]`` —
    #: so a host that has been through two rate changes carries all three
    #: forms. Core's own matcher is ``^(?:\[old\d*\] |)``; this mirrors it.
    #: A ``startswith("[old]")`` catches only the first and lets the rest
    #: through as sources, which is the bug this pattern replaces.
    _CSSK_SUPERSEDED_PREFIX = re.compile(r"^\s*\[old\d*\]\s")

    def _cssk_tax_is_superseded(self, tax):
        """Has the chart already replaced this tax?

        Such a tax is history already. Generating a historical twin OF it
        produces a duplicate of the twin we generate from the live tax, and
        names it for two rates into the bargain.

        ⚠️ **Every language is checked, not the active one.** ``name`` is
        translatable and core's rename at ``chart_template.py`` is a plain
        assignment, so the marker lands in whichever language the load ran
        under and nowhere else. On a database built with ``sk_SK`` the two
        records read::

            {"en_US": "[old] 23% BAD DEBT", "sk_SK": "23 % POH"}
            {"en_US": "23% BAD DEBT",       "sk_SK": "23 % POH"}

        — identical in Slovak, and `tax.name` resolves in the environment's
        language. Testing that alone makes the marker invisible on exactly the
        databases this module exists for, and the skip silently stops working.
        """
        field = tax._fields["name"]
        stored = None
        # A NewId has no row to read; unit tests build records that way.
        if field.translate and isinstance(tax.id, int):
            stored = field._get_stored_translations(tax)
        values = list(stored.values()) if stored else [tax.name or ""]
        return any(
            self._CSSK_SUPERSEDED_PREFIX.match(value or "")
            for value in values
        )

    #: A leading rate token: "23%", "23 %", "12,5 %", "12.5%".
    _CSSK_RATE_PREFIX = re.compile(r"^\s*(\d+(?:[.,]\d+)?)(\s*)%")

    def _cssk_historic_tax_name(self, name, source_rate, rate):
        """The historical twin's name, by substituting the leading rate.

        Both charts name a tax for its rate and then qualify it — ``23% RC``,
        ``12% EU G`` — so substituting the leading token yields exactly the name
        the same tax would have had at the older rate. That is what makes
        adoption possible: a rate created by hand before this module existed
        already carries the generated name, and is taken over rather than
        duplicated.

        ⚠️ **The chart's spacing is not ours to assume.** This used to test
        ``name.startswith("%g%%" % source_rate)``, which is ``"23%"`` — and a
        chart naming the same tax ``"23 % EÚ"``, with a space, failed the test
        and fell through to the collision-avoiding branch. The result was
        ``"20% 23 % EÚ"``: two rates in one name, saying neither. Cosmetic in
        isolation, and it broke cross-host tax matching by name outright —
        found on a client instance where every pre-2025 tax read that way,
        while a host whose chart writes ``"23%"`` was clean.

        So the leading rate is matched as a TOKEN and the chart's own spacing
        is carried into the replacement: ``"23 % EÚ"`` → ``"20 % EÚ"``,
        ``"23% RC"`` → ``"20% RC"``. Substitution happens only when that token
        IS the source rate — a name leading with some other rate is left to the
        fallback rather than silently renamed onto a rate it never had.
        """
        match = self._CSSK_RATE_PREFIX.match(name or "")
        if match:
            found = float(match.group(1).replace(",", "."))
            # Rates are percentages with at most a couple of decimals; an exact
            # float compare would miss 12,50 against 12.5.
            if abs(found - source_rate) < 0.001:
                return "%g%s%%%s" % (rate, match.group(2), name[match.end():])
        # A chart that names taxes some other way still gets a distinct,
        # rate-bearing name rather than a collision.
        return "%g%% %s" % (rate, name)

    def _cssk_historic_tax_group(self, source_group, rate):
        """The tax group for a historical rate — reused if one already exists.

        A group is a display grouping: it is what a printed invoice totals
        under. Leaving a 20 % tax in the ``VAT 23%`` group makes a historical
        document print a heading that contradicts its own lines, so the group is
        matched by name and created from the source's if absent — which carries
        the payable/receivable account configuration with it.
        """
        self.ensure_one()
        name = "VAT %g%%" % rate
        Group = self.env["account.tax.group"].with_company(self)
        existing = Group.search(
            [("name", "=", name), ("company_id", "=", self.id)], limit=1
        )
        if existing:
            return existing
        if not source_group:
            return source_group
        return source_group.copy({"name": name})

    def _cssk_create_historic_vat_taxes(self):
        """Create (or adopt) the archived historical-rate taxes. Idempotent.

        Safe to re-run: a tax already carrying the name this would generate is
        stamped and archived rather than duplicated. That path is not
        hypothetical — it is how the reference companies' hand-made rates were
        brought under management, four in the Slovak company and six in the
        Czech one, each created ad hoc for one import and left active.
        """
        Tax = self.env["account.tax"]
        touched = Tax.browse()
        for company in self:
            rates = company._cssk_historic_vat_rates()
            if not rates:
                continue
            company_taxes = Tax.with_company(company).with_context(
                active_test=False
            )
            created = adopted = 0
            for spec in rates:
                rate, source_rate, valid_from, valid_to = spec[:4]
                tag_remap = spec[4] if len(spec) > 4 else None
                sources = company_taxes.search([
                    ("company_id", "=", company.id),
                    ("amount", "=", source_rate),
                    ("amount_type", "=", "percent"),
                    # Never clone a clone: without this, a second run would
                    # generate historical twins OF the historical twins.
                    ("cssk_historic_valid_from", "=", False),
                ])
                # ...nor clone what the CHART already superseded. Core renames
                # a tax it replaces to "[old] <name>" and leaves it in place,
                # so a host that has been through a rate change carries both
                # "23% BAD DEBT" and "[old] 23% BAD DEBT" at the same amount.
                # Both passed the filter above — neither is one of ours — and
                # the generator made a historical twin of EACH: "20% BAD DEBT"
                # and "20% [old] 23% BAD DEBT". Same concept, same rate, same
                # type_tax_use, two records, one of them named for two rates.
                #
                # A superseded tax is already history; a historical twin of it
                # is not a period this company ever filed under. Measured on a
                # client instance: six such duplicates, and they are why the
                # 1.7.0 name repair was a no-op there — the fixed generator and
                # the buggy one agree on a name whose leading token is "[old]"
                # rather than a rate, so there was nothing for it to rewrite.
                sources = sources.filtered(
                    lambda t: not company._cssk_tax_is_superseded(t))
                stamp = {
                    "cssk_historic_valid_from": valid_from,
                    "cssk_historic_valid_to": valid_to,
                    "active": False,
                }
                for source in sources:
                    name = company._cssk_historic_tax_name(
                        source.name, source_rate, rate
                    )
                    existing = company_taxes.search([
                        ("company_id", "=", company.id),
                        ("name", "=", name),
                        ("type_tax_use", "=", source.type_tax_use),
                    ], limit=1)
                    if existing:
                        existing.write(dict(
                            stamp, cssk_historic_source_tax_id=source.id
                        ))
                        company._cssk_remap_historic_tags(existing, tag_remap)
                        touched |= existing
                        adopted += 1
                        continue
                    clone = source.copy({
                        "name": name,
                        "amount": rate,
                        "invoice_label": "%g%%" % rate,
                        "tax_group_id": company._cssk_historic_tax_group(
                            source.tax_group_id, rate
                        ).id,
                        "cssk_historic_source_tax_id": source.id,
                    })
                    # Archived AFTER the copy: creating a tax inactive makes
                    # some of Odoo's own onchange defaults skip, and the
                    # repartition has to be in place before it is hidden.
                    clone.write(stamp)
                    company._cssk_remap_historic_tags(clone, tag_remap)
                    touched |= clone
                    created += 1
            if created or adopted:
                _logger.info(
                    "%s: %s historical VAT taxes created, %s adopted",
                    company.display_name, created, adopted,
                )
        return touched

    def _cssk_remap_historic_tags(self, tax, tag_remap):
        """Point a historical rate's tags at the lines that existed back then.

        A no-op unless the country table asks for it, which it should only
        where a later form **split or renamed** the line — see
        ``_cssk_historic_vat_rates``. Matched by tag NAME within the company's
        fiscal country, because that is what the line definitions reference.
        """
        self.ensure_one()
        if not tag_remap or not tax:
            return 0
        Tag = self.env["account.account.tag"]
        country = self.account_fiscal_country_id
        moved = 0
        for rep in (tax.invoice_repartition_line_ids
                    | tax.refund_repartition_line_ids):
            wanted = Tag.browse()
            changed = False
            for tag in rep.tag_ids:
                target = tag_remap.get(tag.name)
                if not target:
                    wanted |= tag
                    continue
                replacement = Tag.search([
                    ("name", "=", target), ("applicability", "=", "taxes"),
                    ("country_id", "=", country.id),
                ], limit=1)
                if replacement:
                    wanted |= replacement
                    changed = True
                else:
                    # No such tag in this chart: keep what is there rather than
                    # drop the line's only route to the return. Reported, since
                    # a silently untagged reverse charge is exactly the failure
                    # this remap exists to prevent.
                    wanted |= tag
                    _logger.warning(
                        "cssk: %s asks to remap tag %s to %s, which this "
                        "chart does not define — left as it was",
                        tax.name, tag.name, target,
                    )
            if changed:
                rep.tag_ids = [(6, 0, wanted.ids)]
                moved += 1
        if moved:
            _logger.info(
                "cssk: %s repartition line(s) of %s remapped to the tags of "
                "the form in force at the time", moved, tax.name,
            )
        return moved

    def _cssk_historic_vat_taxes(self):
        """Every historical-rate tax of these companies, archived ones included."""
        return self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "in", self.ids),
            ("cssk_historic_valid_from", "!=", False),
        ])

    def action_cssk_create_historic_vat_taxes(self):
        """Button: generate the historical rates for the selected companies."""
        taxes = self._cssk_create_historic_vat_taxes()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if taxes else "warning",
                "sticky": False,
                "message": _(
                    "%s historical VAT rate(s) are available. They are "
                    "archived: an importer can use them, and they will not "
                    "appear when raising a new document.", len(taxes),
                ) if taxes else _(
                    "No historical VAT rates are defined for this company's "
                    "chart of accounts."
                ),
            },
        }
