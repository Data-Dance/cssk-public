# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Parser for Fio's payment-order import response.

Reference: *FIO API BANKOVNICTVÍ* v1.9, §6.1; schema at
``https://www.fio.cz/schema/responseImportIB.xsd``.

**``errorCode = 2`` means the orders were accepted**, with warnings — the
documentation says so in as many words ("příkazy s odpovědí warning byly
přijaty bankou"). Treating any non-zero code as a failure would report an
accepted batch as rejected, and the operator would send it twice.

The documentation names the elements but not the shape of the tree around the
per-order messages, so the parse is deliberately lenient: the summary elements
are looked up anywhere in the document, and every ``<message>`` is collected
with whatever attributes it carries.
"""

from collections import namedtuple

from lxml import etree

#: §6.1
ERROR_CODES = {
    0: "The orders were accepted.",
    1: "Errors found while checking the orders — nothing was accepted.",
    2: "The orders were accepted, but some values raised warnings.",
    11: "Syntax error in the uploaded file.",
    12: "Empty import — the file contains no orders.",
    13: "The file is longer than 2 MB.",
    14: "Empty file — the file contains no orders.",
}

#: Codes under which the bank has created a batch.
ACCEPTED_CODES = frozenset({0, 2})

FioMessage = namedtuple("FioMessage", ["status", "error_code", "text", "order"])


class FioImportResult:
    """Outcome of one ``/import/`` call."""

    def __init__(self, error_code=None, id_instruction=None, status=None,
                 sum_debet=None, sum_credit=None, messages=(), raw=b""):
        self.error_code = error_code
        self.id_instruction = id_instruction
        self.status = status
        self.sum_debet = sum_debet
        self.sum_credit = sum_credit
        self.messages = list(messages)
        self.raw = raw

    @property
    def accepted(self):
        """True when Fio created a batch — including the warnings case."""
        return self.error_code in ACCEPTED_CODES

    @property
    def summary(self):
        base = ERROR_CODES.get(
            self.error_code, "Fio returned error code %s." % self.error_code
        )
        if self.accepted and self.id_instruction:
            return "%s Batch number %s — it still has to be authorised in Fio " \
                   "internet banking." % (base, self.id_instruction)
        return base

    def __repr__(self):
        return "<FioImportResult errorCode=%s idInstruction=%s messages=%s>" % (
            self.error_code, self.id_instruction, len(self.messages),
        )


class FioResponseParseError(ValueError):
    """The bank's answer is not a recognisable import response."""


def _first_text(root, name):
    for element in root.iter():
        if etree.QName(element).localname == name and element.text:
            return element.text.strip()
    return None


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_float(value):
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def parse_import_response(data):
    """Parse the XML answer of ``/import/`` into a :class:`FioImportResult`."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False,
    )
    try:
        root = etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError as exc:
        raise FioResponseParseError(
            "Fio's answer is not valid XML (%s): %s"
            % (exc, data[:200].decode("utf-8", "replace"))
        ) from None

    error_code = _to_int(_first_text(root, "errorCode"))
    if error_code is None:
        raise FioResponseParseError(
            "Fio's answer carries no errorCode: %s"
            % data[:200].decode("utf-8", "replace")
        )

    messages = []
    for element in root.iter():
        if etree.QName(element).localname != "message":
            continue
        # The per-order id lives on the enclosing element in the published
        # schema; fall back to the message's own attributes.
        parent = element.getparent()
        order_id = None
        while parent is not None and order_id is None:
            order_id = parent.get("id")
            parent = parent.getparent()
        messages.append(FioMessage(
            status=element.get("status"),
            error_code=_to_int(element.get("errorCode")),
            text=(element.text or "").strip(),
            order=order_id,
        ))

    return FioImportResult(
        error_code=error_code,
        id_instruction=_first_text(root, "idInstruction"),
        status=_first_text(root, "status"),
        sum_debet=_to_float(_first_text(root, "sumDebet")),
        sum_credit=_to_float(_first_text(root, "sumCredit")),
        messages=messages,
        raw=data,
    )
