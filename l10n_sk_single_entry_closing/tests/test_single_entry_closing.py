# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


def _xml_template(env, name):
    """A version must name a renderer — the field is required, and a version
    that cannot produce its XML is not a filing version. Same fixture the
    VAT-return suite uses, for the same reason."""
    return env["ir.ui.view"].create({
        "name": name,
        "type": "qweb",
        "arch": "<t t-name='%s'><vykaz/></t>" % name,
    })


@tagged("post_install", "-at_install")
class TestJuZavierkaCashRows(AccountTestInvoicingCommon):
    """The statement rows that read the peňažný denník.

    The statutory row list of the výkaz o príjmoch a výdavkoch is shipped as
    data; this tests the mechanism underneath it on a version built here, so the
    two can be wrong independently and the failure says which.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.cssk_bookkeeping_regime = "ju"

        cls.income_account = cls.company_data["default_account_revenue"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account.cssk_cash_category_id = cls.env.ref(
            "l10n_sk_cash_journal.cat_p_vyrobky")
        cls.expense_account.cssk_cash_category_id = cls.env.ref(
            "l10n_sk_cash_journal.cat_v_zasoby")
        cls.bank_journal = cls.company_data["default_journal_bank"]

        cls.version = cls.env["cssk.fs.statement.version"].create({
            "name": "Test — výkaz o príjmoch a výdavkoch",
            "country_id": cls.env.ref("base.sk").id,
            "statement_kind": "profit_loss",
            "valid_from": "2020-01-01",
            "xml_root_element": "vykaz",
            "xml_template_ref_id": _xml_template(
                cls.env, "l10n_sk_single_entry_closing.test_template").id,
            "xml_schema_optional": True,
            "line_def_ids": [
                (0, 0, {
                    "code": "p", "name": "Príjmy spolu",
                    "kind": "cash_categories",
                    "cash_category_formula": "P1,P2,P3",
                    "sequence": 10,
                }),
                (0, 0, {
                    "code": "v", "name": "Výdavky spolu",
                    "kind": "cash_categories",
                    "cash_category_formula": "V1,V2,V3,V4,V5,V6,V9",
                    "sequence": 20,
                }),
                (0, 0, {
                    "code": "r", "name": "Rozdiel príjmov a výdavkov",
                    "kind": "aggregate", "aggregate_formula": "p - v",
                    "sequence": 30,
                }),
            ],
        })

    # -- helpers -------------------------------------------------------

    def _invoice(self, move_type="out_invoice", amount=1000.0, account=None,
                 invoice_date="2026-02-01"):
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.to_date(invoice_date),
            "date": fields.Date.to_date(invoice_date),
            "invoice_line_ids": [(0, 0, {
                "name": "položka",
                "quantity": 1.0,
                "price_unit": amount,
                "account_id": (account or self.income_account).id,
                "tax_ids": [(5, 0, 0)],
            })],
        })
        invoice.action_post()
        return invoice

    def _pay(self, invoice, payment_date="2026-03-01"):
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids,
        ).create({
            "payment_date": fields.Date.to_date(payment_date),
            "journal_id": self.bank_journal.id,
        })
        return wizard._create_payments()

    def _statement(self):
        statement = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        statement.action_compute_lines()
        return {line.code: line.current_value for line in statement.line_ids}

    def _generate(self):
        return self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company,
            fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"),
        )

    # -- tests ---------------------------------------------------------

    def test_the_statement_reads_the_dennik(self):
        self._pay(self._invoice(amount=1000.0))
        self._pay(self._invoice(move_type="in_invoice", amount=400.0,
                                account=self.expense_account),
                  payment_date="2026-03-10")
        self._generate()
        values = self._statement()
        self.assertAlmostEqual(values["p"], 1000.0, places=2)
        self.assertAlmostEqual(values["v"], 400.0, places=2)
        self.assertAlmostEqual(values["r"], 600.0, places=2)

    def test_an_aggregate_over_cash_rows_is_computed_after_them(self):
        """The parent pass evaluates aggregates before the cash rows exist.

        Without recomputing them afterwards the difference row would report
        zero against perfectly good príjmy and výdavky — which is the kind of
        plausible wrong number this codebase has been bitten by before.
        """
        self._pay(self._invoice(amount=750.0))
        self._generate()
        values = self._statement()
        self.assertAlmostEqual(values["p"], 750.0, places=2)
        self.assertAlmostEqual(values["r"], 750.0, places=2)

    def test_non_cash_rows_stay_out_of_a_statement_of_money(self):
        """An odpis belongs to the tax base, not to príjmy a výdavky."""
        depreciation = self.expense_account.copy({
            "code": "551900",
            "cssk_cash_category_id": self.env.ref(
                "l10n_sk_cash_journal.cat_z_odpisy").id,
        })
        accumulated = self.expense_account.copy({"code": "082900"})
        move = self.env["account.move"].create({
            "journal_id": self.company_data["default_journal_misc"].id,
            "date": fields.Date.to_date("2026-12-31"),
            "line_ids": [
                (0, 0, {"account_id": depreciation.id, "name": "odpis",
                        "debit": 900.0, "credit": 0.0}),
                (0, 0, {"account_id": accumulated.id, "name": "odpis",
                        "debit": 0.0, "credit": 900.0}),
            ],
        })
        move.action_post()
        self._generate()
        self.assertTrue(
            self.env["cssk.cash.journal.line"].search_count([
                ("company_id", "=", self.company.id), ("non_cash", "=", True),
            ]),
            "the denník does carry the odpis")
        values = self._statement()
        self.assertAlmostEqual(values["v"], 0.0, places=2,
                               msg="but the výkaz o príjmoch a výdavkoch does not")

    def test_a_storno_reduces_its_own_row(self):
        """A refunded sale lowers príjmy; it is not an expense of the year."""
        self._pay(self._invoice(amount=1000.0))
        refund = self.env["account.move"].create({
            "move_type": "out_refund",
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.to_date("2026-03-04"),
            "date": fields.Date.to_date("2026-03-04"),
            "invoice_line_ids": [(0, 0, {
                "name": "vrátenie", "quantity": 1.0, "price_unit": 150.0,
                "account_id": self.income_account.id,
                "tax_ids": [(5, 0, 0)],
            })],
        })
        refund.action_post()
        self._pay(refund, payment_date="2026-03-05")
        self._generate()
        values = self._statement()
        self.assertAlmostEqual(values["p"], 850.0, places=2)
        self.assertAlmostEqual(values["v"], 0.0, places=2)

    def test_a_nested_aggregate_over_a_cash_row_is_not_stale(self):
        """An aggregate over an aggregate, with the parent sequenced FIRST.

        The recompute pass has to run in dependency order. In sequence order it
        computes `outer` from `inner`'s stale zero and only then fixes `inner`,
        so `outer` comes back 0 against a perfectly good cash row — no error,
        just a wrong total. Raised by a gpt-5.3-codex review of the override.
        """
        version = self.env["cssk.fs.statement.version"].create({
            "name": "Test — forward-pointing aggregates",
            "country_id": self.env.ref("base.sk").id,
            "statement_kind": "profit_loss",
            "valid_from": "2020-01-01",
            "xml_root_element": "vykaz",
            "xml_schema_optional": True,
            "xml_template_ref_id": _xml_template(
                self.env, "l10n_sk_single_entry_closing.test_template_nested").id,
            "line_def_ids": [
                # `outer` is sequenced ABOVE both rows it depends on, the way a
                # statutory form numbers its totals first.
                (0, 0, {"code": "outer", "name": "Outer", "kind": "aggregate",
                        "aggregate_formula": "inner", "sequence": 10}),
                (0, 0, {"code": "inner", "name": "Inner", "kind": "aggregate",
                        "aggregate_formula": "cash", "sequence": 20}),
                (0, 0, {"code": "cash", "name": "Cash", "kind": "cash_categories",
                        "cash_category_formula": "P2", "sequence": 30}),
            ],
        })
        self._pay(self._invoice(amount=640.0))
        self._generate()
        statement = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id,
            "version_id": version.id,
            "date_from": fields.Date.to_date("2026-01-01"),
            "date_to": fields.Date.to_date("2026-12-31"),
        })
        statement.action_compute_lines()
        values = {line.code: line.current_value for line in statement.line_ids}
        self.assertAlmostEqual(values["cash"], 640.0, places=2)
        self.assertAlmostEqual(values["inner"], 640.0, places=2)
        self.assertAlmostEqual(values["outer"], 640.0, places=2,
                               msg="the nested aggregate must not read a stale zero")

    def test_a_negated_token_subtracts(self):
        totals = {"P1": 100.0, "V1": 40.0}
        evaluate = self.env["cssk.fs.statement"]._cssk_eval_cash_categories
        self.assertAlmostEqual(evaluate("P1,-V1", totals), 60.0, places=2)
        self.assertAlmostEqual(evaluate("", totals), 0.0, places=2)
        self.assertAlmostEqual(evaluate("P9", totals), 0.0, places=2)


@tagged("post_install", "-at_install")
class TestUzfoV14(AccountTestInvoicingCommon):
    """The statutory version: rows, the eForm's own arithmetic, and the XML."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.cssk_bookkeeping_regime = "ju"
        # A DIČ that passes the checksum; the header carries it.
        cls.company.vat = "SK2022749619"
        # Checksum-valid IČO (mod 11, weights 8..2), as the core validator wants.
        cls.company.company_registry = "12345679"
        cls.version = cls.env.ref("l10n_sk_single_entry_closing.uzfo_v14")
        cls.bank_journal = cls.company_data["default_journal_bank"]

    def _account(self, code):
        return self.env["account.account"].with_company(self.company).search([
            ("company_ids", "in", self.company.id), ("code", "=like", code + "%"),
        ], limit=1)

    def _statement(self, date_from="2026-01-01", date_to="2026-12-31"):
        statement = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": fields.Date.to_date(date_from),
            "date_to": fields.Date.to_date(date_to),
        })
        statement.action_compute_lines()
        return statement

    def _values(self, statement):
        return {line.code: line.current_value for line in statement.line_ids}

    # -- the form itself ------------------------------------------------

    def test_the_version_carries_the_whole_tlacivo(self):
        """12 rows of Úč FO 1-01 and 21 of Úč FO 2-01, no more and no fewer."""
        codes = set(self.version.line_def_ids.mapped("code"))
        self.assertEqual(codes, {"f%02d" % n for n in range(1, 13)}
                         | {"m%02d" % n for n in range(1, 22)})

    def test_the_schema_is_the_published_one(self):
        """A vintage-only stamp is why the digest is pinned, not the version."""
        import hashlib
        import base64
        data = base64.b64decode(self.version.xml_schema_data)
        self.assertEqual(len(data), 8482)
        self.assertEqual(hashlib.md5(data).hexdigest(),
                         "b4878f4640ea0101943146d0a7c6b931")
        self.assertEqual(self.version.xml_root_element, "dokument")

    def test_the_income_rows_read_the_dennik_and_the_totals_agree(self):
        """r. 04 = Σ01..03, r. 11 = Σ05..10, r. 12 = r.04 − r.11 (eForm)."""
        revenue = self.company_data["default_account_revenue"]
        revenue.cssk_cash_category_id = self.env.ref(
            "l10n_sk_cash_journal.cat_p_tovar")
        expense = self.company_data["default_account_expense"]
        expense.cssk_cash_category_id = self.env.ref(
            "l10n_sk_cash_journal.cat_v_zasoby")
        for move_type, amount, account in (
            ("out_invoice", 1000.0, revenue), ("in_invoice", 400.0, expense),
        ):
            invoice = self.env["account.move"].create({
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.to_date("2026-02-01"),
                "date": fields.Date.to_date("2026-02-01"),
                "invoice_line_ids": [(0, 0, {
                    "name": "x", "quantity": 1.0, "price_unit": amount,
                    "account_id": account.id, "tax_ids": [(5, 0, 0)],
                })],
            })
            invoice.action_post()
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids,
            ).create({
                "payment_date": fields.Date.to_date("2026-03-01"),
                "journal_id": self.bank_journal.id,
            })._create_payments()
        self.env["cssk.cash.journal.line"]._cssk_regenerate(
            self.company, fields.Date.to_date("2026-01-01"),
            fields.Date.to_date("2026-12-31"))

        values = self._values(self._statement())
        self.assertAlmostEqual(values["f01"], 1000.0, places=2)
        self.assertAlmostEqual(values["f05"], 400.0, places=2)
        self.assertAlmostEqual(values["f04"], 1000.0, places=2)
        self.assertAlmostEqual(values["f11"], 400.0, places=2)
        self.assertAlmostEqual(values["f12"], 600.0, places=2)

    def test_the_neovplyvnujuce_columns_stay_out_of_uc_fo_1(self):
        """§ 4 ods. 6 f)/g): they are their own prehľady and not on this form."""
        formulas = " ".join(
            self.version.line_def_ids.filtered(
                lambda d: d.kind == "cash_categories"
            ).mapped("cash_category_formula"))
        for code in ("PN1", "PN2", "PN3", "PN9", "VN1", "VN2", "VN3", "VN4",
                     "VN5", "VN9", "C1"):
            self.assertNotIn(code, formulas.split(","))

    def test_odpisy_reach_ostatne_vydavky(self):
        """§ 4 ods. 9 names odpisy in r. 10 — a statement of money that holds
        one non-cash row, by the opatrenie's own instruction."""
        row = self.version.line_def_ids.filtered(lambda d: d.code == "f10")
        self.assertIn("Z1", row.cash_category_formula.split(","))

    def test_the_asset_rows_balance_against_the_liability_rows(self):
        """r. 15 − r. 20 = r. 21, on real postings rather than on zeros."""
        bank = self.bank_journal.default_account_id
        loan = self._account("461")
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-04-01"),
            "line_ids": [
                (0, 0, {"account_id": bank.id, "name": "úver",
                        "debit": 5000.0, "credit": 0.0}),
                (0, 0, {"account_id": loan.id, "name": "úver",
                        "debit": 0.0, "credit": 5000.0}),
            ],
        })
        move.action_post()
        values = self._values(self._statement())
        self.assertAlmostEqual(values["m11"], 5000.0, places=2)
        self.assertAlmostEqual(values["m18"], 5000.0, places=2,
                               msg="a liability is reported positive")
        self.assertAlmostEqual(values["m15"] - values["m20"], values["m21"],
                               places=2)
        self.assertAlmostEqual(values["m21"], 0.0, places=2)

    def test_an_overdrawn_bank_account_is_an_uver_not_a_negative_asset(self):
        """The vysvetlivky put a negative kontokorent balance in r. 18."""
        bank = self.bank_journal.default_account_id
        expense = self.company_data["default_account_expense"]
        move = self.env["account.move"].create({
            "journal_id": self.bank_journal.id,
            "date": fields.Date.to_date("2026-04-02"),
            "line_ids": [
                (0, 0, {"account_id": expense.id, "name": "výdaj",
                        "debit": 800.0, "credit": 0.0}),
                (0, 0, {"account_id": bank.id, "name": "výdaj",
                        "debit": 0.0, "credit": 800.0}),
            ],
        })
        move.action_post()
        values = self._values(self._statement())
        self.assertAlmostEqual(values["m11"], 0.0, places=2)
        self.assertAlmostEqual(values["m18"], 800.0, places=2)

    # -- what the demo instance taught ----------------------------------

    def test_the_statement_is_named_after_the_form_it_is(self):
        """The filed file's name reaches the register, so it must be right.

        The framework names a statement from its ``statement_kind``, and this
        version must declare one of the four it knows. It declares
        ``profit_loss``, so on the demo instance the exported file came out as
        "Výkaz ziskov a strát — 2026-12-31.xml" — an income statement, which
        this is not.
        """
        statement = self._statement()
        self.assertIn("Úč FO", statement.name)
        self.assertNotIn("ziskov", statement.name)

    def test_the_unmapped_warning_ignores_what_the_form_never_reports(self):
        """Úč FO 2-01 carries majetok and záväzky, and nothing else.

        Unfiltered, the framework's diagnostic reported 57 unmapped accounts on
        the demo instance — every one a class 5/6, equity or podsúvahový account
        that this form correctly ignores. A diagnostic that cries wolf is
        worthless on the day it is right.
        """
        revenue = self.company_data["default_account_revenue"]
        expense = self.company_data["default_account_expense"]
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": fields.Date.to_date("2026-02-01"),
            "date": fields.Date.to_date("2026-02-01"),
            "invoice_line_ids": [(0, 0, {
                "name": "x", "quantity": 1.0, "price_unit": 900.0,
                "account_id": revenue.id, "tax_ids": [(5, 0, 0)],
            })],
        })
        invoice.action_post()
        statement = self._statement()
        note = statement.unmapped_note or ""
        for code in (revenue.code, expense.code):
            self.assertNotIn(
                code, note,
                "a class 5/6 account is not a mapping hole in this form")

    # -- the XML --------------------------------------------------------

    def test_the_export_validates_against_the_published_schema(self):
        statement = self._statement()
        statement.action_export_xml()
        self.assertTrue(statement.xml_attachment_id,
                        "the export produced a file")

    def test_the_xml_is_whole_euros_and_the_first_zavierka_leaves_s1_empty(self):
        """The tlačivo is headed '(v celých eurách)'; § 22 ods. 4 empties col. 1."""
        import base64
        from lxml import etree
        revenue = self.company_data["default_account_revenue"]
        revenue.cssk_cash_category_id = self.env.ref(
            "l10n_sk_cash_journal.cat_p_tovar")
        self.env["cssk.cash.journal.line"].create({
            "company_id": self.company.id,
            "date": fields.Date.to_date("2026-05-05"),
            "kind": "income", "money_direction": "in", "payment_kind": "bank",
            "category_id": self.env.ref("l10n_sk_cash_journal.cat_p_tovar").id,
            "taxable": True, "amount": 1234.56, "manual": True,
        })
        statement = self._statement()
        self.assertTrue(statement.cssk_first_zavierka,
                        "no entries before the period, so there is no prior one")
        statement.action_export_xml()
        xml = base64.b64decode(statement.xml_attachment_id.datas)
        root = etree.fromstring(xml)
        self.assertEqual(root.tag, "dokument")
        self.assertEqual(root.findtext("telo/ucFo1/r01"), "1235",
                         "whole euros, rounded")
        self.assertEqual(root.findtext("telo/ucFo2/r01/s1"), None or "",
                         "the preceding period is left empty")
        self.assertEqual(len(root.findall("telo/ucFo2/*")), 21)


