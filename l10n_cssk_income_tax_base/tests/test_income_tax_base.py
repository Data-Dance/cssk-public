# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestIncomeTaxBase(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.account_fiscal_country_id = cls.env.ref("base.sk")
        cls.misc = cls.company_data["default_journal_misc"]
        # Dedicated accounts with SK-style codes (5xx expense, 6xx income, 2xx
        # asset) so the '5,6' P&L formula is exercised independently of the
        # generic test chart's coding.
        def _acc(code, name, atype):
            return cls.env["account.account"].create({
                "name": name, "code": code, "account_type": atype,
                "company_ids": [Command.link(cls.company.id)],
            })
        cls.income = _acc("602000", "Tržby", "income")
        cls.expense = _acc("501000", "Spotreba", "expense")
        cls.bank = _acc("221000", "Bankové účty", "asset_cash")

        cls.template = cls.env["ir.ui.view"].create({
            "name": "cssk income tax test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_income_tax_test_template'><dokument/></t>",
        })
        # A minimal XSD for the one-element test template. Without it the
        # two export tests below fail on "carries no XML schema" — the export
        # refuses an unvalidated document on purpose, and the fixture predates
        # that guard. (Pre-existing: reproduced on pristine HEAD.)
        schema = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            '<xs:element name="dokument"/>'
            "</xs:schema>"
        )
        cls.version = cls.env["cssk.income.tax.version"].create({
            "name": "TEST DPPO",
            "country_id": cls.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": cls.template.id,
            "xml_root_element": "dokument",
            "xml_schema_data": base64.b64encode(schema.encode()),
            "xml_schema_filename": "test_dppo.xsd",
        })
        cls.env["cssk.income.tax.type"].create({
            "version_id": cls.version.id, "code": "R", "name": "Riadne",
            "fa_xml_value": "1",
        })
        defs = [
            ("r100", "Accounting profit before tax", 10, "account", "5,6", None),
            ("r110", "Non-deductible expenses (manual)", 20, "manual", None, None),
            ("r130", "Non-taxable income (manual)", 30, "manual", None, None),
            ("r400", "Tax base", 40, "aggregate", None, "r100 + r110 - r130"),
            ("r500", "Tax (21%)", 50, "aggregate", None, "round(r400 * 0.21, 2)"),
        ]
        for code, name, seq, kind, acc, agg in defs:
            cls.env["cssk.income.tax.line.def"].create({
                "version_id": cls.version.id, "code": code, "name": name,
                "sequence": seq, "kind": kind,
                "account_formula": acc, "aggregate_formula": agg,
            })

    def _post_pl(self, revenue, expense):
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.misc.id, "date": "2025-06-30",
            "line_ids": [
                Command.create({"account_id": self.income.id, "debit": 0.0, "credit": revenue}),
                Command.create({"account_id": self.expense.id, "debit": expense, "credit": 0.0}),
                Command.create({"account_id": self.bank.id,
                                "debit": revenue - expense, "credit": 0.0}),
            ],
        })
        move.action_post()

    def _make_return(self):
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.version.statement_type_ids[0].id,
            "date_from": "2025-01-01", "date_to": "2025-12-31",
        })
        ret.action_compute_lines()
        return ret

    def _set_dic(self, value):
        """Set the Slovak DIČ, if this install has one.

        This module depends on ``account``, ``mail``, ``l10n_cssk_core`` and
        ``l10n_cssk_submission_base`` — NOT on ``l10n_sk_base``, which is what
        puts ``l10n_sk_dic`` on the company. Production knows that and
        feature-detects with ``getattr``; the tests wrote the field
        unconditionally, so the suite raised ``AttributeError`` on a CZ-only
        install — the very configuration the dependency list promises works.

        Returns whether the field was there, so a caller can assert the DIČ
        path only where there is a DIČ to assert it with.
        """
        if "l10n_sk_dic" not in self.company._fields:
            return False
        self.company.l10n_sk_dic = value
        return True

    def _val(self, ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def test_accounting_result_from_pl(self):
        self._post_pl(revenue=2000.0, expense=800.0)
        ret = self._make_return()
        # profit before tax = revenue - expense
        self.assertAlmostEqual(self._val(ret, "r100"), 1200.0, places=2)

    def test_spine_aggregates(self):
        self._post_pl(revenue=2000.0, expense=800.0)
        ret = self._make_return()
        # tax base = 1200 + 0 - 0 = 1200 ; tax = 21% = 252
        self.assertAlmostEqual(self._val(ret, "r400"), 1200.0, places=2)
        self.assertAlmostEqual(self._val(ret, "r500"), 252.0, places=2)

    def test_eval_accounts_negation_and_overlap(self):
        """Task-3 regression (read_group evaluator): the token semantics are
        IDENTICAL to the historical per-prefix search — default sign −1
        (P&L: revenues − expenses come out positive), a leading '-' flips to
        +1, and an account matched by two tokens contributes once PER
        TOKEN."""
        self._post_pl(revenue=2000.0, expense=800.0)
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.version.statement_type_ids[0].id,
            "date_from": "2025-01-01", "date_to": "2025-12-31",
        })
        # bal(5xx) = +800 (debit), bal(6xx) = −2000 (credit)
        self.assertAlmostEqual(ret._eval_accounts("5,6"), 1200.0, places=2)
        self.assertAlmostEqual(ret._eval_accounts("-5,6"), 2800.0, places=2)
        # '5' and '50' both match 501000 → it contributes once per token
        self.assertAlmostEqual(ret._eval_accounts("5,50,6"), 400.0, places=2)

    def test_manual_override_feeds_aggregate(self):
        self._post_pl(revenue=2000.0, expense=800.0)
        ret = self._make_return()
        # accountant adds 300 non-deductible expenses on r110
        r110 = ret.line_ids.filtered(lambda l: l.code == "r110")
        r110.write({"is_overridden": True, "manual_value": 300.0})
        ret.action_compute_lines()
        self.assertAlmostEqual(self._val(ret, "r110"), 300.0, places=2)
        # base now 1200 + 300 = 1500 ; tax = 315
        self.assertAlmostEqual(self._val(ret, "r400"), 1500.0, places=2)
        self.assertAlmostEqual(self._val(ret, "r500"), 315.0, places=2)

    def test_export_preflight_accepts_dic_or_vat(self):
        """Task 3 regression: the DPPO preflight accepts EITHER the DIČ
        (l10n_sk_dic — what the SK template emits) or the VAT number; with
        neither set the export fails early naming the field."""
        self._post_pl(revenue=2000.0, expense=800.0)
        ret = self._make_return()
        self.company.vat = False
        self._set_dic(False)
        with self.assertRaises(UserError) as cm:
            ret.action_export_xml()
        self.assertIn("DIČ", str(cm.exception))

        # A DIČ alone (no VAT number) satisfies the DPPO identification —
        # assertable only where l10n_sk_base is installed to provide it.
        # Everywhere else the VAT number is the other accepted half, and that
        # half must be asserted on every install, not skipped with it.
        if not self._set_dic("2020317068"):
            self.company.vat = "SK2020317068"
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")

    def test_export_runs_kontroly_hook(self):
        """Task-1 regression: the consolidated pipeline gives the DPPO the
        ``_cssk_check_kontroly`` stage (no-op by default, ready for country
        kontrolné pravidlá) — an error returned by it must block the export
        BEFORE rendering."""
        from unittest.mock import patch
        self._post_pl(revenue=2000.0, expense=800.0)
        if not self._set_dic("2020317068"):
            self.company.vat = "SK2020317068"   # no l10n_sk_base on this install
        ret = self._make_return()
        Model = type(self.env["cssk.income.tax.return"])

        # patch with ``new=`` plain functions, NEVER a MagicMock — the
        # registry's ``_ondelete_methods`` scan would cache the mock (it
        # auto-creates an ``_ondelete`` attribute) as an unlink hook.
        calls = []

        def fake_hook(model):
            calls.append(True)
            return True

        with patch.object(Model, "_cssk_check_kontroly", new=fake_hook):
            ret.action_export_xml()
        self.assertEqual(len(calls), 1)
        self.assertEqual(ret.state, "exported")
        # and a failing hook blocks the export before any XML is attached
        ret2 = self._make_return()

        def failing_hook(model):
            raise UserError("kontroly failed")

        def no_render(model):
            raise AssertionError("must not render")

        with patch.object(Model, "_cssk_check_kontroly", new=failing_hook), \
             patch.object(Model, "_render_xml", new=no_render):
            with self.assertRaises(UserError):
                ret2.action_export_xml()
        self.assertFalse(ret2.xml_attachment_id)
        self.assertNotEqual(ret2.state, "exported")
