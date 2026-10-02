"""Shared primitives for the CZ/SK bank-file builders.

* ``BankPaymentItem`` — the normalized payment line passed to the builders, so
  the format logic never touches ``account.payment`` vs ``account.payment.line``
  directly.
* ``payments_to_items`` — the ``account.payment`` mapping the Enterprise
  bridges share.
* ``parse_cz_account`` / ``fold_to_ascii`` / ``format_amount_haler`` — helpers
  common to both ABO and MultiCash.
* ``resolve_symbol`` — VS/KS/SS resolution (explicit value, else a ``VS:``-style
  token parsed from the free-text communication).
"""
import re
import unicodedata
from collections import namedtuple

# National bank account: ``[prefix-]account/bank`` (prefix 0-6, account 2-10,
# bank 4). Identical in CZ and SK, and a 4-digit bank code alone cannot tell
# them apart — hence the ``country`` of this form is always unknown.
_CZ_ACC_RE = re.compile(r'^\s*(?:(\d{1,6})-)?(\d{2,10})\s*/\s*(\d{4})\s*$')
# CZ and SK IBANs are structurally identical:
# cc + 2 check + 4 bank + 6 prefix + 10 account.
_NAT_IBAN_RE = re.compile(r'^(CZ|SK)\d{2}(\d{4})(\d{6})(\d{10})$')

_VS_RE = re.compile(r'\bVS\s*[:=]?\s*(\d{1,10})\b', re.IGNORECASE)
_KS_RE = re.compile(r'\bKS\s*[:=]?\s*(\d{1,4})\b', re.IGNORECASE)
_SS_RE = re.compile(r'\bSS\s*[:=]?\s*(\d{1,10})\b', re.IGNORECASE)


# One normalized payment line. ABO uses the first 9 fields; MultiCash also uses
# partner / ref_id / iso_priority / iso_charge_bearer (default None).
BankPaymentItem = namedtuple(
    "BankPaymentItem",
    [
        "partner_bank",     # res.partner.bank record (beneficiary)
        "amount",           # float, in the item's currency
        "currency_name",    # str, e.g. 'CZK'
        "vs", "ks", "ss",   # resolved symbol strings
        "message",          # str (memo / communication)
        "date",             # datetime.date (caller resolves any fallback)
        "label",            # str, used in error messages
        "partner",          # res.partner record (beneficiary) — MultiCash
        "ref_id",           # int/str fallback reference — MultiCash CFA/MT101
        "iso_priority",     # 'URGP' or None — MultiCash CFA
        "iso_charge_bearer",  # ISO20022 charge-bearer code or None
    ],
    defaults=(None, None, None, None),
)


def payments_to_items(payments, fallback_date=None):
    """Normalize ``account.payment`` records into :class:`BankPaymentItem`.

    Lives beside the builders rather than in the edition shims so the ABO and
    MultiCash Enterprise bridges share one mapping — the OCA side maps
    ``account.payment.line`` instead, which has different field names.

    The records are duck-typed (this module imports nothing from ``account``).
    VS/KS/SS come from ``l10n_cssk_payment_symbols``, the ISO 20022 priority and
    charge bearer from ``account_iso20022``; both are read defensively so a
    caller that does not depend on them still gets a usable item.
    """
    items = []
    for payment in payments:
        text = payment.memo or payment.payment_reference or ''
        items.append(BankPaymentItem(
            partner_bank=payment.partner_bank_id,
            amount=payment.amount,
            currency_name=payment.currency_id.name,
            vs=resolve_symbol(
                'VS', getattr(payment, 'l10n_cssk_variable_symbol', None), text),
            ks=resolve_symbol(
                'KS', getattr(payment, 'l10n_cssk_constant_symbol', None), text),
            ss=resolve_symbol(
                'SS', getattr(payment, 'l10n_cssk_specific_symbol', None), text),
            message=text,
            date=payment.date or fallback_date,
            label=payment.display_name,
            partner=payment.partner_id,
            ref_id=payment.id,
            iso_priority=getattr(payment, 'iso20022_priority', None),
            iso_charge_bearer=getattr(payment, 'iso20022_charge_bearer', None),
        ))
    return items


