from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestEcSummaryBase(TransactionCase):
    """Smoke tests for the shared EC sales list framework."""

    def test_models_load(self):
        for model in (
            "cssk.ec.summary.statement.version",
            "cssk.ec.summary.statement",
            "cssk.ec.summary.statement.line",
        ):
            self.assertIn(model, self.env)

    def test_account_tax_field_present(self):
        self.assertIn(
            "cssk_ec_summary_code", self.env["account.tax"]._fields
        )

    def test_an_entry_shaped_supply_is_not_reported_negative(self):
        """The sign must come from the TAX being sale-side, not the move type.

        Every tax carrying `cssk_ec_summary_code` is a sale-side tax — that is
        what puts a supply on this report at all — so a line reaching the
        amount helper is on the supply side whatever shape its document has.
        Reading the sign from `move_type` assumed an invoice, and an imported
        supply posted as a journal ENTRY arrived inverted.

        Found on the first measurement of the súhrnný výkaz ever made against
        filed returns: a synthesised base of -1 836.07 on an entry, reported as
        -1 836.07 where the filing has +2 235.57. Sixteen of eighteen rows
        matched because those documents stayed invoices.
        """
        company = self.env.company
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", company.id)], limit=1)
        account = self.env["account.account"].search(
            [("company_ids", "in", company.id)], limit=1)
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": journal.id, "date": "2026-06-30",
            "line_ids": [
                (0, 0, {"account_id": account.id, "debit": 1836.07,
                        "credit": 0.0}),
                (0, 0, {"account_id": account.id, "debit": 0.0,
                        "credit": 1836.07}),
            ],
        })
        supply = move.line_ids.filtered(lambda l: l.credit)
        self.assertAlmostEqual(
            supply._cssk_ec_amount(), 1836.07, places=2,
            msg="a supply on an entry must report positive, as it does on an "
                "invoice — the report has no notion of an inbound row")

        correction = move.line_ids.filtered(lambda l: l.debit)
        self.assertAlmostEqual(
            correction._cssk_ec_amount(), -1836.07, places=2,
            msg="the correction case must still come out negative, by "
                "arithmetic rather than by a second rule")

    def test_vies_preflight_blocks_invalid(self):
        template = self.env["ir.ui.view"].create({
            "name": "cssk ec summary test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_ec_summary_test_template'><SDV/></t>",
        })
        version = self.env["cssk.ec.summary.statement.version"].create({
            "name": "T", "country_id": self.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "SDV",
        })
        st_type = self.env["cssk.ec.summary.statement.type"].create({
            "version_id": version.id, "code": "R", "name": "Riadny",
            "fa_xml_value": "R",
        })
        st = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.env.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month", "statement_type_id": st_type.id,
        })
        self.env["cssk.ec.summary.statement.line"].create({
            "statement_id": st.id, "partner_country_code": "",
            "partner_vat": "", "transaction_code": "0",
        })
        st.state = "preview"
        from odoo.exceptions import UserError
        # master-data preflight fires first: no company VAT → named error
        self.env.company.vat = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        self.assertIn("VAT", str(cm.exception))
        # with the company VAT set, the VIES line gate still hard-blocks the
        # line with the missing/non-EU customer VAT
        self.env.company.vat = "SK2023456787"
        with self.assertRaises(UserError):
            st.action_export_xml()

    def _make_statement(self):
        template = self.env["ir.ui.view"].create({
            "name": "cssk ec summary override test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_ec_summary_ovr_template'><SDV/></t>",
        })
        version = self.env["cssk.ec.summary.statement.version"].create({
            "name": "TOVR", "country_id": self.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "SDV",
        })
        st_type = self.env["cssk.ec.summary.statement.type"].create({
            "version_id": version.id, "code": "R", "name": "Riadny",
            "fa_xml_value": "R",
        })
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.env.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month", "statement_type_id": st_type.id,
        })

    def _line_vals(self, st, vat="DE811907980", country="DE", code="0",
                   amount=1000.0):
        return [{
            "statement_id": st.id,
            "partner_country_code": country,
            "partner_vat": vat,
            "transaction_code": code,
            "total_amount": amount,
            "supplies_count": 1,
        }]

    def _compute_patch(self, st, **line_kwargs):
        # NB: patch with ``new=`` (a plain function), NEVER a MagicMock — the
        # registry's lazy ``_ondelete_methods`` scan collects every class
        # attribute that *has* an ``_ondelete`` attribute, and a MagicMock
        # auto-creates one on ``getattr``, so it would be cached as an unlink
        # hook and poison unrelated tests.
        def fake_compute(model):
            return self._line_vals(st, **line_kwargs)
        return patch.object(
            type(self.env["cssk.ec.summary.statement"]),
            "_compute_line_values", new=fake_compute)

    def test_manual_override_survives_recompute(self):
        """Task-2 regression: an EC line's manual override must survive
        ``action_compute_lines`` (the recompute is destructive) — re-applied
        to the row with the same (country, VAT, transaction code)."""
        st = self._make_statement()
        with self._compute_patch(st):
            st.action_compute_lines()
        self.assertAlmostEqual(st.line_ids.total_amount, 1000.0, places=2)

        st.line_ids.write({"is_overridden": True, "manual_value": 750.0})
        with self._compute_patch(st):
            st.action_compute_lines()
        line = st.line_ids
        self.assertEqual(len(line), 1)
        self.assertTrue(line.is_overridden)
        self.assertAlmostEqual(line.manual_value, 750.0, places=2)
        self.assertAlmostEqual(line.total_amount, 750.0, places=2,
                               msg="the override must be the reported value")

    def test_unmatched_override_warns_in_chatter(self):
        """Task-2 regression: an override whose row disappears on recompute
        is reported in the chatter (listing the row), not silently lost."""
        st = self._make_statement()
        with self._compute_patch(st):
            st.action_compute_lines()
        st.line_ids.write({"is_overridden": True, "manual_value": 750.0})

        # the DE row disappears; only an FR row remains after the recompute
        with self._compute_patch(st, vat="FR40303265045", country="FR"):
            st.action_compute_lines()
        line = st.line_ids
        self.assertEqual(line.partner_vat, "FR40303265045")
        self.assertFalse(line.is_overridden,
                         "the override must not leak onto a different row")
        warn = st.message_ids.filtered(
            lambda m: "DE811907980" in (m.body or ""))
        self.assertTrue(warn, "the dropped override must be named in chatter")


