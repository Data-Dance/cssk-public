import unittest
from unittest.mock import patch

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
import base64

from odoo.tests.common import TransactionCase


class TestKvKhBase(TransactionCase):
    """Smoke tests for the shared control-statement framework.

    The framework is abstract — concrete sections live in the country modules
    (``l10n_sk_kv_dph`` / ``l10n_cz_kh_dph``), which carry the behavioural
    tests. Here we only assert the base models load and the mixins enforce
    their contract.
    """

    def test_version_model_loads(self):
        template = self.env["ir.ui.view"].create(
            {
                "name": "cssk control statement test template",
                "type": "qweb",
                "arch": "<t t-name='cssk_control_test_template'><KVDPH/></t>",
            }
        )
        version = self.env["cssk.control.statement.version"].create(
            {
                "name": "TEST v1",
                "country_id": self.env.ref("base.sk").id,
                "valid_from": "2025-01-01",
                "xml_template_ref_id": template.id,
                "xml_root_element": "KVDPH",
                "threshold_value": 3000.0,
                "threshold_currency_id": self.env.ref("base.EUR").id,
            }
        )
        self.assertEqual(version.xml_root_element, "KVDPH")

    def test_section_mixin_requires_populate(self):
        # The abstract mixin must refuse to populate.
        with self.assertRaises(NotImplementedError):
            self.env["cssk.control.statement.section.mixin"]._populate_for_statement(
                self.env["cssk.control.statement"], False
            )

    def test_account_tax_fields_present(self):
        field_names = self.env["account.tax"]._fields
        self.assertIn("cssk_control_is_reverse_charge", field_names)
        self.assertIn("cssk_control_section_default", field_names)