def parse_national_account(partner_bank, countries=('CZ',)):
    """Return ``(country, prefix, account, bank_code)`` from a ``res.partner.bank``.

    Accepts an IBAN of one of ``countries``, or the free-form
    ``[prefix-]account/bank``. An empty prefix is returned as ``''`` (the caller
    renders it per the target format). ``country`` is the IBAN's country, or
    ``None`` for the national form — which carries no country at all, since CZ
    and SK share the ``account/bank`` shape and the 4-digit bank code space is
    not disjoint enough to guess from.

    ``countries`` is what the *caller's* format can actually send to, and it
    defaults to CZ alone so that ABO and MultiCash keep refusing everything
    else. CZ and SK IBANs are structurally identical, so quietly accepting an
    SK one into a Czech-only file format would build a plausible-looking file
    that the bank then rejects — a loud refusal here is worth more. Fio's XML,
    which serves both countries on one API, passes ``('CZ', 'SK')``.
    """
    if not partner_bank:
        raise ValueError("Partner bank account is missing")
    acc = (partner_bank.acc_number or '').strip().upper().replace(' ', '')
    m = _NAT_IBAN_RE.match(acc)
    if m and m.group(1) in countries:
        country, bank, prefix, account = m.groups()
        return country, prefix.lstrip('0'), account.lstrip('0') or '0', bank
    if not m:
        m = _CZ_ACC_RE.match(acc)
        if m:
            return None, m.group(1) or '', m.group(2), m.group(3)
    raise ValueError(
        "Bank account %r is not usable here (expected an IBAN of %s, or the "
        "prefix-account/bank format)."
        % (partner_bank.acc_number, '/'.join(countries))
    )


def parse_cz_account(partner_bank):
    """Return ``(prefix, account, bank_code)`` — the CZ-only view.

    Kept as its own name because ABO and MultiCash are Czech formats and every
    one of their call sites means "a Czech account". Everything else should
    call :func:`parse_national_account` and say which countries it accepts.

    The refusal message is restated here rather than inherited: it is what an
    ABO or MultiCash user reads when an account will not parse, and "not a
    Czech account" says the useful thing in a way the generic wording does not.
    """
    if not partner_bank:
        raise ValueError("Partner bank account is missing")
    try:
        _country, prefix, account, bank_code = parse_national_account(partner_bank)
    except ValueError:
        raise ValueError(
            "Bank account %r is not a Czech account (expected IBAN CZxx... or "
            "prefix-account/bank format)." % partner_bank.acc_number
        ) from None
    return prefix, account, bank_code


class _AccNumber:
    """Duck-typed ``res.partner.bank`` for a bare account string."""

    def __init__(self, acc_number):
        self.acc_number = acc_number

    def __bool__(self):
        return bool(self.acc_number)


def national_account_key(acc_number, countries=('CZ', 'SK')):
    """``(bank, prefix, number)`` of a CZ/SK account in either spelling.

    The same Czech account is written ``CZ65 0800 0000 1920 0014 5399``,
    ``19-2000145399/0800`` or, in a bank statement, ``0800/192000145399`` —
    and a string comparison, sanitized or not, pairs none of them. Statement
    imports compare this key instead when looking for the journal a file
    belongs to. ``None`` for anything that is neither form.
    """
    try:
        _country, prefix, number, bank = parse_national_account(
            _AccNumber(acc_number), countries=countries)
    except ValueError:
        return None
    return bank, prefix.lstrip('0'), number.lstrip('0') or '0'


def fold_to_ascii(text):
    """Strip diacritics, return ASCII-only text."""
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def format_amount_haler(amount):
    """``45.67`` -> ``"4567"`` (no separator, last two digits are haléř)."""
    return str(int(round(amount * 100)))


def resolve_symbol(kind, explicit, fallback_text):
    """VS/KS/SS resolution: explicit value wins, else parse a ``VS:``/``KS:``/
    ``SS:`` token from ``fallback_text`` (the communication/memo)."""
    if explicit:
        return explicit
    if not fallback_text:
        return ''
    regex = {'VS': _VS_RE, 'KS': _KS_RE, 'SS': _SS_RE}[kind]
    m = regex.search(fallback_text)
    return m.group(1) if m else ''
