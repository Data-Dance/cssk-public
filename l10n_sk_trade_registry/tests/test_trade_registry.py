# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTradeRegistryStatement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "ESET, spol. s r.o.", "is_company": True}
        )

    def _statement(self, **vals):
        self.partner.write(vals)
        return self.partner.l10n_sk_trade_registry_statement

    def test_the_sentence_a_slovak_invoice_has_to_carry(self):
        self.assertEqual(
            self._statement(
                l10n_sk_register_name="Obchodný register",
                l10n_sk_register_office="Mestský súd Bratislava III",
                l10n_sk_register_number="Sro/3586/B",
            ),
            "Zapísaná v Obchodnom registri Mestského súdu Bratislava III, "
            "oddiel: Sro, vložka č.: 3586/B",
        )

    def test_okresny_sud_declines_too(self):
        self.assertEqual(
            self._statement(
                l10n_sk_register_name="Obchodný register",
                l10n_sk_register_office="Okresný súd Žilina",
                l10n_sk_register_number="Sro/12345/L",
            ),
            "Zapísaná v Obchodnom registri Okresného súdu Žilina, "
            "oddiel: Sro, vložka č.: 12345/L",
        )

    def test_a_sole_trader_gets_the_masculine_form_and_an_urad(self):
        trader = self.env["res.partner"].create(
            {
                "name": "Ján Novák",
                "is_company": False,
                "l10n_sk_register_name": "Živnostenský register",
                "l10n_sk_register_office": "Okresný úrad Trnava",
                "l10n_sk_register_number": "250-12345",
            }
        )
        self.assertEqual(
            trader.l10n_sk_trade_registry_statement,
            "Zapísaný v Živnostenskom registri Okresného úradu Trnava, "
            "číslo zápisu: 250-12345",
        )

    def test_an_unknown_authority_passes_through_verbatim(self):
        """A stiff sentence beats a confidently wrong one on a statutory doc."""
        self.assertEqual(
            self._statement(
                l10n_sk_register_name="Register partnerov verejného sektora",
                l10n_sk_register_office="Ministerstvo spravodlivosti SR",
                l10n_sk_register_number="",
            ),
            "Zapísaná v Register partnerov verejného sektora "
            "Ministerstvo spravodlivosti SR",
        )

    def test_nothing_to_say_stays_empty(self):
        self.assertFalse(
            self._statement(
                l10n_sk_register_name="",
                l10n_sk_register_office="",
                l10n_sk_register_number="",
            )
        )

    def test_a_manual_override_sticks_until_a_coordinate_moves(self):
        self._statement(
            l10n_sk_register_name="Obchodný register",
            l10n_sk_register_office="Mestský súd Bratislava III",
            l10n_sk_register_number="Sro/3586/B",
        )
        self.partner.l10n_sk_trade_registry_statement = "Vlastné znenie"
        self.assertEqual(
            self.partner.l10n_sk_trade_registry_statement, "Vlastné znenie"
        )
        # ...and the register moving is what takes it back.
        self.partner.l10n_sk_register_office = "Okresný súd Trenčín"
        self.assertEqual(
            self.partner.l10n_sk_trade_registry_statement,
            "Zapísaná v Obchodnom registri Okresného súdu Trenčín, "
            "oddiel: Sro, vložka č.: 3586/B",
        )

    def test_the_company_feeds_the_field_l10n_sk_actually_prints(self):
        company = self.env["res.company"].create({"name": "Testovacia s.r.o."})
        company.write(
            {
                "l10n_sk_register_name": "Obchodný register",
                "l10n_sk_register_office": "Mestský súd Košice",
                "l10n_sk_register_number": "Sro/999/V",
            }
        )
        self.assertEqual(
            company.trade_registry,
            "Zapísaná v Obchodnom registri Mestského súdu Košice, "
            "oddiel: Sro, vložka č.: 999/V",
        )

    def test_oddiel_vlozka_wording_is_only_for_the_obchodny_register(self):
        """A ŽR number can contain a slash; it has no oddiel and no vložka."""
        self.assertEqual(
            self._statement(
                l10n_sk_register_name="Živnostenský register",
                l10n_sk_register_office="Okresný úrad Nitra",
                l10n_sk_register_number="430-12345/2019",
            ),
            "Zapísaná v Živnostenskom registri Okresného úradu Nitra, "
            "číslo zápisu: 430-12345/2019",
        )

    def test_the_court_alone_is_still_worth_saying(self):
        self.assertEqual(
            self._statement(
                l10n_sk_register_name="",
                l10n_sk_register_office="Mestský súd Bratislava III",
                l10n_sk_register_number="",
            ),
            "Zapísaná, Mestského súdu Bratislava III",
        )

    def test_clearing_the_coordinates_clears_the_printed_sentence(self):
        """Stale statutory text on an invoice is the failure being prevented."""
        company = self.env["res.company"].create(
            {
                "name": "Zaniknutá s.r.o.",
                "l10n_sk_register_name": "Obchodný register",
                "l10n_sk_register_office": "Mestský súd Košice",
                "l10n_sk_register_number": "Sro/999/V",
            }
        )
        self.assertTrue(company.trade_registry)
        company.write(
            {
                "l10n_sk_register_name": "",
                "l10n_sk_register_office": "",
                "l10n_sk_register_number": "",
            }
        )
        self.assertFalse(company.trade_registry)

    def test_editing_the_partner_directly_still_reaches_the_company(self):
        company = self.env["res.company"].create(
            {
                "name": "Presťahovaná s.r.o.",
                "l10n_sk_register_name": "Obchodný register",
                "l10n_sk_register_office": "Mestský súd Košice",
                "l10n_sk_register_number": "Sro/999/V",
            }
        )
        company.partner_id.l10n_sk_register_office = "Okresný súd Prešov"
        self.assertIn("Okresného súdu Prešov", company.trade_registry)

    def test_a_hand_written_trade_registry_is_not_clobbered(self):
        company = self.env["res.company"].create(
            {
                "name": "Iná s.r.o.",
                "l10n_sk_register_name": "Obchodný register",
                "l10n_sk_register_office": "Mestský súd Košice",
                "l10n_sk_register_number": "Sro/999/V",
            }
        )
        company.trade_registry = "Ručne napísané"
        self.assertEqual(company.trade_registry, "Ručne napísané")
        # ...and it survives a later coordinate change, because the module can
        # tell its own output from wording a person typed.
        company.l10n_sk_register_office = "Okresný súd Trenčín"
        self.assertEqual(company.trade_registry, "Ručne napísané")

    def test_an_explicit_trade_registry_at_create_time_is_respected(self):
        company = self.env["res.company"].create(
            {
                "name": "Tretia s.r.o.",
                "trade_registry": "Zadané pri založení",
                "l10n_sk_register_name": "Obchodný register",
                "l10n_sk_register_office": "Mestský súd Košice",
                "l10n_sk_register_number": "Sro/777/V",
            }
        )
        self.assertEqual(company.trade_registry, "Zadané pri založení")


