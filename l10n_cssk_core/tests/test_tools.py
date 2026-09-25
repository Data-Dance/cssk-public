# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import BaseCase

from odoo.addons.l10n_cssk_core.tools import (
    is_valid_ico,
    normalize_registry,
    normalize_vat,
    registry_key,
    statutory_round,
    statutory_whole,
)


class TestNormalizeVat(BaseCase):
    def test_empty_and_falsy(self):
        self.assertEqual(normalize_vat(""), "")
        self.assertEqual(normalize_vat(None), "")
        self.assertEqual(normalize_vat(False), "")
        self.assertEqual(normalize_vat("", keep_prefix=True), "")

    def test_strips_prefix_by_default(self):
        self.assertEqual(normalize_vat("CZ25663585"), "25663585")
        self.assertEqual(normalize_vat("SK2020317068"), "2020317068")

    def test_inner_whitespace_and_lowercase(self):
        # inner spaces, tabs and NBSP all go; result is uppercased
        self.assertEqual(normalize_vat("cz 256 63 585"), "25663585")
        self.assertEqual(normalize_vat("cz\t25 663 585"), "25663585")
        self.assertEqual(
            normalize_vat(" sk 2020 317 068 ", keep_prefix=True),
            "SK2020317068")

    def test_nonstandard_prefixes(self):
        # Greece files as EL, Northern Ireland as XI — both are 2-letter
        # alphabetic prefixes and must strip exactly like CZ/SK.
        self.assertEqual(normalize_vat("EL123456789"), "123456789")
        self.assertEqual(normalize_vat("xi 110 305 878"), "110305878")

    def test_keep_prefix(self):
        self.assertEqual(normalize_vat("cz 25663585", keep_prefix=True),
                         "CZ25663585")
        self.assertEqual(normalize_vat("EL123456789", keep_prefix=True),
                         "EL123456789")

    def test_prefixless_and_short_values(self):
        # purely numeric DIČ passes through; a 2-char value is never stripped
        self.assertEqual(normalize_vat("25663585"), "25663585")
        self.assertEqual(normalize_vat("cz"), "CZ")


class TestStatutoryRounding(BaseCase):
    # smoke-level guard so the module's own test scope covers the file
    def test_half_up(self):
        self.assertEqual(statutory_round(2.675, 2), 2.68)
        self.assertEqual(statutory_whole(-9.7), -10)


# Real IČOs, taken from the Data Dance production partner base and confirmed
# against the live registers (ORSF for SK, ARES for CZ) on 2026-09-07.
VALID_ICOS = (
    ("54093431", "Data Dance s.r.o. (SK)"),
    ("36459488", "eezysmile spol. s r.o. (SK)"),
    ("00614556", "Moore BDR s. r. o. (SK, leading zeros)"),
    ("47068370", "Cloudfarms a.s. (SK)"),
    ("56040890", "Táborčatá s. r. o. (SK, recent)"),
    ("57152063", "AVENTIC s. r. o. (SK)"),
    ("32112475", "Jana Havelková-HAVELKA (SK, sole trader)"),
    ("25380141", "TRAIVA, s.r.o. (CZ)"),
    ("14042576", "PEMAT CZECHIA s.r.o. (CZ)"),
    ("41603141", "Bitt technology ČS (CZ)"),
    ("28585658", "VITAMINÁTOR s.r.o. (CZ)"),
    ("00216054", "Helian Group s.r.o. (CZ, leading zeros)"),
)

# Every value the checksum rejected on that same base. Three are the company
# NAME typed into the number field, which is the failure the check exists for.
INVALID_ICOS = (
    ("11111111111111", "14 digits"),
    ("531121554", "9 digits"),
    ("111111", "repunit"),
    ("12345", "placeholder"),
    ("1234567890", "10 digits"),
    ("20239413", "8 digits, wrong check digit"),
    ("Test", "placeholder word"),
    ("-", "dash"),
    ("cepatay111", "mailbox name"),
    ("TRAIVA, s.r.o.", "company name in the number field"),
    ("JUSTICE.CZ", "register's website"),
    ("Bitt technology ČS, spol. s r.o.", "company name in the number field"),
)