@tagged("post_install", "-at_install")
class TestUzfoV14Partition(AccountTestInvoicingCommon):
    """Does every account reach exactly one row of Úč FO 2-01?

    Two different questions, per ``docs/writing-a-statement-module.md`` § 6:
    uniqueness is provable from the chart alone and belongs in a static test,
    while coverage belongs at runtime on customer data. This is the static half,
    and it found real holes when it was first run — poskytnuté preddavky na
    dlhodobý majetok (051/052/055), komplexné náklady budúcich období (382),
    derivatives (373/376) and the long-term liabilities 471/473/478/481 reached
    no row at all, so their balances would have vanished from the statement
    without a word.

    **The matcher is duplicated here on purpose.** A test validating row DATA
    must not run through the production code path whose behaviour it checks.
    """

    #: Equity reaches no row BY DESIGN: Úč FO 2-01 reports majetok and záväzky,
    #: and r. 21 "Rozdiel majetku a záväzkov" IS the owner's equity. That also
    #: keeps the statement able to fail — the difference is computed, not
    #: plugged, so an unmapped balance shows up as a difference that does not
    #: match the books instead of being absorbed silently.
    ALLOWED_UNCLAIMED_TYPES = ("equity", "equity_unaffected", "off_balance")

    #: Accounts the form deliberately reports on two rows, resolved per account
    #: by the sign of its own balance: a bank account in funds against an
    #: overdraft, the opravná položka k nadobudnutému majetku active against
    #: passive, DPH receivable against payable, derivatives and deferred tax.
    TWO_SIDED = ("221", "097", "098", "343", "373", "481")

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.version = cls.env.ref("l10n_sk_single_entry_closing.uzfo_v14")
        cls.accounts = cls.env["account.account"].with_company(
            cls.env.company).search([("company_ids", "in", cls.env.company.id)])

    def _claims(self):
        """``{account: rows claiming it}`` — matched by prefix, as the form is."""
        claims = {}
        for ldef in self.version.line_def_ids.filtered(
            lambda d: d.kind == "accounts"
        ):
            tokens = [
                token.strip().lstrip("-")
                for formula in (ldef.account_formula,
                                ldef.account_formula_correction)
                for token in (formula or "").split(",")
                if token.strip()
            ]
            for account in self.accounts:
                if any(account.code.startswith(token) for token in tokens):
                    claims.setdefault(account, set()).add(ldef.code)
        return claims

    def test_no_account_is_claimed_by_two_rows(self):
        """Except the two-sided ones, where the balance's own sign decides."""
        offenders = {
            account.code: sorted(rows)
            for account, rows in self._claims().items()
            if len(rows) > 1
            and not account.code.startswith(self.TWO_SIDED)
        }
        self.assertFalse(offenders, "these accounts would count twice: %s"
                         % offenders)

    def test_every_balance_account_reaches_a_row(self):
        """A balance that reaches no row vanishes from the statement in silence."""
        claims = self._claims()
        missing = sorted(
            account.code for account in self.accounts
            if account.code[:1] in "01234"
            and account.account_type not in self.ALLOWED_UNCLAIMED_TYPES
            and account not in claims
        )
        self.assertFalse(missing, "these accounts reach no row: %s" % missing)

    def test_the_difference_row_is_not_a_plug(self):
        """r. 21 must be computed from the two totals, not from a subtraction
        that makes the statement balance by construction.

        The Slovak Úč POD 1 defines its result row as total assets minus
        everything else on the passive side, which cannot fail to balance and
        therefore cannot report that something is wrong. This form's r. 15 and
        r. 20 are independent sums, and r. 21 is their difference.
        """
        definitions = {d.code: d for d in self.version.line_def_ids}
        self.assertEqual(definitions["m21"].aggregate_formula, "m15 - m20")
        for code in ("m15", "m20"):
            self.assertEqual(definitions[code].kind, "aggregate")
            self.assertNotIn("m21", definitions[code].aggregate_formula)
