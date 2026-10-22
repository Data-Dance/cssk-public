# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Synthetic receipt photographs, generated at test time.

The decoding was designed against real receipt photographs, which are a
company's actual expenses and are not committed anywhere. These stand in for
them: generated, so nothing identifying is stored, and shaped like the cases
that mattered — a loyalty-app QR printed ABOVE the fiscal one, a single fiscal
code, no code at all.
"""
import io

from PIL import Image

#: An identifier in the shape of an on-line eKasa receipt's, synthetic.
FISCAL_ID = "O-ABCDEF0000000002ABCDEF0000000002"
#: The kind of code printed above the fiscal one on a fuel receipt.
LOYALTY_LINK = "https://loyalty.example.com/download"


def qr_available():
    try:
        import qrcode  # noqa: F401 - shipped with Odoo
        import zxingcpp  # noqa: F401
    except ImportError:
        return False
    return True


def receipt_image(codes, size=(1080, 1920), image_format="JPEG"):
    """A white "receipt" with the given QR payloads stacked top to bottom."""
    import qrcode

    canvas = Image.new("RGB", size, "white")
    top = 160
    for text in codes:
        code = qrcode.QRCode(box_size=7, border=4)
        code.add_data(text)
        code.make(fit=True)
        tile = code.make_image(fill_color="black", back_color="white").convert("RGB")
        canvas.paste(tile, ((size[0] - tile.width) // 2, top))
        top += tile.height + 220
    out = io.BytesIO()
    canvas.save(out, format=image_format, quality=90)
    return out.getvalue()
