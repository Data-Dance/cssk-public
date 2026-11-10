# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech data box system (ISDS) web services, without Odoo.

Follows the operator's WSDL and XSD, version 3.11 (``dm_operations.wsdl``,
``dm_info.wsdl``, ``db_access.wsdl``, ``dmBaseTypes.xsd``, ``dbTypes.xsd``,
https://www.mojedatovaschranka.cz/static/wsdl/v20/): SOAP 1.1, namespace
``http://isds.czechpoint.cz/v20``, each service on its own path of the same
host, a user signing in with the box's login and password (HTTP Basic).

Only what filing needs is here:

* ``CreateMessage`` (dm_operations) sends a data message with attachments;
* ``GetListOfReceivedMessages`` (dm_info) lists what arrived in a period;
* ``MessageDownload`` (dm_operations) fetches one message with its files;
* ``GetOwnerInfoFromLogin`` (db_access) says whose box the login opens.

A status code other than ``0000`` is an error the operator reports in
``dmStatus`` / ``dbStatus``. Kept free of Odoo so it can be tested on its own.
"""

import base64
import os
import secrets
import ssl
import tempfile

import requests
from requests.adapters import HTTPAdapter
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from lxml import etree

NS = "http://isds.czechpoint.cz/v20"
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
#: gMessageEnvelopeSub, in schema order: every element is required and
#: nillable, so each is sent, as xsi:nil when unused.
ENVELOPE_FIELDS = (
    "dmSenderOrgUnit", "dmSenderOrgUnitNum", "dbIDRecipient",
    "dmRecipientOrgUnit", "dmRecipientOrgUnitNum", "dmToHands",
    "dmAnnotation", "dmRecipientRefNumber", "dmSenderRefNumber",
    "dmRecipientIdent", "dmSenderIdent", "dmLegalTitleLaw",
    "dmLegalTitleYear", "dmLegalTitleSect", "dmLegalTitlePar",
    "dmLegalTitlePoint", "dmPersonalDelivery", "dmAllowSubstDelivery",
)

#: The operator moved production to datovka.gov.cz in June 2026 and the test
#: environment (formerly czebox.cz) to datovka-test.gov.cz in January 2026.
HOSTS = {
    "production": "https://ws1.datovka.gov.cz",
    "test": "https://ws1.datovka-test.gov.cz",
}
#: The hosts that take a client certificate in the TLS handshake.
CERT_HOSTS = {
    "production": "https://ws1c.datovka.gov.cz",
    "test": "https://ws1c.datovka-test.gov.cz",
}
#: Path of each service for a login with a password.
PATHS = {"operations": "/DS/dz", "info": "/DS/dx", "access": "/DS/DsManage"}
#: How the client signs in, and the path prefix each way uses on its host:
#: a login and password (ws1); a login and password together with a
#: commercial certificate assigned to that user (ws1c, /certds); or a system
#: certificate registered on the box for an external application, without
#: any password (ws1c, /cert).
AUTH_MODES = {
    "password": ("", False, True),
    "password_cert": ("/certds", True, True),
    "system_cert": ("/cert", True, False),
}
#: (connect, read) seconds; a message with a large attachment takes a while.
TIMEOUT = (15, 120)
STATUS_OK = "0000"


class IsdsError(Exception):
    """The operator refused the call or could not be reached.

    ``code`` is the operator's status code (``None`` for a transport failure,
    ``"HTTP 401"`` for refused credentials). ``maybe_sent`` says whether a
    CreateMessage may have been delivered anyway, which decides whether the
    caller may send it again.
    """

    def __init__(self, message, code=None, maybe_sent=False, retryable=False):
        super().__init__(message)
        self.code = code
        self.maybe_sent = maybe_sent
        self.retryable = retryable


def _parser():
    # The operator's answer is parsed, not trusted.
    return etree.XMLParser(resolve_entities=False, load_dtd=False,
                           no_network=True, huge_tree=True)


def _q(tag):
    return "{%s}%s" % (NS, tag)


def _sub(parent, tag, text=None):
    el = etree.SubElement(parent, _q(tag))
    if text is not None:
        el.text = str(text)
    return el


def _nil(parent, tag):
    el = etree.SubElement(parent, _q(tag))
    el.set("{%s}nil" % NS_XSI, "true")
    return el


def envelope(body_element):
    """A SOAP 1.1 envelope around *body_element*, as bytes."""
    env = etree.Element("{%s}Envelope" % NS_SOAP, nsmap={"soap": NS_SOAP})
    etree.SubElement(env, "{%s}Body" % NS_SOAP).append(body_element)
    return etree.tostring(env, xml_declaration=True, encoding="UTF-8")


# -- requests -------------------------------------------------------------
def create_message(recipient, annotation, files, sender_ref=None,
                   sender_ident=None):
    """The ``CreateMessage`` element: one message to *recipient* (a box ID)
    carrying *files*, ``[(name, bytes, mimetype)]``; the first is the main
    document. *sender_ref* (naše č. j.) and *sender_ident* (naše spisová
    značka) come back on an answer the recipient files against them."""
    req = etree.Element(_q("CreateMessage"), nsmap={None: NS, "xsi": NS_XSI})
    env = _sub(req, "dmEnvelope")
    values = {
        "dbIDRecipient": recipient,
        "dmAnnotation": (annotation or "")[:255],
        "dmSenderRefNumber": (sender_ref or "")[:50],
        "dmSenderIdent": (sender_ident or "")[:50],
    }
    for tag in ENVELOPE_FIELDS:
        if values.get(tag):
            _sub(env, tag, values[tag])
        else:
            _nil(env, tag)
    filelist = _sub(req, "dmFiles")
    for index, (name, data, mimetype) in enumerate(files):
        f = _sub(filelist, "dmFile")
        f.set("dmMimeType", mimetype)
        f.set("dmFileMetaType", "main" if index == 0 else "enclosure")
        f.set("dmFileDescr", name)
        _sub(f, "dmEncodedContent", base64.b64encode(data).decode())
    return req


def list_received(date_from, date_to, offset=1, limit=1000):
    """The ``GetListOfReceivedMessages`` element for messages delivered in
    [*date_from*, *date_to*] (``datetime``), any status."""
    req = etree.Element(_q("GetListOfReceivedMessages"),
                        nsmap={None: NS, "xsi": NS_XSI})
    _sub(req, "dmFromTime", date_from.strftime("%Y-%m-%dT%H:%M:%S"))
    _sub(req, "dmToTime", date_to.strftime("%Y-%m-%dT%H:%M:%S"))
    _nil(req, "dmRecipientOrgUnitNum")
    # -1: every status (delivered, read, ...).
    _sub(req, "dmStatusFilter", "-1")
    _sub(req, "dmOffset", offset)
    _sub(req, "dmLimit", limit)
    return req


def message_download(dm_id):
    req = etree.Element(_q("MessageDownload"), nsmap={None: NS})
    _sub(req, "dmID", dm_id)
    return req


def load_p12(data, password):
    """``(key, certificate, chain)`` from a PKCS#12 file."""
    try:
        key, cert, chain = pkcs12.load_key_and_certificates(
            data, (password or "").encode() or None)
    except ValueError:
        if password:
            raise
        # An empty password and no password are not the same to PKCS#12.
        key, cert, chain = pkcs12.load_key_and_certificates(data, b"")
    if key is None or cert is None:
        raise ValueError("the PKCS#12 file holds no private key and "
                         "certificate")
    return key, cert, list(chain or [])