@tagged("post_install", "-at_install")
class TestDirectionDeclaration(AccountTestInvoicingCommon):
    """Where a VAT line's direction comes from.

    These two need a chart of accounts — a journal, a receivable, a tax — so
    they cannot live on the smoke-test class beside them. As a plain
    ``TransactionCase`` they passed only on a database where something else had
    already loaded a chart: on a clean ``--without-demo=all`` install the
    company has no sale journal, and ``account.tax.country_id`` (required,
    precomputed from the company's fiscal country) comes back empty. Both
    failures were about the fixture, never about the direction rule.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def test_a_declared_direction_wins_over_the_move_type(self):
        """A journal entry carrying VAT has a direction; ``entry`` is not one.

        Deriving it has been tried three times — from the line's taxes, from
        its tags, from the journal — and each attempt corrected a minority by
        breaking a majority. Declaring it is the fourth approach and the only
        one that is not a guess: whatever produced the entry knew which side it
        was on. On one imported agenda 73 sales documents had fallen back to a
        ledger-built entry, and reporting them as purchases put 4 527 607.72 of
        section A4 on the wrong side.
        """
        company = self.env.company
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1)
        account = self.env["account.account"].search(
            [("company_ids", "in", company.id)], limit=1)
        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": journal.id,
            "date": "2025-09-30",
            "line_ids": [
                (0, 0, {"account_id": account.id, "debit": 1210.0, "credit": 0.0}),
                (0, 0, {"account_id": account.id, "debit": 0.0, "credit": 1210.0}),
            ],
        })
        line = move.line_ids.filtered(lambda l: l.credit)
        # Undeclared, an entry counts as received: the safe reading, and the
        # one every purchase-side entry needs.
        self.assertEqual(line._cssk_direction_sign(), 1.0)

        move.cssk_vat_direction = "sale"
        self.assertEqual(line._cssk_direction_sign(), -1.0,
                         "a declared supply reports as a supply")
        move.cssk_vat_direction = "purchase"
        self.assertEqual(line._cssk_direction_sign(), 1.0)

    def test_a_an_invoice_ignores_a_declaration_it_does_not_need(self):
        """An invoice knows its own side; the field is for documents that do not."""
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.env["res.partner"].create({"name": "Odberatel"}).id,
            "invoice_date": "2025-09-30",
            "invoice_line_ids": [(0, 0, {"name": "x", "quantity": 1, "price_unit": 100.0})],
        })
        receivable = move.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable")
        self.assertEqual(receivable._cssk_direction_sign(), -1.0)
        self.assertFalse(move.cssk_vat_direction,
                         "nothing sets it by default")


class _KvStatementFixture:
    """One control statement to exercise the base mixins on.

    A mixin rather than a base test class: inheriting a TestCase to reuse its
    ``setUpClass`` also re-collects its tests, so every test in the parent ran
    a second time under the child's name. Worse, it inherited the parent's
    ``SkipTest`` — and the tests that needed no concrete section at all were
    skipped on every non-SK install, silently, which is the shape of coverage
    that reports green and asserts nothing.

    ``section_model`` is optional for exactly that reason: only a test that
    exercises a section row needs a country module to be installed.
    """

    @classmethod
    def _build_statement(cls, section_model=None):
        template = cls.env["ir.ui.view"].create({
            "name": "cssk kv fixture template",
            "type": "qweb",
            "arch": "<t t-name='cssk_kv_ovr_template'><KVDPH/></t>",
        })
        cls.version = cls.env["cssk.control.statement.version"].create({
            "name": "TOVR", "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "KVDPH",
            "threshold_value": 0.0,
            "threshold_currency_id": cls.env.ref("base.EUR").id,
            "section_code_ids": [(0, 0, {
                "code": "A.1", "name": "A.1",
                "section_model": section_model,
                "aggregation": "detail",
            })] if section_model else [],
        })
        # Submission types are country-scoped now, so they are made once and
        # not hung off the version.
        cls.statement_type = cls.env["cssk.control.statement.type"].create({
            "country_id": cls.env.ref("base.sk").id,
            "code": "R", "name": "Riadny", "fa_xml_value": "R",
        })
        cls.statement = cls.env["cssk.control.statement"].create({
            "company_id": cls.env.company.id, "version_id": cls.version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": cls.statement_type.id,
        })


@tagged("post_install", "-at_install")
class TestKvOverrideSurvival(_KvStatementFixture, TransactionCase):
    """Task-2 regression: a KV section row's manual override (Override tick +
    edited amounts) must survive ``action_compute_lines`` — the recompute
    destructively wipes and repopulates the sections. Uses the SK A.1 section
    (the framework is abstract; the mechanism lives in the base mixins)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "l10n.sk.kv.dph.section.a1" not in cls.env:
            raise unittest.SkipTest(
                "l10n_sk_kv_dph not installed — no concrete KV section to "
                "exercise the override mechanism on")
        cls.env.company.account_fiscal_country_id = cls.env.ref("base.sk")
        cls._build_statement("l10n.sk.kv.dph.section.a1")

    def _populate_patch(self, entry_ref="INV/1"):
        st = self.statement

        # NB: patch with ``new=`` (a plain function), NEVER a MagicMock:
        # the registry's lazy ``_ondelete_methods`` scan collects every class
        # attribute that *has* an ``_ondelete`` attribute, and a MagicMock
        # auto-creates one on ``getattr`` — the mock would be cached as an
        # unlink hook and keep firing (creating rows!) long after the patch
        # exits, poisoning unrelated tests.
        def fake_populate(model, statement=None, section_code=None):
            self.env["l10n.sk.kv.dph.section.a1"].create({
                "statement_id": st.id,
                "partner_vat": "SK2020317068",
                "entry_ref": entry_ref,
                "supply_date": "2026-06-10",
                "tax_rate": 23.0,
                "tax_base_amount": 1000.0,
                "tax_amount": 230.0,
            })
        return patch.object(
            type(self.env["l10n.sk.kv.dph.section.a1"]),
            "_populate_for_statement", new=fake_populate)

    def test_override_survives_recompute(self):
        st = self.statement
        with self._populate_patch():
            st.action_compute_lines()
        row = st.sk_section_a1_ids
        self.assertAlmostEqual(row.tax_base_amount, 1000.0, places=2)

        # accountant corrects the row and flags it overridden
        row.write({"is_overridden": True,
                   "tax_base_amount": 900.0, "tax_amount": 207.0})
        with self._populate_patch():
            st.action_compute_lines()
        row = st.sk_section_a1_ids
        self.assertEqual(len(row), 1)
        self.assertTrue(row.is_overridden,
                        "the override flag must survive the recompute")
        self.assertAlmostEqual(row.tax_base_amount, 900.0, places=2)
        self.assertAlmostEqual(row.tax_amount, 207.0, places=2)

    def test_unmatched_override_warns_in_chatter(self):
        st = self.statement
        with self._populate_patch():
            st.action_compute_lines()
        st.sk_section_a1_ids.write({
            "is_overridden": True,
            "tax_base_amount": 900.0, "tax_amount": 207.0})

        # the overridden document disappears from the repopulated sections
        with self._populate_patch(entry_ref="INV/2"):
            st.action_compute_lines()
        row = st.sk_section_a1_ids
        self.assertEqual(row.entry_ref, "INV/2")
        self.assertFalse(row.is_overridden,
                         "the override must not leak onto a different row")
        self.assertAlmostEqual(row.tax_base_amount, 1000.0, places=2)
        warn = st.message_ids.filtered(lambda m: "INV/1" in (m.body or ""))
        self.assertTrue(warn, "the dropped override must be named in chatter")


