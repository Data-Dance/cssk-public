# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTradeRegistryStatement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Zkušební s.r.o.", "is_company": True}
        )

    def _statement(self, **vals):
        self.partner.write(vals)
        return self.partner.l10n_cz_trade_registry_statement

    def test_the_statement_a_czech_invoice_has_to_carry(self):
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Obchodní rejstřík",
                l10n_cz_register_office="Městský soud v Praze",
                l10n_cz_register_number="C 12345",
            ),
            "Obchodní rejstřík vedený Městským soudem v Praze, "
            "oddíl C, vložka 12345",
        )

    def test_krajsky_soud_declines_too(self):
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="obchodní rejstřík",
                l10n_cz_register_office="Krajský soud v Brně",
                l10n_cz_register_number="B 678",
            ),
            "Obchodní rejstřík vedený Krajským soudem v Brně, "
            "oddíl B, vložka 678",
        )

    def test_the_statement_does_not_depend_on_who_the_subject_is(self):
        """No participle agrees with the legal form, so a sole trader in the
        obchodní rejstřík reads the same as a company."""
        trader = self.env["res.partner"].create(
            {
                "name": "Zkušební Podnikatel",
                "is_company": False,
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "A 4321",
            }
        )
        self.assertEqual(
            trader.l10n_cz_trade_registry_statement,
            "Obchodní rejstřík vedený Krajským soudem v Ostravě, "
            "oddíl A, vložka 4321",
        )

    def test_the_other_public_registers_use_the_same_wording(self):
        for register, oddil in (
            ("Spolkový rejstřík", "L"),
            ("Nadační rejstřík", "N"),
            ("Rejstřík ústavů", "U"),
            ("Rejstřík společenství vlastníků jednotek", "S"),
            ("Rejstřík obecně prospěšných společností", "O"),
        ):
            self.assertEqual(
                self._statement(
                    l10n_cz_register_name=register,
                    l10n_cz_register_office="Krajský soud v Plzni",
                    l10n_cz_register_number=f"{oddil} 77",
                ),
                f"{register} vedený Krajským soudem v Plzni, "
                f"oddíl {oddil}, vložka 77",
            )

    def test_a_two_letter_oddil_and_a_missing_space_still_parse(self):
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Obchodní rejstřík",
                l10n_cz_register_office="Krajský soud v Hradci Králové",
                l10n_cz_register_number="Dr123",
            ),
            "Obchodní rejstřík vedený Krajským soudem v Hradci Králové, "
            "oddíl Dr, vložka 123",
        )

    def test_a_sole_trader_states_the_other_evidence(self):
        """§ 435: one entered in no public register states the entry in
        another evidence. No court, no oddíl, no vložka."""
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Živnostenský rejstřík",
                l10n_cz_register_office="",
                l10n_cz_register_number="",
            ),
            "Živnostenský rejstřík",
        )

    def test_oddil_vlozka_wording_is_only_for_the_public_registers(self):
        """Another evidence numbers its entries its own way."""
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Evidence zemědělského podnikatele",
                l10n_cz_register_office="Městský úřad Vzorov",
                l10n_cz_register_number="A 123",
            ),
            "Evidence zemědělského podnikatele, Městský úřad Vzorov, "
            "číslo zápisu: A 123",
        )

    def test_an_unknown_authority_passes_through_verbatim(self):
        """A stiff statement beats a confidently wrong one on a statutory doc."""
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Obchodní rejstřík",
                l10n_cz_register_office="Rejstříkový soud Vzorov",
                l10n_cz_register_number="C 5",
            ),
            "Obchodní rejstřík, Rejstříkový soud Vzorov, oddíl C, vložka 5",
        )

    def test_a_number_in_another_shape_is_printed_whole(self):
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="Obchodní rejstřík",
                l10n_cz_register_office="Městský soud v Praze",
                l10n_cz_register_number="C 12345/MSPH",
            ),
            "Obchodní rejstřík vedený Městským soudem v Praze, "
            "spisová značka C 12345/MSPH",
        )

    def test_nothing_to_say_stays_empty(self):
        self.assertFalse(
            self._statement(
                l10n_cz_register_name="",
                l10n_cz_register_office="",
                l10n_cz_register_number="",
            )
        )

    def test_the_court_and_the_znacka_alone_are_still_worth_saying(self):
        self.assertEqual(
            self._statement(
                l10n_cz_register_name="",
                l10n_cz_register_office="Městský soud v Praze",
                l10n_cz_register_number="",
            ),
            "Městský soud v Praze",
        )
        self.assertEqual(
            self._statement(l10n_cz_register_number="C 12345"),
            "Městský soud v Praze, oddíl C, vložka 12345",
        )
        self.assertEqual(
            self._statement(l10n_cz_register_office=""),
            "Číslo zápisu: C 12345",
        )

    def test_a_manual_override_sticks_until_a_coordinate_moves(self):
        self._statement(
            l10n_cz_register_name="Obchodní rejstřík",
            l10n_cz_register_office="Městský soud v Praze",
            l10n_cz_register_number="C 12345",
        )
        self.partner.l10n_cz_trade_registry_statement = "Vlastní znění"
        self.assertEqual(
            self.partner.l10n_cz_trade_registry_statement, "Vlastní znění"
        )
        # ...and the register moving is what takes it back.
        self.partner.l10n_cz_register_office = "Krajský soud v Brně"
        self.assertEqual(
            self.partner.l10n_cz_trade_registry_statement,
            "Obchodní rejstřík vedený Krajským soudem v Brně, "
            "oddíl C, vložka 12345",
        )

    def test_the_company_feeds_the_field_l10n_cz_actually_prints(self):
        company = self.env["res.company"].create({"name": "Testovací s.r.o."})
        company.write(
            {
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "C 999",
            }
        )
        self.assertEqual(
            company.trade_registry,
            "Obchodní rejstřík vedený Krajským soudem v Ostravě, "
            "oddíl C, vložka 999",
        )

    def test_clearing_the_coordinates_clears_the_printed_statement(self):
        """Stale statutory text on an invoice is the failure being prevented."""
        company = self.env["res.company"].create(
            {
                "name": "Zaniklá s.r.o.",
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "C 999",
            }
        )
        self.assertTrue(company.trade_registry)
        company.write(
            {
                "l10n_cz_register_name": "",
                "l10n_cz_register_office": "",
                "l10n_cz_register_number": "",
            }
        )
        self.assertFalse(company.trade_registry)

    def test_editing_the_partner_directly_still_reaches_the_company(self):
        company = self.env["res.company"].create(
            {
                "name": "Přestěhovaná s.r.o.",
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "C 999",
            }
        )
        company.partner_id.l10n_cz_register_office = "Krajský soud v Plzni"
        self.assertIn("Krajským soudem v Plzni", company.trade_registry)

    def test_a_hand_written_trade_registry_is_not_clobbered(self):
        company = self.env["res.company"].create(
            {
                "name": "Jiná s.r.o.",
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "C 999",
            }
        )
        company.trade_registry = "Ručně napsané"
        self.assertEqual(company.trade_registry, "Ručně napsané")
        # ...and it survives a later coordinate change, because the module can
        # tell its own output from wording a person typed.
        company.l10n_cz_register_office = "Krajský soud v Brně"
        self.assertEqual(company.trade_registry, "Ručně napsané")

    def test_an_explicit_trade_registry_at_create_time_is_respected(self):
        company = self.env["res.company"].create(
            {
                "name": "Třetí s.r.o.",
                "trade_registry": "Zadané při založení",
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Krajský soud v Ostravě",
                "l10n_cz_register_number": "C 777",
            }
        )
        self.assertEqual(company.trade_registry, "Zadané při založení")


