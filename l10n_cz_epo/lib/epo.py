# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech EPO third-party interface ("Podatelna EPO"), without Odoo.

Everything here follows "Obecný popis struktury souborů a rozhraní pro třetí
strany společného technického zařízení správců daně (Podatelny EPO)", verze
1.11 (https://adisspr.mfcr.cz/dpr/adis/idpr_pub/epo2_info/PodatelnaEPO.pdf):

* a filing is the ``<Pisemnost>`` XML wrapped in a PKCS#7 v1.5 ``signedData``
  object, DER-encoded, carrying the data, the signer's certificate and exactly
  one signature — made with a QUALIFIED certificate (ZAREP) (p. 4);
* ``epo_podani`` takes it; ``?test=1`` runs every check and files nothing
  (p. 6); the answer is a signed potvrzení, an ``<Odpoved>`` for a large filing
  processed off-line, or a ``<Chyby>`` list;
* ``epo_stav`` reports the processing state of a filing by its podací číslo
  and heslo; ``epo_prijeti`` fetches the potvrzení of an off-line one.

Kept free of Odoo so it can be tested on its own and so the one place that
turns a query parameter into a real filing is easy to read.
"""

import requests
from asn1crypto import cms
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12, pkcs7
from lxml import etree

BASE_URL = "https://mojedane.gov.cz/dpr"
SUBMIT_URL = f"{BASE_URL}/epo_podani"
STATUS_URL = f"{BASE_URL}/epo_stav"
RECEIPT_URL = f"{BASE_URL}/epo_prijeti"
TIMEOUT = 120

#: Chyba/@Typ (Příloha 3): what each error class means for the filer.
ERROR_TYPES = {
    "I": "informativní",
    "S": "chyba struktury",
    "K": "kritická",
    "N": "závažná, propustná",
    "P": "propustná",
    "E": "výjimka serveru",
}
#: Types that stop a filing; the rest are warnings.
BLOCKING_TYPES = {"S", "K", "E"}

#: Epo_stav/@stav_podapl.
STATE_UNPROCESSED, STATE_REJECTED, STATE_ACCEPTED = "1", "2", "3"


class EpoError(Exception):
    """A transport failure: EPO could not be reached or answered nonsense.

    ``maybe_sent`` says whether the request may have reached EPO. It matters
    for a filing: if it may have, sending it again could file it twice, so
    the caller must not retry blindly.
    """

    def __init__(self, message, maybe_sent=True):
        super().__init__(message)
        self.maybe_sent = maybe_sent


def _parser():
    # EPO's answer is parsed, not trusted: no DTD, no entities, no network.
    return etree.XMLParser(resolve_entities=False, load_dtd=False,
                           no_network=True, huge_tree=False)


def load_p12(data, password):
    """``(key, certificate, chain)`` from a PKCS#12 file."""
    key, cert, chain = pkcs12.load_key_and_certificates(
        data, (password or "").encode() or None)
    if key is None or cert is None:
        raise ValueError("the PKCS#12 file holds no private key and certificate")
    return key, cert, list(chain or [])


def sign(xml_bytes, key, cert, chain=()):
    """The filing as EPO takes it: PKCS#7 signedData, DER, data embedded.

    ``Binary`` signs the bytes as they are — without it the builder would
    canonicalise line endings and sign something other than what is sent.
    ``NoCapabilities`` leaves out the S/MIME capabilities attribute, which is
    e-mail vocabulary and not part of the specification.
    """
    builder = pkcs7.PKCS7SignatureBuilder().set_data(xml_bytes).add_signer(
        cert, key, hashes.SHA256())
    for extra in chain:
        builder = builder.add_certificate(extra)
    return builder.sign(
        serialization.Encoding.DER,
        [pkcs7.PKCS7Options.Binary, pkcs7.PKCS7Options.NoCapabilities])


def unwrap(der):
    """The content of a PKCS#7 signedData object (a signed potvrzení)."""
    info = cms.ContentInfo.load(der)
    return info["content"]["encap_content_info"]["content"].native


def _post(url, data=None, form=None, params=None, session=None):
    http = session or requests
    try:
        if form is not None:
            resp = http.post(url, data=form, params=params, timeout=TIMEOUT)
        else:
            resp = http.post(
                url, data=data, params=params, timeout=TIMEOUT,
                headers={"Content-Type": "application/pkcs7-signature"})
    except (requests.ConnectTimeout, requests.exceptions.SSLError) as exc:
        # The connection was never established: nothing reached EPO.
        raise EpoError(f"EPO could not be reached: {exc}", maybe_sent=False) from exc
    except requests.RequestException as exc:
        raise EpoError(f"EPO did not answer: {exc}") from exc
    if resp.status_code >= 500:
        raise EpoError(f"EPO answered HTTP {resp.status_code}")
    return resp.content


def submit(signed, test, session=None):
    """POST a signed filing. ``test`` is REQUIRED and has no default: the
    caller says, every time, whether this files.

    Returns the parsed answer (see :func:`parse_answer`).
    """
    params = {"test": "1"} if test else None
    return parse_answer(_post(SUBMIT_URL, data=signed, params=params,
                              session=session))


def status(number, password, session=None):
    return parse_answer(_post(STATUS_URL, form={"C": number, "H": password},
                              session=session))


def receipt(transfer_id, password, session=None):
    return parse_answer(_post(RECEIPT_URL, form={"C": transfer_id, "H": password},
                              session=session))


def parse_answer(raw):
    """Classify an EPO answer.

    Returns a dict with ``kind`` one of:

    * ``receipt`` — a filing was taken: ``number`` (podací číslo), ``date``,
      ``password`` (heslo), ``xml`` (the potvrzení), ``raw`` (as received);
    * ``offline`` — a large filing queued for off-line processing:
      ``transfer_id``, ``password``;
    * ``errors`` — ``errors`` (list of dicts), ``test_clean`` (only the
      TEST_REZIM notice), ``blocking`` (any S/K/E);
    * ``status`` — ``state`` (1/2/3) and the raw fields.
    """
    if not raw:
        raise EpoError("EPO sent an empty answer")
    stripped = raw.lstrip()
    xml = stripped
    if not stripped.startswith(b"<"):
        try:
            xml = unwrap(raw)
        except Exception as exc:  # noqa: BLE001 - neither XML nor PKCS#7
            raise EpoError("EPO sent an answer that is neither XML nor "
                           "a signed receipt") from exc
    try:
        root = etree.fromstring(xml, parser=_parser())
    except etree.XMLSyntaxError as exc:
        raise EpoError(f"EPO sent malformed XML: {exc}") from exc
    tag = etree.QName(root).localname

    if tag == "Chyby":
        errors = []
        # Elements only: with entities left unresolved, the tree also holds
        # entity nodes, which have no tag name.
        for node in root.iter(etree.Element):
            if etree.QName(node).localname != "Chyba":
                continue
            text = node.findtext("Text") or (node.text or "").strip()
            errors.append({
                "type": node.get("Typ") or "",
                "code": node.get("Zkr") or "",
                "row": node.get("Radek") or "",
                "field": node.get("Polozka") or "",
                "section": node.get("Oddil") or "",
                "detail": node.get("DoplInfo") or "",
                "text": (text or "").strip(),
            })
        real = [e for e in errors if e["code"] != "TEST_REZIM"]
        return {
            "kind": "errors", "errors": errors, "xml": xml,
            "test_clean": bool(errors) and not real,
            "blocking": any(e["type"] in BLOCKING_TYPES for e in real),
        }
    if tag == "Odpoved":
        node = root.find(".//Potvrzeni")
        if node is None:
            raise EpoError("EPO sent an <Odpoved> without a <Potvrzeni>")
        return {"kind": "offline", "transfer_id": node.get("ID_predani"),
                "password": node.get("Heslo"), "xml": xml}
    if tag == "Stav" or root.find(".//stav_podapl") is not None \
            or root.get("stav_podapl"):
        fields = {k: v for k, v in root.attrib.items()}
        for child in root.iter(etree.Element):
            if child is not root and child.text and child.text.strip():
                fields.setdefault(etree.QName(child).localname, child.text.strip())
        return {"kind": "status", "state": fields.get("stav_podapl", ""),
                "fields": fields, "xml": xml}
    if tag == "StavZpracovani":
        return {"kind": "status", "state": root.get("Stav", ""),
                "fields": dict(root.attrib), "xml": xml}
    podani = root.find(".//Podani")
    if tag == "Pisemnost" and podani is not None:
        return {"kind": "receipt", "number": podani.get("Cislo"),
                "date": podani.get("Datum"), "password": podani.get("Heslo"),
                "xml": xml, "raw": raw}
    raise EpoError(f"EPO sent an answer this module does not know: <{tag}>")