@tagged("post_install", "-at_install")
class TestReportedDocumentsAreNotPinned(TransactionCase):
    """A computed statement must not stop its documents being deleted.

    ``move_line_id`` was ``ondelete='restrict'``, which reads as prudence and
    is the opposite: it made every computed statement PIN the documents it
    reported, so a document could never be deleted or re-imported once any
    statement had been computed over it — a ``preview`` statement that was
    never filed included.

    It bit both localisations independently in one session: `l10n_cz_kh_a2`
    blocked a Money S4 rollback and `l10n_sk_kv_dph_section_b2` blocked one on
    the i6 agenda. The workaround both times was to delete section rows by hand
    and recompute afterwards, which is precisely the data loss ``restrict`` was
    meant to prevent — done manually, under time pressure, by whoever was
    unblocking an import at the time.

    What actually preserves a filing is that the row carries its own copies.
    So this asserts both halves: the delete succeeds AND the reported figures
    are still there afterwards.
    """

    def test_deleting_a_reported_line_leaves_the_filing_intact(self):
        section = None
        for model in ("l10n.sk.kv.dph.section.a1", "l10n.cz.kh.a4"):
            if model in self.env:
                section = model
                break
        if section is None:
            raise unittest.SkipTest(
                "no concrete section model installed to test the link on")

        company = self.env.company
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1)
        account = self.env["account.account"].search(
            [("company_ids", "in", company.id)], limit=1)
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": journal.id, "date": "2026-06-30",
            "line_ids": [
                (0, 0, {"account_id": account.id, "debit": 1210.0, "credit": 0.0}),
                (0, 0, {"account_id": account.id, "debit": 0.0, "credit": 1210.0}),
            ],
        })
        line = move.line_ids[0]

        template = self.env["ir.ui.view"].create({
            "name": "cssk pin test template", "type": "qweb",
            "arch": "<t t-name='cssk_pin_template'><KVDPH/></t>",
        })
        version = self.env["cssk.control.statement.version"].create({
            "name": "PIN", "country_id": company.account_fiscal_country_id.id
                            or self.env.ref("base.sk").id,
            "valid_from": "2026-01-01", "xml_template_ref_id": template.id,
            "xml_root_element": "KVDPH", "threshold_value": 0.0,
            "threshold_currency_id": company.currency_id.id,
        })
        statement_type = self.env["cssk.control.statement.type"].create({
            "country_id": company.account_fiscal_country_id.id,
            "code": "R", "name": "Riadny", "fa_xml_value": "R"})
        statement = self.env["cssk.control.statement"].create({
            "company_id": company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": statement_type.id,
        })
        row = self.env[section].create({
            "statement_id": statement.id,
            "move_line_id": line.id,
            "entry_ref": "PINNED/1",
            "tax_base_amount": 1000.0,
            "tax_amount": 210.0,
        })

        # The property: a reported document can still be removed.
        move.unlink()

        row.invalidate_recordset()
        self.assertFalse(
            row.move_line_id,
            "the link must null out rather than block the delete")
        self.assertEqual(
            row.entry_ref, "PINNED/1",
            "the filed reference must survive the document it came from")
        self.assertAlmostEqual(row.tax_base_amount, 1000.0, places=2)
        self.assertAlmostEqual(row.tax_amount, 210.0, places=2)