@tagged("post_install", "-at_install")
class TestRegisterStatus(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Zaniknutá s.r.o.", "is_company": True}
        )

    def test_status_parses_from_the_code_or_the_slovak_word(self):
        parse = self.env["res.partner"]._l10n_sk_parse_register_status
        self.assertEqual(parse("dissolved", None), "dissolved")
        self.assertEqual(parse(None, "zrušená"), "dissolved")
        self.assertEqual(parse(None, "Pozastavená"), "suspended")
        self.assertEqual(parse("active", "zrušená"), "active")

    def test_an_unrecognised_status_is_false_not_unknown(self):
        """"We did not parse it" and "the register says unknown" differ."""
        parse = self.env["res.partner"]._l10n_sk_parse_register_status
        self.assertFalse(parse(None, None))
        self.assertFalse(parse("liquidating", "v likvidácii"))
        self.assertEqual(parse("unknown", None), "unknown")

    def test_only_the_non_trading_statuses_raise_the_flag(self):
        for status, inactive in (
            ("active", False), ("unknown", False),
            ("dissolved", True), ("deleted", True), ("suspended", True),
        ):
            self.partner.l10n_sk_register_status = status
            self.assertEqual(
                self.partner.l10n_sk_register_inactive, inactive, status
            )

    def test_the_warning_names_the_status_and_the_date(self):
        self.partner.write(
            {"l10n_sk_register_status": "dissolved",
             "l10n_sk_dissolved_on": "2013-09-03"}
        )
        warning = self.partner._l10n_sk_register_warning()
        self.assertIn("zrušená", warning)
        self.assertIn("2013-09-03", warning)

    def test_an_active_partner_says_nothing(self):
        self.partner.l10n_sk_register_status = "active"
        self.assertEqual(self.partner._l10n_sk_register_warning(), "")


