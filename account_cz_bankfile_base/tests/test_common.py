# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Account parsing, which four bank-file formats depend on being exact."""

# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from odoo.addons.account_cz_bankfile_base.utils.common import (
    parse_cz_account,
    parse_national_account,
)


class FakeBank:
    """Duck-typed ``res.partner.bank`` — these utils import nothing from Odoo."""

    def __init__(self, acc_number, acc_type="bank"):
        self.acc_number = acc_number
        self.acc_type = acc_type

    def __bool__(self):
        return bool(self.acc_number)


class TestParseCzAccount(TestCase):
    """``parse_cz_account`` is CZ-only and must stay that way.

    ABO and MultiCash are Czech formats. CZ and SK IBANs are structurally
    identical, so an SK IBAN accepted here would silently build a file the bank
    then rejects — these cases pin the refusal.
    """

    def test_cz_iban(self):
        self.assertEqual(
            parse_cz_account(FakeBank("CZ6508000000192000145399", "iban")),
            ("19", "2000145399", "0800"),
        )

    def test_national_form(self):
        self.assertEqual(
            parse_cz_account(FakeBank("2212-2000000699/0300")),
            ("2212", "2000000699", "0300"),
        )

    def test_national_form_without_prefix(self):
        self.assertEqual(
            parse_cz_account(FakeBank("1234567890/1100")),
            ("", "1234567890", "1100"),
        )

    def test_sk_iban_is_refused(self):
        with self.assertRaises(ValueError):
            parse_cz_account(FakeBank("SK3111000000002926862190", "iban"))

    def test_other_country_is_refused(self):
        with self.assertRaises(ValueError):
            parse_cz_account(FakeBank("AT611904300234573201", "iban"))

    def test_rubbish_is_refused(self):
        with self.assertRaises(ValueError):
            parse_cz_account(FakeBank("not an account"))

    def test_missing_account_is_refused(self):
        with self.assertRaises(ValueError):
            parse_cz_account(FakeBank(""))


class TestParseNationalAccount(TestCase):
    def test_country_is_reported_for_an_iban(self):
        self.assertEqual(
            parse_national_account(
                FakeBank("SK8983300000002900123456", "iban"), ("CZ", "SK"),
            ),
            ("SK", "", "2900123456", "8330"),
        )

    def test_country_is_none_for_the_national_form(self):
        """``account/bank`` is shared by both countries and the 4-digit bank
        code cannot separate them, so the country is unknown — not CZ."""
        self.assertEqual(
            parse_national_account(FakeBank("1234567890/1100"), ("CZ", "SK")),
            (None, "", "1234567890", "1100"),
        )

    def test_countries_is_a_whitelist(self):
        bank = FakeBank("SK3111000000002926862190", "iban")
        self.assertEqual(
            parse_national_account(bank, ("CZ", "SK"))[0], "SK",
        )
        with self.assertRaises(ValueError):
            parse_national_account(bank, ("CZ",))

    def test_leading_zeros_are_stripped_from_the_iban_account(self):
        self.assertEqual(
            parse_national_account(
                FakeBank("CZ7920100000002111111111", "iban"), ("CZ",),
            ),
            ("CZ", "", "2111111111", "2010"),
        )

    def test_the_message_names_the_accepted_countries(self):
        with self.assertRaises(ValueError) as caught:
            parse_national_account(
                FakeBank("AT611904300234573201", "iban"), ("CZ", "SK"),
            )
        self.assertIn("CZ/SK", str(caught.exception))


class TestNationalAccountKey(TestCase):
    """The key statement imports pair a file's account with a journal by."""

    def test_iban_and_national_forms_agree(self):
        from odoo.addons.account_cz_bankfile_base.utils.common import (
            national_account_key,
        )
        key = ('0800', '19', '2000145399')
        self.assertEqual(national_account_key('CZ65 0800 0000 1920 0014 5399'), key)
        self.assertEqual(national_account_key('19-2000145399/0800'), key)
        self.assertEqual(national_account_key('000019-2000145399/0800'), key)

    def test_sk_accepted_other_refused(self):
        from odoo.addons.account_cz_bankfile_base.utils.common import (
            national_account_key,
        )
        self.assertEqual(national_account_key('SK3112000000198742637541'),
                         ('1200', '19', '8742637541'))
        self.assertIsNone(national_account_key('DE89370400440532013000'))
        self.assertIsNone(national_account_key(''))
