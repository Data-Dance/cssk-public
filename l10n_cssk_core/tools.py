# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Statutory rounding helpers.

CZ/SK statutory arithmetic rounds HALF-UP — ties go away from zero — while
Python's built-in ``round()`` is banker's rounding (round-half-to-even) and
the ``int(x + 0.5)`` idiom truncates toward zero for negatives
(``int(-9.7 + 0.5) == -9``, statutorily it must be ``-10``). Every statutory
computation in the l10n_cz_* / l10n_sk_* modules should round through these
helpers instead.
"""
import difflib
import re

from odoo.tools import float_round


def statutory_round(value, digits=0):
    """Round HALF-UP (away from zero on ties) to ``digits`` decimal places."""
    return float_round(
        value or 0.0, precision_digits=digits, rounding_method="HALF-UP"
    )


def statutory_whole(value):
    """Round HALF-UP to whole units and return an ``int`` (e.g. whole euros
    on the Súhrnný výkaz per the SVDPHv20 poučenie: −9.7 → −10, not −9)."""
    return int(statutory_round(value, 0))


#: A Czech or Slovak IČO is eight digits, zero-padded when shorter.
ICO_LENGTH = 8
#: Fewest digits an unpadded IČO may be written with.
#:
#: The check digit alone does not bound the length: one number in eleven passes
#: it, so ``1``, ``19``, ``27`` … all satisfy the arithmetic once zero-padded,
#: and **10 000** values of five digits or fewer would be accepted as IČOs.
#: Every genuine IČO is written with at least six (the oldest carry leading
#: zeros -- ``00614556``, ``00216054`` -- and are printed as ``614556``), so
#: this floor rejects all 10 000 and costs nothing real.
ICO_MIN_DIGITS = 6
#: Weights applied to the first seven digits by the mod-11 check.
_ICO_WEIGHTS = (8, 7, 6, 5, 4, 3, 2)


def normalize_registry(value):
    """Canonical STORAGE form of a CZ/SK company registry (IČO).

    Whitespace goes and the number is zero-padded to eight digits, so the
    register's ``00 585 441`` and a user's ``585441`` both become
    ``00585441``. The leading zeros are significant and are KEPT — a Czech
    IČO is printed with them, and dropping them corrupts the number on an
    invoice.

    Anything that is not a plain number of :data:`ICO_MIN_DIGITS` to
    :data:`ICO_LENGTH` digits is returned with only its outer whitespace
    trimmed. This function never destroys an unrecognised value: the caller
    sees back what was typed, so a validation error can quote it, and a
    foreign registry (``HRB 6089``, ``93-1564675``) passes through untouched.

    **The lower bound is load-bearing, not tidiness.** Padding is what makes
    ``614556`` and ``00614556`` the same number — but pad with no floor and
    ``1`` becomes ``00000001``, which satisfies the check digit. The floor in
    :func:`is_valid_ico` cannot catch that on its own, because by the time it
    looks there are eight digits. Both functions must refuse the same short
    values or one launders junk past the other.

    See :func:`registry_key` for the form to COMPARE with, which is not this
    one.
    """
    if not value:
        return ""
    compact = "".join(str(value).split())
    if compact.isdigit() and ICO_MIN_DIGITS <= len(compact) <= ICO_LENGTH:
        return compact.zfill(ICO_LENGTH)
    return str(value).strip()


def registry_key(value):
    """Canonical COMPARISON form: digits only, leading zeros dropped.

    Deliberately different from :func:`normalize_registry`. Matching wants
    ``00682811`` and ``682811`` to be the same key; storage wants the padded
    form. Using the storage form as a match key misses half the matches it
    should make, and using this one for storage puts an unpadded IČO on a
    statutory document.

    Returns ``""`` for anything carrying no digits, so callers must treat an
    empty key as "no basis to match on" rather than as a value.
    """
    return "".join(c for c in str(value or "") if c.isdigit()).lstrip("0")


def is_valid_ico(value):
    """True if ``value`` is a checksum-valid Czech or Slovak IČO.

    Both countries use the same mod-11 scheme: weight the first seven digits
    by 8…2, take the remainder of the sum modulo 11, and the check digit is
    ``11 - remainder`` — except that a remainder of 0 gives 1 and a remainder
    of 1 gives 0.

    An unpadded number is accepted (``614556`` is ``00614556``), but not one
    shorter than :data:`ICO_MIN_DIGITS` — see there for why the check digit
    alone is not enough.

    Measured against the Data Dance production partner base: 12 of 96 CZ/SK
    values fail, and every one of the 84 genuine companies passes. Scope this
    to CZ/SK at the call site — other countries' registers do not use it, and
    applying it there rejects legitimate numbers.
    """
    digits = "".join(str(value or "").split())
    if not digits.isdigit():
        return False
    if not ICO_MIN_DIGITS <= len(digits) <= ICO_LENGTH:
        return False
    digits = digits.zfill(ICO_LENGTH)
    total = sum(int(d) * w for d, w in zip(digits[:7], _ICO_WEIGHTS))
    remainder = total % 11
    if remainder == 0:
        check = 1
    elif remainder == 1:
        check = 0
    else:
        check = 11 - remainder
    return check == int(digits[7])


# ---------------------------------------------------------------------------
# Company names
#
# Legal forms are CANONICALISED, never stripped. In CZ/SK the legal form is
# part of the identity: "Alfa s.r.o." and "Alfa a.s." are two different
# companies that both reduce to "alfa". Merging them would post one supplier's
# bill against the other -- worse than the duplicate this is meant to prevent.
#
# Canonicalising collapses only the formatting ("a.s." == "a. s." == "as")
# while keeping the form as a distinguishing token. It also removes the need to
# anchor at end-of-string: mapping the English word "as" to "as" is a no-op, so
# an over-eager match cannot change a name's meaning.
#
# Longest and most specific patterns first -- "spol. s r.o." before "s.r.o.".
# ---------------------------------------------------------------------------
_LEGAL_FORM_CANON = [
    (r"spol\.?\s*s\s*r\.?\s*o", "sro"),
    (r"sp\.?\s*z\s*o\.?\s*o", "spzoo"),
    (r"s\.?\s*r\.?\s*o", "sro"),
    (r"v\.?\s*o\.?\s*s", "vos"),
    (r"a\.?\s*s", "as"),
    (r"k\.?\s*s", "ks"),
    (r"o\.?\s*z", "oz"),
    (r"z\.?\s*s", "zs"),
    (r"s\.?\s*p", "sp"),
    (r"l\.?\s*l\.?\s*c", "llc"),
    (r"n\.?\s*o", "no"),
]
_LEGAL_FORM_CANON = [
    (re.compile(r"\b" + pattern + r"\b\.?", re.IGNORECASE), repl)
    for pattern, repl in _LEGAL_FORM_CANON
]

#: The canonical legal-form tokens, so callers can avoid picking one as a
#: search key: "ABC s.r.o." normalises to "abc sro", and an SQL ILIKE on "sro"
#: would never match the stored "ABC s.r.o." with its dots.
LEGAL_FORM_TOKENS = frozenset(repl for _pattern, repl in _LEGAL_FORM_CANON)


def normalize_company_name(name):
    """Casefolded name with legal form and punctuation canonicalised.

    Deliberately NOT a fuzzy match: it collapses formatting differences only,
    so two genuinely different names still differ — including two that differ
    only by legal form. Callers must still guard against merging parties whose
    registry numbers or countries disagree.
    """
    text = (name or "").casefold().replace("&", " and ")
    for pattern, repl in _LEGAL_FORM_CANON:
        text = pattern.sub(repl, text)
    text = re.sub(r"[^0-9a-zÀ-ɏ]+", " ", text)
    return " ".join(text.split())


def name_search_token(normalized_name):
    """Longest token of a normalised name that is safe to use in an ILIKE.

    Returns ``""`` when the name is nothing but a legal form.
    """
    words = [w for w in normalized_name.split() if w not in LEGAL_FORM_TOKENS]
    return max(words, key=len) if words else ""


def company_name_similarity(left, right):
    """How alike two company names are, 0.0 to 1.0, after normalisation.

    Plain ``difflib.SequenceMatcher`` over the normalised strings — no extra
    library, and no token-set or token-sort variant, because this ratio is the
    one that was **calibrated against the register**. Measured on 45 real
    Slovak companies (stored name vs the name ORSF returned): 44 scored
    exactly 1.000, including every case where the raw strings differed —
    ``DEMI Šport plus`` vs ``DEMI šport plus`` (case), ``spol. s r.o.`` vs
    ``spol.s r.o.`` (spacing), ``Europe Express s. r. o.`` vs ``Europe
    Express, s. r. o.`` (comma). The single outlier scored 0.716:
    ``Nakladatelství FORUM s.r.o.`` against the register's ``…, organizačná
    zložka``, which is a real difference and belongs in review.

    Swapping in a cleverer ratio would move those numbers and invalidate the
    thresholds derived from them, so do not — re-measure first.
    """
    a, b = normalize_company_name(left), normalize_company_name(right)
    if not a or not b:
        # No basis to compare. Never 1.0: two empty names are not a match.
        return 0.0
    if a == b:
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def normalize_vat(vat, keep_prefix=False):
    """The one VAT/DIČ/IČ DPH normaliser for statutory outputs.

    Uppercases and strips ALL whitespace (inner included, incl. NBSP:
    ``'cz 25 663 585'`` → ``'CZ25663585'``). Unless ``keep_prefix`` is set,
    a leading 2-letter alphabetic country prefix (CZ/SK/EL/XI/…) is dropped.
    Falsy input returns ``""``.

    Callers that must strip one SPECIFIC prefix (e.g. ADIS wants the DIČ =
    VAT minus ``CZ``, but a foreign ``SK…`` number passed through verbatim)
    should call with ``keep_prefix=True`` and strip that prefix explicitly.
    """
    if not vat:
        return ""
    vat = "".join(str(vat).split()).upper()
    if not keep_prefix and len(vat) > 2 and vat[:2].isalpha():
        vat = vat[2:]
    return vat
