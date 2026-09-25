"""ABO credit-transfer (úhrada, data type 1501) file builder.

``build_abo_file(company_bank, company_name, items)`` renders the raw bytes of a
batch (hromadný) ABO file. ``items`` is a list of
:class:`~.common.BankPaymentItem`. The orderer (debit) account lives in the
group header; items omit the debit account per the batch-order arrangement.
"""
import re
from datetime import datetime

from odoo import _
from odoo.exceptions import UserError

from .common import fold_to_ascii, parse_cz_account

_ABO_DATA_TYPE_TRANSFER = '1501'

# Characters the ČSAS spec flags as risky in payment messages (note 7); the
# pipe ``|`` is deliberately kept (recipient/sender message separator).
_FORBIDDEN_CHARS = set("˘˙°`¨{}‘’“”<>˝@#;§!&_*=+\\?[]ˇ")


def format_account_abo(prefix, account):
    """``"123456-1234567890"`` or ``"1234567890"`` when no prefix."""
    if prefix:
        return '%s-%s' % (prefix, account)
    return account


def format_date_ddmmrr(d):
    """ABO file dates: ``DDMMYY``."""
    return d.strftime('%d%m%y')


def to_win1250_safe(text):
    """Return text encodable in WIN1250 (CP1250); ASCII-fold what isn't."""
    if not text:
        return ''
    try:
        text.encode('cp1250')
        return text
    except UnicodeEncodeError:
        return fold_to_ascii(text)


def sanitize_message(text, max_len=35):
    """Clean a free-text ABO item message (collapse whitespace, strip forbidden
    characters keeping ``|``, truncate)."""
    if not text:
        return ''
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    cleaned = to_win1250_safe(cleaned)
    cleaned = ''.join(c for c in cleaned if c not in _FORBIDDEN_CHARS)
    cleaned = re.sub(r' +', ' ', cleaned).strip()
    return cleaned[:max_len]


def sanitize_client_name(text, max_len=20):
    """Client name in UHL1: alphanumeric, right-padded with spaces to width."""
    if not text:
        return ' ' * max_len
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    cleaned = re.sub(r'[^A-Za-z0-9 ]', '', fold_to_ascii(cleaned))
    return cleaned[:max_len].ljust(max_len, ' ')


def pack_constant_symbol(ks, partner_bank_code):
    """Pack the ABO KS field: positions 5–8 from the right = partner bank code,
    positions 1–4 = the actual KS. e.g. ('0308','0300') -> '03000308'."""
    ks_str = (ks or '').strip().zfill(4)[-4:]
    bank_str = (partner_bank_code or '').strip().zfill(4)[-4:]
    return bank_str + ks_str


def build_abo_file(company_bank, company_name, items):
    """Render an ABO úhrada file and return raw bytes."""
    if not items:
        raise UserError(_("Cannot generate an ABO file from an empty payment list."))
    if not company_bank:
        raise UserError(_("The bank journal has no bank account configured."))
    try:
        company_prefix, company_account, company_bank_code = parse_cz_account(company_bank)
    except ValueError as e:
        raise UserError(_("Orderer bank account: %s", str(e)))

    due_date = items[0].date

    total_haler = 0
    item_lines = []
    for item in items:
        if not item.partner_bank:
            raise UserError(_("Payment line %s is missing a partner bank account.", item.label))
        try:
            partner_prefix, partner_account, partner_bank_code = parse_cz_account(item.partner_bank)
        except ValueError as e:
            raise UserError(_("Payment line %(name)s: %(err)s", name=item.label, err=str(e)))
        if item.currency_name != 'CZK':
            raise UserError(_(
                "ABO only supports CZK payments — payment line %(name)s is in %(cur)s.",
                name=item.label, cur=item.currency_name,
            ))

        credit_acc = format_account_abo(partner_prefix, partner_account)
        amount_haler = int(round(item.amount * 100))
        total_haler += amount_haler
        vs = item.vs or '0'
        ks_field = pack_constant_symbol(item.ks, partner_bank_code)
        ss = item.ss or '0'
        message = sanitize_message(item.message or '', max_len=35)
        parts = [credit_acc, str(amount_haler), vs, ks_field, ss]
        line = ' '.join(parts)
        if message:
            line += ' ' + message
        item_lines.append(line)

    client_name = sanitize_client_name(company_name, 20)
    client_account = company_account.zfill(10)
    uhl1 = ''.join((
        'UHL1', format_date_ddmmrr(due_date), client_name, client_account,
        '001', '999', '000000', '000000',
    ))
    accounting_file_no = '%06d' % (datetime.now().microsecond % 1_000_000)
    acc_file_header = '1 %s %s %s' % (
        _ABO_DATA_TYPE_TRANSFER, accounting_file_no, company_bank_code)
    orderer_acc = format_account_abo(company_prefix, company_account)
    group_header = '2 %s %s %s' % (
        orderer_acc, total_haler if total_haler else 0, format_date_ddmmrr(due_date))

    out_lines = [uhl1, acc_file_header, group_header]
    out_lines.extend(item_lines)
    out_lines.append('3 +')
    out_lines.append('5 +')

    text = '\r\n'.join(out_lines) + '\r\n'
    try:
        return text.encode('cp1250')
    except UnicodeEncodeError:
        return fold_to_ascii(text).encode('ascii', errors='replace')