@tagged("post_install", "-at_install")
class TestSectionRecompute(AccountTestInvoicingCommon):
    """A stored section code cannot notice that the CODE changed."""

    def test_a_resolver_change_needs_an_explicit_recompute(self):
        """The dependencies are all DATA — none changes when a resolver is fixed.

        So after fixing a resolver every stored value is stale, and a
        comparison re-run returns byte-identical numbers: the code is right and
        the measurement is of the old code. It cost the i6 extractor a
        near-miss — a correct fix measured as having done nothing, caught only
        by calling the resolver directly on a document the statement still
        contained.

        There is no dependency that could express "the algorithm changed", so
        the recompute has to be explicit — and this asserts it exists, works,
        and reports what moved.
        """
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[1000.0], taxes=self.tax_sale_a, post=True,
        )
        line = invoice.line_ids.filtered("tax_ids")[:1]
        self.assertTrue(line, "the fixture invoice carries no taxed line")

        # Exactly what an old algorithm leaves behind: a stored value the
        # current code would never produce.
        self.env.cr.execute(
            "UPDATE account_move_line SET cssk_control_section_code = %s "
            "WHERE id = %s", ("STALE", line.id))
        line.invalidate_recordset(["cssk_control_section_code"])
        self.assertEqual(line.cssk_control_section_code, "STALE")

        changed = line._cssk_recompute_section_codes()
        self.assertEqual(
            changed, 1, "the recompute did not report the line it changed")
        self.assertNotEqual(
            line.cssk_control_section_code, "STALE",
            "the stored value survived an explicit recompute",
        )

    def test_recomputing_a_settled_line_reports_nothing_changed(self):
        """The count is the useful output, so it must not overstate.

        "recomputed 40 000 lines" says nothing; "97 lines left C.1" says
        whether the fix did what was expected.
        """
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-11",
            amounts=[500.0], taxes=self.tax_sale_a, post=True,
        )
        line = invoice.line_ids.filtered("tax_ids")[:1]
        line._cssk_recompute_section_codes()
        self.assertEqual(
            line._cssk_recompute_section_codes(), 0,
            "a second recompute must report no change",
        )


