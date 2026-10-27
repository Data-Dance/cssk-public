# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from xml.sax.saxutils import escape

import requests
from lxml import etree

from odoo import api, models
from odoo.addons.l10n_cssk_core.tools import normalize_vat

_logger = logging.getLogger(__name__)

# ADIS "rozhraní CRP DPH" SOAP endpoint + namespace (per the published WSDL).
_ADIS_URL = (
    "https://adisrws.mfcr.cz/dpr/axis2/services/"
    "rozhraniCRPDPH.rozhraniCRPDPHSOAP"
)
_NS = "http://adis.mfcr.cz/rozhraniCRPDPH/"

_RELIABILITY = {"ANO": "unreliable", "NE": "reliable", "NENALEZEN": "unknown"}

#: A Czech account in the domestic form: [předčíslí-]číslo/kód banky.
_DOMESTIC_ACCOUNT = re.compile(r"^(?:(\d{1,6})-)?(\d{1,10})/(\d{4})$")


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ------------------------------------------------------------------
    def _cz_adis_dic(self):
        # ADIS wants the DIČ = the VAT number minus its 'CZ' prefix; a
        # foreign prefix (e.g. 'SK…') passes through verbatim — so normalize
        # keeping the prefix and strip exactly 'CZ' explicitly.
        vat = normalize_vat(self.vat, keep_prefix=True)
        return vat[2:] if vat[:2] == "CZ" else vat

    def _cz_adis_status(self):
        """Return the ``statusPlatceDPH`` element for this partner, or None."""
        dic = self._cz_adis_dic()
        if not dic:
            return None
        envelope = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soapenv:Envelope'
            ' xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
            f' xmlns:roz="{_NS}"><soapenv:Body>'
            # dic comes from the user-editable partner VAT: escape it so a
            # crafted value cannot inject XML into the SOAP request.
            f'<roz:StatusNespolehlivyPlatceRequest><roz:dic>{escape(dic)}</roz:dic>'
            '</roz:StatusNespolehlivyPlatceRequest>'
            '</soapenv:Body></soapenv:Envelope>'
        )
        try:
            resp = requests.post(
                _ADIS_URL,
                data=envelope.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "getStatusNespolehlivyPlatce",
                },
                timeout=20,
            )
            resp.raise_for_status()
            # Hardened parser: never resolve (external) entities, never touch
            # the network while parsing an untrusted response (XXE).
            parser = etree.XMLParser(resolve_entities=False, no_network=True)
            root = etree.fromstring(resp.content, parser=parser)
        except (requests.exceptions.RequestException, etree.XMLSyntaxError):
            _logger.exception("ADIS reliability query failed for %s", dic)
            return None
        for el in root.iter():
            # skip comments / PIs / unresolved entity refs
            if not isinstance(el.tag, str):
                continue
            if etree.QName(el).localname == "statusPlatceDPH":
                return el
        return None

    # ------------------------------------------------------------------
    # Deriving both answers from one fetched status element
    # ------------------------------------------------------------------
    @api.model
    def _cz_reliability_from_status(self, status):
        if status is None:
            return None
        return _RELIABILITY.get((status.get("nespolehlivyPlatce") or "").upper())

    @api.model
    def _cz_accounts_from_status(self, status):
        if status is None:
            return None
        if (status.get("nespolehlivyPlatce") or "").upper() == "NENALEZEN":
            # Not in the register of VAT payers. § 109 makes the recipient
            # liable for the tax of "jiný plátce" only, so an account this
            # subject never had to publish is not a finding: "unavailable",
            # not "NOT registered".
            return None
        accounts = []
        for el in status.iter():
            if not isinstance(el.tag, str):
                continue
            ln = etree.QName(el).localname
            if ln == "standardniUcet":
                iban = self._cz_account_to_iban(
                    el.get("predcisli"), el.get("cislo"), el.get("kodBanky")
                )
                if iban:
                    accounts.append(iban)
            elif ln == "nestandardniUcet":
                cislo = (el.get("cislo") or "").replace(" ", "").upper()
                if cislo:
                    accounts.append(cislo)
        return accounts

    # ------------------------------------------------------------------
    def _cssk_get_tax_reliability(self):
        self.ensure_one()
        if (self.country_id.code or "") != "CZ":
            return super()._cssk_get_tax_reliability()
        return self._cz_reliability_from_status(self._cz_adis_status())

    def _cssk_get_registered_accounts(self):
        self.ensure_one()
        if (self.country_id.code or "") != "CZ":
            return super()._cssk_get_registered_accounts()
        return self._cz_accounts_from_status(self._cz_adis_status())

    def _cssk_get_reliability_data(self):
        """ADIS returns accounts + reliability in ONE response: fetch the
        status once per check and derive both answers from it, instead of
        firing two identical SOAP roundtrips."""
        self.ensure_one()
        if (self.country_id.code or "") != "CZ":
            return super()._cssk_get_reliability_data()
        status = self._cz_adis_status()
        return (
            self._cz_accounts_from_status(status),
            self._cz_reliability_from_status(status),
        )

    def _cssk_paid_account_key(self, bank_account):
        """A Czech account typed in the domestic form, as the IBAN that
        ADIS's published accounts are compared in. Sanitising alone turns
        ``19-2000145399/0800`` into ``1920001453990800``, which matches no
        IBAN, so the published account read as NOT registered."""
        raw = (bank_account.acc_number or "").replace(" ", "")
        match = _DOMESTIC_ACCOUNT.match(raw)
        if match and (self.country_id.code or "") == "CZ":
            iban = self._cz_account_to_iban(*match.groups())
            if iban:
                return iban
        return super()._cssk_paid_account_key(bank_account)

    @staticmethod
    def _cz_account_to_iban(predcisli, cislo, kod_banky):
        """Czech domestic account (předčíslí-číslo/kódBanky) → IBAN."""
        if not (cislo and kod_banky):
            return False
        try:
            bban = "%04d%06d%010d" % (
                int(kod_banky), int(predcisli or 0), int(cislo)
            )
        except (ValueError, TypeError):
            return False
        # check digits: move 'CZ00' to the end, C->12 Z->35, mod 97
        check = 98 - (int(bban + "123500") % 97)
        return "CZ%02d%s" % (check, bban)
