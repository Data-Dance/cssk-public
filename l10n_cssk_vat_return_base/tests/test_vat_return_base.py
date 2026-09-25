from unittest.mock import patch

import base64

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


def _xml_template(env, name):
    """A QWeb view to satisfy ``cssk.vat.return.version.xml_template_ref_id``.

    That field is REQUIRED — a version with no renderer cannot produce the
    statutory XML, which is the point of a version. A fixture that omits it
    only survives while the column allows NULL, so these two lines are what
    keeps a fixture honest about what a version is.
    """
    return env["ir.ui.view"].create({
        "name": name,
        "type": "qweb",
        "arch": "<t t-name='%s'><DPH/></t>" % name,
    })


class TestVatReturnBase(TransactionCase):
    """Smoke tests for the shared VAT-return framework (run at install)."""

    def test_models_load(self):
        for model in (
            "cssk.vat.return.version",
            "cssk.vat.return.line.def",
            "cssk.vat.return",
            "cssk.vat.return.line",
        ):
            self.assertIn(model, self.env)


class TestHistoricTaxNaming(TransactionCase):
    """The historical twin's name must not carry two rates.

    ``_cssk_historic_tax_name`` used to test ``name.startswith("23%")``. A
    chart writing ``"23 % EÚ"`` — with a space — failed that test and fell
    through to the collision-avoiding branch, yielding ``"20% 23 % EÚ"``. Two
    rates in one name, saying neither.

    It surfaced as a cross-host defect: a recipe of "match on name +
    type_tax_use + amount" derived on a host whose chart writes ``"23%"``
    matched nothing on a host whose chart writes ``"23 %"``. The names are the
    only thing that differed.
    """

    def _name(self, name, source_rate, rate):
        return self.env["res.company"]._cssk_historic_tax_name(
            name, source_rate, rate)

    def test_a_spaced_chart_does_not_produce_two_rates(self):
        """The reported case, verbatim."""
        for name, want in (
            ("23 % EÚ", "20 % EÚ"),
            ("23 % PREN", "20 % PREN"),
            ("23 % TRI", "20 % TRI"),
            ("23 % ODL", "20 % ODL"),
        ):
            got = self._name(name, 23.0, 20.0)
            self.assertEqual(got, want)
            self.assertNotIn("23", got, "the old rate must not survive: %r" % got)

    def test_an_unspaced_chart_is_unchanged(self):
        """The host that was already correct must stay correct."""
        for name, want in (("23% RC", "20% RC"), ("23%", "20%"),
                           ("23% EU G", "20% EU G")):
            self.assertEqual(self._name(name, 23.0, 20.0), want)

    def test_the_chart_s_own_spacing_is_carried_over(self):
        """We substitute the rate, we do not restyle the name."""
        self.assertEqual(self._name("23 % X", 23.0, 20.0), "20 % X")
        self.assertEqual(self._name("23% X", 23.0, 20.0), "20% X")

    def test_a_leading_rate_that_is_not_the_source_is_not_substituted(self):
        """Renaming 5 % onto 20 % would collide with a real 20 % tax.

        Only the source rate is replaced; anything else falls through to the
        distinct-name branch, which is ugly but cannot claim a rate the tax
        never had.
        """
        got = self._name("5 % NEZ", 23.0, 20.0)
        self.assertNotEqual(got, "20 % NEZ")
        self.assertIn("5 % NEZ", got)

    def test_a_name_with_no_rate_still_gets_a_distinct_one(self):
        self.assertEqual(self._name("Something else", 23.0, 20.0),
                         "20% Something else")

    def test_a_decimal_rate_matches_in_either_notation(self):
        """12,5 and 12.5 are the same rate written two ways."""
        self.assertEqual(self._name("12,5 % X", 12.5, 10.0), "10 % X")
        self.assertEqual(self._name("12.5% X", 12.5, 10.0), "10% X")

    # ------------------------------------------------------------------
    # a superseded tax is not a source
    # ------------------------------------------------------------------
    def test_a_superseded_tax_is_recognised(self):
        """Core renames a replaced tax and leaves it in place.

        ``account/models/chart_template.py`` builds the prefix as
        ``f"[old{n if n > 1 else ''}] "`` — so the SECOND rename produces
        ``[old1]``, the third ``[old2]``. A host through two rate changes
        carries all three forms, and a ``startswith("[old]")`` sees only one
        of them.
        """
        company = self.env["res.company"]
        Tax = self.env["account.tax"]
        for name, superseded in (
            ("[old] 23% BAD DEBT", True),
            ("[old1] 23% BAD DEBT", True),
            ("[old2] 23% BAD DEBT", True),
            (" [old] 23% X", True),
            ("23% BAD DEBT", False),
            ("23 % EÚ", False),
            ("20%", False),
            # Not the marker: core's own matcher is \[old\d*\] followed by a
            # space, so a name that merely starts similarly is a real tax.
            ("[older] X", False),
            ("[old]NOSPACE", False),
        ):
            self.assertEqual(
                company._cssk_tax_is_superseded(Tax.new({"name": name})),
                superseded, "%r" % name)

    def _tax_group(self):
        """A tax group these tests can rely on existing.

        ``account.tax.tax_group_id`` is REQUIRED with a precomputed default
        that resolves through the company's chart of accounts. This class is a
        plain ``TransactionCase`` with no chart loaded, so on a database where
        nothing else has left a group behind the default comes back empty and
        the INSERT dies with NotNullViolation on ``tax_group_id``. It passed
        wherever some other module happened to have created one, which is why
        it looked fine until a full-install run said otherwise.
        """
        group = self.env["account.tax.group"].search([], limit=1)
        return group or self.env["account.tax.group"].create({
            "name": "CSSK test tax group"})

    def _probe_tax(self, name):
        """An ``account.tax`` that can be created without a chart of accounts.

        The same trap as ``_tax_group`` above, one field along.
        ``account.tax.country_id`` is REQUIRED and precomputed from
        ``company_id.account_fiscal_country_id or company_id.country_id`` — and
        a plain ``TransactionCase`` with ``--without-demo=all`` has a company
        with neither, so the compute yields empty and the INSERT dies on
        ``country_id``. Naming the country here says what these probes are
        about: the tax is Slovak because the naming rule under test is, not
        because the company happened to have a chart loaded.
        """
        return self.env["account.tax"].create({
            "name": name,
            "amount": 23.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "tax_group_id": self._tax_group().id,
            "country_id": self.env.ref("base.sk").id,
        })

    def test_the_marker_is_found_in_any_language(self):
        """Core writes the marker in ONE language; we must not read only one.

        ``name`` is translatable and ``chart_template.py``'s rename is a plain
        assignment, so on a database loaded as ``sk_SK`` the superseded copy
        and the live one are byte-identical in Slovak and differ only in
        ``en_US``. Reading ``tax.name`` in a Slovak environment therefore sees
        no marker at all — and this module's whole audience runs in Slovak.
        """
        self.env["res.lang"]._activate_lang("sk_SK")
        tax = self._probe_tax("23% CSSK LANG PROBE")
        # The Slovak chart named it; then a reload renamed the en_US value only.
        tax.with_context(lang="sk_SK").name = "23 % SONDA"
        tax.with_context(lang="en_US").name = "[old] 23% CSSK LANG PROBE"

        company = self.env["res.company"]
        sk_tax = tax.with_context(lang="sk_SK")
        # The premise: in Slovak the marker is simply not there.
        self.assertEqual(sk_tax.name, "23 % SONDA")
        self.assertFalse(
            company._CSSK_SUPERSEDED_PREFIX.match(sk_tax.name),
            "fixture: the Slovak name must carry no marker")
        # ...and it is recognised anyway.
        self.assertTrue(
            company._cssk_tax_is_superseded(sk_tax),
            "a superseded tax must be recognised whatever language we read in")

    def test_a_live_tax_is_not_flagged_in_any_language(self):
        """The other direction: no language carries a marker, so no skip."""
        self.env["res.lang"]._activate_lang("sk_SK")
        tax = self._probe_tax("23% CSSK LANG PROBE")
        tax.with_context(lang="sk_SK").name = "23 % SONDA"
        self.assertFalse(
            self.env["res.company"]._cssk_tax_is_superseded(
                tax.with_context(lang="sk_SK")))

    def test_the_superseded_name_is_exactly_what_the_generator_mangles(self):
        """Why the 1.7.0 name repair could not reach these.

        The leading token of "[old] 23% BAD DEBT" is not a rate, so the token
        rule correctly declines to substitute and the collision branch prefixes
        instead — the fixed generator and the buggy one AGREE on this input.
        Nothing to rewrite, which is why the fix had to be at the source
        selection rather than in the naming.
        """
        got = self._name("[old] 23% BAD DEBT", 23.0, 20.0)
        self.assertEqual(got, "20% [old] 23% BAD DEBT")
        self.assertIn("23", got, "both rates survive — that is the point")