def owner_info():
    req = etree.Element(_q("GetOwnerInfoFromLogin"), nsmap={None: NS})
    _sub(req, "dbDummy", "")
    return req


# -- answers --------------------------------------------------------------
def _body(raw):
    try:
        root = etree.fromstring(raw, _parser())
    except etree.XMLSyntaxError as exc:
        raise IsdsError("The data box system answered with unreadable XML: "
                        "%s" % exc) from exc
    fault = root.find(".//{%s}Fault" % NS_SOAP)
    if fault is not None:
        raise IsdsError("The data box system refused the request: %s" % (
            (fault.findtext("faultstring") or "").strip() or "SOAP fault"),
            code="SOAP")
    body = root.find("{%s}Body" % NS_SOAP)
    if body is None or not len(body):
        raise IsdsError("The data box system answered without a body.")
    return body[0]


def _check_status(answer, tag="dmStatus"):
    status = answer.find(_q(tag))
    code = status is not None and status.findtext(_q(tag + "Code"))
    if code != STATUS_OK:
        message = status is not None and status.findtext(_q(tag + "Message"))
        raise IsdsError("The data box system refused it: %s (%s)" % (
            message or "no message", code or "no status"), code=code or None)


def parse_create(raw):
    """The ID of the message just sent."""
    answer = _body(raw)
    _check_status(answer)
    dm_id = answer.findtext(_q("dmID"))
    if not dm_id:
        raise IsdsError("The data box system confirmed the message without "
                        "giving its ID.", maybe_sent=True)
    return dm_id


