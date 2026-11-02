# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Field formatting against the §4 data types.

Fio's field table is terse — ``18d``, ``140i``, ``35e``, ``10n`` — and getting
any of them wrong means the bank rejects the batch, or worse, accepts a
silently mangled one. These are the rules, pinned.
"""

from datetime import date
# ``odoo.tests.BaseCase`` rather than ``unittest.TestCase``: it is the same
# plain TestCase — no database, no cursor — but its ``__init_subclass__``
# assigns the ``standard``/``at_install`` tags. Odoo's TagsSelector silently
# SKIPS any class without ``test_tags``, so a bare unittest.TestCase in a
# tests/ package never runs under ``odoo-bin --test-enable`` at all.
from odoo.tests import BaseCase as TestCase

from odoo.addons.account_fio_base.utils.orders import (
    _account_from,
    _amount,
    _digits,
    _remittance,
    _text,
)

from .test_order_builder import FakeBank


class TestAmountFormatting(TestCase):
    """``18d`` — decimal point, two places."""

    def test_two_decimal_places_always(self):
        self.assertEqual(_amount(100), "100.00")
        self.assertEqual(_amount("100"), "100.00")
        self.assertEqual(_amount(1234.5), "1234.50")

    def test_rounding_is_half_up_on_the_decimal_not_the_float(self):
        """The classic haléř bug.

        ``round(2.675, 2)`` is 2.67, because 2.675 has no exact float
        representation. Money must not be rounded that way, so the builder goes
        through ``Decimal`` with an explicit ROUND_HALF_UP.
        """
        self.assertEqual(_amount("2.675"), "2.68")
        self.assertEqual(_amount("1.005"), "1.01")
        self.assertEqual(_amount("0.005"), "0.01")
        self.assertEqual(round(2.675, 2), 2.67)  # what we are avoiding

    def test_no_thousands_separator_and_no_comma(self):
        rendered = _amount("1234567.89")
        self.assertEqual(rendered, "1234567.89")
        self.assertNotIn(",", rendered)
        self.assertNotIn(" ", rendered)


class TestTextFormatting(TestCase):
    """``i`` keeps diacritics, ``e``/``x`` do not; both allow only
    ``, . / -`` and space beyond alphanumerics."""

    def test_truncation_at_the_exact_limit(self):
        self.assertEqual(len(_text("A" * 40, 35)), 35)
        self.assertEqual(len(_text("A" * 35, 35)), 35)
        self.assertEqual(len(_text("A" * 34, 35)), 34)

    def test_diacritics_kept_for_the_i_type(self):
        self.assertEqual(_text("Příspěvek za duben", 140), "Příspěvek za duben")

    def test_diacritics_folded_for_the_e_type(self):
        self.assertEqual(
            _text("Příliš žluťoučký kůň", 35, ascii_only=True),
            "Prilis zlutoucky kun",
        )

    def test_disallowed_punctuation_is_dropped(self):
        """§4 allows only ``, . / -`` and space beyond alphanumerics."""
        self.assertEqual(_text("Faktura #42 (záloha) 50%", 140), "Faktura 42 záloha 50")
        self.assertEqual(_text("A, B. C/D-E", 140), "A, B. C/D-E")

    def test_whitespace_is_collapsed(self):
        self.assertEqual(_text("  a \n b  ", 140), "a b")

    def test_empty_becomes_none_so_the_element_is_omitted(self):
        self.assertIsNone(_text("", 35))
        self.assertIsNone(_text(None, 35))
        self.assertIsNone(_text("###", 35))


class TestSymbolFormatting(TestCase):
    """``vs`` is ``10n``, ``ks`` ``4n``, ``ss`` ``10n`` — numeric fields."""

    def test_truncated_to_the_field_width(self):
        self.assertEqual(_digits("12345678901234", 10), "1234567890")
        self.assertEqual(_digits("05581", 4), "0558")

    def test_non_digits_are_stripped(self):
        self.assertEqual(_digits("VS 2026/0042", 10), "20260042")

    def test_a_symbol_with_no_digits_is_dropped_not_sent_empty(self):
        self.assertIsNone(_digits("N/A", 10))
        self.assertIsNone(_digits("", 4))
        self.assertIsNone(_digits(None, 4))


class TestRemittanceSplitting(TestCase):
    def test_split_into_35_character_slots(self):
        self.assertEqual(_remittance("A" * 80, 4), ["A" * 35, "A" * 35, "A" * 10])

    def test_never_more_slots_than_the_element_offers(self):
        """T2Transaction has three remittance elements, ForeignTransaction four."""
        self.assertEqual(len(_remittance("A" * 500, 3)), 3)
        self.assertEqual(len(_remittance("A" * 500, 4)), 4)

    def test_empty_yields_nothing(self):
        self.assertEqual(_remittance("", 4), [])
        self.assertEqual(_remittance(None, 4), [])


class TestOrdererAccount(TestCase):
    """``accountFrom`` is ``16n`` — the number alone, no bank code.

    ``_account_from`` returns ``(country, account)``: Fio serves CZ and SK on
    one API, and §6.3.2's platební-titul threshold depends on which of the two
    holds the *ordering* account.
    """

    def test_from_a_cz_iban(self):
        self.assertEqual(
            _account_from(FakeBank("CZ8020100000002111111111", "iban")),
            ("CZ", "2111111111"),
        )

    def test_from_an_sk_iban(self):
        """Fio's Slovak branch is bank code 8330, and its accounts are normally
        configured as SK IBANs. This used to raise a bare ``ValueError``."""
        self.assertEqual(
            _account_from(FakeBank("SK9783300000002900123456", "iban")),
            ("SK", "2900123456"),
        )

    def test_from_the_national_form(self):
        """``account/bank`` names no country — but ``accountFrom`` is always a
        Fio account, and Fio has exactly two bank codes."""
        self.assertEqual(
            _account_from(FakeBank("2111111111/2010")), ("CZ", "2111111111"),
        )
        self.assertEqual(
            _account_from(FakeBank("2900123456/8330")), ("SK", "2900123456"),
        )

    def test_an_unknown_bank_code_leaves_the_country_unknown(self):
        """Not a Fio code, so nothing can be concluded — and a country-specific
        rule must then be skipped rather than guessed at."""
        self.assertEqual(
            _account_from(FakeBank("2111111111/0800")), (None, "2111111111"),
        )

    def test_a_non_fio_country_is_refused(self):
        from odoo.addons.account_fio_base.utils.orders import FioOrderError

        with self.assertRaises(FioOrderError):
            _account_from(FakeBank("AT611904300234573201", "iban"))

    def test_an_all_zero_iban_prefix_is_not_a_prefix(self):
        """Every CZ IBAN carries six prefix digits; all-zero means there is none."""
        self.assertEqual(
            _account_from(FakeBank("CZ8020100000002111111111", "iban")),
            ("CZ", "2111111111"),
        )

    def test_a_real_prefix_is_refused_and_named(self):
        """``CZ65 0800 000019 2000145399`` has prefix 19.

        ``16n`` is a plain number: there is no way to express ``19-2000145399``,
        and quietly dropping or concatenating the prefix would send the money to
        a different account. The refusal names the prefix so the message is
        actionable.
        """
        from odoo.addons.account_fio_base.utils.orders import FioOrderError

        with self.assertRaises(FioOrderError) as caught:
            _account_from(FakeBank("CZ6508000000192000145399", "iban"))
        self.assertIn("19-", str(caught.exception))
