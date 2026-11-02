# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from lxml import etree

from odoo.addons.account_cz_bankfile_base.utils.common import BankPaymentItem
from odoo.addons.account_fio_base.utils.orders import (
    KIND_DOMESTIC,
    KIND_EURO,
    KIND_FOREIGN,
    FioOrderError,
    account_from_country,
    build_fio_import_xml,
    classify,
    order_from_item,
    validate_order,
)


class FakeCountry:
    def __init__(self, code):
        self.code = code


class FakePartner:
    def __init__(self, name="Dodavatel s.r.o.", street=None, city=None,
                 country=None):
        self.name = name
        self.street = street
        self.city = city
        self.country_id = FakeCountry(country) if country else None


class FakeBank:
    """Duck-typed ``res.partner.bank`` — the utils import nothing from Odoo."""

    def __init__(self, acc_number, acc_type="bank", bic=None):
        self.acc_number = acc_number
        self.acc_type = acc_type
        self.bank_bic = bic

    def __bool__(self):
        return bool(self.acc_number)


COMPANY_BANK = FakeBank("CZ8020100000002111111111", acc_type="iban")
#: Fio's Slovak branch — bank code 8330. Fio runs both countries on one API,
#: so this is as valid an ordering account as the Czech one above.
COMPANY_BANK_SK = FakeBank("SK9783300000002900123456", acc_type="iban")


def item(bank, amount=100, currency="CZK", partner=None, **kwargs):
    values = dict(
        partner_bank=bank,
        amount=amount,
        currency_name=currency,
        vs="1234567890",
        ks="0558",
        ss="",
        message="Faktura 2026/0042",
        date=date(2026, 4, 25),
        label="PL/0001",
        partner=partner or FakePartner(),
    )
    values.update(kwargs)
    return BankPaymentItem(**values)


class TestFioClassification(TestCase):
    def test_czech_iban_is_domestic(self):
        self.assertEqual(
            classify(FakeBank("CZ9030000000000019012333", "iban"), "CZK"),
            KIND_DOMESTIC,
        )

    def test_czech_bban_is_domestic(self):
        self.assertEqual(
            classify(FakeBank("2212-2000000699/0300"), "CZK"), KIND_DOMESTIC,
        )

    def test_czech_account_stays_domestic_in_another_currency(self):
        """§6.3.1 allows a foreign-currency transfer between Fio accounts."""
        self.assertEqual(
            classify(FakeBank("CZ9030000000000019012333", "iban"), "USD"),
            KIND_DOMESTIC,
        )

    def test_slovak_iban_in_eur_is_a_europlatba(self):
        """Not domestic: §6.2 says EUR orders to Slovak banks left that path."""
        self.assertEqual(
            classify(FakeBank("SK1502000000001444615051", "iban"), "EUR"),
            KIND_EURO,
        )

    def test_non_sepa_is_foreign(self):
        self.assertEqual(
            classify(FakeBank("PK36SCBL0000001123456702", "iban"), "USD"),
            KIND_FOREIGN,
        )

    def test_eur_outside_sepa_is_foreign(self):
        self.assertEqual(
            classify(FakeBank("PK36SCBL0000001123456702", "iban"), "EUR"),
            KIND_FOREIGN,
        )

    def test_unusable_account_is_reported(self):
        with self.assertRaises(FioOrderError):
            classify(FakeBank("not an account"), "CZK")


