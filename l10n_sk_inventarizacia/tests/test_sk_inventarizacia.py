# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkInventarizacia(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.user = cls.env.user
        cls.keeper = cls.env["res.partner"].create({"name": "Skladník"})

    def _account(self, code):
        return self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )

    def _inventarizacia(self, **overrides):
        vals = {
            "company_id": self.company.id,
            "date_start": "2025-12-20",
            "date_as_of": "2025-12-31",
            "date_end": "2026-01-15",
        }
        vals.update(overrides)
        return self.env["l10n.sk.inventarizacia"].create(vals)

    # ------------------------------------------------------------------
    def test_three_distinct_dates_are_kept(self):
        """§ 30 ods. 2 prescribes three dates, not one."""
        inv = self._inventarizacia()
        self.assertEqual(str(inv.date_start), "2025-12-20")
        self.assertEqual(str(inv.date_as_of), "2025-12-31")
        self.assertEqual(str(inv.date_end), "2026-01-15")

    def test_end_cannot_precede_start(self):
        with self.assertRaises(UserError):
            self._inventarizacia(date_start="2026-01-15", date_end="2025-12-20")

    def test_physical_supis_totals_quantity_times_price(self):
        """§ 30 ods. 2 písm. e): množstvo AND cena, so value is derived."""
        inv = self._inventarizacia()
        supis = self.env["l10n.sk.inventurny.supis"].create(
            {
                "name": "Sklad materiálu",
                "inventarizacia_id": inv.id,
                "inventory_type": "fyzicka",
                "location": "Sklad A, Bratislava",
                "responsible_person_id": self.keeper.id,
                "counted_by_id": self.user.id,
                "line_ids": [
                    Command.create(
                        {
                            "name": "Skrutky M8",
                            "quantity": 250.0,
                            "uom_name": "ks",
                            "unit_price": 0.40,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Plech 2 mm",
                            "quantity": 12.0,
                            "uom_name": "m2",
                            "unit_price": 15.0,
                        }
                    ),
                ],
            }
        )
        self.assertEqual(supis.actual_amount, 280.0)
        self.assertEqual(inv.actual_amount, 280.0)

    def test_dokladova_inventura_reads_the_ledger(self):
        """Inventarizácia účtov: the book state comes from the ledger, not typing."""
        account = self._account("321000")
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2025-11-30",
                "journal_id": journal.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {"account_id": account.id, "debit": 0.0, "credit": 500.0}
                    ),
                    Command.create(
                        {
                            "account_id": self._account("501000").id,
                            "debit": 500.0,
                            "credit": 0.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()

        inv = self._inventarizacia()
        supis = self.env["l10n.sk.inventurny.supis"].create(
            {
                "name": "Dodávatelia — dokladová inventúra",
                "inventarizacia_id": inv.id,
                "inventory_type": "dokladova",
                "account_id": account.id,
                "counted_by_id": self.user.id,
            }
        )
        self.assertEqual(supis.book_amount, -500.0)

        # Confirming the same 500 as actually owed leaves no difference.
        supis.line_ids = [
            Command.create(
                {"name": "Dodávateľ A", "quantity": 1.0, "unit_price": -500.0}
            )
        ]
        self.assertEqual(supis.difference, 0.0)

    def test_ledger_read_ignores_entries_after_the_as_of_date(self):
        account = self._account("321000")
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)], limit=1
        )
        later = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2026-02-01",
                "journal_id": journal.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {"account_id": account.id, "debit": 0.0, "credit": 999.0}
                    ),
                    Command.create(
                        {
                            "account_id": self._account("501000").id,
                            "debit": 999.0,
                            "credit": 0.0,
                        }
                    ),
                ],
            }
        )
        later.action_post()

        inv = self._inventarizacia()
        supis = self.env["l10n.sk.inventurny.supis"].create(
            {
                "name": "Dodávatelia",
                "inventarizacia_id": inv.id,
                "inventory_type": "dokladova",
                "account_id": account.id,
                "counted_by_id": self.user.id,
            }
        )
        # The 2026-02-01 entry is after the deň ku ktorému and must not count.
        self.assertEqual(supis.book_amount, 0.0)

    def test_cannot_close_without_the_prescribed_signature(self):
        """§ 30 ods. 2 písm. i) — the signature is a prescribed particular."""
        inv = self._inventarizacia()
        self.env["l10n.sk.inventurny.supis"].create(
            {
                "name": "Pokladnica",
                "inventarizacia_id": inv.id,
                "inventory_type": "fyzicka",
            }
        )
        inv.action_start()
        with self.assertRaisesRegex(UserError, "zistenie skutočného stavu"):
            inv.action_done()

        inv.supis_ids.counted_by_id = self.user
        inv.action_done()
        self.assertEqual(inv.state, "done")

    def test_cannot_close_with_no_supis_at_all(self):
        inv = self._inventarizacia()
        inv.action_start()
        with self.assertRaises(UserError):
            inv.action_done()

    def test_reports_render(self):
        inv = self._inventarizacia()
        supis = self.env["l10n.sk.inventurny.supis"].create(
            {
                "name": "Sklad",
                "inventarizacia_id": inv.id,
                "inventory_type": "fyzicka",
                "responsible_person_id": self.keeper.id,
                "counted_by_id": self.user.id,
                "line_ids": [
                    Command.create(
                        {"name": "Tovar", "quantity": 3.0, "unit_price": 10.0}
                    )
                ],
            }
        )
        supis_html = self.env["ir.qweb"]._render(
            "l10n_sk_inventarizacia.report_inventurny_supis", {"docs": supis}
        )
        self.assertIn("§ 30 ods. 2", str(supis_html))
        self.assertIn("Sklad", str(supis_html))

        zapis_html = self.env["ir.qweb"]._render(
            "l10n_sk_inventarizacia.report_inventarizacny_zapis", {"docs": inv}
        )
        self.assertIn("§ 30 ods. 3", str(zapis_html))
        self.assertIn("Posúdenie reálnosti ocenenia", str(zapis_html))