# Legitimate registry numbers from countries that do not use the IČO scheme.
# The check must never see these; if it does, it rejects real customers.
FOREIGN_REGISTRIES = (
    "HRB 6089",        # Hetzner Online GmbH (DE)
    "93-1564675",      # Runpod Inc (US EIN)
    "40103265308",     # Ascensio System SIA (LV)
    "1-120979442",     # LABA INTERNATIONAL LIMITED (PG)
    "201871706",       # VATIVAN Ltd. (BG)
)


class TestIco(BaseCase):
    def test_valid(self):
        for ico, label in VALID_ICOS:
            self.assertTrue(is_valid_ico(ico), f"{ico} should be valid — {label}")

    def test_invalid(self):
        for ico, label in INVALID_ICOS:
            self.assertFalse(is_valid_ico(ico), f"{ico!r} should fail — {label}")

    def test_accepts_the_printed_forms(self):
        # The register prints in triplets and users paste that verbatim.
        self.assertTrue(is_valid_ico("00 585 441"))   # KOOPERATIVA (SK)
        self.assertTrue(is_valid_ico("097 25 539"))   # One Glare s.r.o. (CZ)
        # An unpadded number is still the same number.
        self.assertTrue(is_valid_ico("614556"))       # == 00614556
        self.assertTrue(is_valid_ico("216054"))       # == 00216054

    def test_falsy_and_zero(self):
        for value in ("", None, False, "0", "00000000"):
            self.assertFalse(is_valid_ico(value))

    def test_rejects_short_numbers_that_satisfy_the_check_digit(self):
        """The check digit alone does not bound the length.

        One number in eleven satisfies the arithmetic, so zero-padding an
        arbitrary short number makes it "valid": 10 000 values of five digits
        or fewer would pass. These are exactly the junk a signup form
        collects, so the length floor is doing real work, not tidying.
        """
        for value in ("1", "19", "27", "35", "43", "51", "60", "78", "94"):
            self.assertFalse(
                is_valid_ico(value),
                f"{value!r} satisfies the check digit but is not an IČO",
            )

    def test_the_floor_does_not_reject_a_real_number(self):
        """Every genuine IČO is written with at least six digits, including
        the old ones that carry leading zeros."""
        for value in ("614556", "216054", "585441", "695599"):
            self.assertTrue(is_valid_ico(value), f"{value} is a real IČO")


class TestNormalizeRegistry(BaseCase):
    def test_pads_and_strips(self):
        self.assertEqual(normalize_registry("00 585 441"), "00585441")
        self.assertEqual(normalize_registry("097 25 539"), "09725539")
        self.assertEqual(normalize_registry("614556"), "00614556")
        self.assertEqual(normalize_registry(" 54093431 "), "54093431")

    def test_keeps_significant_leading_zeros(self):
        # Dropping these corrupts the number on a Czech invoice.
        self.assertEqual(normalize_registry("00216054"), "00216054")
        self.assertEqual(normalize_registry("02144298"), "02144298")

    def test_never_destroys_an_unrecognised_value(self):
        # A validation error has to be able to quote what was typed.
        for value, _label in INVALID_ICOS:
            if value.isdigit() and len(value) <= 8:
                continue
            self.assertEqual(normalize_registry(value), value.strip())

    def test_foreign_registries_pass_through(self):
        for value in FOREIGN_REGISTRIES:
            self.assertEqual(normalize_registry(value), value)

    def test_falsy(self):
        for value in ("", None, False):
            self.assertEqual(normalize_registry(value), "")

    def test_does_not_pad_a_short_number_into_validity(self):
        """The two functions have to refuse the same short values.

        ``1`` padded to ``00000001`` satisfies the check digit, and
        ``is_valid_ico`` cannot see that it was ever short. If this padded,
        it would launder junk straight past the constraint.
        """
        for value in ("1", "19", "27", "12345"):
            self.assertEqual(normalize_registry(value), value)
            self.assertFalse(is_valid_ico(normalize_registry(value)))


class TestRegistryKey(BaseCase):
    def test_drops_padding_so_the_two_forms_match(self):
        self.assertEqual(registry_key("00614556"), registry_key("614556"))
        self.assertEqual(registry_key("00 585 441"), "585441")

    def test_distinct_numbers_stay_distinct(self):
        self.assertNotEqual(registry_key("54093431"), registry_key("54093432"))

    def test_no_digits_is_no_key(self):
        # Callers must read "" as "nothing to match on", never as a value:
        # matching two of these to each other merges unrelated partners.
        for value in ("", None, False, "Test", "-", "JUSTICE.CZ"):
            self.assertEqual(registry_key(value), "")
