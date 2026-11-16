# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Overlay native tax-return facts onto the unmodified published form.

The published pattern is a static PDF, without AcroForm fields or widgets.
Coordinates are pinned separately; no authority form is reconstructed from
an image. The result remains unsigned and retains all original21 pages.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from io import BytesIO
from copy import deepcopy
import json
import unicodedata

from odoo.tools.pdf import PdfReader, PdfWriter, generic
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

FONT = "SKDppoSans"
PITCH = 14.4


def _cells(canvas, value, rect, name, *, right=False, size=11):
    text = unicodedata.normalize("NFC", str(value or "")).upper()
    count = round((rect[2] - rect[0]) / PITCH)
    if (len(text) > count or any(unicodedata.category(c).startswith("C") for c in text)
            or any(pdfmetrics.stringWidth(c, FONT, size) > PITCH - 2 for c in text)):
        raise ValueError("Value does not fit the official form field: %s" % name)
    start = count - len(text) if right else 0
    canvas.setFont(FONT, size)
    for index, char in enumerate(text):
        canvas.drawCentredString(rect[0] + (start + index + .5) * PITCH,
                                 842 - rect[1] - 14.5, char)


def _text(canvas, value, rect, name):
    text = str(value or "")
    size = 10
    while size > 7 and pdfmetrics.stringWidth(text, FONT, size) > rect[2] - rect[0] - 4:
        size -= .25
    if (any(unicodedata.category(c).startswith("C") for c in text)
            or pdfmetrics.stringWidth(text, FONT, size) > rect[2] - rect[0] - 4):
        raise ValueError("Value does not fit the official form field: %s" % name)
    canvas.setFont(FONT, size)
    canvas.drawString(rect[0] + 2, 842 - rect[1] - 14.5, text)


def _tick(canvas, value, rect):
    if value:
        canvas.setFont(FONT, 9)
        canvas.drawCentredString((rect[0] + rect[2]) / 2,
                                 842 - rect[3] + 1.5, "X")


def _date(canvas, value, boxes, name):
    if not value:
        return
    year, month, day = str(value).split("-")
    if year[:2] != "20":
        raise ValueError("Date does not fit the published form century: %s" % name)
    _cells(canvas, day, boxes[0], name)
    _cells(canvas, month, boxes[1], name)
    year_box = list(boxes[2])
    year_box[0] += 2 * PITCH
    _cells(canvas, year[2:], year_box, name)


def _continuous_integer(canvas, text, rect, name):
    """Right-align whole euros in a continuous, unsegmented printed field.

    Table K has one rectangle for whole euros, not PITCH-wide digit cells.
    Retain the normal numeric font and refuse genuine physical overflow.
    """
    size, margin = 11, 2
    if pdfmetrics.stringWidth(text, FONT, size) > rect[2] - rect[0] - 2 * margin:
        raise ValueError("Value does not fit the official form field: %s" % name)
    canvas.setFont(FONT, size)
    canvas.drawRightString(rect[2] - margin, 842 - rect[1] - 14.5, text)


def _number(canvas, value, spec, name):
    if value is None:
        return
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            raise ValueError()
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("Use a finite amount on the official form: %s" % name) from error
    if spec["kind"] == "integer":
        if number != number.to_integral_value():
            raise ValueError("Use a whole number on the official form: %s" % name)
        _cells(canvas, str(int(number)), spec["rect"], name, right=True)
        return
    try:
        rounded = number.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValueError("Value does not fit the official form field: %s" % name) from error
    whole, cents = format(abs(rounded), ".2f").split(".")
    if rounded < 0:
        if spec.get("sign"):
            sign = spec["sign"]
            canvas.setFont(FONT, 9)
            canvas.drawCentredString((sign[0] + sign[2]) / 2,
                                     842 - sign[3] + 1.5, "-")
        elif not spec.get("printed_minus"):
            whole = "-" + whole
    if spec.get("continuous_integer"):
        _continuous_integer(canvas, whole, spec["integer"], name)
    else:
        _cells(canvas, whole, spec["integer"], name, right=True)
    _cells(canvas, cents, spec["decimal"], name, right=True)


