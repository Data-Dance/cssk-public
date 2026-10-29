# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)

#: Czech VAT rates that are no longer in force, as
#: ``(rate, source_rate, valid_from, valid_to)``. ``source_rate`` is the
#: **current** rate whose taxes are cloned, and therefore which statutory slots
#: the historical rate reports in — a standard rate from the standard rate, a
#: reduced one from a reduced one.
#:
#: Rate history under zákon č. 235/2004 Sb. o dani z přidané hodnoty, § 47:
#:
#: * 2004-05-01 – 2007-12-31   19 % základní, 5 % snížená
#: * 2008-01-01 – 2009-12-31   19 % základní, 9 % snížená
#: * 2010-01-01 – 2011-12-31   20 % základní, 10 % snížená
#: * 2012-01-01 – 2012-12-31   20 % základní, 14 % snížená
#: * 2013-01-01 – 2014-12-31   21 % základní, 15 % snížená
#: * 2015-01-01 – 2023-12-31   21 % základní, 15 % první a 10 % druhá snížená
#: * 2024-01-01 –              21 % základní, 12 % snížená
#:
#: Reaching back to 2004-05-01 is not arbitrary: that is when the current VAT
#: Act took effect, on EU accession, and it is the earliest date whose documents
#: this localisation's statements are built to describe at all.
#:
#: **10 % gets one entry, not two.** It was the reduced rate from 2010 to 2011
#: and the *second* reduced rate from 2015 to 2023, with three years between in
#: which it did not exist. Two taxes at the same rate would be
#: indistinguishable to whoever has to pick one, so it is a single tax spanning
#: both, and the gap is recorded here rather than in the data.
CZ_HISTORIC_VAT_RATES = (
    (20.0, 21.0, "2010-01-01", "2012-12-31"),
    (19.0, 21.0, "2004-05-01", "2009-12-31"),
    (15.0, 12.0, "2013-01-01", "2023-12-31"),
    (14.0, 12.0, "2012-01-01", "2012-12-31"),
    (10.0, 12.0, "2010-01-01", "2023-12-31"),
    (9.0, 12.0, "2008-01-01", "2009-12-31"),
    (5.0, 12.0, "2004-05-01", "2007-12-31"),
)


#: ``l10n_cz`` intra-Community acquisition tax -> the domestic purchase tax it
#: replaces under the Intra-Community fiscal position. ``l10n_cz`` ships these
#: four with an empty ``original_tax_ids`` (the Extra-Community ones are
#: mapped), so the position maps nothing and an EU vendor bill keeps the
#: domestic 21 % / 12 % charged by the supplier instead of self-assessing.
CZ_INTRA_COMMUNITY_PURCHASE_MAP = {
    "l10n_cz_21_acquisition_goods_eu": "l10n_cz_21_receipt_domestic_supplies",
    "l10n_cz_12_purchase_goods_eu": "l10n_cz_12_receipt_domestic_supplies",
    "l10n_cz_21_receipt_service_person_eu":
        "l10n_cz_21_receipt_domestic_services",
    "l10n_cz_12_receipt_service_person_eu":
        "l10n_cz_12_receipt_domestic_service",
}


#: ``l10n_cz`` extra-Community SERVICE tax -> the domestic service purchase
#: tax it replaces. The chart points both of them at the domestic **goods**
#: tax instead, which breaks the Extra-Community position in two directions at
#: once. Measured on 19.0 with a 1 000 CZK bill from a US vendor carrying the
#: domestic ``21% G``::
#:
#:     21% G  ->  21% EX G, 21% EX S, 0% EX G.Custom
#:
#: Three taxes for one line. The money still nets — each self-assessment
#: cancels itself — so the bill totals 1 000.00 and posts without complaint,
#: and the RETURN is what is wrong: the same 1 000 is declared on ř. 7
#: (import of goods), on ř. 12 (services from abroad) and on ř. 42 (daň
#: zaplacená celnímu orgánu), and ř. 43 deducts 420.00 against a real 210.00.
#:
#: And in the other direction ``21% S`` maps to nothing at all, so a service
#: bought from outside the EU keeps the Czech 21 % the supplier never charged
#: and is never self-assessed — the same defect, and the same repair, as the
#: intra-Community mapping in ``CZ_INTRA_COMMUNITY_PURCHASE_MAP``.
#:
#: This is the one place in this module where a link is **removed** rather than
#: only added: a wrong source cannot be repaired by adding the right one
#: beside it, because ``map_tax`` returns every destination it finds.
#: Deliberately narrow — only the goods tax the chart itself wired is taken
#: off, so a mapping a user added survives.
CZ_EXTRA_COMMUNITY_SERVICE_MAP = {
    "l10n_cz_21_receipt_service_person_non_eu": (
        "l10n_cz_21_receipt_domestic_services",
        "l10n_cz_21_receipt_domestic_supplies",
    ),
    "l10n_cz_12_receipt_service_person_non_eu": (
        "l10n_cz_12_receipt_domestic_service",
        "l10n_cz_12_receipt_domestic_supplies",
    ),
}


