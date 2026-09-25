"""MultiCash file builders (CFD / CFU / CFA / MT101).

``build_multicash_file(company_bank, company_partner, company_name, items,
payment_method_code, batch_type)`` returns the raw bytes of the export file.
``items`` is a list of :class:`~.common.BankPaymentItem`.

Format specs (Česká spořitelna MultiCash 3.2):
  CFD - domestic CZ transfer (HD:11) / direct debit (HD:32)
  CFU - urgent domestic CZ transfer (HD:01)
  CFA - foreign payment (:01:..:07: header + SWIFT-like braced blocks)
  MT101 - SWIFT Request For Transfer
"""
import re
import unicodedata
from datetime import datetime

from odoo import _
from odoo.exceptions import UserError

from .common import fold_to_ascii, parse_cz_account

_CFD_TYPE_TRANSFER = '11'
_CFD_TYPE_INKASO = '32'
_CFU_TYPE_URGENT = '01'

# ISO 20022 ChrgBr -> MultiCash CFA charge-bearer mapping
_CHRGBR_MAP = {'SHAR': 'BN1', 'SHA': 'BN1', 'DEBT': 'OUR', 'OUR': 'OUR',
               'CRED': 'BN2', 'BEN': 'BN2'}

# SWIFT-X allowed character set (simplified)
_SWIFT_X_RE = re.compile(r"[^A-Za-z0-9 /\-?:().,'+]")


# ---------------------------------------------------------------------------
# text / amount helpers
# ---------------------------------------------------------------------------
def to_cp852_safe(text):
    if not text:
        return ''
    try:
        text.encode('cp852')
        return text
    except UnicodeEncodeError:
        return fold_to_ascii(text)


def sanitize_field(text, max_len=None, ascii_only=False, uppercase=True):
    if text is None:
        return ''
    cleaned = re.sub(r'\s+', ' ', str(text)).strip()
    if ascii_only:
        cleaned = fold_to_ascii(cleaned)
        cleaned = _SWIFT_X_RE.sub('', cleaned)
    else:
        cleaned = to_cp852_safe(cleaned)
    if uppercase:
        cleaned = cleaned.upper()
    if max_len is not None:
        cleaned = cleaned[:max_len]
    return cleaned


def split_into_lines(text, line_len, max_lines):
    if not text:
        return []
    words = text.split(' ')
    lines, current = [], ''
    for word in words:
        if not word:
            continue
        if not current:
            current = word[:line_len]
            continue
        if len(current) + 1 + len(word) <= line_len:
            current += ' ' + word
        else:
            lines.append(current)
            if len(lines) >= max_lines:
                return lines
            current = word[:line_len]
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def format_amount_comma(amount, decimals=2):
    """``12345.67`` -> ``"12345,67"``."""
    return ('{:.%df}' % decimals).format(amount).replace('.', ',')


def format_amount_haler(amount):
    return str(int(round(amount * 100)))


def format_date_yymmdd(d):
    return d.strftime('%y%m%d')


def format_partner_address(partner, max_lines=4, line_len=35, ascii_only=False):
    lines = []
    name = sanitize_field(partner.name or '', max_len=line_len, ascii_only=ascii_only)
    if name:
        lines.append(name)
    for component in (partner.street, partner.street2,
                      ' '.join(filter(None, [partner.zip, partner.city])),
                      partner.country_id.code or ''):
        if len(lines) >= max_lines:
            break
        if not component:
            continue
        cleaned = sanitize_field(component, max_len=line_len, ascii_only=ascii_only)
        if cleaned:
            lines.append(cleaned)
    return lines[:max_lines]


