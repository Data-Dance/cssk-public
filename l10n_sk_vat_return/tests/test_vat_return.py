import base64

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkVatReturn(TransactionCase):
    """Smoke tests for the SK VAT return country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "dokument")
        self.assertTrue(version.xml_schema_data, "DPH XSD not loaded")
        codes = set(version.line_def_ids.mapped("code"))
        self.assertIn("r03", codes)
        self.assertIn("r17", codes)


class TestSkVatReturnVintages(TransactionCase):
    """The two form vintages, and the boundary between them.

    The vzor changed on 1. 7. 2025 and the RATE changed on 1. 1. 2025, six
    months earlier — so January to June 2025 is the current rate on the old
    grid. That window is why the pre-July record exists and is not simply the
    2025 grid with an earlier date, which is what it used to be.
    """

    def _grid(self, xmlid):
        version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
        return version, set(version.line_def_ids.mapped("code"))

    def test_the_two_vintages_meet_without_a_gap_or_an_overlap(self):
        """A period must resolve to exactly one grid, and every period must.

        Measured evidence for the boundary, from the MRP agenda's 38 filed
        returns: r09/r10 carry a value in 15 periods from 2023-02 to 2025-06
        and r09b/r10b in 6 periods from 2025-07 to 2025-12. Not one r09 after
        June 2025, not one r09b before July.
        """
        old = self.env.ref("l10n_sk_vat_return.dph_version_2024")
        new = self.env.ref("l10n_sk_vat_return.dph_version_2025")
        self.assertEqual(str(old.valid_to), "2025-06-30")
        self.assertEqual(str(new.valid_from), "2025-07-01")
        self.assertFalse(new.valid_to, "the current vzor has no end date")

    def test_no_two_versions_of_one_country_overlap(self):
        """The invariant that actually decides which grid a return uses.

        Asserted per COUNTRY, and that qualifier is the whole point. The i6
        extractor's harness found two versions matching every Slovak period
        from January 2025 on, because `DPHDP3 2025` is Czech and open-ended —
        which is correct data and not a conflict, since a Slovak return never
        considers it. A domain that forgets `country_id` sees a clash that is
        not there; a country that genuinely overlaps itself makes the chosen
        grid depend on search order, which is a real one.
        """
        Version = self.env["cssk.vat.return.version"]
        by_country = {}
        for version in Version.search([]):
            by_country.setdefault(version.country_id, []).append(version)

        clashes = []
        for country, versions in by_country.items():
            for i, a in enumerate(versions):
                for b in versions[i + 1:]:
                    a_to = a.valid_to or "9999-12-31"
                    b_to = b.valid_to or "9999-12-31"
                    if str(a.valid_from) <= str(b_to) and \
                            str(b.valid_from) <= str(a_to):
                        clashes.append(
                            "%s: %s (%s..%s) overlaps %s (%s..%s)" % (
                                country.code, a.name, a.valid_from, a_to,
                                b.name, b.valid_from, b_to))
        self.assertFalse(
            clashes,
            "two versions of one country cover the same period, so which grid "
            "a return uses depends on search order: %s" % ("; ".join(clashes),))

    def test_each_vintage_renders_its_own_form_and_validates_against_it(self):
        """The pre-July version used the 2025 template and carried no schema.

        So it emitted the lettered elements DPHv21 does not have, and could
        only ever have validated against the wrong vzor — documented in the
        version data as a follow-up, and covering **18 of 24 periods** of the
        reference agenda, which is three quarters of the filed history.

        Asserted structurally rather than by exporting, because an export needs
        a company and a period: the version must bind ITS OWN template and ITS
        OWN schema, and the two vintages must not share either.
        """
        import base64
        import re
        old = self.env.ref("l10n_sk_vat_return.dph_version_2024")
        new = self.env.ref("l10n_sk_vat_return.dph_version_2025")

        self.assertTrue(old.xml_schema_data, "the pre-July version has no XSD")
        self.assertNotEqual(
            old.xml_schema_data, new.xml_schema_data,
            "each vzor must validate against its own schema")
        self.assertNotEqual(
            old.xml_template_ref_id, new.xml_template_ref_id,
            "each vzor must render its own element set")

        # The schema each version carries must be the one it claims.
        raw = base64.b64decode(old.xml_schema_data)
        self.assertIn(b"DPHv21", raw)
        self.assertNotIn(b"r09b", raw,
                         "DPHv21 has no lettered variants — wrong schema bound")

        # And the template must emit exactly the elements that schema declares.
        arch = old.xml_template_ref_id.arch or ""
        rendered = set(re.findall(r"<(r\d+[a-z]?)\b", arch))
        declared = set(re.findall(rb'element name="(r\d+[a-z]?)"', raw))
        declared = {d.decode() for d in declared}
        self.assertEqual(
            rendered - declared, set(),
            "the template emits elements DPHv21 does not have")
        self.assertEqual(
            declared - rendered, set(),
            "DPHv21 declares elements the template never emits")

    def test_r24_collects_the_received_side_of_a_section_25_correction(self):
        """The chart splits the § 25 BASE by side and the TAX not at all.

        `l10n_sk` puts tag `24` on the ordinary domestic sale rates and `24_PR`
        on the EU and reverse-charge taxes, while `25` is a single tag carried
        by both. That asymmetry is the argument: if `24_PR` belonged to another
        form line, there would be a `25_PR` for that line's tax. There is not.

        With a formula of `-24` alone, a self-assessed § 25 correction reports
        its tax on r25 and omits its base from r24 — the base-short/tax-correct
        signature seen four times on the MRP agenda, and filed: document 324057
        put −190.80 on r24 in a real return with its base line tagged `24_PR`.
        """
        sk = self.env.ref("base.sk")
        Tag = self.env["account.account.tag"]
        self.assertTrue(
            Tag._get_tax_tags("24_PR", sk.id),
            "the chart no longer defines 24_PR — re-check this mapping")
        self.assertFalse(
            Tag._get_tax_tags("25_PR", sk.id),
            "a 25_PR would mean 24_PR belongs to a line of its own, and the "
            "reasoning behind this formula would not hold")

        for xmlid in ("dph_version_2025", "dph_version_2024"):
            version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
            r24 = version.line_def_ids.filtered(lambda d: d.code == "r24")
            self.assertEqual(
                r24.tag_formula, "-24|+24_PR",
                "%s must collect both sides of a § 25 base correction, each with "
                "its own sign"
                % xmlid)

    def test_the_pre_july_grid_is_exactly_the_lines_dph2021_defines(self):
        """Against the official XSD shipped beside it, both ways.

        Both directions matter and they catch opposite mistakes: a line the
        XSD has and the grid lacks is a figure that silently never gets
        computed, and a line the grid has and the XSD lacks is the actual bug
        this vintage was created to fix — a document filing on a row that did
        not exist when it was raised.
        """
        import os
        import re

        from odoo.tools.misc import file_path

        path = file_path("l10n_sk_vat_return/data/dph2021.xsd")
        with open(path, encoding="utf-8") as handle:
            xsd_lines = set(re.findall(r'name="(r\d+[a-z]?)"', handle.read()))
        self.assertTrue(xsd_lines, "dph2021.xsd defines no r-elements — "
                                   "did the file move? (%s)" % os.path.basename(path))

        _version, codes = self._grid("dph_version_2024")
        grid = {c for c in codes if re.fullmatch(r"r\d+[a-z]?", c)}
        self.assertEqual(
            xsd_lines - grid, set(),
            "dph2021.xsd defines lines the pre-July grid never computes")
        self.assertEqual(
            grid - xsd_lines, set(),
            "the pre-July grid computes lines DPHv21 does not have — this is "
            "the defect the vintage exists to fix")

    # ------------------------------------------------------------------
    # The three vzory that precede 2021
    # ------------------------------------------------------------------
    LEGACY = (
        ("dph_version_2012", "dph2012.xsd", "2012-01-01", "2017-12-31"),
        ("dph_version_2018", "dph2018.xsd", "2018-01-01", "2019-12-31"),
        ("dph_version_2020", "dph2020.xsd", "2020-01-01", "2020-12-31"),
    )

    def test_every_published_vzor_has_a_version(self):
        """Five vzory exist and five are seeded.

        Probed across dph2009..dph2026 on 2026-09-09: 2012, 2018, 2020, 2021
        and 2025 answer 200 and every other year is a 404. Before this, a
        period earlier than 2021 resolved to NO version — not a wrong figure
        but no figure, the return refusing to compute.
        """
        for xmlid, schema, vfrom, vto in self.LEGACY:
            version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
            self.assertEqual(version.country_id.code, "SK")
            self.assertEqual(version.xml_root_element, "dokument")
            self.assertEqual(version.xml_schema_filename, schema)
            self.assertTrue(version.xml_schema_data, "%s XSD not loaded" % xmlid)
            self.assertEqual(str(version.valid_from), vfrom)
            self.assertEqual(str(version.valid_to), vto)

    def test_the_vintages_tile_every_period_since_2012(self):
        """No gap and no overlap, checked the way the return resolves it."""
        checks = [
            ("2012-01-01", "2012-03-31", "dph_version_2012"),
            ("2015-07-01", "2015-07-31", "dph_version_2012"),
            ("2017-12-01", "2017-12-31", "dph_version_2012"),
            ("2018-01-01", "2018-01-31", "dph_version_2018"),
            ("2019-12-01", "2019-12-31", "dph_version_2018"),
            ("2020-01-01", "2020-01-31", "dph_version_2020"),
            ("2020-12-01", "2020-12-31", "dph_version_2020"),
            ("2021-01-01", "2021-01-31", "dph_version_2024"),
            ("2025-06-01", "2025-06-30", "dph_version_2024"),
            ("2025-07-01", "2025-07-31", "dph_version_2025"),
        ]
        sk = self.env.ref("base.sk")
        for date_from, date_to, expected in checks:
            found = self.env["cssk.vat.return.version"].search([
                ("country_id", "=", sk.id),
                ("valid_from", "<=", date_to),
                "|", ("valid_to", "=", False), ("valid_to", ">=", date_from),
            ])
            self.assertEqual(
                len(found), 1,
                "%s..%s resolves to %s versions" % (date_from, date_to, len(found)))
            self.assertEqual(found, self.env.ref("l10n_sk_vat_return.%s" % expected),
                             "%s..%s reached the wrong vzor" % (date_from, date_to))

    def test_each_legacy_grid_is_exactly_the_lines_its_xsd_defines(self):
        """Both directions, per vintage — the same check the 2021 grid gets.

        A line the XSD has and the grid lacks never gets computed; a line the
        grid has and the XSD lacks files on a row that did not exist. Internal
        helper codes (r_net, the odpočet totals) are excluded: they are how the
        grid is built, not rows of the form.
        """
        import re

        from odoo.tools.misc import file_path

        for xmlid, schema, _vfrom, _vto in self.LEGACY:
            with open(file_path("l10n_sk_vat_return/data/%s" % schema),
                      encoding="utf-8") as handle:
                xsd_lines = set(re.findall(r'name="(r\d+[a-z]?)"', handle.read()))
            self.assertTrue(xsd_lines, "%s defines no r-elements" % schema)
            _version, codes = self._grid(xmlid)
            grid = {c for c in codes if re.fullmatch(r"r\d+", c)}
            self.assertEqual(xsd_lines - grid, set(),
                             "%s defines lines %s never computes" % (schema, xmlid))
            self.assertEqual(grid - xsd_lines, set(),
                             "%s computes lines %s does not have" % (xmlid, schema))

    def test_the_legacy_vzory_number_their_rows_two_lower_than_2021(self):
        """The renumbering is the whole reason these cannot reuse the 2021 grid.

        The 2021 vzor merged § 69 ods. 3 into r09/r10, shifting every row from
        r11 down by two. Reusing the 2021 grid for a 2019 period would put
        daň celkom on the odpočet row and the vlastná daňová povinnosť two rows
        off — while validating perfectly, because the XSD only counts elements.
        Pinned on the codes the module itself keys on.
        """
        new = self.env.ref("l10n_sk_vat_return.dph_version_2024")
        self.assertEqual((new.own_tax_line_code, new.excess_line_code,
                          new.diff_line_code), ("r32", "r33", "r36"))
        for xmlid, _schema, _vfrom, _vto in self.LEGACY:
            old = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
            self.assertEqual(
                (old.own_tax_line_code, old.excess_line_code,
                 old.diff_line_code), ("r31", "r32", "r37"),
                "%s must use its OWN row numbers" % xmlid)

    def test_r18_is_the_row_that_separates_2018_from_2020(self):
        """Two byte-identical schemas, two different forms.

        dph2018.xsd and dph2020.xsd differ only in their documentation string,
        so nothing in a finished document says which vzor it was written for. A
        2018 return validates perfectly against the 2020 schema while carrying
        the § 81 deregistration liability on a row that means § 48ca. The
        vintages exist to keep those periods apart; this asserts they are in
        fact separate records over separate windows, sharing one template.
        """
        import hashlib

        from odoo.tools.misc import file_path

        digests = {}
        for schema in ("dph2018.xsd", "dph2020.xsd"):
            with open(file_path("l10n_sk_vat_return/data/%s" % schema), "rb") as fh:
                digests[schema] = hashlib.md5(fh.read()).hexdigest()
        self.assertNotEqual(digests["dph2018.xsd"], digests["dph2020.xsd"],
                            "the two files are not the same file")

        v18 = self.env.ref("l10n_sk_vat_return.dph_version_2018")
        v20 = self.env.ref("l10n_sk_vat_return.dph_version_2020")
        self.assertNotEqual(v18, v20)
        self.assertEqual(v18.xml_template_ref_id, v20.xml_template_ref_id,
                         "the two vzory share one document shape")
        for version in (v18, v20):
            r18 = version.line_def_ids.filtered(lambda d: d.code == "r18")
            self.assertEqual(
                r18.kind, "manual",
                "r18 means different things in these two vzory and no l10n_sk "
                "tag routes to either, so it is entered by hand")

    def test_the_69_3_split_reads_the_supplier_not_the_tag(self):
        """r09/r10 and r11/r12 share tags and split on who supplied.

        These vzory give § 69 ods. 3 — služba dodaná zahraničnou osobou — its
        own row pair. The l10n_sk chart has ONE reverse-charge purchase family
        (tags 09/10), because the CURRENT form merges the paragraphs, so no tag
        can separate them. They split on `line_filter` instead, which resolves
        per line from the supplier's country, because that is what the
        paragraph actually says.
        """
        for xmlid, _schema, _vfrom, _vto in self.LEGACY:
            version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
            byc = {d.code: d for d in version.line_def_ids}
            self.assertEqual(byc["r09"].tag_formula, byc["r11"].tag_formula,
                             "%s: the two rows read the same tags" % xmlid)
            self.assertEqual(byc["r10"].tag_formula, byc["r12"].tag_formula)
            self.assertEqual(byc["r09"].line_filter, "not_69_3")
            self.assertEqual(byc["r11"].line_filter, "69_3")
            self.assertEqual(byc["r10"].line_filter, "not_69_3")
            self.assertEqual(byc["r12"].line_filter, "69_3")
            # and r13/r14 are § 69 ods. 7, which the 2021 vzor calls r11/r12
            self.assertEqual(byc["r13"].tag_formula,
                             "11|11a|11b|11c|11d|11e")

    def test_the_current_vzory_use_no_line_filter(self):
        """The mechanism must be invisible to every form that does not need it.

        From 2021 the tlačivo merges the paragraphs, so r09/r10 take the lot
        and a filter there would drop half of it.
        """
        for xmlid in ("dph_version_2024", "dph_version_2025"):
            version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
            self.assertFalse(
                version.line_def_ids.filtered("line_filter"),
                "%s must collect its tags unrestricted" % xmlid)

    def test_the_marker_defaults_to_reading_the_supplier(self):
        """Nothing is preset on the shared reverse-charge taxes, deliberately.

        `vs_rc_5/19/23` are used for § 69 ods. 3 AND for the domestic § 69
        ods. 12 prenos — one tax, two paragraphs, because the current form
        never asks. Marking them § 69 ods. 3 would move every domestic
        construction reverse charge onto r11/r12, which is the error the split
        exists to prevent. They stay on 'auto' and the supplier decides.
        """
        sk_rc = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("l10n_sk_dph_69_par", "!=", "auto"),
        ])
        self.assertFalse(
            sk_rc,
            "a tax was preset to a § 69 paragraph: %s" % sk_rc.mapped("name"))

    def test_the_pre_july_grid_collects_the_bands_2025_split(self):
        """Each single band must gather every sub-band the later vzor made of it.

        Checked as a partition rather than line by line: every tag the current
        grid uses has to appear exactly once somewhere in the older grid, or a
        supply is either dropped or counted twice. The tags 23a/23b/23c are the
        deliberate exception — the 2025 vzor added a fourth deduction CATEGORY
        that has no DPHv21 home, and taxes carrying those tags postdate it.
        """
        new_version, _new_codes = self._grid("dph_version_2025")
        old_version, _old_codes = self._grid("dph_version_2024")

        def tags(version):
            seen = []
            for ldef in version.line_def_ids.filtered(
                    lambda d: d.kind == "tags" and d.tag_formula):
                seen += [n.strip() for n in
                         ldef.tag_formula.lstrip("+-").split("|") if n.strip()]
            return seen

        old_tags = tags(old_version)
        self.assertEqual(
            len(old_tags), len(set(old_tags)),
            "a tag is collected by two lines of the same grid, so its supplies "
            "are counted twice")

        missing = set(tags(new_version)) - set(old_tags) - {"23a", "23b", "23c"}
        self.assertEqual(
            missing, set(),
            "tags the current grid reports and the pre-July grid drops")

        r09 = old_version.line_def_ids.filtered(lambda d: d.code == "r09")
        self.assertEqual(
            r09.tag_formula, "09|09a|09b",
            "the § 69 reverse-charge band was ONE line until 1. 7. 2025")


@tagged("post_install", "-at_install")
class TestSkVatReturnCompute(AccountTestInvoicingCommon):
    """Functional: post a standard-rate sale, compute + export the DPH return."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Identification fields the official dph2025 schema needs.
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })
        cls.tax_sale = cls.tax_sale_a
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")

    def _make_return(self):
        return self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        # Output VAT total, and the NET-payable computation (mirrors l10n_sk):
        # sale only → 230 output, 0 deductions → own liability 230, excess 0.
        self.assertAlmostEqual(vals["r17"], 230.0, places=2)      # total output VAT
        self.assertAlmostEqual(vals["r_net"], 230.0, places=2)    # net
        self.assertAlmostEqual(vals["r32"], 230.0, places=2)      # own VAT liability
        self.assertAlmostEqual(vals["r33"], 0.0, places=2)        # excess deduction
        self.assertAlmostEqual(vals["r35"], 230.0, places=2)      # to be paid

        # Validates against the OFFICIAL dph2025.xsd (root 'dokument', eForm).
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        self.assertEqual(root.findtext(".//telo/r17"), "230.00")
        self.assertEqual(root.findtext(".//telo/r32"), "230.00")
        self.assertEqual(root.findtext(".//telo/r35"), "230.00")
        self.assertEqual(root.findtext(".//hlavicka/zdanObd/rok"), "2026")

    def test_the_deduction_total_reconciles_with_the_net(self):
        """The aggregate evaluates, and agrees with what r_net deducts.

        r_net subtracts the per-rate halves, not this line — it is additive
        and no filed figure moves. That is exactly why it needs its own check:
        nothing else would notice if it stopped agreeing with them.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        self.init_invoice(
            "in_invoice", partner=self.partner_a,
            invoice_date="2026-06-12", amounts=[500.0],
            taxes=self.tax_purchase_a, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}

        halves = sum(v for c, v in vals.items()
                     if c.endswith("_total") and c != "r_deduction_total")
        self.assertTrue(halves, "fixture: the bill must produce a deduction")
        self.assertAlmostEqual(vals["r_deduction_total"], halves, places=2)
        # No r25/r27/r28/r29/r30 in this fixture, so the net is exactly
        # output minus the deduction the new line reports.
        self.assertAlmostEqual(
            vals["r_net"], vals["r17"] - vals["r_deduction_total"], places=2)

    def test_manual_journal_entry_matches_invoice(self):
        """A MANUAL misc-journal entry booking the same output VAT as an
        invoice must contribute to the return lines exactly like the invoice.

        Odoo 19 removed ``tax_tag_invert``: the tag data is unsigned and the
        core tax_tags engine sums RAW signed balances, applying only the
        formula-level '-' sign — which is precisely ``_eval_tags``'s contract.
        This guards that a misc entry (credit income + auto tax line) and an
        equivalent customer invoice produce identical r03/r04/r17 deltas."""
        rate = self.tax_sale.amount
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        vals_inv = {line.code: line.value for line in ret.line_ids}

        entry = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-15",
            "line_ids": [
                Command.create({
                    "account_id": self.company_data[
                        "default_account_receivable"].id,
                    "debit": round(1000.0 * (1 + rate / 100.0), 2),
                    "credit": 0.0,
                }),
                Command.create({
                    "account_id": self.company_data[
                        "default_account_revenue"].id,
                    "debit": 0.0, "credit": 1000.0,
                    "tax_ids": [Command.set(self.tax_sale.ids)],
                }),
            ],
        })
        entry.action_post()
        # The auto-created tax line and the tagged base line must feed the
        # return exactly like the invoice flow does.
        self.assertTrue(entry.line_ids.tax_tag_ids,
                        "the manual entry must carry tax tags")

        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(
            vals["r03"], vals_inv["r03"] + 1000.0, places=2,
            msg="manual entry base must add like an invoice base")
        self.assertAlmostEqual(
            vals["r04"], vals_inv["r04"] + 1000.0 * rate / 100.0, places=2,
            msg="manual entry VAT must add like an invoice VAT")
        self.assertAlmostEqual(
            vals["r17"], vals_inv["r17"] + 1000.0 * rate / 100.0, places=2)

    def test_submit_lock_and_retention(self):
        """Submitting freezes the filed XML and locks the return; reset keeps
        the filed copy (the 'posledná známa daň' baseline)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        ret.action_export_xml()
        filed = ret.xml_attachment_id
        self.assertTrue(filed)

        ret.submission_reference = "FS-2026-0001"
        ret.action_submit()
        self.assertEqual(ret.state, "submitted")
        self.assertEqual(ret.submitted_attachment_id, filed)  # frozen filed copy
        self.assertTrue(ret.submitted_date)

        # A submitted return is locked against re-export and recompute.
        with self.assertRaises(UserError):
            ret.action_export_xml()
        with self.assertRaises(UserError):
            ret.action_compute_lines()

        # Reset is the explicit unlock; the filed copy survives it.
        ret.action_reset_to_draft()
        self.assertEqual(ret.state, "draft")
        self.assertEqual(ret.submitted_attachment_id, filed)

    def test_dodatocne_amendment_r36(self):
        """Create a dodatočné from a submitted original: it links back, and r36
        (rozdiel oproti poslednej známej dani) auto-fills from the original."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        orig = self._make_return()
        orig.action_compute_lines()
        orig.action_export_xml()
        orig.action_submit()
        orig_net = (orig.line_ids.filtered(lambda l: l.code == "r32").value
                    - orig.line_ids.filtered(lambda l: l.code == "r33").value)

        action = orig.action_create_amendment()
        amend = self.env["cssk.vat.return"].browse(action["res_id"])
        self.assertEqual(amend.original_return_id, orig)
        self.assertEqual(amend.state, "draft")

        # A corrective sale of 500 is booked, then the dodatočné is recomputed.
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-20",
            amounts=[500.0], taxes=self.tax_sale, post=True)
        amend.action_compute_lines()
        new_net = (amend.line_ids.filtered(lambda l: l.code == "r32").value
                   - amend.line_ids.filtered(lambda l: l.code == "r33").value)
        r36 = amend.line_ids.filtered(lambda l: l.code == "r36").value
        # r36 = new − posledná známa daň = the daň on the extra 500 @ 23 %.
        self.assertAlmostEqual(r36, new_net - orig_net, places=2)
        self.assertAlmostEqual(r36, 500.0 * self.tax_sale.amount / 100.0, places=2)

        # As a dodatočné it carries the deň zistenia (datumZisteniaDdp), defaulted
        # to today on creation, and emits ddp=1 in the XML.
        self.assertTrue(amend.discovery_date)
        ddp = self.version.statement_type_ids.filtered(lambda t: t.fa_xml_value == "D")
        amend.statement_type_id = ddp[0].id
        amend.action_export_xml()
        root = etree.fromstring(base64.b64decode(amend.xml_attachment_id.datas))
        self.assertEqual(root.findtext(".//typDP/ddp"), "1")
        self.assertTrue(root.findtext(".//typDP/datumZisteniaDdp"),
                        "datumZisteniaDdp must be filled on a dodatočné")

    def test_kontroly(self):
        """daň = základ × sadzba content check: clean on a 23 % sale, and a
        mistuned daň row is flagged (DPH_RATE)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        # r03 (základ 1000) / r04 (daň 230) -> implied 23 % == základná sadzba.
        self.assertEqual(
            ret.check_kontroly(), [],
            "a correctly-taxed 23 %% sale must pass the rate kontroly")

        # Force a wrong rate on r04 (daň 100 on základ 1000 -> 10 %, not 23/19/5).
        r04 = ret.line_ids.filtered(lambda line: line.code == "r04")
        r04.write({"is_overridden": True, "manual_value": 100.0})
        ret.action_compute_lines()
        codes = [v["code"] for v in ret.check_kontroly()]
        self.assertIn("DPH_RATE", codes,
                      "kontroly must flag daň that is not základ × platná sadzba")

    def test_settlement_codes_and_rate_pairs_from_version_data(self):
        """Task-4 regression: the r32/r33/r36 settlement + amendment codes
        and the daň = základ × sadzba pairing are version DATA (fields on the
        version record), not hardcoded — clearing rate_pairs removes the
        DPH_RATE rule."""
        self.assertEqual(self.version.own_tax_line_code, "r32")
        self.assertEqual(self.version.excess_line_code, "r33")
        self.assertEqual(self.version.diff_line_code, "r36")
        self.assertIn(["r03", "r04", 23.0], self.version.rate_pairs)
        self.assertIn(["r01a", "r02a", 5.0], self.version.rate_pairs)

        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale, post=True)
        ret = self._make_return()
        ret.action_compute_lines()
        # settlement codes drive to_pay (own liability 230, excess 0)
        self.assertAlmostEqual(ret.to_pay, 230.0, places=2)

        # mistune r04 → the data-driven rate rule flags it …
        r04 = ret.line_ids.filtered(lambda line: line.code == "r04")
        r04.write({"is_overridden": True, "manual_value": 100.0})
        ret.action_compute_lines()
        self.assertIn("DPH_RATE", [v["code"] for v in ret.check_kontroly()])
        # … and WITHOUT the version data the rule disappears (nothing left
        # hardcoded in the module)
        self.version.rate_pairs = False
        self.assertNotIn("DPH_RATE",
                         [v["code"] for v in ret.check_kontroly()])

    def test_manual_override_carryover(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        ret = self._make_return()
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r35"], 230.0, places=2)  # no override yet

        # Override r34 (excess-deduction offset, a carryover line) = 50.
        r34 = ret.line_ids.filtered(lambda line: line.code == "r34")
        r34.write({"is_overridden": True, "manual_value": 50.0})
        ret.action_compute_lines()

        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r34"], 50.0, places=2)   # override applied
        self.assertAlmostEqual(vals["r35"], 180.0, places=2)  # 230 − 50 (flows through)

        # Override survives the recompute.
        r34 = ret.line_ids.filtered(lambda line: line.code == "r34")
        self.assertTrue(r34.is_overridden)
        self.assertAlmostEqual(r34.manual_value, 50.0, places=2)


class TestDeductionTotalNamesEveryHalf(TransactionCase):
    """``r_deduction_total`` must name EVERY per-rate half its version defines.

    The tlačivo has no rate-agnostic deduction row, so this aggregate exists
    only to give a legacy filing that carries "odpočítaná daň celkom" as one
    number something correct to be compared against. Mapped onto a single
    per-rate half instead, such a figure agrees on an agenda whose purchases
    are all standard-rated and silently drops every reduced-rate deduction —
    a real mapping caught on a real agenda, invisible because the two
    coincided.

    So the test is the INVARIANT, not a direction: whatever halves a vzor
    defines, the total names all of them. A new vintage that adds a rate — as
    2025 did with ``r18a_total`` — fails here rather than quietly under-
    reporting years later.
    """

    def test_every_sk_version_totals_all_of_its_halves(self):
        versions = self.env["cssk.vat.return.version"].search(
            [("country_id.code", "=", "SK")])
        self.assertTrue(versions, "no SK DPH versions seeded")
        for version in versions:
            codes = version.line_def_ids.mapped("code")
            halves = {c for c in codes
                      if c.endswith("_total") and c != "r_deduction_total"}
            self.assertTrue(
                halves, "%s defines no per-rate deduction halves" % version.name)
            total = version.line_def_ids.filtered(
                lambda d: d.code == "r_deduction_total")
            self.assertEqual(
                len(total), 1,
                "%s carries no r_deduction_total" % version.name)
            named = {tok for tok in total.aggregate_formula.replace(
                "+", " ").split()}
            self.assertEqual(
                named, halves,
                "%s: r_deduction_total names %s but the vzor defines halves %s"
                % (version.name, sorted(named), sorted(halves)))

    def test_the_total_is_not_itself_a_row_of_the_form(self):
        """It is internal, and the name has to say so.

        Someone mapping a filed figure onto it needs to see that it is a
        derived quantity on our side too — that is what makes an
        aggregate-to-aggregate correspondence honest rather than a fudge.
        """
        versions = self.env["cssk.vat.return.version"].search(
            [("country_id.code", "=", "SK")])
        for version in versions:
            total = version.line_def_ids.filtered(
                lambda d: d.code == "r_deduction_total")
            self.assertEqual(total.kind, "aggregate")
            self.assertIn("(internal)", total.name)


@tagged("post_install", "-at_install")
class TestSchemaPins(TransactionCase):
    """The bundled schemas must match data/SCHEMA_VERSION.

    Not a check that our copy is CURRENT — nothing local can answer that, which
    is the whole reason the pin file exists. This checks the weaker thing that
    is still worth having: that the bundled bytes are the ones somebody
    verified against the published copy on a stated date. Replacing a schema
    then has to be a deliberate two-file change rather than a silent one, and
    the refresh procedure lives next to the digest that would have to move.
    """

    def test_bundled_schemas_match_the_pinned_digests(self):
        import hashlib
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            path = os.path.join(data, name)
            self.assertTrue(os.path.exists(path), "%s is pinned but missing" % name)
            blob = open(path, "rb").read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(
                hashlib.md5(blob).hexdigest(), digest,
                "%s does not match its pin — if this is a deliberate refresh, "
                "update data/SCHEMA_VERSION and re-run the export tests" % name)

    def test_every_bundled_schema_is_pinned(self):
        """A schema added without a pin is the gap this file exists to close."""
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data = os.path.join(here, "data")
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        pinned = set()
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pinned.add(parts[0])
        self.assertEqual(on_disk, pinned,
                         "unpinned schema(s): %s" % sorted(on_disk - pinned))


@tagged("post_install", "-at_install")
class TestSkVatReturnLegacyExport(AccountTestInvoicingCommon):
    """Each pre-2021 vzor must actually produce a document its own XSD accepts.

    The grid tests compare row codes; this is the one that would catch a
    hlavička built for the wrong vintage — DPHv12 wants a STRUCTURED tel/fax
    and no zastupca69aa, DPHv18 wants a plain telefon/email and has one, and
    both put splneniePodmienok before r32 where the 2021 vzor puts it after.
    Every one of those is element order or element name, so the XSD is the
    only thing that will tell you, and only if you actually export.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "phone": "+421 2 12345678",
            "country_id": cls.env.ref("base.sk").id,
        })

    def _export(self, xmlid, date_from, date_to):
        version = self.env.ref("l10n_sk_vat_return.%s" % xmlid)
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": date_from, "date_to": date_to,
            "period_type": "month",
            "statement_type_id": version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        return ret, etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

    def test_each_legacy_vintage_exports_a_valid_document(self):
        for xmlid, date_from, date_to in (
            ("dph_version_2012", "2015-06-01", "2015-06-30"),
            ("dph_version_2018", "2019-06-01", "2019-06-30"),
            ("dph_version_2020", "2020-06-01", "2020-06-30"),
        ):
            ret, root = self._export(xmlid, date_from, date_to)
            self.assertEqual(etree.QName(root).localname, "dokument")
            # r38 exists in all three and NOT in the 2021 vzor
            self.assertIsNotNone(root.find(".//telo/r38"),
                                 "%s must carry r38" % xmlid)
            # splneniePodmienok sits BEFORE r32 here, after it in 2021
            telo = [etree.QName(e).localname for e in root.find("telo")]
            self.assertLess(telo.index("splneniePodmienok"), telo.index("r32"),
                            "%s puts splneniePodmienok in the 2021 place" % xmlid)
            self.assertEqual(root.findtext(".//hlavicka/zdanObd/rok"),
                             date_from[:4])

    def test_the_2012_hlavicka_is_the_2012_shape(self):
        """Structured tel/fax, no email, no § 69aa representative."""
        _ret, root = self._export("dph_version_2012", "2015-06-01", "2015-06-30")
        self.assertIsNotNone(root.find(".//adresa/tel/cislo"))
        self.assertIsNotNone(root.find(".//adresa/fax"))
        self.assertIsNone(root.find(".//adresa/telefon"))
        self.assertIsNone(root.find(".//adresa/email"))
        self.assertIsNone(root.find(".//osoba/zastupca69aa"))
        self.assertEqual(root.findtext(".//adresa/tel/cislo"), "+421 2 12345678")

    def test_the_2018_hlavicka_is_the_2018_shape(self):
        """Plain telefon/email, and the § 69aa representative flag exists."""
        _ret, root = self._export("dph_version_2018", "2019-06-01", "2019-06-30")
        self.assertIsNotNone(root.find(".//adresa/telefon"))
        self.assertIsNotNone(root.find(".//adresa/email"))
        self.assertIsNone(root.find(".//adresa/fax"))
        self.assertIsNotNone(root.find(".//osoba/zastupca69aa"))

    def test_a_legacy_period_computes_its_own_row_numbers(self):
        """A standard-rate sale lands on r03/r04 and drives r19/r31, not r17/r32.

        Same economics as the 2025 test, two rows apart — which is the entire
        risk this vintage set exists to remove.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2019-06-10", amounts=[1000.0],
            taxes=self.tax_sale_a, post=True,
        )
        ret, root = self._export("dph_version_2018", "2019-06-01", "2019-06-30")
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["r19"], vals["r04"], places=2)  # daň celkom
        self.assertAlmostEqual(vals["r31"], vals["r_net"], places=2)
        self.assertAlmostEqual(vals["r32"], 0.0, places=2)          # no excess
        self.assertEqual(root.findtext(".//telo/r19"),
                         root.findtext(".//telo/r31"))

    def test_a_foreign_service_lands_on_r11_and_a_domestic_one_on_r09(self):
        """The split, on two invoices that differ only in the supplier.

        Same tax, same amount, same period. § 69 ods. 3 is a service from a
        person not established in Slovakia, so the Austrian supplier's line
        belongs on r11/r12 and the Slovak one's on r09/r10. Before this the
        chart could not tell them apart and both went to r09/r10.
        """
        rc = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("company_id", "=", self.company.id),
            ("name", "like", "RC"),
        ], limit=1)
        self.assertTrue(rc, "no reverse-charge purchase tax in the SK chart")

        foreign = self.env["res.partner"].create({
            "name": "Wiener Beratung GmbH",
            "country_id": self.env.ref("base.at").id,
        })
        domestic = self.env["res.partner"].create({
            "name": "Stavebná s.r.o.",
            "country_id": self.env.ref("base.sk").id,
        })
        for partner in (foreign, domestic):
            self.init_invoice(
                "in_invoice", partner=partner, invoice_date="2019-06-10",
                amounts=[1000.0], taxes=rc, post=True,
            )

        ret, root = self._export("dph_version_2018", "2019-06-01", "2019-06-30")
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(abs(vals["r09"]), 1000.0, places=2)  # domestic
        self.assertAlmostEqual(abs(vals["r11"]), 1000.0, places=2)  # foreign
        # and both still reach daň celkom, so the total is untouched by the split
        self.assertAlmostEqual(
            vals["r19"], vals["r10"] + vals["r12"], places=2)
        self.assertIsNotNone(root.find(".//telo/r11"))

    def test_the_marker_overrides_the_supplier(self):
        """A tax used for ONE paragraph beats the country test.

        A dedicated domestic-construction prenos tax is § 69 ods. 12 whoever
        the supplier is; a § 69 ods. 2 goods-with-installation tax has a
        foreign supplier and still belongs on r09/r10. Both are what the
        marker is for.
        """
        rc = self.env["account.tax"].search([
            ("type_tax_use", "=", "purchase"),
            ("company_id", "=", self.company.id),
            ("name", "like", "RC"),
        ], limit=1)
        rc.l10n_sk_dph_69_par = "69_other"
        foreign = self.env["res.partner"].create({
            "name": "Wiener Montage GmbH",
            "country_id": self.env.ref("base.at").id,
        })
        self.init_invoice(
            "in_invoice", partner=foreign, invoice_date="2019-06-10",
            amounts=[1000.0], taxes=rc, post=True,
        )
        ret, _root = self._export("dph_version_2018", "2019-06-01", "2019-06-30")
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(abs(vals["r09"]), 1000.0, places=2)
        self.assertAlmostEqual(vals["r11"], 0.0, places=2)