class ResCompany(models.Model):
    _inherit = "res.company"

    def _cz_map_extra_community_service_taxes(self):
        """Let the Extra-Community position tell goods from services.

        See ``CZ_EXTRA_COMMUNITY_SERVICE_MAP`` for the measurement. Idempotent:
        a destination already naming the service tax and not the goods one is
        left alone.

        ⚠️ ``0% EX G.Custom`` is deliberately NOT touched, although the same
        bill shows it mapping from every domestic purchase tax the chart
        ships. ř. 42 is claimed when the customs office assesses the tax, and
        the amount comes from its decision rather than from the rate — the tax
        is 0 % — so whether it should auto-apply at all is a question about
        the chart's intent, not a wiring mistake with one right answer. It is
        reported here and left for the owner.
        """
        ChartTemplate = self.env["account.chart.template"]
        total = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            # ⚠️ Per company. A counter hoisted out of this loop makes the
            # second company log the first one's changes as its own — the
            # shape this was copied from had exactly that bug, and it is
            # fixed below too. Raised by a GPT-5.3-Codex review.
            touched = 0
            ref = ChartTemplate.with_company(company).ref
            for dest_xmlid, (right_xmlid, wrong_xmlid) in \
                    CZ_EXTRA_COMMUNITY_SERVICE_MAP.items():
                dest = ref(dest_xmlid, raise_if_not_found=False)
                right = ref(right_xmlid, raise_if_not_found=False)
                wrong = ref(wrong_xmlid, raise_if_not_found=False)
                if not dest or not right:
                    _logger.warning(
                        "l10n_cz_vat_return: %s has no %s, extra-Community "
                        "service mapping not set", company.display_name,
                        dest_xmlid if not dest else right_xmlid,
                    )
                    continue
                if right not in dest.original_tax_ids:
                    dest.original_tax_ids = [(4, right.id)]
                    touched += 1
                if wrong and wrong in dest.original_tax_ids:
                    dest.original_tax_ids = [(3, wrong.id)]
                    touched += 1
            total += touched
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s extra-Community service tax "
                    "mapping(s) corrected on %s", touched,
                    company.display_name,
                )
        return total

    def _cz_map_intra_community_purchase_taxes(self):
        """Let the Intra-Community position replace the domestic purchase tax.

        Found on an inter-company bill from a Slovak seller to a Czech buyer:
        30.00 of goods came out at 36.30, the supplier being asked for Czech
        21 % that the buyer has to self-assess instead. Every Czech vendor bill
        from an EU supplier does the same, because ``map_tax`` passes a tax
        through untouched when no destination names it as its original.

        Goods map to ``EU G`` and services to ``EU S`` by the domestic tax the
        product carries (``21% G`` / ``21% S``), which is the only signal of
        goods-versus-service Odoo gives the position.

        Only links are added, never removed, so a mapping a user has set up
        by hand survives. Idempotent. Archived historical rate clones are left
        alone: nothing picks them on a new document.
        """
        ChartTemplate = self.env["account.chart.template"]
        total = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            touched = 0
            ref = ChartTemplate.with_company(company).ref
            for dest_xmlid, src_xmlid in CZ_INTRA_COMMUNITY_PURCHASE_MAP.items():
                dest = ref(dest_xmlid, raise_if_not_found=False)
                src = ref(src_xmlid, raise_if_not_found=False)
                if not dest or not src:
                    # A company whose chart lacks one of these has deleted it
                    # or predates it; say so rather than leave the position
                    # silently half-mapped.
                    _logger.warning(
                        "l10n_cz_vat_return: %s has no %s, intra-Community "
                        "mapping not set", company.display_name,
                        dest_xmlid if not dest else src_xmlid,
                    )
                    continue
                if src in dest.original_tax_ids:
                    continue
                dest.original_tax_ids = [(4, src.id)]
                touched += 1
            total += touched
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s intra-Community purchase tax "
                    "mapping(s) added on %s", touched, company.display_name,
                )
        return total

    def _cssk_historic_vat_rates(self):
        self.ensure_one()
        if self.chart_template == "cz":
            return CZ_HISTORIC_VAT_RATES
        return super()._cssk_historic_vat_rates()


