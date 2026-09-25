# -*- coding: utf-8 -*-
"""Pure-Python client for the Czech EET 2.0 (Elektronická evidence tržeb) SOAP
interface, data-interface version **4.1** (namespace ``http://fs.gov.cz/eet/schema/v4``).

Deliberately free of any Odoo import so it can be unit-tested standalone and
reused outside the ORM.  Only depends on ``lxml``, ``cryptography`` and
``requests`` (all shipped with a standard Odoo 19 stack).

Verified against the official artifacts (EET_popis_rozhrani_v1_EN.pdf = interface
v4.1, EETXMLSchema.xsd, EETServiceSOAP.wsdl and the three signed sample messages).

Signature profile (spec §5.2), all mandatory:
  * sign ONLY ``<soapenv:Body>`` (the ``<v4:Trzba>`` element)
  * digest  = SHA-256            (xmlenc#sha256)
  * signature = RSA-SHA256       (xmldsig-more#rsa-sha256)
  * canonicalization = Exclusive C14N (xml-exc-c14n#)
  * X.509 cert carried inline in a WS-Security BinarySecurityToken (X509v3)
  * no Timestamp, no WS-Addressing (extra headers inflate size -> may be rejected)
"""
import base64
import uuid
from dataclasses import dataclass, field

from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12

# --- namespaces -------------------------------------------------------------
NS = {
    "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
    "v4": "http://fs.gov.cz/eet/schema/v4",
    "wsse": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd",
    "wsu": "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
    "ec": "http://www.w3.org/2001/10/xml-exc-c14n#",
}
# --- algorithm identifiers --------------------------------------------------
ALG_C14N_EXCL = "http://www.w3.org/2001/10/xml-exc-c14n#"
ALG_RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
ALG_SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
BST_ENCODING = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary"
BST_VALUETYPE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"

SOAP_ACTION = "http://fs.gov.cz/eet/OdeslaniTrzby"
ENDPOINT_PLAYGROUND = "https://pg.trzbyeet.gov.cz:443/eet/services/EETServiceSOAP/v4"
ENDPOINT_PRODUCTION = "https://trzbyeet.gov.cz/eet/services/EETServiceSOAP/v4"


def _q(prefix, tag):
    return "{%s}%s" % (NS[prefix], tag)


# --- data payload -----------------------------------------------------------
@dataclass
class Trzba:
    """The evidenced-sale payload.  Attribute names mirror the XSD exactly.

    Only the six mandatory data items are required; optional items are omitted
    from the XML entirely when ``None`` (empty attributes are FORBIDDEN by spec).
    """
    # <Data> mandatory
    eic_popl: str            # ^CZ[0-9]{8,10}$
    id_jednotky: int         # 1..999999999, last digit in {1,2,3,4}
    id_pokl: str             # <=20 chars
    porad_cis: str           # <=25 chars
    dat_trzby: str           # ISO-8601 with mandatory TZ, e.g. 2027-01-08T21:19:40+01:00
    celk_trzba: str          # decimal, exactly 2 places, e.g. "188580.00"
    # <Data> optional
    eic_poverujiciho: str = None
    povereni_vice_popl: bool = None
    urceno_cerp_zuct: str = None
    cerp_zuct: str = None
    # <Hlavicka>
    dat_odesl: str = None            # defaults to dat_trzby if not given
    prvni_zaslani: bool = True
    overeni: bool = False            # True => verification mode (no valid POK)
    uuid_zpravy: str = None

    def __post_init__(self):
        # Generate a UUID when none was supplied (or an explicit None/empty).
        if not self.uuid_zpravy:
            self.uuid_zpravy = str(uuid.uuid4())

    def data_attrs(self):
        """Ordered dict of <Data> attributes, optionals dropped when None."""
        out = {
            "eic_popl": self.eic_popl,
            "id_jednotky": str(self.id_jednotky),
            "id_pokl": self.id_pokl,
            "porad_cis": self.porad_cis,
            "dat_trzby": self.dat_trzby,
            "celk_trzba": self.celk_trzba,
        }
        if self.eic_poverujiciho is not None:
            out["eic_poverujiciho"] = self.eic_poverujiciho
        if self.povereni_vice_popl is not None:
            out["povereni_vice_popl"] = _b(self.povereni_vice_popl)
        if self.urceno_cerp_zuct is not None:
            out["urceno_cerp_zuct"] = self.urceno_cerp_zuct
        if self.cerp_zuct is not None:
            out["cerp_zuct"] = self.cerp_zuct
        return out

    def hlavicka_attrs(self):
        out = {
            "uuid_zpravy": self.uuid_zpravy,
            "dat_odesl": self.dat_odesl or self.dat_trzby,
            "prvni_zaslani": _b(self.prvni_zaslani),
        }
        if self.overeni:
            out["overeni"] = "true"
        return out


