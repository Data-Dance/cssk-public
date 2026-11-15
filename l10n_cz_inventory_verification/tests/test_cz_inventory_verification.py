# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzInventarizace(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.user = cls.env.user
        cls.keeper = cls.env["res.partner"].create({"name": "Skladník"})
        cls.Soupis = cls.env["l10n.cz.inventurni.soupis"]

    def _account(self, code):
        account = self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )
        self.assertTrue(account, "account %s is not in the Czech chart" % code)
        return account

    def _inventarizace(self, **overrides):
        vals = {"company_id": self.company.id, "date_as_of": "2025-12-31"}
        vals.update(overrides)
        return self.env["l10n.cz.inventarizace"].create(vals)

    def _soupis(self, inv, **overrides):
        """A soupis carrying every particular § 30 odst. 7 prescribes."""
        vals = {
            "name": "Sklad",
            "inventarizace_id": inv.id,
            "inventory_type": "fyzicka",
            "method": "počítáním a vážením",
            "datetime_start": "2025-12-20 08:00:00",
            "datetime_end": "2026-01-15 16:00:00",
            "counted_by_id": self.user.id,
            "inventory_responsible_id": self.user.id,
        }
        vals.update(overrides)
        return self.Soupis.create(vals)

    def _post(self, date, account, amount):
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": journal.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {"account_id": account.id, "debit": 0.0, "credit": amount}
                    ),
                    Command.create(
                        {
                            "account_id": self._account("501000").id,
                            "debit": amount,
                            "credit": 0.0,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    # ------------------------------------------------------------------
    def test_prescribed_moments_are_kept(self):
        """§ 30 odst. 7 písm. f), g), h): the rozvahový den on the
        inventarizace; rozhodný den, zahájení and ukončení per inventura."""
        inv = self._inventarizace()
        first = self._soupis(inv, rozhodny_den="2025-11-30")
        self._soupis(
            inv,
            name="Pokladna",
            datetime_start="2025-12-31 15:00:00",
            datetime_end="2025-12-31 17:30:00",
        )
        self.assertEqual(str(inv.date_as_of), "2025-12-31")
        self.assertEqual(str(first.rozhodny_den), "2025-11-30")
        self.assertEqual(str(first.datetime_start), "2025-12-20 08:00:00")
        self.assertEqual(str(first.datetime_end), "2026-01-15 16:00:00")
        # the exercise spans its inventury
        self.assertEqual(str(inv.date_start), "2025-12-20 08:00:00")
        self.assertEqual(str(inv.date_end), "2026-01-15 16:00:00")

    def test_end_cannot_precede_start(self):
        inv = self._inventarizace()
        with self.assertRaises(UserError):
            self._soupis(
                inv,
                datetime_start="2026-01-15 08:00:00",
                datetime_end="2025-12-20 08:00:00",
            )

    def test_rozhodny_den_must_precede_the_rozvahovy_den(self):
        """§ 30 odst. 4: "který předchází rozvahovému dni"."""
        inv = self._inventarizace()
        with self.assertRaises(UserError):
            self._soupis(inv, rozhodny_den="2025-12-31")
        soupis = self._soupis(inv, rozhodny_den="2025-11-30")
        # moving the rozvahový den under an existing rozhodný den is caught too
        with self.assertRaises(UserError):
            inv.date_as_of = "2025-11-30"
        self.assertTrue(soupis.exists())

    def test_window_of_a_periodic_inventarizace_is_warned_about(self):
        """§ 30 odst. 6: four months before, two months after. A warning —
        the true moments of a late inventura must stay recordable."""
        inv = self._inventarizace()
        soupis = self._soupis(inv)
        self.assertFalse(inv.timing_warning)

        soupis.datetime_start = "2025-08-15 08:00:00"
        self.assertIn("písm. a)", inv.timing_warning)
        self.assertNotIn("písm. b)", inv.timing_warning)

        soupis.write(
            {
                "datetime_start": "2025-12-20 08:00:00",
                "datetime_end": "2026-03-15 16:00:00",
            }
        )
        self.assertIn("písm. b)", inv.timing_warning)
        self.assertNotIn("písm. a)", inv.timing_warning)

        # the window binds a periodická inventarizace only
        inv.inventarizace_type = "prubezna"
        self.assertFalse(inv.timing_warning)

    def test_physical_soupis_totals_quantity_times_price(self):
        inv = self._inventarizace()
        soupis = self._soupis(
            inv,
            name="Sklad materiálu",
            location="Sklad A, Brno",
            responsible_person_id=self.keeper.id,
            line_ids=[
                Command.create(
                    {
                        "name": "Šrouby M8",
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
        )
        self.assertEqual(soupis.actual_amount, 280.0)
        self.assertEqual(inv.actual_amount, 280.0)

    def test_dokladova_inventura_reads_the_ledger(self):
        """The stav v účetnictví comes from the ledger, not from typing."""
        account = self._account("321000")
        self._post("2025-11-30", account, 500.0)

        inv = self._inventarizace()
        soupis = self._soupis(
            inv,
            name="Dodavatelé — dokladová inventura",
            inventory_type="dokladova",
            method="odsouhlasením zůstatků",
            account_id=account.id,
        )
        self.assertEqual(soupis.book_amount, -500.0)

        # Confirming the same 500 as actually owed leaves no difference.
        soupis.line_ids = [
            Command.create(
                {"name": "Dodavatel A", "quantity": 1.0, "unit_price": -500.0}
            )
        ]
        self.assertEqual(soupis.difference, 0.0)

    def test_ledger_read_ignores_entries_after_the_rozvahovy_den(self):
        account = self._account("321000")
        self._post("2026-02-01", account, 999.0)

        inv = self._inventarizace()
        soupis = self._soupis(
            inv, name="Dodavatelé", inventory_type="dokladova", account_id=account.id
        )
        # § 30 odst. 7 písm. d): valued as at the rozvahový den, although the
        # inventura itself ended on 2026-01-15.
        self.assertEqual(str(soupis.comparison_date), "2025-12-31")
        self.assertEqual(soupis.book_amount, 0.0)

    def test_prubezna_inventarizace_values_at_the_end_of_the_inventura(self):
        """§ 30 odst. 7 písm. e): ke dni ukončení inventury."""
        account = self._account("321000")
        self._post("2025-05-10", account, 300.0)
        self._post("2025-09-01", account, 700.0)

        inv = self._inventarizace(inventarizace_type="prubezna")
        soupis = self._soupis(
            inv,
            inventory_type="dokladova",
            account_id=account.id,
            datetime_start="2025-06-30 08:00:00",
            datetime_end="2025-06-30 12:00:00",
        )
        self.assertEqual(str(soupis.comparison_date), "2025-06-30")
        self.assertEqual(soupis.book_amount, -300.0)

        # the same soupis under a periodická inventarizace: the rozvahový den
        inv.inventarizace_type = "periodicka"
        self.assertEqual(str(soupis.comparison_date), "2025-12-31")
        self.assertEqual(soupis.book_amount, -1000.0)

    def test_cannot_close_without_the_prescribed_particulars(self):
        """§ 30 odst. 7: both signatures (písm. b)), the method (písm. c))
        and the two moments (písm. h)) are things a soupis "musí obsahovat"."""
        inv = self._inventarizace()
        soupis = self.Soupis.create(
            {
                "name": "Pokladna",
                "inventarizace_id": inv.id,
                "inventory_type": "fyzicka",
            }
        )
        inv.action_start()
        complete = {
            "counted_by_id": self.user.id,
            "inventory_responsible_id": self.user.id,
            "method": "počítáním",
            "datetime_start": "2025-12-31 15:00:00",
            "datetime_end": "2025-12-31 17:00:00",
        }
        self.assertEqual(set(complete), set(soupis._PRESCRIBED))
        # each one of them, missing on its own, is enough to refuse
        for field in complete:
            soupis.write(dict(complete, **{field: False}))
            with self.assertRaisesRegex(UserError, "Pokladna"):
                inv.action_done()
            self.assertEqual(inv.state, "in_progress")

        soupis.write(complete)
        inv.action_done()
        self.assertEqual(inv.state, "done")

    def test_cannot_close_with_no_soupis_at_all(self):
        inv = self._inventarizace()
        inv.action_start()
        with self.assertRaises(UserError):
            inv.action_done()

    def test_reports_render(self):
        inv = self._inventarizace()
        soupis = self._soupis(
            inv,
            rozhodny_den="2025-11-30",
            responsible_person_id=self.keeper.id,
            line_ids=[
                Command.create({"name": "Zboží", "quantity": 3.0, "unit_price": 10.0})
            ],
        )
        soupis_html = str(self.env["ir.qweb"]._render(
            "l10n_cz_inventory_verification.report_inventurni_soupis", {"docs": soupis}
        ))
        self.assertIn("§ 30 odst. 7", soupis_html)
        for particular in (
            "Sklad",
            "Zboží",
            "počítáním a vážením",
            "Okamžik, ke kterému se sestavuje účetní závěrka",
            "Rozhodný den",
            "Okamžik zahájení inventury",
            "Okamžik ukončení inventury",
            "Osoba odpovědná za zjištění skutečností",
            "Osoba odpovědná za provedení inventury",
            "Hmotně odpovědná osoba",
        ):
            self.assertIn(particular, soupis_html)

        zapis_html = str(self.env["ir.qweb"]._render(
            "l10n_cz_inventory_verification.report_inventarizacni_zapis", {"docs": inv}
        ))
        self.assertIn("Posouzení ocenění majetku a závazků", zapis_html)
        # The act prescribes no closing record: the printout must present
        # itself as an internal one and claim no paragraph as its form.
        self.assertIn("interní záznam", zapis_html)
        self.assertNotIn("§ 30 odst. 3", zapis_html)

    def test_optional_signature_is_printed_only_when_there_is_one(self):
        """The hmotně odpovědná osoba is practice, not § 30 odst. 7."""
        inv = self._inventarizace()
        soupis = self._soupis(inv)
        html = str(self.env["ir.qweb"]._render(
            "l10n_cz_inventory_verification.report_inventurni_soupis", {"docs": soupis}
        ))
        self.assertNotIn("Hmotně odpovědná osoba", html)
        self.assertIn("nestanoven", html)

    def test_soupis_opens_in_a_form_so_its_items_can_be_entered(self):
        """An inline-editable soupis list would never open the soupis form,
        and the items exist only there."""
        from lxml import etree

        arch = self.env["l10n.cz.inventarizace"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        doc = etree.fromstring(arch)
        soupis_list = doc.xpath("//field[@name='soupis_ids']/list")[0]
        self.assertFalse(soupis_list.get("editable"))
        self.assertTrue(doc.xpath(
            "//field[@name='soupis_ids']/form//field[@name='line_ids']"))
        for button in ("action_print_soupisy", "action_refresh_book_amounts",
                       "action_refresh_book_amount"):
            self.assertTrue(doc.xpath("//button[@name='%s']" % button),
                            "%s is in no view" % button)
        # every prescribed particular can be entered
        for field in self.Soupis._PRESCRIBED:
            self.assertTrue(
                doc.xpath("//field[@name='soupis_ids']/form//field[@name='%s']"
                          % field),
                "%s is not on the soupis form" % field)

    def test_soupisy_print_from_the_inventarizace(self):
        inv = self._inventarizace()
        with self.assertRaises(UserError):
            inv.action_print_soupisy()
        soupis = self.Soupis.create({"name": "Sklad", "inventarizace_id": inv.id})
        # discard_logo_check: an admin with no report layout would get the
        # layout configurator first
        action = inv.with_context(discard_logo_check=True).action_print_soupisy()
        self.assertEqual(
            action["report_name"],
            "l10n_cz_inventory_verification.report_inventurni_soupis",
        )
        self.assertEqual(action["context"]["active_ids"], soupis.ids)

    def test_refresh_never_zeroes_a_typed_book_amount(self):
        """A fyzická inventura has no account to read; its typed stav v
        účetnictví must survive the refresh."""
        inv = self._inventarizace()
        soupis = self._soupis(inv, book_amount=500.0)
        inv.action_refresh_book_amounts()
        self.assertEqual(soupis.book_amount, 500.0)

    def test_typed_book_amount_saved_together_with_the_items(self):
        """What saving a new fyzická inventura from its window does: the
        typed stav v účetnictví and the items arrive in one create."""
        inv = self._inventarizace()
        soupis = self._soupis(
            inv,
            book_amount=300.0,
            line_ids=[
                Command.create({"name": "Zboží", "quantity": 28.0, "unit_price": 10.0})
            ],
        )
        self.assertEqual(soupis.book_amount, 300.0)
        self.assertEqual(soupis.actual_amount, 280.0)
        self.assertEqual(soupis.difference, -20.0)
        # and in one write
        soupis.write(
            {
                "book_amount": 290.0,
                "line_ids": [
                    Command.create(
                        {"name": "Obaly", "quantity": 1.0, "unit_price": 5.0}
                    )
                ],
            }
        )
        self.assertEqual(soupis.actual_amount, 285.0)
        self.assertEqual(soupis.difference, -5.0)
        # switching the kind of inventura must not wipe a typed amount
        soupis.inventory_type = "dokladova"
        self.assertEqual(soupis.book_amount, 290.0)

    def test_refresh_picks_up_entries_posted_later(self):
        account = self._account("321000")
        inv = self._inventarizace()
        soupis = self._soupis(
            inv, inventory_type="dokladova", account_id=account.id
        )
        self.assertEqual(soupis.book_amount, 0.0)
        self._post("2025-12-15", account, 250.0)
        inv.action_refresh_book_amounts()
        self.assertEqual(soupis.book_amount, -250.0)

    def test_printouts_carry_the_seat(self):
        """Not a § 30 odst. 7 particular, but a record has to say whose it is."""
        self.company.partner_id.write(
            {"street": "Hlavní 1", "city": "Olomouc", "zip": "77900"})
        inv = self._inventarizace()
        soupis = self._soupis(inv)
        for template, docs in (
            ("report_inventurni_soupis", soupis),
            ("report_inventarizacni_zapis", inv),
        ):
            html = str(self.env["ir.qweb"]._render(
                "l10n_cz_inventory_verification.%s" % template, {"docs": docs}))
            self.assertIn("Sídlo", html)
            self.assertIn("Olomouc", html)

    def test_state_literals_exist(self):
        inv = self._inventarizace()
        states = dict(inv._fields["state"].selection)
        self._soupis(inv)
        for action, state in (
            ("action_start", "in_progress"),
            ("action_done", "done"),
            ("action_draft", "draft"),
        ):
            getattr(inv, action)()
            self.assertEqual(inv.state, state)
            self.assertIn(state, states)