#: The declaration line a self-assessed purchase tax already reports on tells
#: us its RATE BAND, so the deduction band follows without a single rate
#: literal. ř3/ř5/ř10/ř12 are the základní-sazba declaration lines and ř4/ř6/
#: ř11/ř13 the snížená ones — which is why a chart that adds a rate needs no
#: change here.
CZ_SELFASSESSED_BAND = {
    "VAT 3 Base": "43", "VAT 5 Base": "43", "VAT 7 Base": "43",
    "VAT 10 Base": "43", "VAT 12 Base": "43",
    "VAT 4 Base": "44", "VAT 6 Base": "44", "VAT 8 Base": "44",
    "VAT 11 Base": "44", "VAT 13 Base": "44",
}

#: Rows whose self-assessed tax `l10n_cz` declares WITHOUT a deduction leg, so
#: the leg has to be created rather than merely tagged. See
#: ``_cz_build_selfassessed_deduction``.
#:
#: ⚠️ ř9 is deliberately absent. Rows 3-13 are all deductible on ř43/44 by the
#: form's own caption, but ř9 is *pořízení nového dopravního prostředku*, where
#: the deduction is not automatic — so its single leg may well be intended, and
#: nothing here has the evidence to overrule it.
CZ_SELFASSESSED_NO_LEG = ("VAT 7 Base", "VAT 8 Base")