def parse_list(raw):
    """``[{id, annotation, sender, delivered}]`` of the received messages."""
    answer = _body(raw)
    _check_status(answer)
    out = []
    for rec in answer.iter(_q("dmRecord")):
        out.append({
            "id": rec.findtext(_q("dmID")),
            "annotation": rec.findtext(_q("dmAnnotation")) or "",
            "sender": rec.findtext(_q("dbIDSender")) or "",
            "delivered": rec.findtext(_q("dmDeliveryTime")) or "",
        })
    return out


def parse_download(raw):
    """``{id, annotation, sender, files: [(name, bytes, mimetype)]}``."""
    answer = _body(raw)
    _check_status(answer)
    message = answer.find(_q("dmReturnedMessage"))
    dm = message.find(_q("dmDm")) if message is not None else None
    if dm is None:
        raise IsdsError("The data box system returned no message.")
    files = []
    for f in dm.iter(_q("dmFile")):
        content = f.findtext(_q("dmEncodedContent"))
        if content is not None:
            data = base64.b64decode(content)
        else:
            xml = f.find(_q("dmXMLContent"))
            data = etree.tostring(xml[0]) if xml is not None and len(xml) \
                else b""
        files.append((f.get("dmFileDescr") or "", data,
                      f.get("dmMimeType") or ""))
    return {
        "id": dm.findtext(_q("dmID")),
        "annotation": dm.findtext(_q("dmAnnotation")) or "",
        "sender": dm.findtext(_q("dbIDSender")) or "",
        "files": files,
    }


def parse_owner(raw):
    """``{box, name}`` of the box the login opens."""
    answer = _body(raw)
    _check_status(answer, "dbStatus")
    info = answer.find(_q("dbOwnerInfo"))
    if info is None:
        raise IsdsError("The data box system returned no owner.")
    name = info.findtext(_q("firmName")) or " ".join(filter(None, [
        info.findtext(_q("pnFirstName")), info.findtext(_q("pnLastName"))]))
    return {"box": info.findtext(_q("dbID")) or "", "name": name}


# -- transport ------------------------------------------------------------
class _ContextAdapter(HTTPAdapter):
    """Connections made with a given TLS context (the client certificate)."""

    def __init__(self, context, **kwargs):
        self._context = context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self._context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self._context
        return super().proxy_manager_for(*args, **kwargs)