@tagged("post_install", "-at_install")
class TestStatementOnThePrintedInvoice(AccountTestInvoicingCommon):
    """The point of the sync: the statement reaches the document."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()

    def _render(self, invoice):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(
            "account.report_invoice", invoice.ids
        )
        return html.decode()

    def test_the_composed_statement_is_printed(self):
        self.env.company.write(
            {
                "l10n_cz_register_name": "Obchodní rejstřík",
                "l10n_cz_register_office": "Městský soud v Praze",
                "l10n_cz_register_number": "C 12345",
            }
        )
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, amounts=[100.0], post=True
        )
        statement = (
            "Obchodní rejstřík vedený Městským soudem v Praze, "
            "oddíl C, vložka 12345"
        )
        self.assertEqual(self.env.company.trade_registry, statement)
        self.assertIn(statement, self._render(invoice))

    def test_without_coordinates_nothing_is_printed(self):
        self.assertFalse(self.env.company.trade_registry)
        invoice = self.init_invoice(
            "out_invoice", partner=self.partner_a, amounts=[100.0], post=True
        )
        self.assertNotIn('name="trade_registry"', self._render(invoice))


@tagged("post_install", "-at_install")
class TestRegisterStatus(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Zaniklá s.r.o.", "is_company": True}
        )

    def test_status_parses_from_the_code_or_the_czech_word(self):
        parse = self.env["res.partner"]._l10n_cz_parse_register_status
        self.assertEqual(parse("dissolved", None), "dissolved")
        self.assertEqual(parse("ZANIKLY", None), "dissolved")
        self.assertEqual(parse("AKTIVNI", "AKTIVNI"), "active")
        self.assertEqual(parse("POZASTAVENY"), "suspended")
        self.assertEqual(parse("HISTORICKY"), "historical")
        self.assertEqual(parse(None, "Zaniklý subjekt"), "dissolved")
        self.assertEqual(parse("active", "zaniklý"), "active")

    def test_an_unrecognised_status_is_false(self):
        """"This source holds no such subject" is not a status of the subject."""
        parse = self.env["res.partner"]._l10n_cz_parse_register_status
        self.assertFalse(parse(None, None))
        for code in ("NEEXISTUJICI", "BUDOUCI", "LOGICKY_SMAZANY", "v likvidaci"):
            self.assertFalse(parse(code, code), code)

    def test_every_status_the_parser_returns_is_in_the_selection(self):
        from ..models.res_partner import ARES_STATUS_CODES, CZECH_STATUS_WORDS

        valid = dict(
            self.env["res.partner"]._fields["l10n_cz_register_status"].selection
        )
        for value in list(ARES_STATUS_CODES.values()) + list(
            CZECH_STATUS_WORDS.values()
        ):
            self.assertIn(value, valid)

    def test_only_the_non_trading_statuses_raise_the_flag(self):
        for status, inactive in (
            ("active", False), (False, False),
            ("dissolved", True), ("historical", True), ("suspended", True),
        ):
            self.partner.l10n_cz_register_status = status
            self.assertEqual(
                self.partner.l10n_cz_register_inactive, inactive, status
            )

    def test_the_warning_names_the_status_and_the_date(self):
        self.partner.write(
            {"l10n_cz_register_status": "dissolved",
             "l10n_cz_dissolved_on": "2013-09-03"}
        )
        warning = self.partner._l10n_cz_register_warning()
        self.assertIn("zaniklý", warning)
        self.assertIn("2013-09-03", warning)

    def test_an_active_partner_says_nothing(self):
        self.partner.l10n_cz_register_status = "active"
        self.assertEqual(self.partner._l10n_cz_register_warning(), "")


@tagged("post_install", "-at_install")
class TestRegisterStatusOnMoves(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.dead = cls.env["res.partner"].create(
            {
                "name": "Zaniklá s.r.o.",
                "is_company": True,
                "country_id": cls.env.ref("base.cz").id,
                "l10n_cz_register_status": "dissolved",
                "l10n_cz_dissolved_on": "2013-09-03",
            }
        )

    def _move(self, move_type, partner):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": "2026-01-15",
                "invoice_line_ids": [
                    (0, 0, {"name": "X", "quantity": 1, "price_unit": 10}),
                ],
            }
        )

    def test_the_company_under_test_is_czech(self):
        self.assertEqual(self.env.company.account_fiscal_country_id.code, "CZ")

    def test_invoicing_a_dissolved_customer_warns(self):
        move = self._move("out_invoice", self.dead)
        self.assertIn("zaniklý", move.l10n_cz_register_warning)

    def test_a_bill_from_a_dissolved_supplier_warns_about_the_deduction(self):
        move = self._move("in_invoice", self.dead)
        self.assertIn("odpočet daně", move.l10n_cz_register_warning)

    def test_a_live_partner_raises_nothing(self):
        alive = self.env["res.partner"].create(
            {"name": "Živá s.r.o.", "l10n_cz_register_status": "active"}
        )
        self.assertFalse(self._move("out_invoice", alive).l10n_cz_register_warning)

    def test_the_warning_never_blocks_the_posting(self):
        move = self._move("out_invoice", self.dead)
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertTrue(
            move.message_ids.filtered(lambda m: "zaniklý" in (m.body or ""))
        )


@tagged("post_install", "-at_install")
class TestRegisterLists(TransactionCase):
    """Scope of business and history, as the entry itself words them."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Testovací s.r.o.", "is_company": True}
        )

    def test_is_current_tracks_the_entry_and_the_deletion(self):
        Activity = self.env["l10n.cz.register.activity"]
        live = Activity.create(
            {"partner_id": self.partner.id, "name": "A", "valid_from": "2010-01-01"}
        )
        deleted = Activity.create(
            {"partner_id": self.partner.id, "name": "B",
             "valid_from": "2010-01-01", "valid_to": "2015-01-01"}
        )
        undated = Activity.create({"partner_id": self.partner.id, "name": "C"})
        self.assertTrue(live.is_current)
        self.assertFalse(deleted.is_current)
        self.assertTrue(undated.is_current)

    def test_an_activity_is_a_predmet_podnikani_unless_said_otherwise(self):
        activity = self.env["l10n.cz.register.activity"].create(
            {"partner_id": self.partner.id, "name": "Výroba, obchod a služby"}
        )
        self.assertEqual(activity.kind, "business")

    def test_history_holds_both_kinds(self):
        self.env["l10n.cz.register.history"].create([
            {"partner_id": self.partner.id, "kind": "name",
             "value": "Staré jméno s.r.o.", "valid_to": "2019-07-22"},
            {"partner_id": self.partner.id, "kind": "address",
             "value": "Vzorová 9, 100 00 Vzorov", "valid_to": "2009-07-22"},
        ])
        kinds = self.partner.l10n_cz_history_ids.mapped("kind")
        self.assertEqual(sorted(kinds), ["address", "name"])


@tagged("post_install", "-at_install")
class TestInactivePartnersAreReachable(TransactionCase):
    def test_a_menu_opens_the_list(self):
        action = self.env.ref(
            "l10n_cz_trade_registry.action_partner_l10n_cz_register_inactive")
        menus = self.env["ir.ui.menu"].search(
            [("action", "=", f"{action._name},{action.id}")])
        self.assertTrue(menus)

    def test_the_contact_search_can_filter_them(self):
        arch = self.env["res.partner"].get_view(view_type="search")["arch"]
        self.assertIn('name="l10n_cz_register_inactive"', arch)