class ResCompanyCzDeduction(models.Model):
    _inherit = "res.company"

    def _cz_deduction_tag(self, line, kind):
        """The ř43/ř44 tag, created on first use.

        Named to match the chart's own convention for the other deduction
        lines — ``VAT 40 Base`` / ``VAT 40 Total`` for ř40 — so the four new
        tags read like the eight that were already there. `l10n_cz` defines
        none for 43/44: its tag list runs 40, 41, 42 and then jumps to 47.
        """
        self.ensure_one()
        name = "VAT %s %s" % (line, kind)
        Tag = self.env["account.account.tag"]
        country = self.account_fiscal_country_id
        tag = Tag.search([
            ("name", "=", name), ("applicability", "=", "taxes"),
            ("country_id", "=", country.id),
        ], limit=1)
        if not tag:
            tag = Tag.create({
                "name": name, "applicability": "taxes",
                "country_id": country.id,
            })
        return tag

    def _cz_fix_refund_repartition_accounts(self):
        """Give the refund side the tax account the invoice side already has.

        ``l10n_cz`` ships four reverse-charge purchase taxes — ``12% EU G``,
        ``21% EU G``, ``12% EU S``, ``21% EU S`` — whose INVOICE repartition
        names both legs (343112/343212, 343121/343221) while the REFUND
        repartition names only the deductible one. The self-assessed leg of a
        credit note therefore has no tax account, and Odoo leaves that amount
        on the BASE line's account instead.

        The consequence is not a misposted tax line but a **clearing account
        that stops clearing**: on a seven-year Czech import, 64 reverse-charge
        corrections left 289,031.99 sitting on účet 395000, which nets to zero
        in the source. Nothing else disagreed — the VAT return and the control
        statement both read tags, and the tags are right — so the only witness
        was the account balance.

        The invoice side states the intent, so it is copied rather than
        configured: same ``factor_percent``, same account. Historical rate
        clones inherit the defect from whatever they were cloned from and are
        fixed by the same pass, which is why this runs over every tax rather
        than a list of four xmlids.

        Deliberately does NOT touch the mirror case, ``0% EU S``, whose refund
        side names 343221 where the invoice side names nothing. That one posts
        100 % of a zero rate and moves no money; changing it would be a guess
        about intent with nothing measurable behind it.

        Idempotent: a leg that already has an account is left alone.
        """
        Tax = self.env["account.tax"].with_context(active_test=False)
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            for tax in Tax.search([("company_id", "=", company.id)]):
                invoice = {
                    line.factor_percent: line.account_id
                    for line in tax.invoice_repartition_line_ids
                    if line.repartition_type == "tax" and line.account_id
                }
                for line in tax.refund_repartition_line_ids:
                    if line.repartition_type != "tax" or line.account_id:
                        continue
                    account = invoice.get(line.factor_percent)
                    if account:
                        line.account_id = account
                        touched += 1
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s refund repartition account(s) "
                    "restored on %s", touched, company.display_name,
                )
        return touched

    def _cz_build_selfassessed_deduction(self, tax, document_type, base, legs):
        """Build the deduction leg `l10n_cz` leaves off ř. 7/8, or nothing.

        A self-assessed tax has TWO legs: the liability you declare and the
        deduction you claim, and they cancel — because the supplier charges no
        VAT, so nothing extra is owed to anybody. `l10n_cz` models EU
        acquisitions that way and models **import of goods with one leg only**.

        Measured on the shipped Czech chart, the same 1 000 CZK vendor bill::

            21% EU G   untaxed 1000.00  tax   0.00  TOTAL 1000.00
            21% EX G   untaxed 1000.00  tax 210.00  TOTAL 1210.00

        So Odoo asks the user to pay a supplier 1 210 against a 1 000 invoice.
        That is a wrong PAYABLE, not a reporting nicety, and it is wrong on its
        own terms whatever one concludes about ř43/44. The sibling `21% EX S`
        (services, ř. 12/13) already carries the leg, so goods and services
        currently disagree for no reason the form supports — ř43/44 reads "Ze
        zdanitelných plnění vykázaných na řádcích **3 až 13**", which contains
        7 and 8.

        It also breaks the document. With nothing to cancel the computed tax,
        the move stops balancing and Odoo silently adds an automatic balancing
        line: on a real agenda that put 912.87 onto 261000 *Peníze na cestě*,
        an account the source never touched.

        ⚠️ The account is taken from a SIBLING tax of the same rate that
        already has the two-leg shape — on the Czech chart that is the intra-EU
        acquisition, whose negative leg sits on the output account while the
        positive sits on the input one, so the liability and the deduction stay
        separately visible. Where no sibling exists the leg is put on the
        positive leg's own account, which still cancels correctly and is what
        the source systems themselves do; guessing an account code from
        another by string surgery is the one thing not done here.

        Returns the created line, or an empty recordset when the shape is not
        the one this repairs. Idempotent: it only ever fires on a tax with
        exactly one tax leg.
        """
        self.ensure_one()
        if len(legs) != 1 or not any(
            t.name in CZ_SELFASSESSED_NO_LEG for t in base.tag_ids
        ):
            return self.env["account.tax.repartition.line"]
        siblings = self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "=", self.id),
            ("type_tax_use", "=", tax.type_tax_use),
            ("amount", "=", tax.amount),
            ("amount_type", "=", tax.amount_type),
            ("id", "!=", tax.id),
        ])
        account = next(
            (rep.account_id
             for other in siblings
             # ⚠️ The sibling must be self-assessed ITSELF, and the leg must be
             # for the same document type. Without the first, an ordinary
             # purchase tax at the same rate qualifies and lends an account
             # that means something else; without the second, an invoice leg
             # can be built from a refund leg's account. They coincide on the
             # Czech chart, which is exactly why neither would have been
             # noticed here. Raised by a GPT-5.3-Codex review.
             if any(t.name in CZ_SELFASSESSED_BAND
                    for t in other.repartition_line_ids.filtered(
                        lambda r: r.repartition_type == "base").tag_ids)
             for rep in other.repartition_line_ids
             if rep.repartition_type == "tax"
             and rep.document_type == document_type
             and rep.factor_percent < 0
             and rep.account_id),
            legs.account_id,
        )
        return self.env["account.tax.repartition.line"].create({
            "tax_id": tax.id,
            "document_type": document_type,
            "repartition_type": "tax",
            "factor_percent": -100.0,
            "account_id": account.id if account else False,
            # Mirror the leg it is cancelling rather than relying on a default:
            # l10n_cz marks both tax legs of a reverse charge for the closing,
            # and a leg left out of it would quietly skip the VAT closing entry.
            "use_in_tax_closing": legs[:1].use_in_tax_closing,
            "sequence": max(legs.mapped("sequence") or [1]) + 1,
        })

    def _cz_tag_selfassessed_deduction(self):
        """Tag the deduction leg of every self-assessed Czech purchase tax.

        `l10n_cz` tags only the DECLARATION: a reverse charge or intra-EU
        acquisition carries ``VAT 3 Base``/``VAT 3 Tax`` on its base and +100
        legs and leaves the **−100 leg bare**, so the deduction the taxpayer is
        entitled to reaches no line of the return. Measured against 59 filed
        Řádné returns of a real Czech company, ř43 and ř44 computed 0.00 in
        **every** period against filed figures totalling 94.5M of base and
        14 534 001.54 of tax — while the output side of the same returns agreed
        to within 0.03 %.

        Confirmed with a second opinion (gpt-5.3-codex) before building:
        ř43/ř44 are the deduction of tax self-assessed on ř3–13, split
        základní/snížená, and they DO require a base as well as a tax figure;
        tagging the −100 leg is the right mechanism rather than deriving the
        deduction as an aggregate of ř3–13, because a partial or denied
        deduction makes that aggregate wrong; and the base repartition line
        needs the deduction base tag IN ADDITION to the declaration one.

        The band comes from the declaration tag the tax already carries, not
        from its rate — see ``CZ_SELFASSESSED_BAND`` — so a chart that adds a
        rate is handled without touching this.

        ``odkr_zdp*`` (krácený odpočet) stays manual on purpose: a partial
        claim is the taxpayer's coefficient, not a property of the tax.

        Idempotent: a leg already carrying its deduction tag is left alone.
        """
        Tax = self.env["account.tax"].with_context(active_test=False)
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            taxes = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
            ])
            for tax in taxes:
                for document_type, reps in (
                    ("invoice", tax.invoice_repartition_line_ids),
                    ("refund", tax.refund_repartition_line_ids),
                ):
                    base = reps.filtered(lambda r: r.repartition_type == "base")
                    legs = reps.filtered(lambda r: r.repartition_type == "tax")
                    line = next(
                        (CZ_SELFASSESSED_BAND[t.name]
                         for t in base.tag_ids
                         if t.name in CZ_SELFASSESSED_BAND),
                        None,
                    )
                    if not line:
                        continue
                    if len(legs) < 2:
                        # `l10n_cz` declares ř. 7/8 with ONE leg, so there is
                        # nothing to tag until one is built. See
                        # _cz_build_selfassessed_deduction for why that is a
                        # defect rather than a choice.
                        built = company._cz_build_selfassessed_deduction(
                            tax, document_type, base, legs)
                        if not built:
                            continue
                        touched += 1
                        legs |= built
                    base_tag = company._cz_deduction_tag(line, "Base")
                    total_tag = company._cz_deduction_tag(line, "Total")
                    deduction = legs.filtered(
                        lambda r: r.factor_percent < 0)[:1]
                    if not deduction:
                        continue
                    if base_tag not in base.tag_ids:
                        base.tag_ids = [(4, base_tag.id)]
                        touched += 1
                    if total_tag not in deduction.tag_ids:
                        deduction.tag_ids = [(4, total_tag.id)]
                        touched += 1
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s repartition tag(s) added for the "
                    "ř43/ř44 deduction on %s", touched, company.display_name,
                )
        return touched