class TestEcSummaryRowComparison(TransactionCase):
    """Comparing a filed súhrnný výkaz against a fresh computation.

    A výkaz is not a list of boxes: it reports one line per counterparty, so
    "the same row" is (country, IČ DPH, kód) and a difference names a trading
    partner rather than a figure. Until this existed the form declined to
    compare at all, which was honest and useless.
    """

    def _statement(self, **vals):
        version = self.env["cssk.ec.summary.statement.version"].search(
            [], limit=1)
        if not version:
            self.skipTest("no EC summary version installed")
        base = {
            "company_id": self.env.company.id,
            "version_id": version.id,
            "date_from": "2019-06-01", "date_to": "2019-06-30",
            "period_type": "month",
            "statement_type_id": version.statement_type_ids[0].id,
        }
        base.update(vals)
        return self.env["cssk.ec.summary.statement"].create(base)

    def _line(self, statement, vat, amount, country="BE", code="0"):
        return self.env["cssk.ec.summary.statement.line"].create({
            "statement_id": statement.id,
            "partner_country_code": country, "partner_vat": vat,
            "transaction_code": code, "total_amount": amount,
        })

    def test_rows_are_keyed_by_the_counterparty(self):
        """The key is the one the recompute and VIES already use.

        Not a new notion of sameness invented for comparison: an override is
        re-applied to the row with the same country / VAT / code, and that is
        what this compares on. Two notions of "the same row" in one module
        drift apart.
        """
        st = self._statement()
        self._line(st, "BE0477472701", 1000.0)
        self._line(st, "DE811907980", 250.0, country="DE", code="1")
        rows = st._cssk_comparable_rows()
        self.assertEqual(len(rows), 2)
        keys = {identity for _section, identity in rows}
        self.assertIn(("BE", "BE0477472701", "0"), keys)
        self.assertIn(("DE", "DE811907980", "1"), keys)

    def test_the_count_of_supplies_is_not_compared(self):
        """How many documents make a counterparty's total is our bookkeeping.

        A filed výkaz does not state it, so comparing it would show every row
        of a staged filing as differing on a fact the filing never claimed.
        """
        st = self._statement()
        line = self._line(st, "BE0477472701", 1000.0)
        before = st._cssk_comparable_rows()
        line.supplies_count = 7
        self.assertEqual(before, st._cssk_comparable_rows())

    def test_a_counterparty_only_one_side_reports_shows_as_such(self):
        """Both directions, on the shared row vocabulary.

        A counterparty the filing has and we do not is a supply we are
        missing; one we have and it does not is a supply that was never
        filed. Both are findings and neither is a difference of zero.
        """
        st = self._statement()
        filed = {
            ("Line", ("BE", "BE0477472701", "0")): (1000.0,),
            ("Line", ("SK", "SK2023456787", "0")): (40.0,),
        }
        computed = {
            ("Line", ("BE", "BE0477472701", "0")): (1250.0,),
            ("Line", ("DE", "DE811907980", "0")): (99.0,),
        }
        mixin = self.env["cssk.ec.summary.statement"]
        rows = []
        for key in sorted(set(filed) | set(computed), key=mixin._cssk_compare_sort):
            a, b = filed.get(key), computed.get(key)
            if a is None:
                status = "only_computed"
            elif b is None:
                status = "only_filed"
            else:
                status = "ok" if mixin._cssk_rows_equal(a, b) else "differs"
            rows.append((mixin._cssk_compare_label(key, True), status))
        by_label = dict(rows)
        self.assertEqual(by_label["Line BE / BE0477472701 / 0"], "differs")
        self.assertEqual(by_label["Line SK / SK2023456787 / 0"], "only_filed")
        self.assertEqual(by_label["Line DE / DE811907980 / 0"], "only_computed")