def _b(value):
    return "true" if value else "false"


# --- certificate handling ---------------------------------------------------
class Certificate:
    """Wraps the pokladní certifikát loaded from a PKCS#12 (.p12) blob.

    NOTE on the legacy .p12 cipher (RC2-40 cert bag + 3DES key): Python's
    ``cryptography`` (>=41) loads it fine out of the box; only the system
    ``openssl`` CLI needs the legacy provider.  See EET2_CLAUDE.md §12.
    """

    def __init__(self, p12_bytes, password):
        if isinstance(password, str):
            password = password.encode()
        key, cert, _chain = pkcs12.load_key_and_certificates(p12_bytes, password or None)
        if key is None or cert is None:
            raise ValueError("PKCS#12 did not contain a private key + certificate")
        self.private_key = key
        self.cert = cert

    @property
    def der_b64(self):
        return base64.b64encode(self.cert.public_bytes(serialization.Encoding.DER)).decode()

    def sign(self, data):
        return self.private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())


# --- message construction + signing ----------------------------------------
def _c14n(el, inclusive_prefixes):
    return etree.tostring(
        el, method="c14n", exclusive=True, with_comments=False,
        inclusive_ns_prefixes=inclusive_prefixes,
    )


def build_signed_request(trzba: Trzba, cert: Certificate):
    """Return the signed SOAP envelope as bytes, ready to POST.

    The digest/signature are computed on the *serialized wire form* of the tree
    (after a normalize round-trip), because that is what the receiver
    canonicalizes.  Exclusive-C14N ``InclusiveNamespaces`` placement of forced
    prefixes differs between an in-memory lxml tree and its parsed wire form, so
    we build the full scaffold with empty DigestValue/SignatureValue, normalize,
    then fill only those two leaf text nodes (which never shift namespaces).
    """
    body_id = "id-" + uuid.uuid4().hex
    bst_id = "X509-" + uuid.uuid4().hex

    # Envelope declares the two prefixes the signed Body needs in scope.
    env = etree.Element(_q("soapenv", "Envelope"),
                        nsmap={"soapenv": NS["soapenv"], "v4": NS["v4"]})
    header = etree.SubElement(env, _q("soapenv", "Header"))
    body = etree.SubElement(env, _q("soapenv", "Body"),
                            nsmap={"wsu": NS["wsu"]})
    body.set(_q("wsu", "Id"), body_id)

    # --- Body payload: <v4:Trzba> ---
    trzba_el = etree.SubElement(body, _q("v4", "Trzba"))
    hlavicka = etree.SubElement(trzba_el, _q("v4", "Hlavicka"))
    for k, v in trzba.hlavicka_attrs().items():
        hlavicka.set(k, v)
    data_el = etree.SubElement(trzba_el, _q("v4", "Data"))
    for k, v in trzba.data_attrs().items():
        data_el.set(k, v)

    # --- WS-Security header scaffold (DigestValue/SignatureValue left empty) ---
    security = etree.SubElement(
        header, _q("wsse", "Security"),
        nsmap={"wsse": NS["wsse"], "wsu": NS["wsu"]},
    )
    bst = etree.SubElement(
        security, _q("wsse", "BinarySecurityToken"),
        {"EncodingType": BST_ENCODING, "ValueType": BST_VALUETYPE,
         _q("wsu", "Id"): bst_id},
    )
    bst.text = cert.der_b64

    signature = etree.SubElement(security, _q("ds", "Signature"),
                                nsmap={"ds": NS["ds"]})
    signed_info = etree.SubElement(signature, _q("ds", "SignedInfo"))
    cm = etree.SubElement(signed_info, _q("ds", "CanonicalizationMethod"),
                        {"Algorithm": ALG_C14N_EXCL})
    _inclusive_ns(cm, "soapenv v4")
    etree.SubElement(signed_info, _q("ds", "SignatureMethod"),
                    {"Algorithm": ALG_RSA_SHA256})
    ref = etree.SubElement(signed_info, _q("ds", "Reference"),
                        {"URI": "#" + body_id})
    transforms = etree.SubElement(ref, _q("ds", "Transforms"))
    tr = etree.SubElement(transforms, _q("ds", "Transform"),
                        {"Algorithm": ALG_C14N_EXCL})
    _inclusive_ns(tr, "v4")
    etree.SubElement(ref, _q("ds", "DigestMethod"), {"Algorithm": ALG_SHA256})
    etree.SubElement(ref, _q("ds", "DigestValue"))              # filled below
    etree.SubElement(signature, _q("ds", "SignatureValue"))      # filled below
    key_info = etree.SubElement(signature, _q("ds", "KeyInfo"))
    str_el = etree.SubElement(key_info, _q("wsse", "SecurityTokenReference"))
    etree.SubElement(str_el, _q("wsse", "Reference"),
                    {"URI": "#" + bst_id, "ValueType": BST_VALUETYPE})

    # --- normalize to the wire form so C14N is receiver-identical ---
    env = etree.fromstring(etree.tostring(env))
    body = env.find(".//" + _q("soapenv", "Body"))
    signed_info = env.find(".//" + _q("ds", "SignedInfo"))
    dv = env.find(".//" + _q("ds", "DigestValue"))
    sv = env.find(".//" + _q("ds", "SignatureValue"))

    # digest of the Body (exclusive C14N, force-include the v4 prefix)
    dv.text = base64.b64encode(_sha256(_c14n(body, ["v4"]))).decode()
    # sign the SignedInfo (exclusive C14N inheriting soapenv+v4) AFTER DigestValue set
    sv.text = base64.b64encode(cert.sign(_c14n(signed_info, ["soapenv", "v4"]))).decode()

    return etree.tostring(env, xml_declaration=True, encoding="UTF-8")