@tagged("post_install", "-at_install")
class TestVatReturnEngine(AccountTestInvoicingCommon):
    """Functional: the tax-tag evaluator computes line values from real SK
    tags, and the aggregate engine sums them."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.sk = cls.env.ref("base.sk")
        cls.tax_sale = cls.tax_sale_a

    def test_compute_from_real_tags(self):
        inv = self.init_invoice(
            "out_invoice", partner=self.partner_a,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_sale, post=True,
        )
        base_line = inv.line_ids.filtered(
            lambda l: l.tax_ids and not l.tax_line_id
        )
        tax_line = inv.line_ids.filtered(lambda l: l.tax_line_id)
        base_tag = base_line.tax_tag_ids[:1]
        tax_tag = tax_line.tax_tag_ids[:1]
        self.assertTrue(base_tag, "sale base line carries no tax tag")
        self.assertTrue(tax_tag, "sale tax line carries no tax tag")

        template = self.env["ir.ui.view"].create({
            "name": "cssk vat return test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_vat_return_test_template'><DPH/></t>",
        })
        version = self.env["cssk.vat.return.version"].create({
            "name": "TST", "country_id": self.sk.id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "DPH",
            "line_def_ids": [
                (0, 0, {"code": "rbase", "name": "Base", "kind": "tags",
                        "tag_formula": "-" + base_tag.name, "sequence": 10}),
                (0, 0, {"code": "rtax", "name": "Tax", "kind": "tags",
                        "tag_formula": "-" + tax_tag.name, "sequence": 20}),
                (0, 0, {"code": "rtot", "name": "Total", "kind": "aggregate",
                        "aggregate_formula": "rbase + rtax", "sequence": 30}),
            ],
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"}),
            ],
        })
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        vals = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(vals["rbase"], 1000.0, places=2)
        self.assertAlmostEqual(vals["rtax"], 230.0, places=2)
        self.assertAlmostEqual(vals["rtot"], 1230.0, places=2)


@tagged("post_install", "-at_install")
class TestSubmissionLifecycle(AccountTestInvoicingCommon):
    """The shared submission mixin's integrity guarantees: durable filed-copy
    history, unlink protection and the manager-gated reset."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "SK2023456787"
        template = cls.env["ir.ui.view"].create({
            "name": "cssk vat return lifecycle test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_vat_return_lc_template'><DPH/></t>",
        })
        # A minimal schema that accepts exactly the template's document. The
        # version needs ONE because exporting without a schema now raises: a
        # statutory file that was never validated must not reach `exported`
        # looking like one that was. Before that, a schema-less version
        # exported silently and this fixture never noticed.
        schema = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            b'<xs:element name="DPH"/></xs:schema>'
        )
        cls.version = cls.env["cssk.vat.return.version"].create({
            "name": "LC", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "DPH",
            "xml_schema_filename": "lifecycle.xsd",
            "xml_schema_data": base64.b64encode(schema),
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"}),
            ],
        })

    def _make_return(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })
        ret.action_compute_lines()
        return ret

    def test_filed_history_accumulates_across_resubmits(self):
        """Task 1 regression: after reset → recompute → resubmit, the
        ORIGINALLY-filed XML must stay reachable — filed_history_ids
        accumulates every submitted attachment; submitted_attachment_id
        stays 'latest'."""
        ret = self._make_return()
        ret.action_export_xml()
        first = ret.xml_attachment_id
        ret.action_submit()
        self.assertEqual(ret.filed_history_ids, first)
        self.assertEqual(ret.submitted_attachment_id, first)

        ret.action_reset_to_draft()
        ret.action_compute_lines()
        ret.action_export_xml()
        second = ret.xml_attachment_id
        self.assertNotEqual(second, first)
        ret.action_submit()
        # latest pointer moved, history keeps BOTH filed copies
        self.assertEqual(ret.submitted_attachment_id, second)
        self.assertEqual(ret.filed_history_ids, first | second)
        self.assertTrue(first.exists(),
                        "the originally-filed XML must never be lost")

    def test_unlink_blocked_when_submitted(self):
        """Task 2 regression: a submitted filing cannot be deleted; after a
        reset it can."""
        ret = self._make_return()
        ret.action_export_xml()
        ret.action_submit()
        with self.assertRaises(UserError):
            ret.unlink()
        self.assertTrue(ret.exists())
        ret.action_reset_to_draft()
        ret.unlink()
        self.assertFalse(ret.exists())

    def test_reset_to_draft_requires_account_manager(self):
        """Task 2 regression: reset-to-draft is gated on
        account.group_account_manager."""
        ret = self._make_return()
        ret.action_export_xml()
        ret.action_submit()

        Users = self.env["res.users"].with_context(no_reset_password=True)
        clerk = Users.create({
            "name": "CSSK clerk", "login": "cssk_lc_clerk",
            "company_id": self.company.id,
            "company_ids": [(6, 0, self.company.ids)],
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("account.group_account_user").id,
            ])],
        })
        with self.assertRaises(UserError):
            ret.with_user(clerk).action_reset_to_draft()
        self.assertEqual(ret.state, "submitted")

        manager = Users.create({
            "name": "CSSK manager", "login": "cssk_lc_manager",
            "company_id": self.company.id,
            "company_ids": [(6, 0, self.company.ids)],
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("account.group_account_manager").id,
            ])],
        })
        ret.with_user(manager).action_reset_to_draft()
        self.assertEqual(ret.state, "draft")

    def test_export_preflight_requires_company_vat(self):
        """Task 3 regression: exporting without the company VAT fails early
        with a named field, not a cryptic XSD error."""
        ret = self._make_return()
        self.company.vat = False
        with self.assertRaises(UserError) as cm:
            ret.action_export_xml()
        self.assertIn("VAT", str(cm.exception))
        self.company.vat = "SK2023456787"
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")

    def test_kontroly_run_before_render(self):
        """Task-1 regression (consolidated export pipeline): kontrolné
        pravidlá are a CONTENT gate and run BEFORE rendering — a content
        error must surface as the named kontroly violation, never masked
        by a template/XSD problem."""
        ret = self._make_return()
        Model = type(self.env["cssk.vat.return"])

        # patch with ``new=`` plain functions, NEVER a MagicMock — the
        # registry's ``_ondelete_methods`` scan would cache the mock (it
        # auto-creates an ``_ondelete`` attribute) as an unlink hook.
        def fake_kontroly(model):
            return [{"code": "T", "severity": "error",
                     "desc": "test rule", "detail": "boom"}]

        def no_render(model):
            raise AssertionError("render must not run when kontroly fail")

        with patch.object(Model, "check_kontroly", new=fake_kontroly), \
             patch.object(Model, "_render_xml", new=no_render):
            with self.assertRaises(UserError) as cm:
                ret.action_export_xml()
        self.assertIn("kontrolné pravidlá", str(cm.exception))
        self.assertIn("test rule", str(cm.exception))
        self.assertNotEqual(ret.state, "exported")

    def test_to_pay_graceful_without_version_codes(self):
        """Task-4 regression: the settlement line codes are version DATA
        (own_tax_line_code / excess_line_code) — a version that declares
        none yields to_pay = 0 gracefully (no crash, even with carries set)
        and skips the excess-cap check; only the non-negativity constraint
        remains."""
        ret = self._make_return()
        self.assertFalse(self.version.own_tax_line_code)
        self.assertFalse(self.version.excess_line_code)
        self.assertAlmostEqual(ret.to_pay, 0.0, places=2)
        # carries do not produce a half-computed settlement without codes,
        # and no excess-cap constraint fires (there is no excess line)
        ret.write({"excess_carried_in": 10.0, "excess_carried_out": 5.0})
        self.assertAlmostEqual(ret.to_pay, 0.0, places=2)
        # the sign constraint stays active
        with self.assertRaises(ValidationError):
            ret.excess_carried_in = -1.0

    def test_kontroly_warnings_do_not_block(self):
        """Severity 'warning' violations are logged but must not block the
        export (the mixin's shared severity handling)."""
        ret = self._make_return()
        Model = type(self.env["cssk.vat.return"])

        def fake_kontroly(model):
            return [{"code": "T", "severity": "warning",
                     "desc": "advisory", "detail": "just a warning"}]

        with patch.object(Model, "check_kontroly", new=fake_kontroly):
            with self.assertLogs(
                    "odoo.addons.l10n_cssk_core.models"
                    ".cssk_statutory_submission", level="WARNING"):
                ret.action_export_xml()
        self.assertEqual(ret.state, "exported")