class TestFioOrderBuilder(TestCase):
    def _xml(self, orders):
        return etree.fromstring(build_fio_import_xml(orders, COMPANY_BANK))

    def test_domestic_order(self):
        order = order_from_item(item(FakeBank("2212-2000000699/0300")))
        root = self._xml([order])
        el = root.find("Orders/DomesticTransaction")
        self.assertIsNotNone(el)
        self.assertEqual(el.findtext("accountFrom"), "2111111111")
        self.assertEqual(el.findtext("accountTo"), "2212-2000000699")
        self.assertEqual(el.findtext("bankCode"), "0300")
        self.assertEqual(el.findtext("amount"), "100.00")
        self.assertEqual(el.findtext("vs"), "1234567890")
        self.assertEqual(el.findtext("ks"), "0558")
        self.assertIsNone(el.findtext("ss"))
        self.assertEqual(el.findtext("date"), "2026-04-25")
        self.assertEqual(el.findtext("messageForRecipient"), "Faktura 2026/0042")

    def test_domestic_keeps_diacritics(self):
        """messageForRecipient is a ``140i`` field — diacritics are allowed."""
        order = order_from_item(
            item(FakeBank("2212-2000000699/0300"), message="Příspěvek za duben")
        )
        el = self._xml([order]).find("Orders/DomesticTransaction")
        self.assertEqual(el.findtext("messageForRecipient"), "Příspěvek za duben")

    def test_euro_order_folds_to_ascii(self):
        """``benefName`` is a ``35e`` field: no diacritics."""
        order = order_from_item(item(
            FakeBank("AT611904300234573201", "iban", bic="ABAGATWWXXX"),
            currency="EUR",
            partner=FakePartner("Šimon Nový", "Gugitzgasse 2", "Wien", "AT"),
        ))
        el = self._xml([order]).find("Orders/T2Transaction")
        self.assertEqual(el.findtext("benefName"), "Simon Novy")
        self.assertEqual(el.findtext("bic"), "ABAGATWWXXX")
        self.assertEqual(el.findtext("benefCountry"), "AT")

    def test_foreign_order(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Nishtar Rd 13", "Karachi", "PK"),
                message="Payment for hotel 032013",
            ),
            payment_reason="348",
        )
        el = self._xml([order]).find("Orders/ForeignTransaction")
        self.assertEqual(el.findtext("benefStreet"), "Nishtar Rd 13")
        self.assertEqual(el.findtext("remittanceInfo1"), "Payment for hotel 032013")
        self.assertEqual(el.findtext("paymentReason"), "348")
        self.assertEqual(el.findtext("detailsOfCharges"), "470503")

    def test_charge_bearer_from_iso20022(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="Invoice 42",
                iso_charge_bearer="DEBT",
            ),
            payment_reason="348",
        )
        el = self._xml([order]).find("Orders/ForeignTransaction")
        self.assertEqual(el.findtext("detailsOfCharges"), "470501")

    def test_urgent_priority_maps_to_a_payment_type(self):
        order = order_from_item(
            item(FakeBank("2212-2000000699/0300"), iso_priority="URGP")
        )
        el = self._xml([order]).find("Orders/DomesticTransaction")
        self.assertEqual(el.findtext("paymentType"), "431005")

    def test_element_order_is_domestic_euro_foreign(self):
        """§6.3: a file whose order kinds are out of sequence is rejected."""
        foreign = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="Invoice 42",
            ),
            payment_reason="348",
        )
        euro = order_from_item(item(
            FakeBank("AT611904300234573201", "iban", bic="ABAGATWWXXX"),
            currency="EUR",
            partner=FakePartner("Hans Gruber", "Gugitzgasse 2", "Wien", "AT"),
        ))
        domestic = order_from_item(item(FakeBank("2212-2000000699/0300")))
        root = self._xml([foreign, euro, domestic])
        self.assertEqual(
            [child.tag for child in root.find("Orders")],
            ["DomesticTransaction", "T2Transaction", "ForeignTransaction"],
        )

    def test_remittance_info_is_split_into_35_char_slots(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="A" * 80,
            ),
            payment_reason="348",
        )
        el = self._xml([order]).find("Orders/ForeignTransaction")
        self.assertEqual(el.findtext("remittanceInfo1"), "A" * 35)
        self.assertEqual(el.findtext("remittanceInfo2"), "A" * 35)
        self.assertEqual(el.findtext("remittanceInfo3"), "A" * 10)

    def test_non_numeric_symbol_is_dropped_not_sent(self):
        order = order_from_item(item(FakeBank("2212-2000000699/0300"), vs="FA/42"))
        el = self._xml([order]).find("Orders/DomesticTransaction")
        self.assertEqual(el.findtext("vs"), "42")

    def test_schema_location_is_declared(self):
        root = self._xml([order_from_item(item(FakeBank("2212-2000000699/0300")))])
        self.assertEqual(root.tag, "Import")
        self.assertTrue(root.attrib.values()[0].endswith("importIB.xsd"))

    def test_prefix_on_the_orderer_account_is_refused(self):
        """``accountFrom`` is ``16n`` — a prefix cannot be expressed."""
        with self.assertRaises(FioOrderError):
            build_fio_import_xml(
                [order_from_item(item(FakeBank("2212-2000000699/0300")))],
                FakeBank("19-2000145399/2010"),
            )

    def test_nothing_to_send(self):
        with self.assertRaises(FioOrderError):
            build_fio_import_xml([], COMPANY_BANK)

    def test_the_kind_can_be_forced(self):
        """A Czech account paid in EUR through SEPA rather than internally."""
        order = order_from_item(
            item(FakeBank("CZ9030000000000019012333", "iban", bic="FIOBCZPP"),
                 currency="EUR"),
            kind=KIND_EURO,
        )
        self.assertIsNotNone(self._xml([order]).find("Orders/T2Transaction"))

    def test_service_level_charge_bearer_counts_as_shared(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="Invoice 42",
                iso_charge_bearer="SLEV",
            ),
            payment_reason="348",
        )
        el = self._xml([order]).find("Orders/ForeignTransaction")
        self.assertEqual(el.findtext("detailsOfCharges"), "470503")

    def test_an_unknown_charge_bearer_falls_back_to_shared(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="Invoice 42",
                iso_charge_bearer="WHAT",
            ),
            payment_reason="348",
        )
        el = self._xml([order]).find("Orders/ForeignTransaction")
        self.assertEqual(el.findtext("detailsOfCharges"), "470503")

    def test_a_europlatba_needs_no_bic(self):
        """``bic`` is optional on T2Transaction (§6.3.2); the IBAN carries it."""
        order = order_from_item(item(
            FakeBank("AT611904300234573201", "iban"),
            currency="EUR",
            partner=FakePartner("Hans Gruber", "Gugitzgasse 2", "Wien", "AT"),
        ))
        self.assertEqual(validate_order(order), [])
        el = self._xml([order]).find("Orders/T2Transaction")
        self.assertIsNone(el.findtext("bic"))

    def test_a_domestic_order_needs_no_partner_record(self):
        """Domestic payments identify the beneficiary by account number only."""
        order = order_from_item(
            item(FakeBank("2212-2000000699/0300"), partner=None)
        )
        self.assertEqual(validate_order(order), [])
        el = self._xml([order]).find("Orders/DomesticTransaction")
        self.assertIsNone(el.findtext("benefName"))

    def test_several_orders_of_one_kind_all_appear(self):
        orders = [
            order_from_item(item(FakeBank("2212-2000000699/0300"), amount=n))
            for n in (10, 20, 30)
        ]
        el = self._xml(orders).find("Orders")
        self.assertEqual(len(el), 3)
        self.assertEqual(
            [child.findtext("amount") for child in el],
            ["10.00", "20.00", "30.00"],
        )