@tagged("post_install", "-at_install")
class TestSkVatReturnFootprint(AccountTestInvoicingCommon):
    """A posting must be able to say which DPH row it feeds.

    The footprint read the tag formula with a reader of its own, asking for a
    tag literally named ``09|09a|09b``. 55 of the 158 Slovak line definitions
    are multi-term, so those rows were unreachable from any document — the
    § 69 reverse charge among them. The failure was invisible because the same
    posting's control-statement and financial-statement rows reported fine.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava"})

    def _footprint_codes(self, tax, move_type="in_invoice",
                         invoice_date="2025-03-10"):
        # BEFORE 1. 7. 2025 on purpose. The 2025 vzor splits the reverse
        # charge by rate and writes one tag per row; the multi-term formulas
        # this test exists for — '09|09a|09b' — belong to the vzor in force
        # until 30. 6. 2025, so a 2026 date never exercises them.
        move = self.init_invoice(
            move_type, partner=self.partner_a, invoice_date=invoice_date,
            amounts=[1000.0], taxes=tax, post=True)
        codes = set()
        for line in move.line_ids.filtered("tax_tag_ids"):
            codes |= {fp["code"] for fp in line._cssk_statutory_footprint()}
        return codes

    def test_a_multi_term_row_is_reachable(self):
        """The reverse charge is the case that matters and it was unreachable."""
        rc = self.env["account.tax"].search([
            ("company_id", "=", self.company.id),
            ("type_tax_use", "=", "purchase"),
            ("name", "like", "RC"),
        ], limit=1)
        if not rc:
            self.skipTest("no reverse-charge purchase tax in this chart")
        codes = self._footprint_codes(rc)
        self.assertTrue(
            codes, "a reverse-charge posting must feed SOME DPH row")
        self.assertTrue(
            {"r09", "r10"} & codes,
            "the § 69 rows are written '09|09a|09b' and were unreachable: %s"
            % sorted(codes))

    def test_every_multi_term_definition_resolves_to_at_least_one_tag(self):
        """The rows, not the postings — nothing may be dead on arrival.

        A definition whose formula resolves to no tag at all can never appear
        in a footprint, and nothing else would say so: the figure it computes
        comes out of the same formula and would be zero for the same reason,
        which reads as 'no such supply this period'.
        """
        # the pre-July-2025 grid, which is where the multi-term rows live
        version = self.env.ref("l10n_sk_vat_return.dph_version_2024")
        Tag = self.env["account.account.tag"]
        parser = self.env["cssk.vat.return"]
        country = version.country_id
        dead = []
        for ldef in version.line_def_ids.filtered(
                lambda d: d.kind == "tags" and d.tag_formula):
            tags = Tag.browse()
            for _sign, term in parser._iter_tag_terms(ldef.tag_formula):
                tags |= Tag._get_tax_tags(term, country.id)
            if not tags:
                dead.append((ldef.code, ldef.tag_formula))
        self.assertFalse(dead, "line definitions resolving to no tag: %s" % dead)

    def test_the_footprint_uses_the_grammar_s_own_parser(self):
        """Pinned, because this is the third reader that drifted from it.

        `_iter_tag_terms` says so in its own docstring — "ONE parser for the
        grammar, because two read it… They had drifted" — and names the
        earlier `.replace("+", "|")` bug. A fourth reader would fail the same
        way, silently.
        """
        parser = self.env["cssk.vat.return"]
        terms = list(parser._iter_tag_terms("-24|+24_PR"))
        self.assertEqual([t for _s, t in terms], ["24", "24_PR"])
        self.assertEqual([s for s, _t in terms], [-1.0, 1.0],
                         "a term may override the formula's sign")
