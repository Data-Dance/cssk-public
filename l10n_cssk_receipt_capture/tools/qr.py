# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Read the QR codes off a receipt photograph.

Measured on real receipt photographs before this was written, three decoders
against the same images: zxing-cpp was the only one that read BOTH codes on a
fuel receipt carrying a loyalty-app QR above the fiscal one; OpenCV's detector
lost the fiscal code once Odoo had downscaled the upload, and WeChat's read
only the loyalty link at full size. Hence zxing-cpp.

Optional here, because this module is country-neutral and a provider that never
looks at a QR should not force a native wheel on anyone. A provider that does
depend on it declares it (``l10n_sk_ekasa_receipt`` lists ``zxingcpp`` in its
external dependencies), so the dependency is guaranteed exactly where it is
needed.
"""
import io
import logging

_logger = logging.getLogger(__name__)


class QrDecoderUnavailable(Exception):
    """zxing-cpp is not installed in this Odoo."""


def decoder_available():
    try:
        import zxingcpp  # noqa: F401
    except ImportError:
        return False
    return True


def decode_qr_payloads(raw):
    """Every QR payload in the image, top to bottom, and whether one failed.

    Returns ``(payloads, unreadable)``. ``payloads`` are the texts of the codes
    that decoded, in reading order and de-duplicated — ALL of them, because a
    receipt can carry several and the first is not the fiscal one (a loyalty
    link printed above the verification code is exactly that case).
    ``unreadable`` is true when a QR code was found but its error correction
    failed: a code that is present but damaged is a different situation from no
    code at all, and the first deserves the fallback and a message saying so.

    Only QR proper is asked for. Asking for every format makes the decoder
    report Micro-QR "hits" inside an ordinary QR's modules, which are noise.
    """
    try:
        import zxingcpp
        from PIL import Image, ImageOps
    except ImportError as error:
        raise QrDecoderUnavailable(str(error)) from error

    try:
        # Phones store the picture sideways and record the turn in EXIF.
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    except Exception:  # noqa: BLE001 - not an image we can open: nothing to read
        _logger.debug("Not a readable image", exc_info=True)
        return [], False

    results = zxingcpp.read_barcodes(
        image,
        formats=zxingcpp.BarcodeFormat.QRCode,
        try_rotate=True,
        try_downscale=True,
        return_errors=True,
    )
    readable = [r for r in results if r.valid and r.text]
    readable.sort(key=lambda r: (r.position.top_left.y, r.position.top_left.x))
    payloads = []
    for result in readable:
        if result.text not in payloads:
            payloads.append(result.text)
    unreadable = any(not r.valid for r in results)
    return payloads, unreadable