def _company_account(company_bank, company_name):
    if not company_bank:
        raise UserError(_("Journal %s has no bank account configured.", company_name))
    try:
        return parse_cz_account(company_bank)
    except ValueError as e:
        raise UserError(_("Orderer bank account: %s", str(e)))


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
def build_multicash_file(company_bank, company_partner, company_name, items,
                         payment_method_code, batch_type='outbound'):
    if not items:
        raise UserError(_("Cannot generate a MultiCash file from an empty payment list."))
    if payment_method_code == 'multicash_cfd':
        kind = _CFD_TYPE_INKASO if batch_type == 'inbound' else _CFD_TYPE_TRANSFER
        return _render_cfd(company_bank, company_partner, company_name, items, kind)
    if payment_method_code == 'multicash_cfu':
        return _render_cfd(company_bank, company_partner, company_name, items, _CFU_TYPE_URGENT)
    if payment_method_code == 'multicash_cfa':
        return _render_cfa(company_bank, company_partner, company_name, items)
    if payment_method_code == 'multicash_mt101':
        return _render_mt101(company_bank, company_partner, company_name, items)
    raise UserError(_("Unknown MultiCash payment method code: %s", payment_method_code))


# ---------------------------------------------------------------------------
# CFD / CFU
# ---------------------------------------------------------------------------
def _cfd_account_line(tag, prefix, account, short_name):
    short = sanitize_field(short_name or '', max_len=20, uppercase=True)
    if prefix:
        head = '%s:%s %s' % (tag, prefix, account)
    else:
        head = '%s: %s' % (tag, account)
    return '%s %s' % (head, short) if short else head


def _cfd_party_lines(tag, partner):
    addr_lines = format_partner_address(partner, max_lines=4, line_len=35)
    if not addr_lines:
        addr_lines = [sanitize_field(partner.name or 'N/A', max_len=35, uppercase=True)]
    out = ['%s:%s' % (tag, addr_lines[0])]
    for extra in addr_lines[1:]:
        out.append('   %s' % extra)
    return out


def _render_cfd(company_bank, company_partner, company_name, items, hd_type):
    company_prefix, company_account, company_bank_code = _company_account(company_bank, company_name)
    is_inkaso = hd_type == _CFD_TYPE_INKASO
    lines = []
    total_haler = 0

    for sequence, item in enumerate(items, start=1):
        if not item.partner_bank:
            raise UserError(_("Payment %s is missing a partner bank account.", item.label))
        try:
            partner_prefix, partner_account, partner_bank_code = parse_cz_account(item.partner_bank)
        except ValueError as e:
            raise UserError(_("Payment %(name)s: %(error)s", name=item.label, error=str(e)))
        if item.currency_name != 'CZK':
            raise UserError(_(
                "CFD/CFU only supports CZK payments — payment %(name)s is in %(cur)s.",
                name=item.label, cur=item.currency_name,
            ))

        amount_haler = int(round(item.amount * 100))
        total_haler += amount_haler

        if is_inkaso:
            ud_prefix, ud_account = partner_prefix, partner_account
            uk_prefix, uk_account = company_prefix, company_account
            di_partner = item.partner
            ki_partner = company_partner
        else:
            ud_prefix, ud_account = company_prefix, company_account
            uk_prefix, uk_account = partner_prefix, partner_account
            di_partner = company_partner
            ki_partner = item.partner

        lines.append(' '.join((
            'HD:%s' % hd_type, format_date_yymmdd(item.date),
            company_bank_code, str(sequence), partner_bank_code,
        )))
        lines.append(' '.join((
            'KC:%s' % format_amount_haler(item.amount), '000000', 'CZK',
        )))
        lines.append(_cfd_account_line('UD', ud_prefix, ud_account, di_partner.name))
        lines.extend(_cfd_party_lines('DI', di_partner))
        lines.append(_cfd_account_line('UK', uk_prefix, uk_account, ki_partner.name))
        lines.append('AK:%s' % (item.ss or '0'))
        lines.extend(_cfd_party_lines('KI', ki_partner))
        lines.append('EC:%s' % (item.ks or '0'))
        lines.append('ZK:%s' % (item.vs or '0'))

        memo_lines = split_into_lines(sanitize_field(item.message or '', uppercase=True), 35, 4)
        if memo_lines:
            lines.append('AV:%s' % memo_lines[0])
            for extra in memo_lines[1:]:
                lines.append('   %s' % extra)

    count_str = '%09d' % len(items)
    total_str = str(total_haler) if total_haler else '000'
    if hd_type == _CFU_TYPE_URGENT:
        lines.append('S0:%s %s' % (count_str, total_str))
        lines.append('S4:000000000 000')
    elif is_inkaso:
        lines.append('S1:000000000 000')
        lines.append('S3:%s %s' % (count_str, total_str))
    else:
        lines.append('S1:%s %s' % (count_str, total_str))
        lines.append('S3:000000000 000')

    text = '\r\n'.join(lines) + '\r\n'
    return text.encode('cp852', errors='replace')