def _inclusive_ns(parent, prefix_list):
    etree.SubElement(parent, _q("ec", "InclusiveNamespaces"),
                    {"PrefixList": prefix_list}, nsmap={"ec": NS["ec"]})


def _sha256(data):
    h = hashes.Hash(hashes.SHA256())
    h.update(data)
    return h.finalize()


# --- response parsing -------------------------------------------------------
@dataclass
class Odpoved:
    uuid_zpravy: str = None
    dat_prij: str = None
    dat_odmit: str = None
    pok: str = None          # Acknowledgement code (replaces FIK); None on error
    test: bool = False       # non-production flag
    chyba_kod: int = None    # error code; None on success
    chyba_text: str = None
    varovani: list = field(default_factory=list)  # [(kod_varov:int, text:str)]

    @property
    def ok(self):
        """True when the sale was accepted (a POK was issued)."""
        return self.pok is not None and self.chyba_kod is None

    @property
    def retry(self):
        """True for a temporary technical error -> resend later (kod <= -1)."""
        return self.chyba_kod is not None and self.chyba_kod < 0


def parse_response(xml_bytes):
    root = etree.fromstring(xml_bytes)
    odp = root.find(".//" + _q("v4", "Odpoved"))
    if odp is None:
        raise ValueError("No <Odpoved> element in response:\n%s"
                        % xml_bytes.decode("utf-8", "replace")[:2000])
    out = Odpoved()
    hlav = odp.find(_q("v4", "Hlavicka"))
    if hlav is not None:
        out.uuid_zpravy = hlav.get("uuid_zpravy")
        out.dat_prij = hlav.get("dat_prij")
        out.dat_odmit = hlav.get("dat_odmit")
    potvr = odp.find(_q("v4", "Potvrzeni"))
    if potvr is not None:
        out.pok = potvr.get("pok")
        out.test = potvr.get("test") in ("true", "1")
    chyba = odp.find(_q("v4", "Chyba"))
    if chyba is not None:
        out.chyba_kod = int(chyba.get("kod"))
        out.chyba_text = (chyba.text or "").strip()
        if chyba.get("test") in ("true", "1"):
            out.test = True
    for var in odp.findall(_q("v4", "Varovani")):
        out.varovani.append((int(var.get("kod_varov")), (var.text or "").strip()))
    return out


# --- transport --------------------------------------------------------------
@dataclass
class SendResult:
    odpoved: Odpoved
    raw: bytes
    xgtid: str = None        # X-Global-Transaction-Id (spec §5.4) — log for support


def send(envelope_bytes, endpoint=ENDPOINT_PLAYGROUND, timeout=10, verify=True):
    """POST a signed envelope and return a :class:`SendResult`."""
    import requests
    headers = {
        "Content-Type": "text/xml; charset=UTF-8",
        "SOAPAction": '"%s"' % SOAP_ACTION,
    }
    resp = requests.post(endpoint, data=envelope_bytes, headers=headers,
                        timeout=timeout, verify=verify)
    resp.raise_for_status()
    return SendResult(parse_response(resp.content), resp.content,
                    resp.headers.get("X-Global-Transaction-Id"))
