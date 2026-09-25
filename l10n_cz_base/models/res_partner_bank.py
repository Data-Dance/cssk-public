import re

from odoo import api, fields, models

# Czech IBAN layout (CNB): CZ kk BBBB PPPPPP NNNNNNNNNN (24 chars)
#   [2:4] check digits, [4:8] bank code, [8:14] account prefix (predcisli),
#   [14:24] account number.
CZ_IBAN_LEN = 24
_CZ_LEGACY_RE = re.compile(r"^\s*(?:(\d+)-)?(\d+)\s*/\s*(\d{4})\s*$")


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    acc_legacy_number = fields.Char(
        string="Legacy Account Number",
        help="Account number part in legacy (domestic) format, derived from the IBAN.",
        size=10,
        store=True,
        compute="_compute_account_legacy_number",
    )
    account_legacy_starting_number = fields.Char(
        string="Legacy Account Starting Number",
        help="Account prefix (predcisli) in legacy format, derived from the IBAN.",
        size=6,
        store=True,
        compute="_compute_account_legacy_number",
    )
    bank_local_code = fields.Char(
        string="Bank Code",
        help="Four-digit Czech bank code, derived from the IBAN.",
        size=4,
        store=True,
        compute="_compute_account_legacy_number",
    )

    @api.depends("acc_number")
    def _compute_account_legacy_number(self):
        for record in self:
            split = self._cz_split_iban(record.sanitized_acc_number)
            if split:
                record.bank_local_code = split["bank_code"]
                record.account_legacy_starting_number = split["prefix"]
                record.acc_legacy_number = split["number"]
            else:
                record.bank_local_code = False
                record.account_legacy_starting_number = False
                record.acc_legacy_number = False

    # -- Czech IBAN <-> legacy "prefix-number/bankcode" conversion ----------
    # Primary storage is the IBAN; the legacy parts above are computed from it.
    # On input (e.g. an ISDOC document) use `_cz_legacy_to_iban` to normalise to IBAN.

    @api.model
    def _cz_split_iban(self, sanitized):
        """Return {'bank_code', 'prefix', 'number'} for a Czech IBAN, else None."""
        s = (sanitized or "").replace(" ", "").upper()
        if len(s) == CZ_IBAN_LEN and s[:2] == "CZ" and s[2:].isdigit():
            return {"bank_code": s[4:8], "prefix": s[8:14], "number": s[14:24]}
        return None

    @api.model
    def _cz_format_legacy_number(self, prefix, number):
        """Legacy account number, leading zeros stripped: 'prefix-number' or 'number'."""
        number = (number or "").lstrip("0") or "0"
        prefix = (prefix or "").lstrip("0")
        return f"{prefix}-{number}" if prefix else number

    @api.model
    def _cz_iban_from_legacy(self, bank_code, prefix, number):
        """Build a Czech IBAN (ISO 13616 mod-97 check digits) from legacy parts."""
        bban = f"{bank_code:0>4}{(prefix or ''):0>6}{number:0>10}"
        check = 98 - (int(bban + "123500") % 97)  # 'CZ00' -> C=12, Z=35, plus '00'
        return f"CZ{check:02d}{bban}"

    @api.model
    def _cz_legacy_to_iban(self, legacy):
        """Convert a legacy 'prefix-number/bankcode' string to a Czech IBAN, else False."""
        m = _CZ_LEGACY_RE.match(legacy or "")
        if not m:
            return False
        prefix, number, bank_code = m.group(1) or "", m.group(2), m.group(3)
        return self._cz_iban_from_legacy(bank_code, prefix, number)

    def _cz_account_parts(self):
        """(legacy_account_str, bank_code, iban) for this account, from either storage form.
        Foreign accounts yield ('', '', iban_or_empty)."""
        self.ensure_one()
        split = self._cz_split_iban(self.sanitized_acc_number)
        if split:
            return (
                self._cz_format_legacy_number(split["prefix"], split["number"]),
                split["bank_code"],
                self.sanitized_acc_number,
            )
        m = _CZ_LEGACY_RE.match(self.acc_number or "")
        if m:
            prefix, number, bank_code = m.group(1) or "", m.group(2), m.group(3)
            return (
                self._cz_format_legacy_number(prefix, number),
                bank_code,
                self._cz_iban_from_legacy(bank_code, prefix, number),
            )
        sanitized = self.sanitized_acc_number or ""
        return ("", "", sanitized if sanitized[:2].isalpha() else "")
