# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from ..models.res_company import CZ_ASSET_SOURCE_TAGS


@tagged("post_install", "-at_install")
class TestCzAssetAcquisition(AccountTestInvoicingCommon):
    """ř. 47 — hodnota pořízeného majetku vymezeného v § 4 odst. 4 písm. d) a e).

    ``l10n_cz`` declares ``VAT 47 Base`` and ``VAT 47 Total`` in its tax report
    and ships **no tax carrying either**, so the row filed 0.00 whatever the
    taxpayer bought. Checked against a Czech agenda's own filed returns for 11
    periods between 2021-09 and 2025-11, the row carried millions of crowns of
    base in every one of them.

    The figures themselves are deliberately not here. They are a customer's
    filed tax data and this directory ships whole into a published
    repository; the tests below use synthetic amounts, which is all they need.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_vat_return.dphdp3_type_B")
        cls.company._cz_tag_selfassessed_deduction()
        cls.company._cz_map_intra_community_purchase_taxes()
        cls.company._cz_create_asset_acquisition_taxes()

    # -- helpers ----------------------------------------------------------

    def _taxes(self, *domain):
        return self.env["account.tax"].with_context(active_test=False).search(
            [("company_id", "=", self.company.id)] + list(domain))

    def _names(self, reps):
        return set(reps.tag_ids.mapped("name"))

    def _base_tags(self, tax):
        return self._names(tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "base"))

    def _twin(self, source_xmlid):
        """The Majetek twin of one chart tax, resolved by the chart's xmlid.

        ⚠️ Not by name and not by tag. ``AccountTestInvoicingCommon`` seeds its
        own duplicates of the domestic taxes — ``21% G (copy)`` — which carry
        the same ``VAT 40 Base`` and are twinned by the same rule, quite
        correctly: a purchase tax a user duplicates deserves a ř. 47 twin as
        much as the original. So "the 21 % domestic goods twin" is two taxes in
        a test database, and selecting by tag alone silently picks whichever
        the search happens to return first.
        """
        source = self.env["account.chart.template"].with_company(
            self.company).ref(source_xmlid)
        self.assertTrue(source, source_xmlid)
        twin = self._taxes(
            ("cz_asset_source_tax_id", "=", source.id),
            ("cssk_historic_valid_from", "=", False),
        )
        self.assertEqual(
            len(twin), 1,
            "expected exactly one current-rate twin of %s, got %s"
            % (source_xmlid, twin.mapped("name")))
        return twin

    def _return(self, date_from="2025-06-01", date_to="2025-06-30"):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "period_type": "month",
            "date_from": date_from, "date_to": date_to,
        })
        ret.action_compute_lines()
        return ret

    def _v(self, ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def _bill(self, tax, price=1000.0, move_type="in_invoice"):
        bill = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.partner_a.id,
            # DUZP explicitly: the return picks its period by the tax point,
            # and l10n_cz defaults it to the day the record is created.
            "invoice_date": "2025-06-15", "date": "2025-06-15",
            "taxable_supply_date": "2025-06-15",
            "invoice_line_ids": [Command.create({
                "name": "a machine", "quantity": 1, "price_unit": price,
                "tax_ids": [Command.set(tax.ids)]})],
        })
        bill.action_post()
        return bill

    # -- the twins exist, and the right ones ------------------------------

    def test_every_deductible_purchase_tax_has_an_asset_twin(self):
        """Derived from the deduction the tax already claims, not enumerated.

        A purchase tax earns a twin exactly when its acquisition is deductible
        on ř. 40–44, because ř. 47 reports the asset share of that deduction.
        Asserting it over the whole chart is what stops the set being replaced
        by a list of xmlids, which is the version that silently stops covering
        a rate the chart adds.
        """
        current = self._taxes()
        sources = current.filtered(
            lambda t: t.type_tax_use == "purchase"
            and not t.cssk_historic_valid_from
            and not t.cz_asset_source_tax_id
            and (self._base_tags(t) & CZ_ASSET_SOURCE_TAGS))
        self.assertTrue(sources, "no deductible purchase tax was examined")
        twinned = self.company._cz_asset_acquisition_taxes().mapped(
            "cz_asset_source_tax_id")
        missing = [t.name for t in sources if t not in twinned]
        self.assertFalse(
            missing,
            "deductible purchase taxes with no way to report on ř. 47: %s"
            % (missing,))

    def test_a_twin_keeps_its_source_s_declaration_and_deduction(self):
        """The twin must change ř. 47 and nothing else.

        It is a ``copy()`` precisely so that the rate, the repartition shape,
        the accounts and the ř43/44 deduction tags are the source's by
        construction. If a twin declared on a different line from its source,
        picking it would silently restate the return.
        """
        for twin in self.company._cz_asset_acquisition_taxes().filtered(
                lambda t: not t.cssk_historic_valid_from):
            source = twin.cz_asset_source_tax_id
            self.assertEqual(twin.amount, source.amount, twin.name)
            self.assertEqual(twin.type_tax_use, source.type_tax_use, twin.name)
            self.assertEqual(
                self._base_tags(twin) - {"VAT 47 Base"},
                self._base_tags(source) - {"VAT 47 Base"},
                "%s declares on different lines from %s"
                % (twin.name, source.name))

    def test_the_taxes_left_without_a_twin_are_the_ones_that_should_be(self):
        """Three absences, each a decision — see CZ_ASSET_SOURCE_TAGS.

        ř. 9 (new means of transport) because this module deliberately does
        not claim its ř43/44 deduction, so an asset on ř. 47 would contradict
        ř. 46; ř. 42 (daň zaplacená celnímu orgánu) because `l10n_cz` ships
        that tax at 0 %, so a twin would file an asset base against no tax;
        ř. 32 (osvobozené dovozy) because nothing is deducted at all.
        """
        twinned_tags = set()
        for twin in self.company._cz_asset_acquisition_taxes():
            twinned_tags |= self._base_tags(twin.cz_asset_source_tax_id)
        for tag in ("VAT 9 Base", "VAT 42 Base", "VAT 32"):
            self.assertNotIn(
                tag, twinned_tags,
                "%s must not reach ř. 47 — see CZ_ASSET_SOURCE_TAGS" % tag)

    def test_the_r47_tags_sit_on_the_base_and_on_the_positive_leg(self):
        """``od_maj`` reads ``VAT 47 Total`` UNSIGNED.

        So the tag has to sit on a leg whose raw balance is positive on a
        vendor bill — the +100 leg, a debit. On the −100 leg of a
        self-assessed tax it would file ř. 47 negative, which is exactly what
        happened to ř43/ř44 before their formulas were signed.
        """
        twins = self.company._cz_asset_acquisition_taxes()
        self.assertTrue(twins)
        for twin in twins:
            for reps in (twin.invoice_repartition_line_ids,
                         twin.refund_repartition_line_ids):
                base = reps.filtered(lambda r: r.repartition_type == "base")
                legs = reps.filtered(lambda r: r.repartition_type == "tax")
                self.assertIn("VAT 47 Base", self._names(base), twin.name)
                positive = legs.filtered(lambda r: r.factor_percent > 0)
                negative = legs.filtered(lambda r: r.factor_percent < 0)
                self.assertTrue(positive, twin.name)
                for rep in positive:
                    self.assertIn(
                        "VAT 47 Total", self._names(rep),
                        "%s: the +%g leg must carry the ř47 total"
                        % (twin.name, rep.factor_percent))
                for rep in negative:
                    self.assertNotIn(
                        "VAT 47 Total", self._names(rep),
                        "%s: the deduction leg must NOT carry it, or ř. 47 "
                        "files negative" % twin.name)

    # -- figures ----------------------------------------------------------

    def test_a_domestic_asset_purchase_reports_on_both_r40_and_r47(self):
        """ř. 47 is a memo row INSIDE the deduction, not instead of it.

        "Hodnota pořízeného majetku" reports how much of ř. 40–46 was assets,
        so a machine bought domestically has to appear on ř. 40 exactly as it
        would without the twin, AND on ř. 47. A twin that moved the deduction
        off ř. 40 would file a return that understates the claim.
        """
        twin = self._twin("l10n_cz_21_receipt_domestic_supplies")
        self._bill(twin, price=1000.0)
        ret = self._return()
        self.assertEqual(self._v(ret, "pln23"), 1000.0, "ř40 base")
        self.assertEqual(self._v(ret, "odp_tuz23_nar"), 210.0, "ř40 deduction")
        self.assertEqual(self._v(ret, "nar_maj"), 1000.0, "ř47 base")
        self.assertEqual(self._v(ret, "od_maj"), 210.0, "ř47 tax")

    def test_an_eu_asset_acquisition_reports_r3_r43_and_r47(self):
        """The self-assessed case, where the sign is the whole difference.

        An intra-Community acquisition of a machine declares the tax on ř. 3,
        deducts it on ř. 43 — the −100 leg, which the form reads negated — and
        reports the value on ř. 47 from the +100 leg, which it does not. All
        three must come out positive.
        """
        twin = self._twin("l10n_cz_21_acquisition_goods_eu")
        self._bill(twin, price=2000.0)
        ret = self._return()
        self.assertEqual(self._v(ret, "p_zb23"), 2000.0, "ř3 base")
        self.assertEqual(self._v(ret, "dan_pzb23"), 420.0, "ř3 tax")
        self.assertEqual(self._v(ret, "od_zdp23"), 420.0, "ř43 deduction")
        self.assertEqual(self._v(ret, "nar_maj"), 2000.0, "ř47 base")
        self.assertEqual(
            self._v(ret, "od_maj"), 420.0,
            "ř47 must be positive — it reads VAT 47 Total unsigned, so the "
            "tag belongs on the +100 leg")

    def test_a_credit_note_takes_the_asset_back_off_r47(self):
        """Returning the machine un-reports it, and nets to zero in-period.

        The refund repartition is tagged for the same reason the invoice one
        is: a correction that reduced ř. 40 while leaving ř. 47 standing would
        file an asset value the deduction no longer supports.
        """
        twin = self._twin("l10n_cz_21_receipt_domestic_supplies")
        self._bill(twin, price=1000.0)
        self._bill(twin, price=1000.0, move_type="in_refund")
        ret = self._return()
        self.assertEqual(self._v(ret, "nar_maj"), 0.0, "ř47 base nets to zero")
        self.assertEqual(self._v(ret, "od_maj"), 0.0, "ř47 tax nets to zero")

    def test_an_ordinary_purchase_still_reports_nothing_on_r47(self):
        """The negative control. ř. 47 is opt-in, by picking the twin.

        Without it the twins would turn every purchase into an asset, which is
        a wrong return in the other direction and would not be caught by any
        test that only ever uses a twin.
        """
        source = self._twin("l10n_cz_21_receipt_domestic_supplies")\
            .cz_asset_source_tax_id
        self._bill(source, price=1000.0)
        ret = self._return()
        self.assertEqual(self._v(ret, "pln23"), 1000.0, "ř40 still reports")
        self.assertEqual(self._v(ret, "nar_maj"), 0.0)
        self.assertEqual(self._v(ret, "od_maj"), 0.0)

    # -- the fiscal position, and the double-tax regression ---------------

    def test_the_intra_community_position_maps_a_twin_to_exactly_one_tax(self):
        """``map_tax`` returns a LIST, and an inherited mapping doubles it.

        ``_compute_tax_map`` builds ``{source: [destinations]}`` from every
        tax whose ``original_tax_ids`` names the source. A twin of ``21% EU G``
        inherits ``original_tax_ids = [21% G]`` from the copy, so the
        Intra-Community position would map one domestic 21 % line onto BOTH
        ``21% EU G`` and ``21% EU G Majetek`` — self-assessing the acquisition
        twice, on a document that balances and posts.
        """
        position = self.env["account.fiscal.position"].search([
            ("company_id", "=", self.company.id),
            ("country_group_id", "!=", False),
        ])
        domestic = self._twin("l10n_cz_21_receipt_domestic_supplies")
        eu_twin = self._twin("l10n_cz_21_acquisition_goods_eu")
        plain = domestic.cz_asset_source_tax_id
        for pos in position:
            mapped = pos.map_tax(domestic)
            self.assertLessEqual(
                len(mapped), 1,
                "%s maps %s onto %s — more than one destination means the "
                "acquisition is self-assessed twice"
                % (pos.display_name, domestic.name, mapped.mapped("name")))
            self.assertLessEqual(
                len(pos.map_tax(plain)), 1,
                "%s maps the PLAIN %s onto %s"
                % (pos.display_name, plain.name, pos.map_tax(plain).mapped("name")))
        intra = position.filtered(lambda p: eu_twin in p.tax_ids)
        self.assertTrue(
            intra, "the Intra-Community position should carry the EU twin")
        self.assertEqual(
            intra[0].map_tax(domestic), eu_twin,
            "an EU asset purchase picked as %s must be remapped to %s"
            % (domestic.name, eu_twin.name))

    # -- history, and idempotence -----------------------------------------

    def test_the_twins_acquire_the_historical_rates(self):
        """A twin is named ``<rate>% <qualifier> Majetek`` for this reason.

        ``_cssk_historic_tax_name`` substitutes the LEADING rate token, so the
        historic generator clones the twins across all seven Czech rate
        changes since 2004 without knowing they exist — but only while the
        rate stays in front. ``Majetek 21% G`` would acquire nothing.
        """
        self.company._cssk_create_historic_vat_taxes()
        historic = self.company._cz_asset_acquisition_taxes().filtered(
            lambda t: t.cssk_historic_valid_from)
        self.assertTrue(
            historic,
            "the twins must get historical rates too, or a history import has "
            "no way to report a 15 % asset purchase on ř. 47")
        for tax in historic:
            self.assertFalse(
                tax.active, "a historical rate must be archived: %s" % tax.name)
            self.assertIn(
                "VAT 47 Base", self._base_tags(tax),
                "%s lost the ř47 tag in the clone" % tax.name)
        rates = set(historic.mapped("amount"))
        self.assertIn(20.0, rates)
        self.assertIn(15.0, rates)

    def test_running_it_twice_adds_nothing(self):
        """It runs on install, on chart load and from a migration."""
        before = self.company._cz_asset_acquisition_taxes()
        self.company._cz_create_asset_acquisition_taxes()
        after = self.company._cz_asset_acquisition_taxes()
        self.assertEqual(
            after, before,
            "a second run created %s" % ((after - before).mapped("name"),))

    def test_a_twin_is_never_twinned(self):
        """Otherwise a third run ships ``21% G Majetek Majetek``."""
        self.company._cz_create_asset_acquisition_taxes()
        self.company._cz_create_asset_acquisition_taxes()
        doubled = self.company._cz_asset_acquisition_taxes().filtered(
            lambda t: t.cz_asset_source_tax_id.cz_asset_source_tax_id)
        self.assertFalse(doubled, doubled.mapped("name"))

    # -- what a second opinion asked about --------------------------------

    def _czech_source(self, xmlid="l10n_cz_21_receipt_domestic_supplies"):
        """A source tax with a REAL Czech name, and proof that it took.

        ``cs_CZ`` is not active while the suite installs, so the chart's
        ``name@cs`` never reaches the database and
        ``source.with_context(lang="cs_CZ").name`` just falls back to English.
        Both language tests below passed against deliberately broken code
        until this built the scenario instead of assuming it.
        """
        self.env["res.lang"]._activate_lang("cs_CZ")
        source = self.env["account.chart.template"].with_company(
            self.company).ref(xmlid)
        source.update_field_translations("name", {"cs_CZ": "21 % G"})
        self.assertEqual(
            source.with_context(lang="cs_CZ").name, "21 % G",
            "the scenario did not build: the source has no Czech name")
        return source

    def test_a_second_language_does_not_duplicate_the_twins(self):
        """``name`` is translatable and the chart ships ``name@cs``.

        So ``source.name`` reads "21 % G" under cs_CZ and "21% G" under
        en_US, and a name-keyed lookup finds nothing the second time round and
        twins the whole chart again. Raised by a GPT-5.3-Codex review of this
        change; the fix is to look the twin up by ``cz_asset_source_tax_id``.
        """
        self._czech_source()
        before = self.company._cz_asset_acquisition_taxes()
        self.company.with_context(lang="cs_CZ")\
            ._cz_create_asset_acquisition_taxes()
        after = self.company._cz_asset_acquisition_taxes()
        self.assertEqual(
            after, before,
            "a run in another language created %s"
            % ((after - before).mapped("name"),))

    def test_a_twin_is_named_in_every_language_the_source_has(self):
        """Otherwise the Czech dropdown shows two taxes both reading "21 % G".

        ``copy()`` carries the source's translations and the name in the copy
        values overwrites only the active language, so the twin kept the
        SOURCE's Czech name. Nothing breaks; the user simply cannot tell the
        two apart on the one form where it matters.
        """
        source = self._czech_source()
        self._twin("l10n_cz_21_receipt_domestic_supplies").unlink()
        self.company._cz_create_asset_acquisition_taxes()
        twin = self._twin("l10n_cz_21_receipt_domestic_supplies")
        for lang in ("en_US", "cs_CZ"):
            twin_name = twin.with_context(lang=lang).name
            self.assertNotEqual(
                twin_name, source.with_context(lang=lang).name,
                "in %s the twin and its source are both called %r"
                % (lang, twin_name))
            self.assertTrue(
                twin_name.endswith(" Majetek"),
                "in %s the twin is called %r" % (lang, twin_name))

    def test_a_tax_already_twinned_elsewhere_is_not_rebound(self):
        """Adoption is by name, so it has to refuse to steal another's twin.

        Rebinding would orphan the source it belonged to and silently
        re-point its replacement links. Raised by a GPT-5.3-Codex review.
        """
        twin = self._twin("l10n_cz_21_receipt_domestic_supplies")
        other = self._twin("l10n_cz_21_receipt_domestic_services")
        original = twin.cz_asset_source_tax_id
        # Give the first twin the name the second would generate, then re-run.
        twin.name = "%s Majetek" % other.cz_asset_source_tax_id.name
        self.company._cz_create_asset_acquisition_taxes()
        self.assertEqual(
            twin.cz_asset_source_tax_id, original,
            "the twin of %s was rebound to %s"
            % (original.name, twin.cz_asset_source_tax_id.name))

    def test_a_group_tax_is_not_twinned(self):
        """``copy()`` points the twin at the ORIGINAL children.

        So a group tax's twin would apply the untwinned children and reach
        ř. 47 on none of them — a twin that reports nothing, which is worse
        than no twin. `l10n_cz` ships none, so this pins the guard.
        """
        source = self.env["account.chart.template"].with_company(
            self.company).ref("l10n_cz_21_receipt_domestic_supplies")
        group = source.copy({
            "name": "21% Group", "amount_type": "group",
            "children_tax_ids": [(6, 0, source.ids)],
            "cz_asset_source_tax_id": False,
        })
        group.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "base").tag_ids = [
                (4, self.company._cz_deduction_tag("40", "Base").id)]
        self.company._cz_create_asset_acquisition_taxes()
        self.assertFalse(
            self.company._cz_asset_acquisition_taxes().filtered(
                lambda t: t.cz_asset_source_tax_id == group),
            "a group tax must not be twinned")

    def test_a_name_collision_does_not_abort_the_run(self):
        """``_constrains_name`` raises, and a chart load would die with it.

        If the generated name is taken by another source's twin, the pass can
        neither adopt it (that would orphan the other source) nor create it
        (Odoo: "Tax names must be unique!"). It has to skip the source and say
        so. Found by negative-controlling the review fixes: the version that
        merely refused to adopt went on to ``copy()`` and took the whole
        upgrade down.
        """
        goods = self._twin("l10n_cz_21_receipt_domestic_supplies")
        other = self._twin("l10n_cz_21_receipt_domestic_services")
        wanted, scope = goods.name, goods.tax_scope
        # Free the name, then let the OTHER source's twin take it, matching on
        # everything `_constrains_name` keys on.
        goods.unlink()
        other.write({"name": wanted, "tax_scope": scope})
        with self.assertLogs(
                "odoo.addons.l10n_cz_vat_return.models.res_company",
                level="WARNING") as logs:
            self.company._cz_create_asset_acquisition_taxes()
        self.assertTrue(
            any("already the ř47 twin" in line for line in logs.output),
            "the collision must be reported, not swallowed: %s" % logs.output)