def _table_fl(canvas, data, page_index, continuation=None):
    if not data:
        return
    def money(value, left, y, name, sign=None):
        spec = {"kind": "money", "integer": [left, y, left + 144.05, y + 20.1],
                "decimal": [left + 158.4, y, left + 187.2, y + 20.1]}
        if sign is not None:
            spec["sign"] = [sign, y + 8.6, sign + 8.58, y + 17.24]
        _number(canvas, value, spec, name)
    if page_index == 7:
        for key, y in (("revenue", 447.33), ("cost", 472.53), ("profit", 497.73)):
            money(data[key], 330.11, y, "Table F " + key, 318.88)
    if page_index != 10:
        return
    items, offset = data["items"][:26], 0
    if continuation:
        _, offset, items = continuation
    money(data["revenue"], 312.11, 71.85, "Table L 1")
    if continuation:
        canvas.setFont(FONT, 9)
        canvas.drawString(32, 800, "Tabuľka L - pokračovanie")
        for index in range(26):
            y = 125.49 + 25.2 * index
            canvas.setFillColorRGB(.92, .95, .81)
            canvas.rect(295.1, 842 - y - 7, 15.6, 10.3, fill=1, stroke=0)
        canvas.setFillColorRGB(0, 0, 0)
    for index, item in enumerate(items):
        y = 125.49 + 25.2 * index
        if continuation:
            canvas.setFont(FONT, 7)
            # The published first page skips ordinal22: 2..21,23..28.
            # Preserve that page exactly; place missing22 first on the marked
            # continuation, then29..98. All97 input facts remain represented.
            ordinal = 22 if offset + index == 26 else offset + index + 2
            canvas.drawString(296, 842 - y - 5, str(ordinal))
        _text(canvas, item["description"], [31.19, y, 293, y + 20.1], "Table L description")
        # The form has one SIGN box, not separate plus/minus checkboxes.
        # Print the explicit plus as well as the minus for each adjustment.
        sign = [300.88, y + 8.96, 309.46, y + 17.6]
        canvas.setFont(FONT, 9)
        canvas.drawCentredString((sign[0] + sign[2]) / 2, 842 - sign[3] + 1.5,
                                 "+" if item["amount"] >= 0 else "-")
        money(abs(item["amount"]), 312.11, y, "Table L adjustment")
        _cells(canvas, item["row"], [506.73, y, 564.21, y + 20.1], "Table L related row", right=True)
    money(data["taxable"], 312.11, 780.69, "Table L 99")


def _namespace_overlay_fonts(overlay, reader, page_index):
    """Avoid PyPDF's random UUID renaming on background font collisions.

    An explicit per-page namespace makes equal native snapshots produce
    equal bytes, so a repeated download can reuse its existing attachment.
    """
    fonts = overlay["/Resources"].get("/Font")
    if not fonts:
        return
    fonts = fonts.get_object()
    names = {old: generic.NameObject("/SKDPPO_%s_%s" % (page_index, str(old)[1:]))
             for old in list(fonts)}
    for old, new in names.items():
        fonts[new] = fonts.pop(old)
    content = generic.ContentStream(overlay.get_contents(), reader)
    for operands, operation in content.operations:
        if operation == b"Tf" and operands[0] in names:
            operands[0] = names[operands[0]]
    overlay[generic.NameObject("/Contents")] = content