@tagged("post_install", "-at_install")
class TestRegisterStatusOnMoves(AccountTestInvoicingCommon):
    chart_template = "sk"
    country_code = "SK"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dead = cls.env["res.partner"].create(
            {
                "name": "Zaniknutá s.r.o.",
                "is_company": True,
                "country_id": cls.env.ref("base.sk").id,
                "l10n_sk_register_status": "dissolved",
                "l10n_sk_dissolved_on": "2013-09-03",
            }
        )

    def _move(self, move_type, partner):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_line_ids": [
                    (0, 0, {"name": "X", "quantity": 1, "price_unit": 10}),
                ],
            }
        )

    def test_invoicing_a_dissolved_customer_warns(self):
        move = self._move("out_invoice", self.dead)
        self.assertIn("zrušená", move.l10n_sk_register_warning)

    def test_a_bill_from_a_dissolved_supplier_warns_about_the_deduction(self):
        move = self._move("in_invoice", self.dead)
        self.assertIn("odpočítanie dane", move.l10n_sk_register_warning)

    def test_a_live_partner_raises_nothing(self):
        alive = self.env["res.partner"].create(
            {"name": "Živá s.r.o.", "l10n_sk_register_status": "active"}
        )
        self.assertFalse(self._move("out_invoice", alive).l10n_sk_register_warning)

    def test_the_warning_never_blocks_the_posting(self):
        move = self._move("out_invoice", self.dead)
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertTrue(
            move.message_ids.filtered(lambda m: "zrušená" in (m.body or ""))
        )


@tagged("post_install", "-at_install")
class TestRegisterLists(TransactionCase):
    """Activities, filings and history — items 4-6 of the ORSF opportunities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Testovacia s.r.o.", "is_company": True,
             "company_registry": "31333532"}
        )

    def test_a_suspended_activity_is_flagged_while_the_company_stays_active(self):
        """The subject is active; it just may not do that particular work."""
        self.env["l10n.sk.register.activity"].create([
            {"partner_id": self.partner.id, "name": "Kúpa tovaru",
             "valid_from": "2010-01-01"},
            {"partner_id": self.partner.id, "name": "Stavebné práce",
             "valid_from": "2012-01-01", "suspended_from": "2024-05-01"},
        ])
        self.partner.l10n_sk_register_status = "active"
        self.assertTrue(self.partner.l10n_sk_has_suspended_activity)
        self.assertFalse(self.partner.l10n_sk_register_inactive)

    def test_a_lifted_suspension_does_not_flag(self):
        self.env["l10n.sk.register.activity"].create({
            "partner_id": self.partner.id, "name": "Stavebné práce",
            "suspended_from": "2024-05-01", "suspended_to": "2024-11-01",
        })
        self.assertFalse(self.partner.l10n_sk_has_suspended_activity)

    def test_is_current_tracks_the_validity_window(self):
        Activity = self.env["l10n.sk.register.activity"]
        live = Activity.create(
            {"partner_id": self.partner.id, "name": "A", "valid_from": "2010-01-01"}
        )
        ended = Activity.create(
            {"partner_id": self.partner.id, "name": "B",
             "valid_from": "2010-01-01", "valid_to": "2015-01-01"}
        )
        suspended = Activity.create(
            {"partner_id": self.partner.id, "name": "C",
             "valid_from": "2010-01-01", "suspended_from": "2020-01-01"}
        )
        self.assertTrue(live.is_current)
        self.assertFalse(ended.is_current)
        self.assertFalse(suspended.is_current)

    def test_filing_staleness_counts_full_years(self):
        this_year = fields.Date.context_today(self.partner).year
        self.env["l10n.sk.register.filing"].create([
            {"partner_id": self.partner.id, "period": str(this_year - 4),
             "filing_type": "Riadna"},
            {"partner_id": self.partner.id, "period": str(this_year - 3),
             "filing_type": "Riadna"},
        ])
        self.assertEqual(self.partner.l10n_sk_last_filing_period, str(this_year - 3))
        # A závierka for year N is filed during N+1, so by now year-1 is due.
        self.assertEqual(self.partner.l10n_sk_filing_years_overdue, 2)

    def test_an_up_to_date_filer_is_not_overdue(self):
        this_year = fields.Date.context_today(self.partner).year
        self.env["l10n.sk.register.filing"].create(
            {"partner_id": self.partner.id, "period": str(this_year - 1),
             "filing_type": "Riadna"}
        )
        self.assertEqual(self.partner.l10n_sk_filing_years_overdue, 0)

    def test_no_filings_known_is_not_reported_as_overdue(self):
        """Unknown and late are different facts; only one is the register's."""
        self.assertFalse(self.partner.l10n_sk_last_filing_period)
        self.assertEqual(self.partner.l10n_sk_filing_years_overdue, 0)

    def test_history_holds_both_kinds(self):
        self.env["l10n.sk.register.history"].create([
            {"partner_id": self.partner.id, "kind": "name",
             "value": "Staré meno s.r.o.", "valid_to": "2019-07-22"},
            {"partner_id": self.partner.id, "kind": "address",
             "value": "Pionierska 9/A, 831 02 Bratislava", "valid_to": "2009-07-22"},
        ])
        kinds = self.partner.l10n_sk_history_ids.mapped("kind")
        self.assertEqual(sorted(kinds), ["address", "name"])
