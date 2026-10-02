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


class ResCompany(models.Model):
    _inherit = "res.company"

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
        touched = 0
        for company in self:
            if company.chart_template != "cz":
                continue
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
            if touched:
                _logger.info(
                    "l10n_cz_vat_return: %s intra-Community purchase tax "
                    "mapping(s) added on %s", touched, company.display_name,
                )
        return touched

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