def _table_i(canvas, items, *, loans=False, offset=0, continuation=False):
    """Coordinates are white rectangles extracted from the official pattern."""
    top = 87.69 if loans else 608.25
    if continuation:
        canvas.setFillColorRGB(1, 1, 1)
        canvas.rect(27, 842 - (810 if loans else 557), 541,
                    453 if loans else 500, fill=1, stroke=0)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont(FONT, 11)
        canvas.drawString(31, 842 - (380 if loans else 80),
                          "Tabuľka I - pokračovanie (%s %s-%s)" % (
                              "úvery" if loans else "transakcie", offset + 1, offset + len(items)))
    for index, item in enumerate(items):
        y = top + index * 50.4
        if continuation:
            # Replace only the preprinted ordinal on additional copies.
            canvas.setFillColorRGB(.92, .95, .81)
            canvas.rect(28.2, 842 - y - 37, 8.7, 39, fill=1, stroke=0)
            canvas.setFillColorRGB(0, 0, 0)
            canvas.setFont(FONT, 7)
            canvas.drawCentredString(32.6, 842 - y - 26, str(offset + index + 1))
        _cells(canvas, item["code"], [42.11, y, 70.91, y + 20.1], "Table I code")
        _cells(canvas, item["country"], [520.91, y, 564.16, y + 20.1], "Table I country")
        _text(canvas, item["name"], [110.15, y + 25.49, 564.08, y + 45.59], "Table I related name")
        def amount(key, left, sign):
            _number(canvas, item[key], {"kind": "money",
                "integer": [left, y, left + 144.05, y + 20.1],
                "decimal": [left + 158.4, y, left + 187.2, y + 20.1],
                "sign": [sign, y + 7.16, sign + 8.58, y + 15.8]}, "Table I " + key)
        if loans:
            amount("highest", 103.31, 92.44)
            amount("closing", 322.91, 312.04)
        else:
            amount("effect", 322.91, 312.04)
            _tick(canvas, item["aggregated"], [96.04, y + 7.16, 104.62, y + 15.8])
            _tick(canvas, item["permanent_link"], [193.24, y + 7.16, 201.82, y + 15.8])