#: A purchase tax earns a *Majetek* twin exactly when the acquisition it
#: models is deductible on ř. 40–44, because ř. 47 reports the asset share of
#: **that** deduction — "Hodnota pořízeného majetku vymezeného v § 4 odst. 4
#: písm. d) a e)", read against ř. 46 above it.
#:
#: The source tax already says which: ř40/ř41 for an ordinary domestic
#: purchase, and one of the ř3–ř13 declaration lines for a self-assessed one,
#: whose deduction this module puts on ř43/ř44. So the set is derived from
#: ``CZ_SELFASSESSED_BAND``, and a chart that adds a rate gets its twins
#: without a line changing here.
#:
#: Three of the shipped purchase taxes are therefore left WITHOUT a twin, and
#: each absence is a decision:
#:
#: * ``21% Vehicle`` (ř. 9, pořízení nového dopravního prostředku) — a new
#:   means of transport is an asset by any reading, but this module
#:   deliberately does not claim its ř43/44 deduction (see
#:   ``CZ_SELFASSESSED_NO_LEG``). Reporting an asset on ř. 47 whose deduction
#:   appears nowhere in ř. 40–46 would make the two rows contradict each other.
#: * ``0% EX G.Custom`` (ř. 42, daň zaplacená celnímu orgánu) — an imported
#:   machine is a textbook ř. 47 case, but `l10n_cz` ships this tax at **0 %**,
#:   so its ``VAT 42 Total`` computes 0.00 and a twin would file an asset base
#:   against no tax. The defect is upstream in ř. 42 and is not fixed by
#:   duplicating it.
#: * ``0% EX G`` (ř. 32, osvobozené dovozy) — exempt, so nothing is deducted
#:   and nothing belongs on ř. 47.
CZ_ASSET_SOURCE_TAGS = frozenset(CZ_SELFASSESSED_BAND) | {
    "VAT 40 Base", "VAT 41 Base",
}