@tagged("post_install", "-at_install")
class TestVatReturnPeriodSelection(AccountTestInvoicingCommon):
    """The period is decided by the tax point, not by the accounting date.

    Both countries define the obligation to declare by the date of supply.
    The two dates coincide in everyday CZ use because ``l10n_cz`` forces
    ``date = taxable_supply_date`` on draft moves — but ``l10n_sk`` does not,
    and neither does an accounting history imported from a system that keeps
    the two apart.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    @property
    def ret(self):
        """A June-2026 return, built per test.

        Deliberately not a class attribute: an in-memory ``new()`` record does
        not survive the cache invalidation between tests, and comes back with
        its dates silently set to False — which makes the period domain match
        nothing and the tests pass or fail for the wrong reasons.
        """
        return self.env["cssk.vat.return"].new({
            "company_id": self.company.id,
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
        })

    def _invoice(self, accounting_date, supply_date):
        """A posted invoice whose two dates are set independently.

        Both go in the same ``create()`` on purpose: writing
        ``taxable_supply_date`` afterwards drags ``date`` with it on CZ.
        """
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": accounting_date,
            "date": accounting_date,
            "taxable_supply_date": supply_date,
            "invoice_line_ids": [(0, 0, {
                "name": "x", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [(6, 0, self.tax_sale_a.ids)],
            })],
        })
        move.action_post()
        return move

    def test_supplied_in_period_booked_later_is_included(self):
        """Supplied in June, booked in July — it belongs to the June return.

        Customer invoice: the output side follows the tax point.
        """
        move = self._invoice("2026-07-05", "2026-06-28")
        self.assertEqual(str(move.date), "2026-07-05", "premise: dates differ")
        lines = self.ret._period_move_lines()
        self.assertTrue(lines & move.line_ids,
                        "a June supply booked in July is missing from the June return")

    def test_supplied_outside_period_booked_inside_is_excluded(self):
        """Booked in June but supplied in May — it belongs to May, not June."""
        move = self._invoice("2026-06-03", "2026-05-30")
        lines = self.ret._period_move_lines()
        self.assertFalse(lines & move.line_ids,
                         "a May supply booked in June leaked into the June return")

    def test_without_a_tax_point_the_accounting_date_still_decides(self):
        """Entries, bank and cash documents carry no tax point; they must
        still be selected, by accounting date.

        Built as a real journal entry rather than a mutilated invoice: that is
        how the case actually arises, and an invoice re-populates the field.
        """
        account = self.company_data["default_account_revenue"]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": "2026-06-10",
            "line_ids": [
                (0, 0, {"name": "base", "account_id": account.id,
                        "credit": 1000.0, "tax_ids": [(6, 0, self.tax_sale_a.ids)]}),
                (0, 0, {"name": "counterpart", "credit": 0.0, "debit": 1000.0,
                        "account_id": self.company_data["default_account_receivable"].id}),
            ],
        })
        move.action_post()
        tagged = move.line_ids.filtered(lambda line: line.tax_tag_ids)
        self.assertTrue(tagged, "premise: the entry carries tax tags")
        self.assertFalse(move.taxable_supply_date, "premise: entries have no tax point")
        lines = self.ret._period_move_lines()
        self.assertTrue(lines & tagged,
                        "a document without a tax point fell out of the period")

    def _bill(self, accounting_date, supply_date):
        move = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": accounting_date,
            "date": accounting_date,
            "taxable_supply_date": supply_date,
            "invoice_line_ids": [(0, 0, {
                "name": "x", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [(6, 0, self.tax_purchase_a.ids)],
            })],
        })
        move.action_post()
        return move

    def test_the_drill_down_reads_the_same_period_as_the_figure(self):
        """A June supply booked in July counts towards the June figure — and
        must appear in the list that figure drills into.

        ``_tag_source_domain`` selected by ``date`` while the figure selected
        by tax point, so this document was inside the value and outside its own
        drill-down. The row then reports ``source_reconciles`` false and paints
        the return red while being correctly computed — the failure mode is a
        filer chasing a discrepancy that does not exist.
        """
        country = self.env.ref("base.sk")
        tag = self.env["account.account.tag"].create({
            "name": "TDRILL", "applicability": "taxes",
            "country_id": country.id})
        tax = self.env["account.tax"].create({
            "name": "drill 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "country_id": country.id,
            "company_id": self.company.id,
            "invoice_repartition_line_ids": [
                (0, 0, {"repartition_type": "base",
                        "tag_ids": [(6, 0, tag.ids)]}),
                (0, 0, {"repartition_type": "tax"})],
            "refund_repartition_line_ids": [
                (0, 0, {"repartition_type": "base",
                        "tag_ids": [(6, 0, tag.ids)]}),
                (0, 0, {"repartition_type": "tax"})],
        })
        move = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2026-07-05", "date": "2026-07-05",
            "taxable_supply_date": "2026-06-28",
            "invoice_line_ids": [(0, 0, {
                "name": "x", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [(6, 0, tax.ids)]})],
        })
        move.action_post()
        ret = self.env["cssk.vat.return"].new({
            "company_id": self.company.id, "country_id": country.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30"})

        tagged = move.line_ids.filtered(lambda l: tag in l.tax_tag_ids)
        self.assertTrue(tagged, "premise: the base line carries the tag")
        self.assertTrue(tagged & ret._period_move_lines(),
                        "premise: the figure counts a June supply booked in July")

        domain = ret._tag_source_domain("TDRILL")
        self.assertFalse(
            [t for t in domain if t[0] == "date"],
            "the period must not be re-expressed as a date range — that is "
            "the selection the figure deliberately does not use")
        self.assertTrue(
            tagged & self.env["account.move.line"].search(domain),
            "the drill-down must show the line the figure was computed from")

    def test_deduction_claimed_in_period_but_supplied_earlier_is_included(self):
        """The input side follows the claim, not the supply.

        CZ § 73 lets the deduction be exercised in the period the document is
        received. A bill supplied in May and booked in June is deducted in
        June — reporting it by supply date understates the period's deduction.
        """
        move = self._bill("2026-06-04", "2026-05-28")
        lines = self.ret._period_move_lines()
        self.assertTrue(lines & move.line_ids,
                        "a deduction claimed in June was reported in May")

    def test_bill_supplied_in_period_but_claimed_later_is_excluded(self):
        """The mirror: supplied in June, booked in July, deducted in July."""
        move = self._bill("2026-07-02", "2026-06-27")
        lines = self.ret._period_move_lines()
        self.assertFalse(lines & move.line_ids,
                         "a deduction claimed in July leaked into June")

    def test_deduction_date_decides_the_input_period(self):
        """An explicit deduction date overrides the accounting date.

        A bill booked in June but claimed in July belongs to July's return.
        The accounting date is only a proxy for "when the deduction is
        exercised", and the two part company exactly here.
        """
        move = self._bill("2026-06-04", "2026-06-01")
        move.cssk_vat_deduction_date = "2026-07-15"
        lines = self.ret._period_move_lines()
        self.assertFalse(lines & move.line_ids,
                         "a deduction claimed in July was reported in June")

    def test_deduction_date_pulls_an_older_bill_into_the_period(self):
        """The mirror: booked in May, claimed in June, reported in June."""
        move = self._bill("2026-05-20", "2026-05-18")
        move.cssk_vat_deduction_date = "2026-06-10"
        lines = self.ret._period_move_lines()
        self.assertTrue(lines & move.line_ids,
                        "a deduction claimed in June was not reported in June")

    def test_no_deduction_date_still_uses_the_accounting_date(self):
        move = self._bill("2026-06-04", "2026-05-28")
        self.assertFalse(move.cssk_vat_deduction_date)
        lines = self.ret._period_move_lines()
        self.assertTrue(lines & move.line_ids)


@tagged("post_install", "-at_install")
class TestMultiTagFormula(AccountTestInvoicingCommon):
    """A line may collect several tags — that is how a form vintage is expressed."""

    def test_a_line_can_collect_several_tags(self):
        """The earlier form's single band collects what the later form split.

        A tag lives on the TAX and a line belongs to a PERIOD. Where a rate
        spans a form change — Slovak 23 % ran from 1. 1. 2025 and the vzor
        changed on 1. 7. — the same tax files on ``r09`` for six months and
        ``r09b`` for the next six, and no property of the tax can say which.
        Remapping the tax's tags cannot express it: one tax, two answers. The
        version can, because the version is the period.
        """
        ret = self.env["cssk.vat.return"]
        country = self.env.ref("base.sk")
        Tag = self.env["account.account.tag"]
        a = Tag.create({"name": "T09", "applicability": "taxes",
                        "country_id": country.id})
        b = Tag.create({"name": "T09b", "applicability": "taxes",
                        "country_id": country.id})
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-15",
            "line_ids": [
                (0, 0, {"account_id": self.company_data["default_account_revenue"].id,
                        "debit": 100.0, "tax_tag_ids": [(6, 0, a.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_revenue"].id,
                        "debit": 40.0, "tax_tag_ids": [(6, 0, b.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_payable"].id,
                        "credit": 140.0}),
            ],
        })
        move.action_post()
        rec = ret.new({"country_id": country.id,
                       "company_id": self.env.company.id})
        lines = move.line_ids
        self.assertAlmostEqual(rec._eval_tags("T09", lines), 100.0, places=2)
        self.assertAlmostEqual(rec._eval_tags("T09b", lines), 40.0, places=2)
        self.assertAlmostEqual(
            rec._eval_tags("T09|T09b", lines), 140.0, places=2,
            msg="the single band must collect both of the split bands")
        self.assertAlmostEqual(
            rec._eval_tags("-T09|T09b", lines), -140.0, places=2,
            msg="the formula's sign applies to the whole set")

    def test_a_term_may_carry_its_own_sign(self):
        """A line collecting BOTH sides of one quantity cannot have one sign.

        The grid's convention is uniform: every SUPPLIED base line is negative
        (r01 '-01', r03 '-03') and every RECEIVED one positive (r09 '09',
        r18 '18|18a'), because a revenue base is a credit and an expense base a
        debit while the form wants both the same way round.

        SK r24 collects both — `l10n_sk` splits the § 25 base into `24` on the
        domestic sale rates and `24_PR` on the reverse-charge ones — so sharing
        the formula's '-' across the two puts the right MAGNITUDE on the line
        with the wrong SIGN. Measured on a filed return: 2024-12 r24 read
        +190.80 against a filed −190.80.
        """
        ret = self.env["cssk.vat.return"]
        country = self.env.ref("base.sk")
        Tag = self.env["account.account.tag"]
        sale = Tag.create({"name": "T24", "applicability": "taxes",
                           "country_id": country.id})
        purchase = Tag.create({"name": "T24_PR", "applicability": "taxes",
                               "country_id": country.id})
        revenue = self.company_data["default_account_revenue"]
        expense = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-06-15",
            "line_ids": [
                # a supplied correction posts its base as a DEBIT ...
                (0, 0, {"account_id": revenue.id, "debit": 100.0,
                        "tax_tag_ids": [(6, 0, sale.ids)]}),
                # ... and a received one as a CREDIT, already the way the
                # form wants it, which is the whole asymmetry.
                (0, 0, {"account_id": expense.id, "credit": 60.0,
                        "tax_tag_ids": [(6, 0, purchase.ids)]}),
                (0, 0, {"account_id": self.company_data["default_account_payable"].id,
                        "credit": 40.0}),
            ],
        })
        move.action_post()
        rec = ret.new({"country_id": country.id,
                       "company_id": self.env.company.id})
        lines = move.line_ids

        self.assertAlmostEqual(
            rec._eval_tags("-T24|+T24_PR", lines), -160.0, places=2,
            msg="both sides must reduce the base: -100 and -60")
        self.assertAlmostEqual(
            rec._eval_tags("-T24|T24_PR", lines), -40.0, places=2,
            msg="sharing one sign makes the two halves partly cancel — this "
                "is the defect, kept as a test so the difference is visible")
        # An unsigned term still inherits the formula's sign, so every
        # existing definition keeps its meaning exactly.
        self.assertAlmostEqual(
            rec._eval_tags("T24|T24_PR", lines), 40.0, places=2)
        self.assertAlmostEqual(
            rec._eval_tags("-T24", lines), -100.0, places=2)

    def test_one_parser_reads_the_formula_for_both_sides(self):
        """The figure and the drill-down must agree on what a formula says.

        They had drifted: the domain spelled the per-term sign as
        ``.replace("+", "|")``, which turns ``-T24|+T24_PR`` into the right
        tags by accident and ``+T24|-T24_PR`` into a lookup of the literal
        string ``-T24_PR`` — no tag is named that, so the drill-down silently
        dropped half the line. No shipped formula writes it that way round
        today; ``_eval_tags`` and ``test_a_term_may_carry_its_own_sign`` commit
        the grammar, so the drill-down has to read the same one.
        """
        rec = self.env["cssk.vat.return"]
        self.assertEqual(
            list(rec._iter_tag_terms("-T24|+T24_PR")),
            [(-1.0, "T24"), (1.0, "T24_PR")])
        self.assertEqual(
            list(rec._iter_tag_terms("+T24|-T24_PR")),
            [(1.0, "T24"), (-1.0, "T24_PR")],
            "a per-term '-' must be read as a sign, not as part of the name")
        self.assertEqual(
            list(rec._iter_tag_terms("-09|09a|09b")),
            [(-1.0, "09"), (-1.0, "09a"), (-1.0, "09b")],
            "an unsigned term inherits the formula's sign")
        self.assertEqual(list(rec._iter_tag_terms("")), [])
        self.assertEqual(list(rec._iter_tag_terms("-")), [])


@tagged("post_install", "-at_install")
class TestLegacyFilings(AccountTestInvoicingCommon):
    """A historical filing records what was submitted; it is not a filing."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.version = cls.env.ref("l10n_sk_vat_return.dph_version_2025")

    def _return(self, legacy=False, date_from="2026-06-01", date_to="2026-06-30"):
        vals = {
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.version.statement_type_ids[0].id,
            "date_from": date_from, "date_to": date_to,
            "period_type": "month",
        }
        if legacy:
            vals.update(legacy=True, legacy_source="PREMIER",
                        legacy_reference="batch-7")
        return self.env["cssk.vat.return"].create(vals)

    def test_a_legacy_amendment_with_no_discovery_date_can_still_be_USED(self):
        """`datumZisteniaDdp` is required to FILE, so not on a record that
        cannot be filed.

        The importer materialises an amendment by setting `original_return_id`,
        which is what tells the comparator a real amendment from the legacy
        original it descends from. The form then made `discovery_date`
        required — correct for a dodatočné DP we submit, and fatal here: the
        record could not be SAVED, and because a button press saves first, it
        could not run any action at all. Reported from a live instance on
        `cssk.vat.return` 138.

        The date was on the original submission; an importer that did not
        receive it has nothing true to write, and inventing a plausible one
        would put a fabricated statutory date on a record an accountant reads
        as history. So the modifier stands down for `legacy`, which is already
        the flag that refuses a state change and a recompute.
        """
        original = self._return(legacy=True)
        amendment = self._return(legacy=True)
        amendment.original_return_id = original
        self.assertFalse(amendment.discovery_date)

        form = Form(amendment)
        form.save()   # the whole bug: this raised, and so did every button

        # ⚠️ And the modifier must still hold where it belongs. A return we
        # actually file needs the date, and a fix that removed the requirement
        # outright would trade an unusable record for an unfilable one.
        live = self._return()
        live.original_return_id = self._return()
        with self.assertRaises(AssertionError, msg=(
                "discovery_date must stay required on a return that will be "
                "submitted — it is mandatory on a dodatočné DP")):
            Form(live).save()

    def test_a_legacy_filing_refuses_the_three_destructive_actions(self):
        """Each would destroy the only copy of what was actually submitted."""
        ret = self._return(legacy=True)
        for action in ("action_compute_lines", "action_export_xml",
                       "action_submit"):
            with self.assertRaises(UserError, msg=action):
                getattr(ret, action)()
        with self.assertRaises(UserError):
            ret.write({"state": "exported"})

    def test_an_ordinary_filing_is_untouched(self):
        """The guard must not cost anything to a real return."""
        ret = self._return()
        ret.action_compute_lines()
        self.assertTrue(ret.line_ids)

    def test_an_amendment_of_a_legacy_filing_is_an_ordinary_return(self):
        """``copy=False`` on the flag, and why it matters.

        ``action_create_amendment`` builds the amendment with ``copy()``. An
        Odoo Boolean copies by default, so a careless flag would make the
        dodatočné against a historical period itself legacy — unsubmittable and
        unrecomputable, which is the one case the design deliberately keeps.
        """
        legacy = self._return(legacy=True)
        action = legacy.action_create_amendment()
        amendment = self.env["cssk.vat.return"].browse(action["res_id"])
        self.assertFalse(amendment.legacy,
                         "the amendment must be an ordinary return")
        self.assertEqual(amendment.original_return_id, legacy,
                         "and must still point back at what it amends")
        self.assertFalse(amendment.legacy_source)
        amendment.action_compute_lines()   # must not raise

    def test_a_legacy_filing_is_not_the_prior_period_for_the_carry(self):
        """§ 79 carry must not be pulled out of a migrated figure."""
        legacy = self._return(legacy=True, date_from="2026-05-01",
                              date_to="2026-05-31")
        legacy.excess_carried_out = 100.0
        current = self._return()
        self.assertFalse(
            current._find_prior_return(),
            "a historical filing must not answer 'the previous period'")
        real = self._return(date_from="2026-04-01", date_to="2026-04-30")
        self.assertEqual(current._find_prior_return(), real)

    def test_comparison_says_cannot_rather_than_zero_when_no_data(self):
        """"I cannot compute this period" and "I compute zero" are different
        facts, and reporting the first as the second turns an unimportable
        period into a wall of differences."""
        legacy = self._return(legacy=True, date_from="2019-06-01",
                              date_to="2019-06-30")
        result = legacy._cssk_compare_to_computed()
        self.assertFalse(result["comparable"])
        self.assertIn("never imported", result["reason"])
        self.assertEqual(result["rows"], [])

    def _filed(self, legacy, rows):
        self.env["cssk.vat.return.line"].create([
            {"return_id": legacy.id, "code": code, "name": code, "value": val}
            for code, val in rows
        ])

    def test_a_difference_becomes_a_record_somebody_can_answer(self):
        """The chatter records that a difference was seen; it gives nobody a
        way to work through it.

        A difference against a historical filing has a life of its own —
        somebody asks the accountant who filed it whether the filing was right
        — so each one becomes a record with a question and an answer on it.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)   # the helper sets legacy_source
        self._filed(legacy, [("r03", 999.0)])
        legacy.action_cssk_compare_to_computed()

        found = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id)])
        self.assertTrue(found, "no discrepancy was recorded")
        r03 = found.filtered(lambda d: d.code == "r03")
        self.assertEqual(r03.kind, "amount")
        self.assertEqual(r03.filed, 999.0)
        self.assertEqual(r03.state, "open")
        self.assertEqual(r03.legacy_source, "PREMIER")

    def test_an_answer_survives_the_next_comparison(self):
        """The whole point: a recompute must not wipe what the accountant said.

        The figures refresh; the state and the note are left exactly as
        somebody left them. Otherwise the second run asks the same question
        again and the answer is lost with the first.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        legacy.action_cssk_compare_to_computed()
        Disc = self.env["cssk.filing.discrepancy"]
        rec = Disc.search([("res_id", "=", legacy.id), ("code", "=", "r03")])
        rec.write({"state": "correct_as_filed",
                   "note": "Asked 2026-09-10. Rounding policy, filed as-is."})
        self.assertTrue(rec.resolved_uid, "resolving must stamp who and when")

        legacy.action_cssk_compare_to_computed()
        rec.invalidate_recordset()
        self.assertEqual(rec.state, "correct_as_filed")
        self.assertIn("Rounding policy", rec.note)
        self.assertEqual(
            Disc.search_count([("res_id", "=", legacy.id), ("code", "=", "r03")]),
            1, "the row must be updated, not duplicated")

    def test_a_row_that_stops_differing_is_marked_not_deleted(self):
        """A deleted resolved item looks exactly like one nobody ever saw.

        Same reasoning as the carry-over notes: the next reader would raise it
        a second time. It is marked stale and kept.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        # r03 matches, so the vocabularies meet and rZZ is reported on its own
        # rather than collapsed into "not mapped" — see the collapse test.
        self._filed(legacy, [("r03", 999.0), ("rZZ", 5.0)])
        legacy.action_cssk_compare_to_computed()
        Disc = self.env["cssk.filing.discrepancy"]
        rec = Disc.search([("res_id", "=", legacy.id), ("code", "=", "rZZ")])
        self.assertTrue(rec)
        rec.state = "filing_error"

        legacy.line_ids.filtered(lambda ln: ln.code == "rZZ").unlink()
        legacy.action_cssk_compare_to_computed()
        rec.invalidate_recordset()
        self.assertTrue(rec.exists(), "a resolved item must not be deleted")
        self.assertTrue(rec.stale)
        self.assertEqual(rec.state, "filing_error", "and keeps its answer")

    def test_one_amount_on_two_different_rows_is_ONE_disagreement(self):
        """A classification disagreement, paired and labelled as such.

        Two engines can agree on an amount and disagree about which row it
        belongs on. That arrives as a row only the filing has and a row only
        we compute, offsetting exactly — one disagreement, not two, and the
        question is which box is right rather than which figure. Measured on
        real data: a § 69 reverse charge filed on the goods pair and computed
        onto the services row, 59.00 on each side.
        """
        legacy = self._return(legacy=True)
        bad = [
            {"code": "r09", "filed": 59.0, "computed": None,
             "diff": -59.0, "status": "only_filed"},
            {"code": "r11", "filed": None, "computed": 59.0,
             "diff": 59.0, "status": "only_computed"},
            {"code": "r25", "filed": None, "computed": 12.0,
             "diff": 12.0, "status": "only_computed"},
        ]
        pairs = legacy._cssk_pair_classifications(bad)
        self.assertEqual(pairs.get("r09"), "r11")
        self.assertEqual(pairs.get("r11"), "r09")
        self.assertNotIn("r25", pairs,
                         "an unmatched amount is not a classification pair")

    def test_an_unmapped_vocabulary_is_ONE_record_not_forty(self):
        """Rows that are each true and collectively false.

        A filing staged under a source's own names shares no code with what we
        compute, so every computed row becomes a difference the filing
        "lacks". Reported individually that says we found forty problems in
        the period rather than one, and it buries the differences that are
        real: on the first agenda this ran against, 1 292 of 1 294 records
        were exactly this and the two that mattered were lost in them.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        # filed under the SOURCE's vocabulary — nothing we would ever emit
        self._filed(legacy, [("P03_DODANI", 1000.0), ("P02_ZDAN_D", 200.0)])
        legacy.action_cssk_compare_to_computed()

        found = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id),
            ("stale", "=", False)])
        self.assertEqual(len(found), 1,
                         "an unmapped vocabulary is one fact: %s"
                         % found.mapped("code"))
        self.assertEqual(found.kind, "unmapped")
        self.assertIn("have not been mapped", found.detail)

    def test_one_matched_row_is_enough_to_report_each_difference(self):
        """...and the moment the vocabularies DO meet, nothing is collapsed.

        A single agreeing code proves the two sides are talking about the same
        form, and from then on a one-sided row is a genuine finding — a line
        the filing omitted, or one we produce that it never had. Collapsing
        then would hide exactly what the comparison is for.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0), ("P03_DODANI", 1000.0)])
        legacy.action_cssk_compare_to_computed()

        found = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id),
            ("stale", "=", False)])
        kinds = set(found.mapped("kind"))
        self.assertNotIn("unmapped", kinds,
                         "one matched row means the vocabularies meet")
        self.assertIn("amount", kinds, "and r03 must be reported as differing")
        self.assertIn("P03_DODANI", found.mapped("code"))

    def test_every_discrepancy_carries_its_company(self):
        """Cheap, and it was asked: the field is set unconditionally.

        A worklist that cannot be filtered by company is not usable on a
        multi-company database, and an unset company_id would silently drop
        rows out of any search that filters on it.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        legacy.action_cssk_compare_to_computed()
        found = self.env["cssk.filing.discrepancy"].search(
            [("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id)])
        self.assertTrue(found)
        self.assertFalse(found.filtered(lambda d: not d.company_id),
                         "every discrepancy must name its company")
        self.assertEqual(set(found.mapped("company_id")), {self.company})

    def test_an_empty_row_nobody_filed_is_not_a_finding(self):
        """A row with no money on either side crowds out the ones with money.

        A form row we compute as zero that the filing did not carry is not a
        difference in either direction — the tax office cannot tell an unfiled
        row from a zero one. On the period that prompted this, 32 of 38
        one-sided rows were exactly that, sitting around the two findings that
        mattered.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])   # matches, so nothing collapses
        legacy.action_cssk_compare_to_computed()

        found = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id),
            ("stale", "=", False)])
        empty = found.filtered(
            lambda d: d.kind == "only_computed" and not d.computed)
        self.assertFalse(empty, "empty one-sided rows must not be recorded: %s"
                                % empty.mapped("code"))
        self.assertIn("r03", found.mapped("code"),
                      "and the row that differs must survive")

    def test_a_filed_zero_IS_a_finding(self):
        """The asymmetry, asserted.

        A row the filing carries as 0.00 is a positive statement — the company
        reported nothing there — so disagreeing with it is a finding. A row we
        happen to leave empty says nothing at all. Mirroring the zero-drop
        onto the filed side would silently drop the first kind.
        """
        legacy = self._return(legacy=True)
        bad = [
            {"code": "rA", "filed": 0.0, "computed": None,
             "diff": 0.0, "status": "only_filed"},
            {"code": "rB", "filed": None, "computed": 0.0,
             "diff": 0.0, "status": "only_computed"},
            {"code": "rC", "filed": None, "computed": 12.0,
             "diff": 12.0, "status": "only_computed"},
        ]
        kept = {r["code"] for r in legacy._cssk_drop_empty_rows(bad)}
        self.assertIn("rA", kept, "a filed zero is a statement, and stays")
        self.assertNotIn("rB", kept, "a computed zero nobody filed is not")
        self.assertIn("rC", kept, "and a computed figure stays")

    def test_a_ROW_BASED_form_compares_tuples_and_must_not_raise(self):
        """The shape the whole comparison path had never been handed.

        A coded form compares floats; a control statement and an EC sales list
        compare a TUPLE per row — (base, tax, rate, deduction, …). Three
        places asked ``abs()`` of that value, which is a TypeError, so
        comparing a KV with a ledger behind it died outright. Found by running
        it: KV/KH 2017-03 on a live agenda, "bad operand type for abs():
        'tuple'".

        Emptiness has to read the WHOLE tuple as well. Testing only the
        leading figure drops a row whose base is zero and whose daň is not,
        which on a KV is a § 69 reverse charge.
        """
        legacy = self._return(legacy=True)
        bad = [
            {"code": "A.1 SK202/1", "filed": (91.67, 18.33, 20.0, 0.0, ""),
             "computed": None, "diff": -91.67, "status": "only_filed"},
            {"code": "B.2 SK303/9", "filed": None,
             "computed": (91.67, 18.33, 20.0, 0.0, ""),
             "diff": 91.67, "status": "only_computed"},
            {"code": "B.1 SK404/7", "filed": None,
             "computed": (0.0, 0.0, 0.0, 0.0, ""),
             "diff": 0.0, "status": "only_computed"},
            {"code": "B.1 SK505/3", "filed": None,
             "computed": (0.0, 12.0, 20.0, 0.0, ""),
             "diff": 0.0, "status": "only_computed"},
        ]
        kept = {r["code"] for r in legacy._cssk_drop_empty_rows(bad)}
        self.assertNotIn("B.1 SK404/7", kept, "every figure zero: not a finding")
        self.assertIn("B.1 SK505/3", kept,
                      "a zero base with daň on it IS a finding")
        pairs = legacy._cssk_pair_classifications(bad)
        self.assertEqual(pairs.get("A.1 SK202/1"), "B.2 SK303/9",
                         "the same money on two rows is one disagreement")

    def test_comparison_diffs_filed_against_a_fresh_computation(self):
        """And compares the UNION: a line we produce and the filing does not
        is as interesting as the reverse."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        # what "was filed": one line, deliberately wrong, and one we never emit
        self.env["cssk.vat.return.line"].create([
            {"return_id": legacy.id, "code": "r03", "name": "r03",
             "value": 999.0},
            {"return_id": legacy.id, "code": "rZZ", "name": "rZZ",
             "value": 5.0},
        ])
        result = legacy._cssk_compare_to_computed()
        self.assertTrue(result["comparable"], result["reason"])
        rows = {r["code"]: r for r in result["rows"]}
        self.assertEqual(rows["r03"]["status"], "differs")
        self.assertEqual(rows["r03"]["filed"], 999.0)
        self.assertEqual(rows["rZZ"]["status"], "only_filed")
        self.assertIn("only_computed",
                      {r["status"] for r in result["rows"]},
                      "lines we produce and the filing lacks must show up")
        # the scratch record must not survive
        self.assertEqual(
            self.env["cssk.vat.return"].search_count([
                ("company_id", "=", self.company.id),
                ("date_from", "=", "2026-06-01"),
            ]), 1, "the scratch computation must be destroyed")

    # ------------------------------------------------------------------
    # the `legacy` STATE — one fact, written two ways, joined in the ORM
    # ------------------------------------------------------------------
    def test_creating_a_legacy_filing_lands_on_the_legacy_state(self):
        """The flag and the state cannot come apart, and this is why.

        The importer sets ``legacy`` and never touches ``state``, so before
        the two were joined every materialised filing kept the default and
        read "Draft" — 134 control statements, 81 VAT returns and 2 DPPO on
        one agenda, all completed and submitted years ago, all claiming to be
        unfinished work. A ribbon on the form does not reach a list view.
        """
        legacy = self._return(legacy=True)
        self.assertEqual(legacy.state, "legacy")
        self.assertTrue(legacy.legacy)

    def test_flagging_an_existing_filing_moves_it_too(self):
        """``create`` is not the only way in — a re-materialisation writes."""
        ret = self._return()
        self.assertEqual(ret.state, "draft")
        ret.write({"legacy": True, "legacy_source": "MRP"})
        self.assertEqual(ret.state, "legacy")

    def test_the_legacy_state_is_terminal(self):
        """No transition leads out of it, by any route."""
        legacy = self._return(legacy=True)
        for target in ("draft", "preview", "exported", "submitted",
                       "cancelled"):
            with self.assertRaises(UserError, msg=target):
                legacy.write({"state": target})
        self.assertEqual(legacy.state, "legacy")

    def test_a_legacy_filing_can_still_be_DELETED(self):
        """The one thing "frozen" must NOT mean, and the reason it is a test.

        Marking these ``submitted`` would have been factually true and would
        have deadlocked every one of them: ``unlink`` refuses a submitted
        record and points at ``action_reset_to_draft``, which changes
        ``state`` and is therefore refused in turn by
        ``_cssk_check_not_legacy``. Permanently undeletable — against an
        importer whose whole method is reload-and-remeasure. Same shape as the
        ``ondelete="restrict"`` incident that already cost manual row deletion
        under time pressure on two agendas.
        """
        legacy = self._return(legacy=True)
        legacy.unlink()   # must not raise
        self.assertFalse(legacy.exists())

    def test_an_amendment_leaves_the_legacy_state_behind(self):
        """The amendment is an ordinary return, in state AND in flag.

        ``action_create_amendment`` copies, and ``copy=False`` on the flag
        plus an explicit ``state: draft`` are what keep the copy ordinary. A
        dodatočné raised against a historical period is the one thing these
        records exist to make possible.
        """
        legacy = self._return(legacy=True)
        action = legacy.action_create_amendment()
        amendment = self.env["cssk.vat.return"].browse(action["res_id"])
        self.assertFalse(amendment.legacy)
        self.assertEqual(amendment.state, "draft")
        amendment.action_compute_lines()   # must not raise

    def test_every_statement_model_offers_the_legacy_state(self):
        """The lifecycle is declared FIVE TIMES, so assert it stayed one.

        ``state`` is defined verbatim in each statement base rather than once
        on the mixin. That is the shape of defect this repository keeps paying
        for, and until it is collapsed the only thing standing between five
        copies and four is a test that reads all of them.
        """
        missing = []
        for model in ("cssk.vat.return", "cssk.control.statement",
                      "cssk.ec.summary.statement", "cssk.fs.statement",
                      "cssk.income.tax.return", "l10n.sk.uzpod"):
            if model not in self.env:
                continue
            values = dict(self.env[model]._fields["state"].selection)
            if "legacy" not in values:
                missing.append(model)
        self.assertFalse(
            missing, "these statement models cannot hold a historical "
                     "filing: %s" % ", ".join(missing))

    def test_the_state_alone_marks_a_filing_historical(self):
        """Normalisation runs BOTH ways.

        The importer writes the flag, but a server action or a fixture is as
        likely to write the state, and one direction would let the pair come
        apart depending on which end a caller happened to touch.
        """
        ret = self._return()
        ret.write({"state": "legacy"})
        self.assertTrue(ret.legacy, "the state must carry the flag with it")
        self.assertEqual(ret.state, "legacy")

    def test_clearing_the_flag_alone_is_refused(self):
        """The hole the normalisation alone did not close.

        ``write({"legacy": False})`` names no state, so nothing normalises and
        the record would be left un-flagged but still in state ``legacy`` —
        the exact disagreement the two are joined to prevent. The constraint
        is the guarantee; create/write are only the convenience.
        """
        legacy = self._return(legacy=True)
        with self.assertRaises(ValidationError):
            legacy.write({"legacy": False})

    def test_a_context_default_cannot_leave_the_pair_broken(self):
        """``default_legacy`` is applied by create AFTER the override reads vals.

        So the normalisation cannot see it and only the constraint can. The
        assertion is on the INVARIANT rather than on which of the two fires:
        whether Odoo refuses the create or lets it through, what must never
        exist afterwards is a record whose flag and state disagree.
        """
        vals = {
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.version.statement_type_ids[0].id,
            "date_from": "2026-07-01", "date_to": "2026-07-31",
            "period_type": "month",
        }
        try:
            rec = self.env["cssk.vat.return"].with_context(
                default_legacy=True).create(vals)
        except ValidationError:
            return          # refused, which is the outcome we want
        self.assertEqual(
            bool(rec.legacy), rec.state == "legacy",
            "a context default left the flag and the state disagreeing")

    # ------------------------------------------------------------------
    # the comparison is the rows; the chatter is not a comparison screen
    # ------------------------------------------------------------------
    def test_comparing_posts_NOTHING_to_the_chatter(self):
        """The comparison used to post a copy of itself on every run.

        It is re-run whenever anything changes, which does not make a
        timestamped audit trail — it makes a thread nobody can read, and it
        buries the record it claims to be. The record of the comparison is the
        rows: queryable, answerable, and carrying what the accountant said.
        This asserts the absence, because a stray ``message_post`` added back
        anywhere on this path would look harmless in review.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        before = legacy.message_ids
        action = legacy.action_cssk_compare_to_computed()
        self.assertFalse(
            legacy.message_ids - before,
            "comparing must not post to the chatter: %s"
            % (legacy.message_ids - before).mapped("body"))
        self.assertEqual(action["type"], "ir.actions.act_window",
                         "and it must open the comparison instead")
        self.assertEqual(action["res_model"], "cssk.filing.discrepancy")

    def test_the_rows_that_AGREE_are_recorded_too(self):
        """Otherwise the screen is a defect list, not a comparison.

        A migration is judged by how much of it landed. On the agenda this was
        built for, 583 of 608 rows agree and there was no way to see it: the
        accountant was shown the 25 that did not and nothing else, which reads
        as a broken import rather than a good one.

        They are recorded in state ``agrees`` so the worklist filter (state
        ``open`` / ``asked``) is not buried by them — present when somebody
        opens the comparison, absent when somebody is working through findings.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        # r04 stays wrong on purpose: a filing where EVERY row agrees is the
        # one shape this could pass by accident, since the collapse would not
        # fire either way.
        self._filed(legacy, [("r03", 999.0), ("r04", 1.0)])
        result = legacy._cssk_compare_to_computed()
        r03 = next(r["computed"] for r in result["rows"] if r["code"] == "r03")
        self.assertTrue(r03, "the fixture must produce an r03 to agree on")
        legacy.line_ids.filtered(lambda ln: ln.code == "r03").value = r03
        legacy.action_cssk_compare_to_computed()

        Disc = self.env["cssk.filing.discrepancy"]
        agreed = Disc.search([("res_id", "=", legacy.id),
                              ("res_model", "=", "cssk.vat.return"),
                              ("code", "=", "r03")])
        self.assertTrue(agreed, "an agreeing row must be recorded")
        self.assertEqual(agreed.kind, "ok")
        self.assertEqual(agreed.state, "agrees")
        self.assertEqual(agreed.difference, 0.0)
        worklist = Disc.search([("res_id", "=", legacy.id),
                                ("res_model", "=", "cssk.vat.return"),
                                ("state", "in", ["open", "asked"])])
        self.assertNotIn(agreed, worklist,
                         "an agreeing row must stay out of the worklist")

    def test_a_row_the_source_cannot_state_is_informational_not_a_finding(self):
        """PREMIER keeps ten summary figures; the priznanie has thirty-seven
        rows.

        Every row the source has no column for is missing from the filed side
        for a structural reason. Reported as a difference it is a finding a
        month, on every agenda, that nobody can ever act on — 33 of 57 review
        items on the first PREMIER agenda. The migration says which rows the
        source could state; the rest are recorded for information.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        # r03 agrees on purpose: the point is that the rows the source cannot
        # state do not turn a clean comparison into a worklist.
        result = legacy._cssk_compare_to_computed()
        r03 = next(r["computed"] for r in result["rows"] if r["code"] == "r03")
        legacy.line_ids.filtered(lambda ln: ln.code == "r03").value = r03
        legacy.legacy_stated_codes = "r03"
        legacy.action_cssk_compare_to_computed()

        Disc = self.env["cssk.filing.discrepancy"]
        rows = Disc.search([("res_id", "=", legacy.id),
                            ("res_model", "=", "cssk.vat.return")])
        unstated = rows.filtered(lambda r: r.code != "r03")
        self.assertTrue(unstated, "the computed rows must still be recorded")
        self.assertEqual(set(unstated.mapped("kind")), {"info"})
        self.assertEqual(set(unstated.mapped("state")), {"agrees"},
                         "an informational row is not a worklist item")
        self.assertFalse(rows.comparison_id.finding_count,
                         "rows the source cannot state are not findings")
        self.assertTrue(all(r.detail for r in unstated),
                        "each says why there is nothing to compare")

    def test_a_row_whose_leading_amount_agrees_says_what_moved(self):
        """A KV row compares five figures and the screen shows one delta.

        Where the base matches and the deducted amount does not, the row was
        listed as a difference of 0.00 — a worklist item with no visible
        reason. Two of 24 review items on the first PREMIER agenda were this.
        """
        Submission = self.env["cssk.vat.return"]
        detail = Submission._cssk_row_difference_detail(
            (5487.0, 1262.01, 23.0, 0.0, "202603"),
            (5487.0, 1262.01, 23.0, 1262.01, ""),
        )
        self.assertTrue(detail)
        self.assertIn("4", detail, "it names which figure moved")
        self.assertIn("1262.01", detail)
        self.assertFalse(Submission._cssk_row_difference_detail(
            (1.0, 2.0), (1.0, 2.0)), "rows that agree have nothing to say")

    def test_a_row_the_source_states_and_omits_is_still_a_finding(self):
        """The distinction is the point: a stated row that is absent differs."""
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        result = legacy._cssk_compare_to_computed()
        stated = [r["code"] for r in result["rows"]]
        legacy.legacy_stated_codes = ",".join(stated)
        legacy.action_cssk_compare_to_computed()

        Disc = self.env["cssk.filing.discrepancy"]
        rows = Disc.search([("res_id", "=", legacy.id),
                            ("res_model", "=", "cssk.vat.return"),
                            ("kind", "=", "only_computed")])
        self.assertTrue(rows, "a row the source states but omits still counts")

    def test_an_answered_row_that_starts_agreeing_keeps_its_answer(self):
        """The state is the machine's only while nobody has engaged with it.

        ``open`` and ``agrees`` both mean "nobody has said anything yet", so
        they follow the figures. Anything past them is somebody's answer, and
        a row that now agrees still has a conversation to close — overwriting
        it to ``agrees`` would throw that away silently, which is exactly the
        failure the notes were built to prevent.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        self._filed(legacy, [("r03", 999.0)])
        legacy.action_cssk_compare_to_computed()
        Disc = self.env["cssk.filing.discrepancy"]
        rec = Disc.search([("res_id", "=", legacy.id), ("code", "=", "r03")])
        rec.write({"state": "asked", "note": "Asked 2026-09-13."})

        legacy.line_ids.filtered(lambda ln: ln.code == "r03").value = rec.computed
        legacy.action_cssk_compare_to_computed()
        rec.invalidate_recordset()
        self.assertEqual(rec.kind, "ok", "the figures must refresh")
        self.assertEqual(rec.state, "asked", "and the answer must survive")
        self.assertIn("2026-09-13", rec.note)

    def test_rows_that_AGREE_prove_the_vocabularies_meet(self):
        """The case the collapse heuristic could not see, and misreported.

        ``_cssk_collapse_unmapped`` is handed only the non-ok rows, so the one
        piece of evidence it accepted that the two sides share a vocabulary was
        a row that DIFFERS. A row that matches to the cent — the strongest
        proof available — had been filtered out one line earlier.

        Found on a live migration: a DPH 2018-02 return where 19 rows mapped
        and agreed exactly, 0 differed, and 23 were rows we compute that the
        filing does not carry. The accountant was told the vocabulary was not
        mapped at all. On that dataset most periods have that shape, so the
        better the import, the more confidently the screen lied about it.
        """
        self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True)
        legacy = self._return(legacy=True)
        # r03 is filed at exactly what we compute, so it lands as `ok`.
        computed = legacy.copy({"legacy": False, "legacy_source": False,
                                "legacy_reference": False, "state": "draft",
                                "original_return_id": False})
        computed.action_compute_lines()
        r03 = computed.line_ids.filtered(lambda ln: ln.code == "r03")
        agreed = r03.value if r03 else 0.0
        computed.unlink()
        self._filed(legacy, [("r03", agreed)])

        result = legacy._cssk_compare_to_computed()
        statuses = {r["status"] for r in result["rows"]}
        self.assertIn("ok", statuses, "r03 must agree for this test to mean "
                                      "anything: %s" % statuses)
        self.assertNotIn("differs", statuses,
                         "no row may differ, or the old code would pass too")

        legacy.action_cssk_compare_to_computed()
        found = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.vat.return"), ("res_id", "=", legacy.id),
            ("stale", "=", False)])
        self.assertNotIn(
            "unmapped", set(found.mapped("kind")),
            "rows that agree are proof the vocabularies meet; the collapse "
            "must not fire")