class TestFioOrderValidation(TestCase):
    """Problems are collected, not raised one at a time — the caller shows a list."""

    def test_missing_bank_account(self):
        with self.assertRaises(FioOrderError):
            order_from_item(item(FakeBank("")))

    def test_foreign_payment_requires_everything(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban"),
                currency="USD",
                partner=FakePartner("Amir Khan"),
                message="",
            ),
        )
        problems = validate_order(order)
        joined = " ".join(problems)
        self.assertIn("BIC", joined)
        self.assertIn("street", joined)
        self.assertIn("platební titul", joined)
        self.assertIn("remittanceInfo1", joined)

    def test_invalid_payment_reason(self):
        order = order_from_item(
            item(
                FakeBank("PK36SCBL0000001123456702", "iban", bic="ALFHPKKAXXX"),
                currency="USD",
                partner=FakePartner("Amir Khan", "Rd 13", "Karachi", "PK"),
                message="Invoice 42",
            ),
            payment_reason="999",
        )
        self.assertTrue(
            any("platební titul" in problem for problem in validate_order(order))
        )

    def test_negative_amount(self):
        order = order_from_item(item(FakeBank("2212-2000000699/0300"), amount=-5))
        self.assertTrue(any("positive" in p for p in validate_order(order)))

    def test_build_reports_every_problem_at_once(self):
        bad = order_from_item(item(FakeBank("2212-2000000699/0300"), amount=0))
        worse = order_from_item(
            item(FakeBank("2212-2000000699/0300"), amount=0, date=None)
        )
        with self.assertRaises(FioOrderError) as caught:
            build_fio_import_xml([bad, worse], COMPANY_BANK)
        self.assertEqual(len(str(caught.exception).splitlines()), 3)