# ---------------------------------------------------------------------------
# CFA (foreign payments)
# ---------------------------------------------------------------------------
def _render_cfa(company_bank, company_partner, company_name, items):
    if not company_bank or not company_bank.bank_id or not company_bank.bank_id.bic:
        raise UserError(_("Journal %s requires a bank with a BIC for CFA export.", company_name))

    sender_bic = company_bank.bank_id.bic.replace(' ', '').upper()
    if len(sender_bic) == 8:
        sender_bic += 'XXX'
    company_prefix, company_account, _company_bank_code = _company_account(company_bank, company_name)
    company_acc_field = '%s%s' % ((company_prefix or '').zfill(6), company_account.zfill(10))

    total = sum(it.amount for it in items)
    header_lines = [
        ':01:REF%s' % datetime.now().strftime('%y%m%d%H%M%S'),
        ':02:%s' % format_amount_comma(total).ljust(17),
        ':03:%05d' % len(items),
        ':04:%s' % sender_bic,
    ]
    addr_lines = format_partner_address(company_partner, max_lines=4, line_len=35) or [sanitize_field(company_partner.name, 35)]
    header_lines.append(':05:%s' % addr_lines[0])
    for extra in addr_lines[1:]:
        header_lines.append(extra)
    header_lines.append(':07:%s' % ('CFA%s' % datetime.now().strftime('%y%m%d%H%M%S'))[:12])

    blocks = []
    for sequence, item in enumerate(items, start=1):
        partner_bank = item.partner_bank
        if not partner_bank:
            raise UserError(_("Payment %s is missing a partner bank account.", item.label))

        receiver_bic = (partner_bank.bank_id.bic or '').replace(' ', '').upper() if partner_bank.bank_id else ''
        if receiver_bic and len(receiver_bic) == 8:
            receiver_bic += 'XXX'
        if not receiver_bic:
            receiver_bic = 'X' * 11

        urgent = item.iso_priority == 'URGP'
        priority_flag = 'S1' if urgent else 'N1'

        block = [
            '{1:F01%sAXXX%04d%06d}{2:I100%sAXXX%s}{4:' % (
                sender_bic[:8], sequence, sequence, receiver_bic, priority_flag,
            ),
            ':20:%s' % sanitize_field(item.message or str(item.ref_id), max_len=16, uppercase=True).ljust(16),
            ':32A:%s%s%s' % (
                format_date_yymmdd(item.date), item.currency_name,
                format_amount_comma(item.amount),
            ),
        ]
        orderer = format_partner_address(company_partner, max_lines=4, line_len=35)
        if not orderer:
            orderer = [sanitize_field(company_name, 35)]
        block.append(':50:%s' % orderer[0])
        block.extend(orderer[1:])

        recipient_country = (item.partner.country_id.code or 'XX').upper()
        recipient_bank_country = (partner_bank.bank_id.country.code if partner_bank.bank_id and partner_bank.bank_id.country else recipient_country).upper()
        block.extend([
            ':52D:%s' % company_acc_field,
            company_acc_field,
            '%s %s' % (item.currency_name, item.currency_name),
            '%s %s %s' % ('000', recipient_country, recipient_bank_country),
        ])

        if partner_bank.bank_id and partner_bank.bank_id.bic:
            block.append(':57A:%s' % receiver_bic)
        else:
            bank_name = partner_bank.bank_id.name if partner_bank.bank_id else ''
            bank_lines = split_into_lines(sanitize_field(bank_name, uppercase=True), 35, 2) or ['UNKNOWN']
            bank_addr = []
            if partner_bank.bank_id:
                bank_addr = split_into_lines(
                    sanitize_field(' '.join(filter(None, [partner_bank.bank_id.street, partner_bank.bank_id.city])), uppercase=True),
                    35, 2,
                )
            block.append(':57D:%s' % bank_lines[0])
            for extra in bank_lines[1:]:
                block.append(extra)
            for extra in bank_addr:
                block.append(extra)

        beneficiary_acc = (partner_bank.acc_number or '').replace(' ', '').upper()
        beneficiary_addr = format_partner_address(item.partner, max_lines=4, line_len=35) or [sanitize_field(item.partner.name, 35)]
        block.append(':59:/%s' % beneficiary_acc)
        block.extend(beneficiary_addr)

        purpose_lines = split_into_lines(sanitize_field(item.message or '', uppercase=True), 35, 4)
        if purpose_lines:
            block.append(':70:%s' % purpose_lines[0])
            block.extend(purpose_lines[1:])

        iso_cb = item.iso_charge_bearer or 'SHAR'
        block.append(':71A:%s' % _CHRGBR_MAP.get(iso_cb, 'BN1'))
        block.append(':72:00 00 00 00')
        block.append('-}')
        blocks.append('\r\n'.join(block))

    body = ('\r\n').join(header_lines) + '\r\n' + '$'.join(blocks) + '\r\n'
    return body.encode('cp852', errors='replace')