@tagged("post_install", "-at_install")
class TestFilingComparisonRollup(AccountTestInvoicingCommon):
    """The comparison parent: identity, and the state it derives.

    The derived state is the part worth testing, because the rule that makes
    it right is the one a reader would not guess: ``expected`` and ``info``
    rows are NOT findings. The row model calls them "findings of neither
    agreement nor error" — a KV is a proper subset of the priznanie — so a
    comparison whose only non-agreeing rows are structural must read
    ``clean``. Counting them would flag every correct KV as needing review,
    which is precisely what this screen exists to avoid.

    Every fixture below uses SEVERAL codes on purpose. An earlier bug in this
    area survived four tests because each of them used one, so none ever
    reached the second iteration of the loop that was broken.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.version = cls.env["cssk.vat.return.version"].create({
            "name": "RU", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": _xml_template(cls.env, "cssk_rollup_tmpl").id,
            "xml_root_element": "DPH",
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"}),
            ],
        })

    def _make_return(self):
        return self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    @staticmethod
    def _row(code, kind, filed=0.0, computed=0.0):
        return {"code": code, "label": "row %s" % code, "kind": kind,
                "filed": filed, "computed": computed,
                "diff": filed - computed}

    def _upsert(self, ret, rows, basis="recomputed"):
        ret._cssk_upsert_comparison_rows(rows, basis)
        return self.env["cssk.filing.comparison"].search(
            [("res_model", "=", ret._name), ("res_id", "=", ret.id),
             ("basis", "=", basis)])

    # -- identity ------------------------------------------------------
    def test_one_parent_per_filing_and_basis(self):
        ret = self._make_return()
        rows = [self._row("01", "ok"), self._row("02", "ok"),
                self._row("03", "amount", 10.0, 7.0)]
        first = self._upsert(ret, rows)
        self.assertEqual(len(first), 1)
        self.assertEqual(first.line_ids.mapped("code"), ["01", "02", "03"])
        # `mapped` on a Many2one returns a deduplicated recordset, so every
        # line pointing at this parent makes it equal to the parent itself.
        # This used to read `all(... == first)`, which asks `all()` to iterate
        # the BOOLEAN that comparing two recordsets produces — an error the
        # test never reached, because its own setUpClass died first.
        self.assertEqual(first.line_ids.mapped("comparison_id"), first)

    def test_a_re_run_reuses_the_parent(self):
        ret = self._make_return()
        rows = [self._row("01", "ok"), self._row("02", "amount", 5.0, 1.0)]
        first = self._upsert(ret, rows)
        again = self._upsert(ret, rows)
        self.assertEqual(first, again, "a re-run must not create a second "
                                       "comparison for the same basis")

    def test_a_second_basis_is_a_second_comparison(self):
        """``basis`` is in the key because the same filing put beside a
        recomputation of itself and beside účet 343 is two comparisons."""
        ret = self._make_return()
        rows = [self._row("01", "ok"), self._row("02", "ok")]
        recomputed = self._upsert(ret, rows, "recomputed")
        ledger = self._upsert(ret, rows, "ledger")
        self.assertNotEqual(recomputed, ledger)
        self.assertEqual(ret.cssk_comparison_count, 2)

    # -- the derived state ---------------------------------------------
    def test_every_row_agreeing_is_clean(self):
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok"), self._row("02", "ok"),
                                  self._row("03", "ok")])
        self.assertEqual(comp.state, "clean")
        self.assertEqual(comp.agree_count, 3)
        self.assertEqual(comp.finding_count, 0)

    def test_a_structural_gap_is_not_a_finding(self):
        """The rule the whole screen turns on. ``expected`` and ``info`` are
        neither agreement nor error, so a comparison carrying only those
        beside agreeing rows is CLEAN and must not enter anybody's worklist."""
        ret = self._make_return()
        comp = self._upsert(ret, [
            self._row("01", "ok"),
            self._row("02", "expected", 100.0, 0.0),
            self._row("03", "info", 40.0, 25.0),
        ])
        self.assertEqual(comp.finding_count, 0)
        self.assertEqual(comp.state, "clean")

    def test_an_unanswered_difference_is_open(self):
        ret = self._make_return()
        comp = self._upsert(ret, [
            self._row("01", "ok"),
            self._row("02", "amount", 10.0, 7.0),
            self._row("03", "only_filed", 5.0, 0.0),
        ])
        self.assertEqual(comp.finding_count, 2)
        self.assertEqual(comp.open_count, 2)
        self.assertEqual(comp.state, "open")

    def test_answering_some_is_in_progress_and_all_is_resolved(self):
        ret = self._make_return()
        comp = self._upsert(ret, [
            self._row("01", "ok"),
            self._row("02", "amount", 10.0, 7.0),
            self._row("03", "only_computed", 0.0, 4.0),
        ])
        findings = comp.line_ids.filtered(lambda r: r.code in ("02", "03"))
        findings[0].state = "correct_as_filed"
        self.assertEqual(comp.state, "in_progress")
        self.assertEqual(comp.answered_count, 1)
        findings[1].state = "our_error"
        self.assertEqual(comp.state, "resolved")
        self.assertEqual(comp.open_count, 0)

    def test_asking_is_engagement_not_an_answer(self):
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok"),
                                  self._row("02", "amount", 9.0, 2.0)])
        comp.line_ids.filtered(lambda r: r.code == "02").state = "asked"
        self.assertEqual(comp.state, "in_progress")
        self.assertEqual(comp.answered_count, 0)
        self.assertEqual(comp.asked_count, 1)

    def test_a_row_that_stops_appearing_stops_counting(self):
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok"),
                                  self._row("02", "amount", 10.0, 7.0),
                                  self._row("03", "amount", 3.0, 1.0)])
        self.assertEqual(comp.state, "open")
        # The second run no longer produces 02 or 03 at all.
        comp = self._upsert(ret, [self._row("01", "ok")])
        self.assertEqual(comp.stale_count, 2)
        self.assertEqual(comp.finding_count, 0)
        self.assertEqual(comp.state, "clean")

    # -- the sign-off is not the state ---------------------------------
    def test_sign_off_is_independent_of_the_derived_state(self):
        """A clean comparison nobody has read must be visibly different from
        one somebody has accepted, so the sign-off cannot live on ``state``."""
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok"), self._row("02", "ok")])
        self.assertEqual(comp.state, "clean")
        self.assertFalse(comp.signed_off_uid)
        comp.action_cssk_sign_off()
        self.assertEqual(comp.signed_off_uid, self.env.user)
        self.assertEqual(comp.state, "clean")
        comp.action_cssk_unsign()
        self.assertFalse(comp.signed_off_date)

    # -- the label follows the READER, which is the whole point ----------
    def test_the_form_label_renders_in_the_reader_s_language(self):
        """The defect this replaced: the label was stored as text in the
        language of whoever ran the comparison, so a comparison run in English
        read English to everybody afterwards and the only repair was to re-run
        it — seven filings by hand on the demo box to turn one screen Slovak.

        ``res_model`` stores the key; the label is rendered from it per reader.
        Same record, two languages, two labels.
        """
        self.env["res.lang"]._activate_lang("sk_SK")
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok"), self._row("02", "ok")])
        self.assertEqual(comp.res_model, "cssk.vat.return",
                         "the stored value is the key, not a label")

        def label(lang):
            rec = comp.with_context(lang=lang)
            return dict(rec._fields["res_model"]._description_selection(rec.env)
                        ).get("cssk.vat.return")

        en, sk = label("en_US"), label("sk_SK")
        self.assertEqual(en, "VAT return")
        self.assertEqual(sk, "daňové priznanie k DPH")
        self.assertNotEqual(en, sk, "the label must follow the reader")

    def test_the_form_key_is_still_groupable(self):
        """Keeping it groupable is why this is a Selection and not a plain
        computed label — the 'Form' group-by needs a stored column."""
        ret = self._make_return()
        self._upsert(ret, [self._row("01", "ok"), self._row("02", "amount", 5.0, 1.0)])
        groups = self.env["cssk.filing.comparison"]._read_group(
            [("res_model", "=", ret._name)], ["res_model"], ["__count"])
        self.assertTrue(groups)
        self.assertEqual(groups[0][0], "cssk.vat.return")

    def test_the_recomputed_basis_stores_no_redundant_label(self):
        """It used to restate the (translated) `basis` selection in English,
        and being stored it was written in the runner's language."""
        ret = self._make_return()
        comp = self._upsert(ret, [self._row("01", "ok")])
        self.assertFalse(comp.basis_label)
        self.assertEqual(comp.basis, "recomputed")


