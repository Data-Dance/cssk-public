# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkInventoryDifferences(AccountTestInvoicingCommon):
    """§ 30 ods. 5 až 7 zákona 431/2002 and § 11 of the postupy účtovania."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.user = cls.env.user
        cls.keeper = cls.env["res.partner"].create({"name": "Pokladníčka"})
        cls.Line = cls.env["l10n.sk.inventarizacny.rozdiel"]

    def _account(self, code):
        account = self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )
        self.assertTrue(account, "account %s is not in the Slovak chart" % code)
        return account

    def _inventarizacia(self, state="in_progress"):
        inv = self.env["l10n.sk.inventarizacia"].create({
            "company_id": self.company.id,
            "date_start": "2025-12-20",
            "date_as_of": "2025-12-31",
            "date_end": "2026-01-15",
        })
        if state != "draft":
            inv.action_start()
        return inv

    def _supis(self, inv, code, book, actual, name=None, **vals):
        """A fyzická inventúra kept on ``code`` with a typed book state."""
        return self.env["l10n.sk.inventurny.supis"].create({
            "name": name or "Súpis %s" % code,
            "inventarizacia_id": inv.id,
            "inventory_type": "fyzicka",
            "account_id": self._account(code).id,
            "counted_by_id": self.user.id,
            "book_amount": book,
            "line_ids": [Command.create(
                {"name": "Stav", "quantity": 1.0, "unit_price": actual})],
            **vals,
        })

    def _items(self, move):
        """{account code: (debit, credit)} of a journal entry."""
        result = {}
        for line in move.line_ids:
            debit, credit = result.get(line.account_id.code, (0.0, 0.0))
            result[line.account_id.code] = (
                debit + line.debit, credit + line.credit)
        return result

    # ------------------------------------------------------------------
    def test_cash_schodok_is_a_receivable_not_an_expense(self):
        """Postupy § 11 ods. 1 písm. b): 335/211, dated the deň ku ktorému."""
        inv = self._inventarizacia()
        supis = self._supis(inv, "211000", 1000.0, 950.0)
        self.assertEqual(supis.difference, -50.0)
        self.assertEqual(inv.difference_state, "to_settle")

        inv.action_propose_differences()
        line = inv.difference_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.kind, "shortage")
        self.assertEqual(line.amount, 50.0)
        self.assertEqual(line.account_id.code, "211000")
        self.assertEqual(line.counterpart_account_id.code, "335000")
        self.assertEqual(supis.difference_residual, 0.0)
        self.assertEqual(inv.difference_state, "ready")

        line.partner_id = self.keeper
        inv.action_create_difference_entries()
        move = line.move_id
        self.assertEqual(move.state, "draft")
        self.assertEqual(str(move.date), "2025-12-31")
        self.assertEqual(move.ref, inv.name)
        self.assertEqual(move.journal_id, inv.difference_journal_id)
        self.assertEqual(
            self._items(move),
            {"335000": (50.0, 0.0), "211000": (0.0, 50.0)},
        )
        self.assertEqual(move.line_ids.partner_id, self.keeper)
        self.assertEqual(inv.difference_move_ids, move)
        self.assertEqual(inv.difference_state, "draft")
        move.action_post()
        self.assertEqual(inv.difference_state, "posted")

    def test_cash_prebytok(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 1012.5)
        inv.action_propose_differences()
        line = inv.difference_line_ids
        self.assertEqual((line.kind, line.amount), ("surplus", 12.5))
        inv.action_create_difference_entries()
        self.assertEqual(
            self._items(line.move_id),
            {"211000": (12.5, 0.0), "668000": (0.0, 12.5)},
        )

    def test_stock_manko_split_into_norm_and_claim(self):
        """§ 43 ods. 2 písm. d) and § 68 ods. 8: 549 above the norm, 501
        within it; § 55 ods. 9 písm. a): the claim is 378/648."""
        inv = self._inventarizacia()
        supis = self._supis(inv, "112000", 1000.0, 900.0)
        inv.action_propose_differences()
        manko = inv.difference_line_ids
        self.assertEqual(manko.counterpart_account_id.code, "549000")
        manko.amount = 70.0
        self.assertEqual(supis.difference_residual, -30.0)
        self.assertEqual(inv.difference_state, "to_settle")
        norm = self.Line.create({
            "inventory_id": inv.id, "sheet_id": supis.id,
            "kind": "natural_loss", "amount": 30.0,
        })
        self.assertEqual(norm.account_id.code, "112000")
        self.assertEqual(norm.counterpart_account_id.code, "501000")
        claim = self.Line.create({
            "inventory_id": inv.id, "sheet_id": supis.id,
            "kind": "claim", "amount": 40.0, "partner_id": self.keeper.id,
        })
        self.assertEqual(claim.account_id.code, "378000")
        self.assertEqual(claim.counterpart_account_id.code, "648000")
        # the claim explains none of the difference
        self.assertEqual(supis.difference_residual, 0.0)

        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        self.assertEqual(len(move), 1)
        self.assertEqual(
            self._items(move),
            {
                "549000": (70.0, 0.0),
                "501000": (30.0, 0.0),
                "112000": (0.0, 100.0),
                "378000": (40.0, 0.0),
                "648000": (0.0, 40.0),
            },
        )

    def test_proposed_accounts_follow_the_postupy(self):
        inv = self._inventarizacia()
        cases = [
            # code, kind, counterpart
            ("132000", "shortage", "549000"),
            ("132000", "natural_loss", "504000"),
            ("132000", "surplus", "648000"),
            ("123000", "shortage", "549000"),
            ("123000", "natural_loss", "613000"),
            ("123000", "surplus", "613000"),
            ("213000", "shortage", "335000"),
            ("213000", "surplus", "668000"),
            # § 21 ods. 2: newly found depreciated asset against 384
            ("022000", "surplus", "384000"),
            # the manko of a depreciated asset goes through the oprávky:
            # nothing one line could propose
            ("022000", "shortage", False),
            ("321000", "shortage", False),
            ("321000", "surplus", False),
        ]
        for code, kind, expected in cases:
            supis = self._supis(inv, code, 100.0, 100.0, name="%s %s" % (code, kind))
            line = self.Line.new({
                "inventory_id": inv.id, "sheet_id": supis.id,
                "kind": kind, "amount": 1.0,
            })
            self.assertEqual(
                line.counterpart_account_id.code or False, expected,
                "%s %s" % (code, kind))

    def test_fixed_asset_line_warns_about_the_register(self):
        inv = self._inventarizacia()
        supis = self._supis(inv, "022000", 5000.0, 6000.0)
        inv.action_propose_differences()
        self.assertTrue(inv.difference_line_ids.warning)
        cash = self._supis(inv, "211000", 10.0, 11.0)
        inv.action_propose_differences()
        self.assertFalse(
            inv.difference_line_ids.filtered(lambda l: l.sheet_id == cash).warning)
        self.assertTrue(supis.exists())

    def test_liability_found_by_dokladova_inventura(self):
        """Debit-minus-credit signs: −500 in the books, −620 confirmed. The
        account is credited, and the counterpart is the accountant's call."""
        account = self._account("321000")
        inv = self._inventarizacia()
        supis = self.env["l10n.sk.inventurny.supis"].create({
            "name": "Dodávatelia",
            "inventarizacia_id": inv.id,
            "inventory_type": "dokladova",
            "account_id": account.id,
            "counted_by_id": self.user.id,
            "line_ids": [Command.create(
                {"name": "Dodávateľ A", "quantity": 1.0, "unit_price": -120.0})],
        })
        self.assertEqual(supis.difference, -120.0)
        inv.action_propose_differences()
        line = inv.difference_line_ids
        self.assertEqual(line.kind, "shortage")
        self.assertFalse(line.counterpart_account_id)
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        line.counterpart_account_id = self._account("518000")
        inv.action_create_difference_entries()
        self.assertEqual(
            self._items(line.move_id),
            {"518000": (120.0, 0.0), "321000": (0.0, 120.0)},
        )

    def test_every_difference_must_be_settled_or_explained(self):
        inv = self._inventarizacia()
        cash = self._supis(inv, "211000", 1000.0, 950.0)
        stock = self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.difference_line_ids.filtered(lambda l: l.sheet_id == stock).unlink()
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        self.assertFalse(inv.difference_move_ids)
        # a reason is part of the statement
        with self.assertRaises(ValidationError):
            stock.difference_skip = True
        stock.write({
            "difference_skip": True,
            "difference_skip_reason": "Upravené inventúrou v sklade",
        })
        self.assertEqual(stock.difference_residual, 0.0)
        inv.action_create_difference_entries()
        self.assertEqual(len(inv.difference_move_ids.line_ids), 2)
        self.assertTrue(cash.difference_line_ids.move_id)
        # … and a skipped súpis takes no settlement lines
        with self.assertRaises(ValidationError):
            self.Line.create({
                "inventory_id": inv.id, "sheet_id": stock.id,
                "kind": "shortage", "amount": 20.0,
            })

    def test_nothing_is_booked_before_the_start_or_twice(self):
        inv = self._inventarizacia(state="draft")
        self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        inv.action_start()
        inv.action_create_difference_entries()
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        self.assertEqual(len(inv.difference_move_ids), 1)

    def test_amount_is_positive_and_the_supis_is_of_the_inventarizacia(self):
        inv = self._inventarizacia()
        other = self._inventarizacia()
        supis = self._supis(inv, "211000", 1000.0, 950.0)
        for amount in (0.0, -5.0):
            with self.assertRaises(ValidationError):
                self.Line.create({
                    "inventory_id": inv.id, "sheet_id": supis.id,
                    "kind": "shortage", "amount": amount,
                })
        with self.assertRaises(ValidationError):
            self.Line.create({
                "inventory_id": other.id, "sheet_id": supis.id,
                "kind": "shortage", "amount": 50.0,
            })

    def test_a_booked_difference_is_frozen(self):
        inv = self._inventarizacia()
        supis = self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        line = inv.difference_line_ids
        with self.assertRaises(UserError):
            line.amount = 60.0
        with self.assertRaises(UserError):
            line.unlink()
        with self.assertRaises(UserError):
            supis.unlink()
        with self.assertRaises(UserError):
            inv.unlink()
        # the label is not what the entry was built from
        line.name = "Schodok pokladnice"
        # the súpis moving under a booked entry is flagged, not blocked
        self.assertFalse(inv.difference_stale)
        supis.book_amount = 1010.0
        self.assertTrue(inv.difference_stale)

    def test_reopening_deletes_a_draft_entry(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        inv.action_done()
        inv.action_draft()
        self.assertFalse(move.exists())
        self.assertFalse(inv.difference_move_ids)
        self.assertFalse(inv.difference_line_ids.move_id)
        self.assertEqual(inv.state, "draft")
        # the settlement itself survives and can be booked again
        inv.action_start()
        self.assertEqual(inv.difference_state, "ready")
        inv.action_create_difference_entries()
        self.assertEqual(inv.difference_state, "draft")

    def test_reopening_reverses_a_posted_entry_in_the_same_period(self):
        """§ 30 ods. 7 holds for the reversal as it did for the entry."""
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        move.action_post()
        inv.action_done()

        inv.action_draft()
        reversal = inv.difference_move_ids - move
        self.assertEqual(len(reversal), 1)
        self.assertEqual(reversal.reversed_entry_id, move)
        self.assertEqual(reversal.state, "posted")
        self.assertEqual(str(reversal.date), "2025-12-31")
        # a Slovak company reverses by storno: the same sides, negative
        self.assertEqual(
            self._items(reversal),
            {"549000": (-20.0, 0.0), "132000": (0.0, -20.0)},
        )
        self.assertFalse(inv.difference_line_ids.move_id)
        self.assertEqual(inv.difference_state, "ready")
        # net effect on the stock account is nil
        balance = sum(self.env["account.move.line"].search([
            ("move_id", "in", (move | reversal).ids),
            ("account_id.code", "=", "132000"),
        ]).mapped("balance"))
        self.assertEqual(balance, 0.0)

    def test_a_locked_period_refuses_the_reopening(self):
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        move.action_post()
        inv.action_done()
        self.company.fiscalyear_lock_date = "2025-12-31"
        with self.assertRaises(UserError), self.cr.savepoint():
            inv.action_draft()
        self.env.invalidate_all()
        self.assertEqual(inv.state, "done")
        self.assertEqual(inv.difference_line_ids.move_id, move)
        self.assertEqual(move.state, "posted")
        self.assertEqual(inv.difference_move_ids, move)

    def test_a_locked_period_refuses_the_booking(self):
        """Odoo would not refuse: it moves the date past the lock on
        posting, into the next accounting period."""
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        self.company.fiscalyear_lock_date = "2025-12-31"
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        self.assertFalse(inv.difference_move_ids)

    def test_posting_into_a_period_locked_meanwhile_is_refused(self):
        """Odoo alone would move the entry to the first open day."""
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        self.company.fiscalyear_lock_date = "2025-12-31"
        with self.assertRaises(UserError):
            move.action_post()
        self.assertEqual(move.state, "draft")
        self.assertEqual(str(move.date), "2025-12-31")

    def test_an_entry_dated_elsewhere_is_flagged(self):
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        self.assertFalse(inv.difference_misdated)
        inv.difference_move_ids.date = "2026-01-05"
        self.assertTrue(inv.difference_misdated)

    def test_an_entry_reversed_in_accounting_frees_the_difference(self):
        inv = self._inventarizacia()
        self._supis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        move.action_post()
        move._reverse_moves([{"date": move.date}], cancel=True)
        self.assertEqual(inv.difference_state, "ready")
        inv.action_create_difference_entries()
        again = inv.difference_line_ids.move_id
        self.assertNotEqual(again, move)
        self.assertEqual(again.state, "draft")
        # reopening now touches only the live entry
        inv.action_draft()
        self.assertFalse(again.exists())
        self.assertEqual(move.state, "posted")

    def test_accounts_follow_the_supis_until_booked(self):
        inv = self._inventarizacia()
        supis = self._supis(inv, "112000", 1000.0, 900.0)
        inv.action_propose_differences()
        line = inv.difference_line_ids
        supis.account_id = self._account("132000")
        self.assertEqual(line.account_id.code, "132000")
        inv.action_create_difference_entries()
        supis.account_id = self._account("112000")
        self.assertEqual(line.account_id.code, "132000")
        self.assertEqual(line.counterpart_account_id.code, "549000")

    def test_proposals_do_not_depend_on_the_active_company(self):
        """Account codes are company-dependent: a user working in another
        company must get the same proposal, not an empty one."""
        other = self.env["res.company"].create({"name": "Iná spoločnosť"})
        self.env.user.company_ids |= other
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0)
        stroje = self._supis(inv, "022000", 5000.0, 6000.0)
        # both companies ticked in the switcher, the other one current
        inv = inv.with_context(
            allowed_company_ids=[other.id, self.company.id])
        self.assertEqual(inv.env.company, other)
        inv.action_propose_differences()
        self.assertEqual(
            sorted(inv.difference_line_ids.mapped("counterpart_account_id.id")),
            sorted((self._account("335000") | self._account("384000")).ids),
        )
        self.assertTrue(stroje.difference_line_ids.warning)

    def test_other_companies_do_not_see_the_inventarizacia(self):
        other = self.env["res.company"].create({"name": "Cudzia spoločnosť"})
        user = self.env["res.users"].create({
            "name": "Cudzia účtovníčka",
            "login": "cudzia-inv",
            "company_id": other.id,
            "company_ids": [Command.set(other.ids)],
            "group_ids": [Command.set([
                self.env.ref("base.group_user").id,
                self.env.ref("account.group_account_invoice").id,
            ])],
        })
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        for model in (
            "l10n.sk.inventarizacia",
            "l10n.sk.inventurny.supis",
            "l10n.sk.inventarizacny.rozdiel",
        ):
            self.assertFalse(
                self.env[model].with_user(user).search(
                    [("company_id", "=", self.company.id)]), model)

    def test_an_invoicing_user_can_book_and_take_back(self):
        user = self.env["res.users"].create({
            "name": "Fakturantka",
            "login": "fakturantka-inv",
            "company_id": self.company.id,
            "company_ids": [Command.set(self.company.ids)],
            "group_ids": [Command.set([
                self.env.ref("base.group_user").id,
                self.env.ref("account.group_account_invoice").id,
            ])],
        })
        inv = self._inventarizacia().with_user(user)
        self._supis(inv.sudo(), "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        self.assertEqual(inv.difference_state, "draft")
        inv.action_draft()
        self.assertFalse(inv.sudo().difference_move_ids)

    def test_cancelling_the_booking_keeps_the_inventarizacia_open(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        inv.action_cancel_difference_entries()
        self.assertEqual(inv.state, "in_progress")
        self.assertEqual(inv.difference_state, "ready")
        self.assertFalse(inv.difference_move_ids)

    def test_an_entry_deleted_in_accounting_frees_the_difference(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        inv.difference_move_ids.unlink()
        self.assertEqual(inv.difference_state, "ready")
        inv.difference_line_ids.amount = 50.0

    def test_zapis_prints_the_settlement(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 950.0, name="Pokladnica Bratislava")
        skipped = self._supis(inv, "022000", 5000.0, 4000.0, name="Stroje")
        skipped.write({
            "difference_skip": True,
            "difference_skip_reason": "Vyradené v evidencii majetku",
        })
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_sk_inventory_verification.report_inventarizacny_zapis", inv.ids
        )[0].decode()
        self.assertIn("Vyúčtovanie inventarizačných rozdielov", html)
        self.assertIn("335000", html)
        self.assertIn("v návrhu", html)
        self.assertIn("Vyradené v evidencii majetku", html)

    def test_no_differences_no_section(self):
        inv = self._inventarizacia()
        self._supis(inv, "211000", 1000.0, 1000.0)
        self.assertEqual(inv.difference_state, "none")
        inv.action_propose_differences()
        self.assertFalse(inv.difference_line_ids)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_sk_inventory_verification.report_inventarizacny_zapis", inv.ids
        )[0].decode()
        self.assertNotIn("Vyúčtovanie inventarizačných rozdielov", html)