class TestFioSlovakOrderer(TestCase):
    """Fio operates in CZ and SK on one API, so the *ordering* account may be
    Slovak. Every test above uses a Czech one; these cover the other side.
    """

    def _euro_item(self, amount):
        return item(
            FakeBank("SK1502000000001444615051", "iban"),
            amount=amount,
            currency="EUR",
            partner=FakePartner("Dodavatel s.r.o.", country="SK"),
        )

    def test_sk_iban_is_a_usable_ordering_account(self):
        """The regression: an SK IBAN used to reach ``parse_cz_account`` and
        raise a bare ``ValueError``, which no caller caught."""
        root = etree.fromstring(build_fio_import_xml(
            [order_from_item(item(FakeBank("2212-2000000699/0300")))],
            COMPANY_BANK_SK,
        ))
        self.assertEqual(
            root.findtext(".//DomesticTransaction/accountFrom"), "2900123456",
        )

    def test_ordering_account_country(self):
        self.assertEqual(account_from_country(COMPANY_BANK_SK), "SK")
        self.assertEqual(account_from_country(COMPANY_BANK), "CZ")
        # The national form names no country, but Fio's own two bank codes do.
        self.assertEqual(account_from_country(FakeBank("2900123456/8330")), "SK")
        self.assertEqual(account_from_country(FakeBank("2111111111/2010")), "CZ")
        # A non-Fio bank code concludes nothing — accountFrom would be refused
        # by the bank anyway, but the country must not be guessed.
        self.assertIsNone(account_from_country(FakeBank("2212-2000000699/0300")))
        self.assertIsNone(account_from_country(FakeBank("")))

    def test_foreign_ordering_account_is_refused_clearly(self):
        with self.assertRaises(FioOrderError):
            build_fio_import_xml(
                [order_from_item(item(FakeBank("2212-2000000699/0300")))],
                FakeBank("AT611904300234573201", "iban"),
            )

    def test_sk_branch_needs_payment_reason_above_50000_eur(self):
        order = order_from_item(self._euro_item(50000.01))
        self.assertTrue(
            any("platební titul" in p
                for p in validate_order(order, home_country="SK"))
        )

    def test_sk_branch_threshold_is_exclusive(self):
        order = order_from_item(self._euro_item(50000))
        self.assertEqual(validate_order(order, home_country="SK"), [])

    def test_payment_reason_satisfies_the_sk_rule(self):
        order = order_from_item(self._euro_item(60000), payment_reason="110")
        self.assertEqual(validate_order(order, home_country="SK"), [])

    def test_rule_does_not_apply_to_a_czech_orderer(self):
        order = order_from_item(self._euro_item(60000))
        self.assertEqual(validate_order(order, home_country="CZ"), [])
        self.assertEqual(validate_order(order), [])

    def test_europlatba_still_carries_the_symbols(self):
        """T2Transaction has native ks/vs/ss, so routing a Slovak payment
        through Europlatba loses nothing."""
        root = etree.fromstring(build_fio_import_xml(
            [order_from_item(self._euro_item(100))], COMPANY_BANK_SK,
        ))
        self.assertEqual(root.findtext(".//T2Transaction/vs"), "1234567890")
        self.assertEqual(root.findtext(".//T2Transaction/ks"), "0558")