@tagged("post_install", "-at_install")
class TestArchivedVintages(AccountTestInvoicingCommon):
    """Archiving a superseded vzor must not break the filings that used it.

    The point of keeping historical vintages at all is recomputing legacy
    imports, so archiving them to tidy the configuration list has to stay a
    PRESENTATION decision. It very nearly was not: four lookups in the importer
    and one default here were plain top-level searches, which ``active_test``
    filters — and every one of them answered a miss with a bare ``return
    None``, so an archived vintage would have made every historical filing
    silently fail to materialise while the comparison reported nothing wrong.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.version = cls.env["cssk.vat.return.version"].create({
            "name": "AV", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2016-01-01", "valid_to": "2016-12-31",
            "xml_template_ref_id": _xml_template(cls.env, "cssk_vintage_tmpl").id,
            "xml_root_element": "DPH",
            "statement_type_ids": [
                (0, 0, {"code": "R", "name": "Riadny", "fa_xml_value": "R"}),
            ],
            "line_def_ids": [
                (0, 0, {"code": "01", "name": "Základ 20 %", "sequence": 10}),
                (0, 0, {"code": "02", "name": "Daň 20 %", "sequence": 20}),
            ],
        })

    def test_only_the_version_carries_active(self):
        """The fact the whole approach rests on. If a line definition or a
        statement type gained an ``active`` field, archiving a version would
        start cascading and recomputation WOULD break."""
        for model in ("cssk.vat.return.line.def", "cssk.vat.return.type"):
            self.assertNotIn(
                "active", self.env[model]._fields,
                "%s must not be archivable, or archiving a version would hide "
                "the definitions a historical filing is recomputed from" % model)

    def test_archiving_hides_the_version_from_a_plain_search(self):
        """The hazard itself, asserted rather than assumed — this is what the
        importer's four lookups were walking into."""
        Version = self.env["cssk.vat.return.version"]
        domain = [("country_id", "=", self.env.ref("base.sk").id),
                  ("valid_from", "<=", "2016-06-30")]
        self.assertIn(self.version, Version.search(domain))
        self.version.active = False
        self.assertNotIn(self.version, Version.search(domain))
        self.assertIn(
            self.version,
            Version.with_context(active_test=False).search(domain),
            "active_test=False is the only thing that finds it again")

    def test_an_archived_version_still_yields_its_definitions(self):
        """Recomputing a filing already linked to the vintage goes through the
        stored Many2one and a One2many on a model with no ``active``, so none
        of it is filtered."""
        self.version.active = False
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": "2016-01-01", "date_to": "2016-01-31",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })
        self.assertEqual(ret.version_id, self.version,
                         "an archived Many2one target still reads back")
        self.assertEqual(
            sorted(ret.version_id.line_def_ids.mapped("code")), ["01", "02"],
            "the line definitions must survive the version being archived")