# ---------------------------------------------------------------------------
# MT101 (SWIFT Request For Transfer)
# ---------------------------------------------------------------------------
def _render_mt101(company_bank, company_partner, company_name, items):
    if not company_bank or not company_bank.bank_id or not company_bank.bank_id.bic:
        raise UserError(_("Journal %s requires a bank with a BIC for MT101 export.", company_name))

    sender_bic = company_bank.bank_id.bic.replace(' ', '').upper()
    if len(sender_bic) == 8:
        sender_bic += 'XXX'

    company_acc = (company_bank.acc_number or '').replace(' ', '').upper()
    execution_date = format_date_yymmdd(items[0].date)
    message_ref = datetime.now().strftime('%y%m%d') + '01' + '%08d' % (items[0].ref_id or 1)

    lines = [
        '{-', sender_bic, sender_bic, '101',
        ':20:%s' % message_ref[:16], ':28D:1/1',
        ':50H:/%s' % company_acc,
    ]
    orderer = format_partner_address(company_partner, max_lines=4, line_len=35, ascii_only=True)
    if not orderer:
        orderer = [sanitize_field(company_name, 35, ascii_only=True)]
    lines.extend(orderer)
    lines.append(':30:%s' % execution_date)

    for sequence, item in enumerate(items, start=1):
        partner_bank = item.partner_bank
        if not partner_bank:
            raise UserError(_("Payment %s is missing a partner bank account.", item.label))

        tx_ref = sanitize_field(item.message or str(item.ref_id), max_len=16, ascii_only=True, uppercase=True)
        lines.append(':21:%s' % (tx_ref or ('TX%04d' % sequence)))
        lines.append(':32B:%s%s' % (item.currency_name, format_amount_comma(item.amount)))

        receiver_bic = (partner_bank.bank_id.bic or '').replace(' ', '').upper() if partner_bank.bank_id else ''
        if receiver_bic and len(receiver_bic) == 8:
            receiver_bic += 'XXX'
        if receiver_bic:
            lines.append(':57A:%s' % receiver_bic)

        beneficiary_acc = (partner_bank.acc_number or '').replace(' ', '').upper()
        lines.append(':59:/%s' % beneficiary_acc)
        beneficiary_addr = format_partner_address(item.partner, max_lines=4, line_len=35, ascii_only=True) or [
            sanitize_field(item.partner.name, 35, ascii_only=True)]
        lines.extend(beneficiary_addr)

        purpose_lines = split_into_lines(sanitize_field(item.message or '', ascii_only=True, uppercase=True), 35, 4)
        if purpose_lines:
            lines.append(':70:%s' % purpose_lines[0])
            lines.extend(purpose_lines[1:])

        iso_cb = item.iso_charge_bearer or 'SHAR'
        mt_cb = {'SHAR': 'SHA', 'DEBT': 'OUR', 'CRED': 'BEN'}.get(iso_cb, iso_cb or 'SHA')
        lines.append(':71A:%s' % mt_cb)

    lines.append('-}')
    text = '\r\n'.join(lines) + '\r\n'
    return fold_to_ascii(text).encode('ascii', errors='replace')