class Client:
    """One data box, signed in one of the ways of ``AUTH_MODES``. A
    certificate is ``(key, certificate, chain)`` as ``load_p12`` gives it."""

    def __init__(self, environment, login=None, password=None,
                 auth="password", certificate=None):
        if environment not in HOSTS:
            raise ValueError("unknown data box environment %r" % environment)
        if auth not in AUTH_MODES:
            raise ValueError("unknown data box sign-in %r" % auth)
        prefix, needs_cert, needs_password = AUTH_MODES[auth]
        if needs_cert and not certificate:
            raise ValueError("this sign-in needs a certificate")
        self.host = (CERT_HOSTS if needs_cert else HOSTS)[environment] + prefix
        self.auth = (login or "", password or "") if needs_password else None
        self.certificate = certificate if needs_cert else None

    def _ssl_context(self):
        """A TLS context holding the client certificate.

        Python's ssl loads a key only from a file. The file is written
        encrypted with a random one-time password that lives only in this
        process, loaded, and deleted before any connection is made: it
        exists for milliseconds, and a copy left behind by a crash could not
        be opened."""
        key, cert, chain = self.certificate
        context = ssl.create_default_context(cafile=requests.certs.where())
        once = secrets.token_bytes(32)
        fd, path = tempfile.mkstemp(suffix=".pem")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.BestAvailableEncryption(once)))
                for c in [cert] + list(chain):
                    fh.write(c.public_bytes(serialization.Encoding.PEM))
            context.load_cert_chain(path, password=once)
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        return context

    def _session(self):
        session = requests.Session()
        if self.certificate:
            session.mount(self.host, _ContextAdapter(self._ssl_context()))
        return session

    def _post(self, service, element, sending=False):
        url = self.host + PATHS[service]
        try:
            with self._session() as session:
                # No redirects: a redirect would carry the login or the
                # client certificate to whatever host it names.
                response = session.post(
                    url, data=envelope(element), auth=self.auth,
                    timeout=TIMEOUT, allow_redirects=False,
                    headers={"Content-Type": "text/xml; charset=utf-8",
                             "SOAPAction": '""'})
        except requests.exceptions.SSLError as exc:
            # The handshake failed: nothing was sent. With a certificate the
            # usual cause is that the operator does not accept it for this
            # box (or the box's certificate access is not switched on).
            raise IsdsError("The data box system refused the secure "
                            "connection; check that the certificate is "
                            "registered for the data box: %s" % exc,
                            code="TLS") from exc
        except requests.ConnectTimeout as exc:
            raise IsdsError("The data box system could not be reached: %s"
                            % exc, retryable=True) from exc
        except requests.RequestException as exc:
            # A read timeout or a dropped connection after the request went
            # out: a message may have been created.
            raise IsdsError("The data box system did not answer: %s" % exc,
                            maybe_sent=sending, retryable=not sending) from exc
        if 300 <= response.status_code < 400:
            raise IsdsError("The data box system answered with a redirect "
                            "(HTTP %s), which is not followed."
                            % response.status_code, maybe_sent=sending)
        if response.status_code in (401, 403):
            raise IsdsError("The data box system refused the sign-in (the "
                            "login, the password or the certificate).",
                            code="HTTP %s" % response.status_code)
        if response.status_code >= 500 and b"Fault" not in response.content:
            raise IsdsError("The data box system answered HTTP %s."
                            % response.status_code, maybe_sent=sending,
                            retryable=not sending)
        return response.content

    def send(self, recipient, annotation, files, sender_ref=None,
             sender_ident=None):
        """Send a message; its ID."""
        return parse_create(self._post("operations", create_message(
            recipient, annotation, files, sender_ref, sender_ident),
            sending=True))

    def received(self, date_from, date_to, page=1000):
        """Every message received in the period, page by page."""
        out, offset = [], 1
        while True:
            batch = parse_list(self._post("info", list_received(
                date_from, date_to, offset=offset, limit=page)))
            out += batch
            if len(batch) < page:
                return out
            offset += page

    def download(self, dm_id):
        return parse_download(self._post("operations",
                                         message_download(dm_id)))

    def owner(self):
        return parse_owner(self._post("access", owner_info()))