#: Suffixed, not prefixed. ``_cssk_historic_tax_name`` substitutes the LEADING
#: rate token, so a twin named ``Majetek 21% G`` would never acquire its
#: historical rates — and the whole point of following the chart's
#: ``<rate>% <qualifier>`` shape is that the historic generator then clones the
#: twins for free, across all seven Czech rate changes since 2004.
#:
#: Czech rather than English because it is the form's own word for the thing
#: (ř. 47 "...pořízeného **majetku**..."), it is what the Vario and Pohoda tax
#: position tables call it, and it is the word the accountant choosing it from
#: a dropdown is looking for: a term that IS the statute's own stays in the
#: national language, untranslated, while generic UI text is English.
CZ_ASSET_SUFFIX = "Majetek"


class ResCompanyCzAssetAcquisition(models.Model):
    _inherit = "res.company"

    def _cz_asset_acquisition_tag_legs(self, tax, base_tag, total_tag):
        """Put the ř. 47 tags on one twin. Returns the number of changes.

        ``VAT 47 Base`` goes on the base repartition and ``VAT 47 Total`` on
        the **positive** tax leg(s), on the invoice and refund sides alike so a
        credit note takes the asset back off the row.

        ⚠️ The positive leg, specifically, and that is the whole reason this
        design works without touching the line definitions. ``od_maj`` reads
        ``VAT 47 Total`` **unsigned**, so the tag has to sit on a leg whose raw
        balance is positive on a vendor bill — the +100 leg, a debit. The −100
        leg of a self-assessed tax is a credit, and tagging it there would file
        ř. 47 negative, which is what happened to ř43/ř44 before their formulas
        were signed (see ``_cz_tag_selfassessed_deduction``).

        ⚠️ **Every** positive leg, not the first. A tax that splits its
        deduction — the krácený-odpočet shape, +60 deductible and +40 not —
        has two, and ř. 47 asks for the acquisition "v plné výši", the full
        value. Taking ``[:1]`` would file 60 % of an asset's tax and nothing
        would disagree with it.

        Idempotent: a line already carrying its tag is left alone.
        """
        self.ensure_one()
        touched = 0
        for reps in (tax.invoice_repartition_line_ids,
                     tax.refund_repartition_line_ids):
            base = reps.filtered(lambda r: r.repartition_type == "base")
            legs = reps.filtered(
                lambda r: r.repartition_type == "tax" and r.factor_percent > 0)
            for line, tag in ((base, base_tag), (legs, total_tag)):
                for rep in line:
                    if tag not in rep.tag_ids:
                        rep.tag_ids = [(4, tag.id)]
                        touched += 1
        return touched

    def _cz_suffix_every_translation(self, source, twin):
        """Suffix the twin's name in EVERY language the source has one in.

        ``copy()`` carries the source's translations wholesale and the ``name``
        in the copy values overwrites only the language the pass happens to run
        under. Install under ``en_US`` and the Czech name of ``21% G Majetek``
        stays "21 % G" — the SOURCE's name — so the accountant picking a tax
        in Czech sees two entries reading "21 % G" and no way to tell which
        reports on ř. 47.

        Not a duplicate-creation bug: the twin is found by
        ``cz_asset_source_tax_id``, not by name. It is a dropdown the user
        cannot use, which on this form is nearly as bad.
        """
        self.ensure_one()
        field = twin._fields["name"]
        if not field.translate:
            return False
        stored = field._get_stored_translations(source) or {}
        values = {
            lang: "%s %s" % (value, CZ_ASSET_SUFFIX)
            for lang, value in stored.items()
            # ``_get_stored_translations`` carries bookkeeping keys beginning
            # with an underscore alongside the real languages.
            if value and not lang.startswith("_")
        }
        if not values:
            return False
        return twin.update_field_translations("name", values)

    def _cz_create_asset_acquisition_taxes(self):
        """Create (or adopt) the ``Majetek`` purchase taxes. Idempotent.

        ř. 47 has been computable since this module shipped — `l10n_cz`
        declares ``VAT 47 Base`` and ``VAT 47 Total`` in its tax report, and
        ``nar_maj``/``od_maj`` read them — and **no shipped tax carries
        either**, so the row filed 0.00 whatever the taxpayer bought. Checked
        against a Czech agenda's own filed returns for 11 periods between
        2021-09 and 2025-11, the row carried millions of crowns of base in
        every one of them.

        The missing fact is per-document and binary: whether a purchase is
        dlouhodobý majetek. Odoo has nowhere to put it — the asset models are
        downstream of the bill, and the VAT return is computed from
        repartition tags, which are a property of the TAX. So the tax is where
        it goes, exactly as the legacy systems this migrates from do it:
        Vario's tax position table has "Majetek", "Majetek 3" and
        "EU Majetek" beside its ordinary positions, and Pohoda the same.

        A twin is a ``copy()`` of its source, so the rate, the repartition
        shape, the accounts, the fiscal positions and the ř43/44 deduction
        tags are the source's by construction rather than by restatement —
        which is what keeps the two from drifting when the chart changes.

        ⚠️ ``original_tax_ids`` is rewired, in a second pass, and must be.
        ``account.fiscal.position._compute_tax_map`` builds
        ``{source: [destinations]}`` as a **list**, and ``map_tax`` returns
        every destination it finds. A copy of ``21% EU G`` inherits
        ``original_tax_ids = [21% G]``, so the Intra-Community position would
        map one domestic 21 % line onto BOTH ``21% EU G`` and
        ``21% EU G Majetek`` and self-assess the acquisition twice. Pointing
        each twin at its source's twin instead turns that defect into the
        feature: an EU asset purchase picked as ``21% G Majetek`` is remapped
        to ``21% EU G Majetek`` by the position, with no user action.

        ``replacing_tax_ids`` — the same relation read backwards — is cleared
        on a newly created twin for the mirror reason: inherited, it would
        make the twin a second SOURCE for the plain EU and EX destinations.

        An **adopted** twin — a tax somebody had already made by hand under
        the name this would generate — is treated the other way round
        throughout: links are added and none removed, on both ends. Replacing
        its list outright would silently discard a mapping that is the whole
        reason the user made the tax.

        Runs on install, on chart load and from a migration, and
        ``_cssk_create_historic_vat_taxes`` is called **after** it so the twins
        acquire their own historical rates. Safe to re-run: a tax already
        carrying the name this would generate is adopted — stamped and
        re-tagged — rather than duplicated.
        """
        Tax = self.env["account.tax"].with_context(active_test=False)
        total = 0
        for company in self:
            if company.chart_template != "cz":
                continue
            # ⚠️ Per company. Hoisted out of this loop, the second company
            # logs the first one's changes as its own.
            created = adopted = tagged = 0
            base_tag = company._cz_deduction_tag("47", "Base")
            total_tag = company._cz_deduction_tag("47", "Total")
            sources = Tax.search([
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "purchase"),
                # Current rates only. The historical clones are made FROM the
                # twins afterwards; twinning a clone as well would produce two
                # records for one concept, each named for one half of the other.
                ("cssk_historic_valid_from", "=", False),
                # Never twin a twin: "21% G Majetek Majetek".
                ("cz_asset_source_tax_id", "=", False),
            ])
            twins, fresh = {}, set()
            for source in sources:
                # A tax the chart has already replaced is history; see
                # _cssk_tax_is_superseded.
                if company._cssk_tax_is_superseded(source):
                    continue
                names = set(source.invoice_repartition_line_ids.filtered(
                    lambda r: r.repartition_type == "base"
                ).tag_ids.mapped("name"))
                if not (names & CZ_ASSET_SOURCE_TAGS):
                    continue
                if source.amount_type == "group" or source.children_tax_ids:
                    # A group tax's children carry the repartition, and
                    # ``copy()`` points the twin at the ORIGINAL children — so
                    # the twin would apply the untwinned children and reach
                    # ř. 47 on none of them. `l10n_cz` ships no such purchase
                    # tax; a user who builds one gets a warning rather than a
                    # twin that silently reports nothing.
                    _logger.warning(
                        "l10n_cz_vat_return: %s is a group tax, so no ř47 twin "
                        "was made — its children would have to be twinned "
                        "first", source.name,
                    )
                    continue
                # ⚠️ Found by the FIELD, not by the name. ``name`` is
                # translatable and the chart ships ``name@cs``, so
                # ``source.name`` reads "21 % G" under cs_CZ and "21% G" under
                # en_US: a name-keyed lookup finds nothing on the second
                # language and creates a duplicate twin for every tax. The
                # field is why it exists. Raised by a GPT-5.3-Codex review.
                existing = Tax.search([
                    ("company_id", "=", company.id),
                    ("cz_asset_source_tax_id", "=", source.id),
                    ("cssk_historic_valid_from", "=", False),
                ], limit=1)
                name = "%s %s" % (source.name, CZ_ASSET_SUFFIX)
                if not existing:
                    # Nothing of ours yet. A tax somebody made by hand under
                    # the name this would generate is adopted instead of
                    # duplicated — the same courtesy the historical-rate
                    # generator extends.
                    #
                    # ⚠️ Keyed on exactly what ``_constrains_name`` is keyed
                    # on — company root, name, type_tax_use, tax_scope and
                    # country_id. A narrower search adopts a tax the
                    # constraint does not consider a duplicate at all (a
                    # service-scoped one, say); a wider one leaves a real
                    # collision unseen, and then ``copy()`` raises "Tax names
                    # must be unique!" and takes the whole chart load or
                    # upgrade down with it. Both halves of that were found by
                    # a negative control after a GPT-5.3-Codex review.
                    taken = Tax.search([
                        ("company_id", "child_of", company.root_id.id),
                        ("name", "=", name),
                        ("type_tax_use", "=", source.type_tax_use),
                        ("tax_scope", "=", source.tax_scope),
                        ("country_id", "=", source.country_id.id),
                    ])
                    free = taken.filtered(
                        lambda t: not t.cz_asset_source_tax_id)[:1]
                    if free:
                        existing = free
                    elif taken:
                        # The name is spoken for by another source's twin, so
                        # neither adopting nor creating is possible. Say so and
                        # leave this source without a twin rather than abort.
                        _logger.warning(
                            "l10n_cz_vat_return: %s is already the ř47 twin of "
                            "%s, so %s has none — rename one of them",
                            taken[0].name,
                            taken[0].cz_asset_source_tax_id.name, source.name,
                        )
                        continue
                if existing:
                    existing.cz_asset_source_tax_id = source.id
                    twins[source] = existing
                    adopted += 1
                else:
                    existing = source.copy({
                        "name": name,
                        "cz_asset_source_tax_id": source.id,
                    })
                    company._cz_suffix_every_translation(source, existing)
                    existing.replacing_tax_ids = [(5,)]
                    twins[source] = existing
                    fresh.add(source)
                    created += 1
                tagged += company._cz_asset_acquisition_tag_legs(
                    existing, base_tag, total_tag)
            for source, twin in twins.items():
                wanted = [
                    twins[other].id
                    for other in source.original_tax_ids
                    if other in twins
                ]
                if source in fresh:
                    # Freshly created: the inherited list is the source's and
                    # is wrong for the twin, so replace it outright.
                    if set(wanted) != set(twin.original_tax_ids.ids):
                        twin.original_tax_ids = [(6, 0, wanted)]
                else:
                    # Adopted: somebody made this tax by hand and whatever it
                    # replaces may be deliberate. Add what is missing and
                    # remove nothing — the same rule the rest of this module
                    # follows, and the reason `replacing_tax_ids` is not
                    # cleared on an adopted twin either.
                    missing = set(wanted) - set(twin.original_tax_ids.ids)
                    if missing:
                        twin.original_tax_ids = [(4, i) for i in missing]
            total += created + adopted
            if created or adopted:
                _logger.info(
                    "l10n_cz_vat_return: %s asset-acquisition tax(es) created, "
                    "%s adopted, %s ř47 tag(s) placed on %s",
                    created, adopted, tagged, company.display_name,
                )
        return total

    def _cz_asset_acquisition_taxes(self):
        """Every ``Majetek`` tax of these companies, archived ones included."""
        return self.env["account.tax"].with_context(active_test=False).search([
            ("company_id", "in", self.ids),
            ("cz_asset_source_tax_id", "!=", False),
        ])