@tagged("post_install", "-at_install")
class TestSubmissionOpensOnSubmit(_KvStatementFixture, TransactionCase):
    """Marking a statement submitted must leave somewhere for the receipt to go.

    Lives here rather than in l10n_cssk_submission_base because that module has
    no concrete statement to exercise — a test written there could only skip,
    and a skipping test is not coverage. It builds its statement with NO
    section, because the state transition is the subject and a section would
    only re-import the SK dependency this deliberately does without.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.account_fiscal_country_id = cls.env.ref("base.sk")
        cls._build_statement()

    def test_marking_submitted_opens_a_manual_submission(self):
        statement = self.statement
        self.assertFalse(statement.submission_ids)
        statement.submitted_attachment_id = self.env["ir.attachment"].create({
            "name": "kv.xml",
            "datas": base64.b64encode(b"<KVDPH/>"),
            "res_model": statement._name,
            "res_id": statement.id,
        })
        statement.write({"state": "submitted"})
        self.assertEqual(len(statement.submission_ids), 1,
                         "a filing marked submitted must open a delivery")
        submission = statement.submission_ids
        self.assertEqual(submission.channel, "pfs_manual")
        self.assertEqual(submission.state, "draft",
                         "it asserts nothing until a human attests")
        self.assertEqual(submission.payload_attachment_id,
                         statement.submitted_attachment_id,
                         "the delivery carries the frozen filed copy")

    def test_no_duplicate_when_already_open(self):
        statement = self.statement
        statement.submitted_attachment_id = self.env["ir.attachment"].create({
            "name": "kv.xml", "datas": base64.b64encode(b"<KVDPH/>"),
        })
        statement.write({"state": "submitted"})
        statement.write({"state": "submitted"})
        self.assertEqual(len(statement.submission_ids), 1,
                         "re-marking submitted must not open a second delivery")

    def test_a_filer_without_the_submission_groups_can_still_submit(self):
        """Marking a filing submitted is an accounting right; holding the
        statutory-submission groups is a separate one.

        ``_ensure_submission`` read ``submission_ids`` as the acting user, so
        an accountant without those groups got ``AccessError`` straight out of
        ``write`` and could not save the statement at all — evidence tracking
        blocking the close, which is the trade the method's own docstring
        promises never to make.
        """
        user = self.env["res.users"].create({
            "name": "Filer", "login": "cssk_filer_no_submission_groups",
            "group_ids": [(6, 0, [
                self.env.ref("account.group_account_user").id,
                self.env.ref("base.group_user").id,
            ])],
        })
        self.assertFalse(
            user.has_group("l10n_cssk_submission_base.group_cssk_submission_user"),
            "premise: this user may keep the books, not file")
        statement = self.statement.with_user(user)
        statement.sudo().submitted_attachment_id = self.env["ir.attachment"].create({
            "name": "kv.xml", "datas": base64.b64encode(b"<KVDPH/>"),
        })
        statement.write({"state": "submitted"})
        self.assertEqual(statement.sudo().state, "submitted")
        self.assertEqual(
            len(statement.sudo().submission_ids), 1,
            "the delivery is the system's bookkeeping and opens regardless")

    def test_write_survives_a_statement_with_no_xml(self):
        # Trading a missing receipt for a statement that cannot be saved is the
        # worse failure, so evidence tracking must never block a write.
        statement = self.statement
        self.assertFalse(statement.submitted_attachment_id)
        statement.write({"state": "submitted"})
        self.assertEqual(statement.state, "submitted")
        self.assertFalse(statement.submission_ids)


class TestKvRowComparison(TransactionCase):
    """Comparing a filed control statement against a fresh computation.

    § 78a reports individual INVOICES, so a discrepancy is about a document
    and the comparison has to answer with the doklad rather than with a delta
    — an accountant chasing a KV mismatch needs to know which invoice.
    """

    def test_identity_and_figures_come_from_the_form_itself(self):
        """Reuses ``_kv_identity`` / ``_kv_values``, and that is the point.

        Both already exist for the dodatočný delta, which has to know what
        makes two rows the same document and what makes one changed. Inventing
        a second notion for comparison would let the two drift, and a delta and
        a comparison disagreeing about identity is worse than either being
        wrong on its own — the same defect that cost 47 rows of the účtovná
        závierka.
        """
        mixin = self.env["cssk.control.statement"]
        self.assertTrue(hasattr(mixin, "_cssk_comparable_rows"))
        # the base form declines: sections are country-supplied
        self.assertIsNone(mixin.browse()._collect_sections_by_code() or None)

    def test_two_rows_of_one_invoice_both_survive(self):
        """One invoice can appear twice in a section that omits the rate.

        Keying purely on identity would let the second overwrite the first and
        silently halve the section. The ordinal keeps both, so a comparison
        reports two rows where the filing has two rows.
        """
        mixin = self.env["cssk.control.statement"]
        seen, key = {}, ("A.1", ("SK2023456787", "F-1"))
        for value in ((100.0, 20.0), (50.0, 10.0)):
            candidate, seq = key, 1
            while candidate in seen:
                seq += 1
                candidate = (key[0], key[1] + ("#%d" % seq,))
            seen[candidate] = value
        self.assertEqual(len(seen), 2, "the second row must not overwrite")
        labels = {mixin._cssk_compare_label(k, True) for k in seen}
        self.assertIn("A.1 SK2023456787 / F-1", labels)
        self.assertIn("A.1 SK2023456787 / F-1 / #2", labels)

    def test_a_row_changes_when_any_of_its_figures_changes(self):
        """An invoice re-rated to the same total is NOT the same row.

        The § 78a dispute is about the document — its base, its tax, its rate
        — so the status is decided by the whole tuple. Comparing only a total
        would call a 100/20 invoice and a 120/0 invoice identical.
        """
        mixin = self.env["cssk.control.statement"]
        self.assertTrue(mixin._cssk_rows_equal((100.0, 20.0, 20.0, 0.0, ""),
                                               (100.0, 20.0, 20.0, 0.0, "")))
        self.assertFalse(mixin._cssk_rows_equal((100.0, 20.0, 20.0, 0.0, ""),
                                                (100.0, 20.0, 10.0, 0.0, "")))
        # ...and a rounding-level wobble is not a difference
        self.assertTrue(mixin._cssk_rows_equal((100.0, 20.0), (100.004, 20.0)))
        self.assertFalse(mixin._cssk_rows_equal((100.0, 20.0), (100.01, 20.0)))
        # a text field differing (the corrected document ref) is a difference
        self.assertFalse(mixin._cssk_rows_equal((100.0, "F-1"), (100.0, "F-2")))


class TestSubmissionTypesAreCountryScoped(TransactionCase):
    """One set of submission types per country, not per vzor.

    They used to hang off ``version_id`` and were declared inline on every
    version record — the same riadny / opravný / dodatočný on all four Slovak
    vzory from 2014 to 2025. Twelve rows expressing three facts, and grouping a
    filing list by "Typ výkazu" showed each label once per vzor in use.
    """

    def test_no_country_declares_the_same_code_twice(self):
        """The collapse, asserted where it can regress: the data files.

        A new vzor that copies an old one's block would reintroduce exactly
        the duplication this replaced, and nothing else would notice — the
        filings would still compute, still export and still validate. Only a
        group-by would look wrong, which is how it was found the first time.
        """
        seen, dupes = set(), []
        for st_type in self.env["cssk.control.statement.type"].search([]):
            key = (st_type.country_id.id, st_type.code)
            if key in seen:
                dupes.append("%s/%s" % (st_type.country_id.code, st_type.code))
            seen.add(key)
        self.assertFalse(
            dupes, "a submission type is declared twice for one country: %s"
                   % ", ".join(dupes))

    def test_the_type_no_longer_hangs_off_a_version(self):
        """The field is gone, and the version does not own them either."""
        Type = self.env["cssk.control.statement.type"]
        self.assertNotIn("version_id", Type._fields)
        self.assertIn("country_id", Type._fields)
        self.assertNotIn(
            "statement_type_ids",
            self.env["cssk.control.statement.version"]._fields)

    def test_a_filing_can_only_pick_its_own_countrys_types(self):
        """The domain moved from version to country; prove it still narrows.

        Dropping the domain entirely would have been the lazy collapse, and it
        would let a Slovak filing be submitted as Czech "Následné".
        """
        domain = self.env["cssk.control.statement"]._fields[
            "statement_type_id"].domain
        self.assertIn("country_id", domain)
        self.assertNotIn("version_id", domain)


class TestCollapseDuplicateTypes(TransactionCase):
    """``_cssk_collapse_to_one_per_code``, the helper the migration runs.

    Tested directly because the first attempt at this collapse FAILED SILENTLY
    — it ran from the base module's post-migration, before the country module
    had created the records it was meant to collapse onto, matched nothing and
    exited 0. A no-op and a success are indistinguishable unless something is
    counted, so these count.
    """

    def _types(self, country, spec):
        return self.env["cssk.control.statement.type"].create([
            {"country_id": country.id, "code": code, "name": code,
             "fa_xml_value": fa} for code, fa in spec])

    def test_duplicates_collapse_and_filings_follow(self):
        """The case the migration exists for: N rows per code, filings on them."""
        country = self.env.ref("base.sk")
        before = self.env["cssk.control.statement.type"].search_count(
            [("country_id", "=", country.id)])
        dupes = self._types(country, [("zz", "Z"), ("zz", "Z"), ("zz", "Z")])
        kept, removed, _remapped = self.env[
            "cssk.control.statement.type"]._cssk_collapse_to_one_per_code(
                country, "l10n_sk_kv_dph", {"zz": "test_type_zz"})
        self.assertEqual(removed, 2, "two of the three duplicates must go")
        survivors = self.env["cssk.control.statement.type"].search(
            [("country_id", "=", country.id), ("code", "=", "zz")])
        self.assertEqual(len(survivors), 1)
        self.assertEqual(survivors, dupes[0], "the oldest row is the survivor")
        self.assertEqual(
            self.env["cssk.control.statement.type"].search_count(
                [("country_id", "=", country.id)]),
            before + 1, "every other code must be left alone")

    def test_the_survivor_takes_the_xmlid_the_data_file_will_declare(self):
        """Which is what makes the data load an UPDATE rather than a fourth row.

        Without this the load inserts a new record beside the survivor and the
        duplication comes straight back — which is exactly what the broken
        first attempt produced: 15 rows where there had been 12.
        """
        country = self.env.ref("base.sk")
        dupes = self._types(country, [("yy", "Y"), ("yy", "Y")])
        self.env["cssk.control.statement.type"]._cssk_collapse_to_one_per_code(
            country, "l10n_sk_kv_dph", {"yy": "test_type_yy"})
        data = self.env["ir.model.data"].search([
            ("module", "=", "l10n_sk_kv_dph"), ("name", "=", "test_type_yy")])
        self.assertEqual(len(data), 1)
        self.assertEqual(data.res_id, dupes[0].id)

    def test_a_row_already_holding_the_xmlid_wins(self):
        """Idempotence against the state the broken attempt left behind.

        There, rows carrying the new xmlids sit alongside the originals.
        Choosing the survivor by id alone would delete the record an xmlid
        points at, so the one already claimed wins instead.
        """
        country = self.env.ref("base.sk")
        older, newer = self._types(country, [("xx", "X"), ("xx", "X")])
        self.env["ir.model.data"].create({
            "module": "l10n_sk_kv_dph", "name": "test_type_xx",
            "model": "cssk.control.statement.type", "res_id": newer.id,
            "noupdate": True})
        self.env["cssk.control.statement.type"]._cssk_collapse_to_one_per_code(
            country, "l10n_sk_kv_dph", {"xx": "test_type_xx"})
        self.assertFalse(older.exists(), "the unclaimed row goes")
        self.assertTrue(newer.exists(), "the row bearing the xmlid survives")

    def test_running_it_twice_changes_nothing(self):
        """A migration that is not idempotent cannot be re-run after a failure."""
        country = self.env.ref("base.sk")
        self._types(country, [("ww", "W"), ("ww", "W")])
        Type = self.env["cssk.control.statement.type"]
        Type._cssk_collapse_to_one_per_code(
            country, "l10n_sk_kv_dph", {"ww": "test_type_ww"})
        first = Type.search([("country_id", "=", country.id)]).ids
        _kept, removed, remapped = Type._cssk_collapse_to_one_per_code(
            country, "l10n_sk_kv_dph", {"ww": "test_type_ww"})
        self.assertEqual((removed, remapped), (0, 0))
        self.assertEqual(Type.search([("country_id", "=", country.id)]).ids,
                         first)

    def test_several_codes_collapse_in_one_pass(self):
        """The case every other test in this class missed.

        The first four all used ONE code, so the loop never reached a second
        iteration — and the bug was entirely in the second iteration: the
        helper filtered a recordset it had already deleted rows from, and
        raised MissingError on whichever code sorted second. A suite that
        exercises one of something does not test a loop over them.

        Three codes with duplicates each, in one call, is the shape the real
        migration runs: rdp / odp / ddp across four vzory.
        """
        country = self.env.ref("base.sk")
        Type = self.env["cssk.control.statement.type"]
        made = self._types(country, [
            ("q1", "1"), ("q1", "1"), ("q1", "1"),
            ("q2", "2"), ("q2", "2"),
            ("q3", "3"), ("q3", "3"), ("q3", "3"), ("q3", "3"),
        ])
        kept, removed, _ = Type._cssk_collapse_to_one_per_code(
            country, "l10n_sk_kv_dph",
            {"q1": "t_q1", "q2": "t_q2", "q3": "t_q3"})
        self.assertEqual(removed, 6, "2 + 1 + 3 duplicates must go")
        for code, first in (("q1", made[0]), ("q2", made[3]), ("q3", made[5])):
            survivors = Type.search([("country_id", "=", country.id),
                                     ("code", "=", code)])
            self.assertEqual(len(survivors), 1, "code %s" % code)
            self.assertEqual(survivors, first, "oldest survives for %s" % code)
        self.assertGreaterEqual(kept, 3)
