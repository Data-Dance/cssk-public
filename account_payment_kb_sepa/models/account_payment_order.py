# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Komerční banka's profile of the OCA pain.001.001.03 SEPA credit transfer.

OCA ``account_banking_sepa_credit_transfer`` already writes the XML KB takes
for foreign payments (*Klientský formát XML SEPA CT v KB*: pain.001.001.03,
TRF, service level SEPA, charges SLEV, EUR). Two things differ from what KB
documents, and this module changes exactly those, and only when the debtor
account is a KB account and the flavour is pain.001.001.03:

* **Postal address.** OCA writes pain.001.001.03 addresses as ``Ctry`` plus
  free ``AdrLine`` lines. KB's tag list for ``Dbtr``/``Cdtr`` has no
  ``AdrLine`` — it reads the structured ``StrtNm``, ``BldgNb``, ``PstCd``,
  ``TwnNm``, ``Ctry`` — and says that once any address element is given, the
  town and the country are both required. So the address is written
  structured, and left out altogether when the partner has no town or no
  country (it is optional for SEPA).
* **Character set.** KB accepts only the SWIFT set for SEPA, "tedy výhradně
  bez diakritiky"; OCA converts to ASCII only when the payment method says
  so. For a KB order it always does.
"""

from lxml import etree

from odoo import api, models

from odoo.addons.account_cz_bankfile_base.utils.common import (
    national_account_key,
)

KB_BANK_CODE = "0100"


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _kb_sepa_profile(self, gen_args=None):
        """KB's profile applies: one order, pain.001.001.03, KB debtor account."""
        if len(self) != 1:
            return False
        flavor = (gen_args or {}).get("pain_flavor") or (
            self.payment_mode_id.payment_method_id.pain_version or ""
        )
        if not flavor.startswith("pain.001.001.03"):
            return False
        key = national_account_key(
            self.journal_id.bank_account_id.acc_number or "", countries=("CZ",)
        )
        return bool(key) and key[0] == KB_BANK_CODE

    def _prepare_field(self, field_name, field_value, eval_ctx, max_size=0,
                       gen_args=None):
        if self._kb_sepa_profile(gen_args):
            gen_args = dict(gen_args or {}, convert_to_ascii=True)
        return super()._prepare_field(
            field_name, field_value, eval_ctx, max_size=max_size,
            gen_args=gen_args,
        )

    @api.model
    def generate_address_block(self, parent_node, partner, gen_args):
        if not self._kb_sepa_profile(gen_args):
            return super().generate_address_block(parent_node, partner, gen_args)
        if not partner.country_id or not partner.city:
            # optional for SEPA, but any element makes town and country
            # mandatory — so none at all rather than a rejected half
            return True
        street = partner.street or ""
        building = ""
        # base_address_extended splits the street; use the parts when present
        if getattr(partner, "street_name", False) and getattr(
            partner, "street_number", False
        ):
            street = partner.street_name
            building = partner.street_number
        # PostalAddress6 sequence: StrtNm, BldgNb, PstCd, TwnNm, Ctry
        elements = []
        for tag, label, value, size in (
            ("StrtNm", "Street", street, 70),
            ("BldgNb", "Building number", building, 16),
            ("PstCd", "Zip", partner.zip or "", 16),
            ("TwnNm", "City", partner.city, 35),
            ("Ctry", "Country", partner.country_id.code or "", 2),
        ):
            if not value:
                continue
            text = self._prepare_field(
                label, "value", {"value": value}, size, gen_args=gen_args
            ).strip()
            if text:
                elements.append((tag, text))
        # checked on the converted values: a town that transliterates to
        # nothing is no town
        present = {tag for tag, _text in elements}
        if not {"TwnNm", "Ctry"} <= present:
            return True
        postal_address = etree.SubElement(parent_node, "PstlAdr")
        for tag, text in elements:
            etree.SubElement(postal_address, tag).text = text
        return True