def _table_d(canvas, data, page_index):
    for item in data.get("items", []):
        column = item["column"]
        if column == 1:
            left, top = 376.91, 86.97
        else:
            left = 182.51 if column % 2 == 0 else 376.91
            top = 257.25 + ((column - 2) // 2) * 169.2
            if column == 8:
                top = 765.21
            if page_index == 6:
                x = 212.19 if column % 2 == 0 else 406.59
                y = top - 50.52
                for key, date_top in (("date_from", y), ("date_to", y + 25.2)):
                    _date(canvas, item[key], [[x, date_top, x + 28.31, date_top + 20.6],
                        [x + 36, date_top, x + 64.31, date_top + 20.6],
                        [x + 71.29, date_top - .06, x + 127.9, date_top + 20.54]], "Table D period")
        for row, key in enumerate(("loss", "deducted", "remaining", "prior")):
            target = 7 if column == 8 and row > 0 else 6
            if page_index != target:
                continue
            y = 58.89 + (row - 1) * 25.2 if target == 7 else top + row * 25.2
            _number(canvas, item[key], {"kind": "money",
                "integer": [left, y, left + 144.05, y + 20.1],
                "decimal": [left + 158.4, y, left + 187.2, y + 20.1]}, "Table D " + key)
    if page_index == 7 and data.get("items"):
        _number(canvas, data["total"], {"kind": "money",
            "integer": [376.91, 58.89, 520.96, 78.99],
            "decimal": [535.31, 58.89, 564.11, 78.99]}, "Table D total")


def _table_ek(canvas, data, page_index, continuation=None):
    if page_index == 7 and data.get("table_e"):
        for index, amount in enumerate(data["table_e"]["rows"]):
            y = 176.974 + 25.2 * index
            percent = index in (2, 5)
            left, width, decimal = 330.108, (43.25 if percent else 144.05), (387.708 if percent else 488.508)
            _number(canvas, amount, {"kind": "money",
                "integer": [left, y, left + width, y + 20.1],
                "decimal": [decimal, y, decimal + 28.8, y + 20.1]}, "Table E row %s" % (index + 1))
    if page_index == 9 and not continuation and data.get("table_k"):
        for index, item in enumerate(data["table_k"]["items"]):
            y = 560.014 + 50.4 * index
            for offset, key in ((0, "date_from"), (25.2, "date_to")):
                dy = 560.252 + 50.4 * index + offset
                _date(canvas, item[key], [[37.592, dy, 65.9, dy + 20.1],
                    [73.59, dy, 101.898, dy + 20.1],
                    [108.877, dy, 165.493, dy + 20.1]], "Table K " + key)
            for key, left, decimal in (("credit", 171.708, 236.508),
                    ("prior", 272.508, 336.948), ("claimed", 371.508, 436.308),
                    ("remaining", 470.868, 535.668)):
                _number(canvas, item[key], {"kind": "money", "continuous_integer": True,
                    "integer": [left, y, left + 57.596, y + 20.1],
                    "decimal": [decimal, y, decimal + 28.8, y + 20.1]}, "Table K " + key)
        if data["table_k"]["items"]:
            for key, left, decimal in (("claimed", 371.508, 436.308), ("remaining", 470.868, 535.668)):
                _number(canvas, sum(item[key] for item in data["table_k"]["items"]),
                    {"kind": "money", "continuous_integer": True,
                     "integer": [left, 761.614, left + 57.596, 781.714],
                     "decimal": [decimal, 761.614, decimal + 28.8, 781.714]}, "Table K total " + key)


def _special_record_lines(value):
    text = unicodedata.normalize("NFC", value)
    if any(unicodedata.category(char).startswith("C") and char != "\n" for char in text):
        raise ValueError("Unsupported control character in official special records.")
    lines = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            if pdfmetrics.stringWidth(word, FONT, 9) > 525:
                raise ValueError("Value does not fit the official special records.")
            trial = (line + " " + word).strip()
            if pdfmetrics.stringWidth(trial, FONT, 9) > 525:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _special_records(canvas, lines, continuation=False, title=None):
    if continuation:
        canvas.setFillColorRGB(1, 1, 1)
        # Keep the authentic identifier/footer, but remove every unrelated
        # section on the continuation copy before drawing its own heading.
        canvas.rect(27, 842 - 800, 542, 745, fill=1, stroke=0)
        canvas.setFillColorRGB(0, 0, 0)
        canvas.setFont(FONT, 10)
        canvas.drawString(35, 842 - 85, title or "IX - pokračovanie osobitných záznamov")
    canvas.setFont(FONT, 9)
    for index, line in enumerate(lines):
        canvas.drawString(35, 842 - (105 if continuation else 627) - index * 12, line)


def render_official_form(template, layout, data):
    """Render a supplied native snapshot; no live records or caller flags."""
    if sha256(template).hexdigest() != layout["template_sha256"]:
        raise ValueError("The pinned official DPPO PDF template changed.")
    reader = PdfReader(BytesIO(template))
    if len(reader.pages) != layout["pages"] or reader.get_fields():
        raise ValueError("The reviewed static DPPO PDF structure changed.")
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    writer = PdfWriter()
    header = data["header"]
    flags = data["flags"]
    table_i = data.get("table_i", {})
    pages = [(index, deepcopy(page), None) for index, page in enumerate(reader.pages)]
    for index, key, capacity in ((8, "transactions", 4), (9, "loans", 5)):
        items = table_i.get(key, [])
        for offset in range(capacity, len(items), capacity):
            pages.append((index, deepcopy(reader.pages[index]), (key, offset, items[offset:offset + capacity])))
    table_fl = data.get("table_fl", {})
    for offset in range(26, len(table_fl.get("items", [])), 26):
        pages.append((10, deepcopy(reader.pages[10]), ("table_l", offset, table_fl["items"][offset:offset + 26])))
    notes = _special_record_lines(data.get("notes", ""))
    for offset in range(14, len(notes), 14):
        pages.append((14, deepcopy(reader.pages[14]), ("notes", offset, notes[offset:offset + 14])))
    fx_lines = _special_record_lines(data.get("fx_annex", ""))
    for offset in range(0, len(fx_lines), 14):
        pages.append((14, deepcopy(reader.pages[14]), ("fx", offset, fx_lines[offset:offset + 14])))
    for output_index, (page_index, page, continuation) in enumerate(pages):
        stream = BytesIO()
        canvas = Canvas(stream, pagesize=(595.22, 842), invariant=1)
        dic_box = [31.28, 150.68, 175.16, 170.72] if page_index == 0 else [206.85, 28.35, 350.72, 48.45]
        _cells(canvas, header["dic"], dic_box, "DIČ")
        _table_fl(canvas, table_fl, page_index, continuation if page_index == 10 else None)
        _table_ek(canvas, data, page_index, continuation)
        if page_index in (6, 7):
            _table_d(canvas, data.get("table_d", {}), page_index)
        if page_index in (8, 9):
            loans = page_index == 9
            key = "loans" if loans else "transactions"
            capacity = 5 if loans else 4
            if continuation:
                _, offset, items = continuation
            else:
                offset, items = 0, table_i.get(key, [])[:capacity]
            _table_i(canvas, items, loans=loans, offset=offset, continuation=bool(continuation))
            if loans and not continuation:
                _tick(canvas, table_i.get("below_threshold"), [41, 342.18, 49.94, 351.12])
        if page_index == 0:
            _cells(canvas, header["ico"], [31.28, 186.68, 204.08, 206.72], "IČO")
            _cells(canvas, header["legal_code"], [189.68, 150.68, 232.88, 170.72], "Právna forma")
            nace = header["nace"]
            for text, box in zip((nace[:2], nace[2:4], nace[4:]),
                                 ([31.47, 225.45, 59.78, 246.05],
                                  [67.47, 225.45, 95.78, 246.05],
                                  [102.76, 225.39, 116.91, 245.98])):
                _cells(canvas, text, box, "SK NACE")
            company_name = unicodedata.normalize("NFC", header["name"]).upper()
            if len(company_name) > 111:
                raise ValueError("Value does not fit the official form field: Obchodné meno")
            for index, top in enumerate((285.98, 310.1, 334.58)):
                _cells(canvas, company_name[index * 37:(index + 1) * 37],
                       [30.99, top, 564.08, top + 20.1], "Obchodné meno")
            for key, box in {
                "street": [31.14, 383.54, 434.22, 403.64],
                "number": [448.68, 383.54, 563.82, 403.64],
                "zip": [31.14, 419.54, 103.08, 439.64],
                "city": [110.34, 419.54, 398.22, 439.64],
                "country": [405.48, 419.54, 563.82, 439.64],
                "phone": [31.14, 455.18, 218.28, 475.28],
            }.items():
                _cells(canvas, header.get(key), box, key)
            _text(canvas, header.get("email"), [232.74, 455.18, 563.94, 475.28], "Email")
            for kind, top in (("R", 154.26), ("O", 170.44), ("D", 186.62)):
                _tick(canvas, data["statement_type"] == kind, [281.88, top, 290.82, top + 9.28])
            for key, top in (("date_from", 155.25), ("date_to", 180.45)):
                _date(canvas, data[key], [[431.9, top, 460.21, top + 20.6],
                                         [467.9, top, 496.21, top + 20.6],
                                         [503.18, top, 559.8, top + 20.6]], key)
            for key, rect in {
                "currency_start": [33.8, 484.02, 42.74, 492.96],
                "currency_end": [33.8, 505.98, 42.74, 514.92],
                "nonresident": [33.8, 532.98, 42.74, 541.92],
                "controlled_transactions": [33.8, 558.18, 42.74, 567.12],
                "patent_exemption": [314.6, 481.5, 323.54, 490.44],
                "micro_taxpayer": [314.6, 498.78, 323.54, 507.72],
                "half_minimum": [314.6, 517.5, 323.54, 526.44],
                "minimum_exemption": [314.6, 535.5, 323.54, 544.44],
                "minimum_credit": [314.6, 553.5, 323.54, 562.44],
            }.items():
                _tick(canvas, flags.get(key), rect)
        for code, spec in layout["line_fields"].items():
            if spec["page"] == page_index and code in data["rows"]:
                _number(canvas, data["rows"][code], spec, code)
        if page_index == 4:
            _date(canvas, data.get("discovered_on"),
                  [[330.11, 70.05, 358.91, 90.15], [366.11, 70.05, 394.91, 90.15],
                   [402.11, 70.05, 459.71, 90.15]], "Dátum zistenia")
        if page_index == 14:
            if not continuation:
                _tick(canvas, data.get("share_not_applied", True), [38.66, 204.58, 48.71, 214.63])
            if notes or continuation:
                _special_records(canvas, continuation[2] if continuation else notes[:14], bool(continuation),
                    "Príloha - prepočet dane zo zahraničia podľa § 31" if continuation and continuation[0] == "fx" else None)
        if page_index == 15:
            person = data.get("person", {})
            for key, box in {
                "last": [30.99, 81.5, 261.27, 101.6],
                "first": [268.53, 81.5, 426.87, 101.6],
                "relationship": [30.99, 116.06, 564.08, 136.16],
                "street": [31.14, 165.02, 434.22, 185.12],
                "number": [448.68, 165.02, 563.82, 185.12],
                "zip": [31.14, 201.02, 103.08, 221.12],
                "city": [110.34, 201.02, 398.22, 221.12],
                "country": [405.48, 201.02, 563.82, 221.12],
                "phone": [31.14, 236.66, 218.28, 256.76],
            }.items():
                _cells(canvas, person.get(key), box, "Authorized person: " + key)
            _text(canvas, person.get("title_before"), [434.13, 81.5, 510.38, 101.6], "Title")
            _text(canvas, person.get("title_after"), [516.93, 81.5, 564.61, 101.6], "Title")
            _text(canvas, person.get("email"), [232.74, 236.66, 563.94, 256.76], "Email")
            _cells(canvas, data.get("annex_count", 5) + max(0, (len(notes) - 1) // 14)
                   + (len(fx_lines) + 13) // 14, [85.14, 268.4, 128.34, 288.5], "Počet príloh")
            _date(canvas, data["prepared_on"],
                  [[38.51, 333.92, 67.25, 354.02], [74.5, 333.92, 103.24, 354.02],
                   [110.5, 333.92, 167.98, 354.02]], "Dátum vyhlásenia")
        if page_index >= 16:
            canvas.setFont(FONT, 8)
            canvas.drawRightString(559, 18.8, str(page_index - 15))
        if continuation:
            canvas.setFillColorRGB(1, 1, 1)
            canvas.rect(500, 12, 64, 17, fill=1, stroke=0)
            canvas.setFillColorRGB(0, 0, 0)
            canvas.setFont(FONT, 8)
            canvas.drawRightString(559, 18.8, "Príloha %s" % (output_index - 15))
        canvas.save()
        overlay_reader = PdfReader(BytesIO(stream.getvalue()))
        overlay = overlay_reader.pages[0]
        _namespace_overlay_fonts(overlay, overlay_reader, output_index)
        page.merge_page(overlay)
        # PyPDF unions ProcSet with a frozenset. Its order otherwise depends
        # on the process hash seed, producing different bytes after a restart.
        resources = page["/Resources"]
        if resources.get("/ProcSet"):
            resources[generic.NameObject("/ProcSet")] = generic.ArrayObject(
                sorted(resources["/ProcSet"], key=str))
        writer.add_page(page)
    writer.add_metadata({
        "/Title": "DPPO MF/014309/2026-721",
        "/Subject": "%s — %s" % (data["date_from"], data["date_to"]),
        "/Producer": "Odoo l10n_sk_dppo",
        "/SourceSHA256": layout["template_sha256"],
        "/DataSHA256": sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
    })
    result = BytesIO()
    writer.write(result)
    return result.getvalue()
