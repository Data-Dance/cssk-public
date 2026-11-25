# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzInventoryDifferences(AccountTestInvoicingCommon):
    """§ 30 odst. 10 a 11 zákona č. 563/1991 Sb. and ČÚS 007."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.user = cls.env.user
        cls.keeper = cls.env["res.partner"].create({"name": "Pokladní"})
        cls.Line = cls.env["l10n.cz.inventarizacni.rozdil"]

    def _account(self, code):
        account = self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )
        self.assertTrue(account, "account %s is not in the Czech chart" % code)
        return account

    def _inventarizace(self, **vals):
        inv = self.env["l10n.cz.inventarizace"].create(
            {"company_id": self.company.id, "date_as_of": "2025-12-31", **vals})
        inv.action_start()
        return inv

    def _soupis(self, inv, code, book, actual, name=None, **vals):
        return self.env["l10n.cz.inventurni.soupis"].create({
            "name": name or "Soupis %s" % code,
            "inventarizace_id": inv.id,
            "inventory_type": "fyzicka",
            "method": "počítáním",
            "datetime_start": "2025-12-31 08:00:00",
            "datetime_end": "2025-12-31 16:00:00",
            "counted_by_id": self.user.id,
            "inventory_responsible_id": self.user.id,
            "account_id": self._account(code).id,
            "book_amount": book,
            "line_ids": [Command.create(
                {"name": "Stav", "quantity": 1.0, "unit_price": actual})],
            **vals,
        })

    def _items(self, move):
        result = {}
        for line in move.line_ids:
            debit, credit = result.get(line.account_id.code, (0.0, 0.0))
            result[line.account_id.code] = (
                debit + line.debit, credit + line.credit)
        return result

    # ------------------------------------------------------------------
    def test_cash_schodek_is_a_financial_expense(self):
        """ČÚS 007 bod 3.1 with § 34 vyhlášky: 569/211 — unlike Slovakia,
        where the schodok is booked straight as a receivable. The claim on
        a financial asset is financial income (§ 33 vyhlášky)."""
        inv = self._inventarizace()
        soupis = self._soupis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        line = inv.difference_line_ids
        self.assertEqual((line.kind, line.amount), ("shortage", 50.0))
        self.assertEqual(line.counterpart_account_id.code, "569000")
        claim = self.Line.create({
            "inventory_id": inv.id, "sheet_id": soupis.id,
            "kind": "claim", "amount": 50.0, "partner_id": self.keeper.id,
        })
        self.assertEqual(claim.account_id.code, "378000")
        self.assertEqual(claim.counterpart_account_id.code, "668000")
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        self.assertEqual(move.state, "draft")
        self.assertEqual(str(move.date), "2025-12-31")
        self.assertEqual(
            self._items(move),
            {
                "569000": (50.0, 0.0),
                "211000": (0.0, 50.0),
                "378000": (50.0, 0.0),
                "668000": (0.0, 50.0),
            },
        )

    def test_proposed_accounts_follow_cus_007(self):
        inv = self._inventarizace()
        cases = [
            ("211000", "surplus", "668000"),
            ("112000", "shortage", "549000"),
            ("112000", "natural_loss", "501000"),
            ("112000", "surplus", "648000"),
            ("132000", "natural_loss", "504000"),
            # bod 3.2.2: zásoby vlastní činnosti through skupina 58
            ("123000", "shortage", "549000"),
            ("123000", "natural_loss", "583000"),
            ("123000", "surplus", "583000"),
            # bod 3.5 písm. b): přebytek against the oprávky
            ("022000", "surplus", "082000"),
            ("022000", "shortage", False),
            # bod 3.6: neodpisovaný
            ("031000", "shortage", "549000"),
            ("031000", "surplus", "413000"),
            ("321000", "shortage", False),
        ]
        for code, kind, expected in cases:
            soupis = self._soupis(inv, code, 100.0, 100.0, name="%s %s" % (code, kind))
            line = self.Line.new({
                "inventory_id": inv.id, "sheet_id": soupis.id,
                "kind": kind, "amount": 1.0,
            })
            self.assertEqual(
                line.counterpart_account_id.code or False, expected,
                "%s %s" % (code, kind))
        # the claim on an operating asset is operating income (bod 3.7)
        stock = self._soupis(inv, "132000", 100.0, 90.0, name="zboží")
        claim = self.Line.new({
            "inventory_id": inv.id, "sheet_id": stock.id,
            "kind": "claim", "amount": 1.0,
        })
        self.assertEqual(claim.counterpart_account_id.code, "648000")

    def test_prubezna_books_each_inventura_on_the_day_it_ended(self):
        """§ 30 odst. 11 with odst. 7 písm. e): one entry per day."""
        inv = self._inventarizace(inventarizace_type="prubezna")
        self._soupis(
            inv, "132000", 500.0, 480.0, name="Sklad A",
            datetime_start="2025-03-10 08:00:00",
            datetime_end="2025-03-10 15:00:00",
        )
        self._soupis(
            inv, "112000", 300.0, 310.0, name="Sklad B",
            datetime_start="2025-09-22 08:00:00",
            datetime_end="2025-09-22 15:00:00",
        )
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        moves = inv.difference_move_ids.sorted("date")
        self.assertEqual(
            [str(d) for d in moves.mapped("date")], ["2025-03-10", "2025-09-22"])
        self.assertEqual(
            self._items(moves[0]),
            {"549000": (20.0, 0.0), "132000": (0.0, 20.0)})
        self.assertEqual(
            self._items(moves[1]),
            {"112000": (10.0, 0.0), "648000": (0.0, 10.0)})

    def test_every_difference_must_be_settled_or_explained(self):
        inv = self._inventarizace()
        self._soupis(inv, "211000", 1000.0, 950.0)
        assets = self._soupis(inv, "022000", 5000.0, 4000.0)
        inv.action_propose_differences()
        # the manko of an odpisovaný asset has no one-line answer
        asset_line = inv.difference_line_ids.filtered(
            lambda l: l.sheet_id == assets)
        self.assertFalse(asset_line.counterpart_account_id)
        self.assertTrue(asset_line.warning)
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()
        asset_line.unlink()
        with self.assertRaises(ValidationError):
            assets.difference_skip = True
        assets.write({
            "difference_skip": True,
            "difference_skip_reason": "Vyřazeno v evidenci majetku",
        })
        inv.action_create_difference_entries()
        self.assertEqual(len(inv.difference_move_ids.line_ids), 2)
        with self.assertRaises(ValidationError):
            self.Line.create({
                "inventory_id": inv.id, "sheet_id": assets.id,
                "kind": "shortage", "amount": 1000.0,
            })

    def test_reopening_reverses_a_posted_entry_in_the_same_period(self):
        inv = self._inventarizace()
        self._soupis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        move.action_post()
        self.assertEqual(inv.difference_state, "posted")
        inv.action_done()

        inv.action_draft()
        reversal = inv.difference_move_ids - move
        self.assertEqual(reversal.reversed_entry_id, move)
        self.assertEqual(reversal.state, "posted")
        self.assertEqual(str(reversal.date), "2025-12-31")
        for code in ("132000", "549000"):
            lines = (move | reversal).line_ids.filtered(
                lambda l: l.account_id.code == code)
            self.assertEqual(sum(lines.mapped("balance")), 0.0, code)
        self.assertFalse(inv.difference_line_ids.move_id)
        self.assertEqual(inv.state, "draft")

    def test_reopening_deletes_a_draft_entry(self):
        inv = self._inventarizace()
        self._soupis(inv, "211000", 1000.0, 1005.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        inv.action_draft()
        self.assertFalse(move.exists())
        self.assertEqual(inv.difference_state, "ready")

    def test_a_locked_period_refuses_booking_and_reopening(self):
        inv = self._inventarizace()
        self._soupis(inv, "132000", 500.0, 480.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        move = inv.difference_move_ids
        move.action_post()
        self.company.fiscalyear_lock_date = "2025-12-31"
        with self.assertRaises(UserError), self.cr.savepoint():
            inv.action_draft()
        self.env.invalidate_all()
        self.assertEqual(inv.state, "in_progress")
        self.assertEqual(inv.difference_line_ids.move_id, move)

        other = self._inventarizace()
        self._soupis(other, "211000", 1000.0, 950.0)
        other.action_propose_differences()
        with self.assertRaises(UserError):
            other.action_create_difference_entries()
        self.assertFalse(other.difference_move_ids)

    def test_a_booked_difference_is_frozen(self):
        inv = self._inventarizace()
        soupis = self._soupis(inv, "211000", 1000.0, 950.0)
        inv.action_propose_differences()
        inv.action_create_difference_entries()
        line = inv.difference_line_ids
        with self.assertRaises(UserError):
            line.kind = "natural_loss"
        with self.assertRaises(UserError):
            soupis.unlink()
        with self.assertRaises(UserError):
            inv.unlink()
        with self.assertRaises(UserError):
            inv.action_create_difference_entries()

    def test_zapis_prints_the_settlement(self):
        inv = self._inventarizace()
        self._soupis(inv, "211000", 1000.0, 950.0, name="Pokladna Praha")
        inv.action_propose_differences()
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_cz_inventory_verification.report_inventarizacni_zapis", inv.ids
        )[0].decode()
        self.assertIn("Vyúčtování inventarizačních rozdílů", html)
        self.assertIn("569000", html)
        self.assertIn("nezaúčtováno", html)
