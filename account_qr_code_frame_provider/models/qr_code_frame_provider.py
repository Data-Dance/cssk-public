# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import io

import qrcode
from odoo import api, models
from odoo.tools.image import image_data_uri
from PIL import Image
from qrcode.image import pil


class FrameProvider(models.Model):
    _inherit = "res.partner.bank"

    def _get_qr_code_base64(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        res = super()._get_qr_code_base64(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )

        params = self._get_qr_code_frame_generation_params(qr_method)
        if params is None:
            return res

        back_color = "transparent"
        fill_color = "black"

        frame = params["frame"]
        if frame:
            frame = frame.resize(params["frame_size"])

        qr = qrcode.QRCode(
            box_size=params["box_size"],
            border=params["border"],
            image_factory=pil.PilImage,
        )
        data = self._get_qr_code_generation_params(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )
        qr.add_data(data["value"])
        qr.make()

        qr_image = qr.make_image(
            fill_color=fill_color,
            back_color=back_color,
            image_factory=pil.PilImage,
        )

        qr_image = qr_image.resize(params["resize_values"], Image.LANCZOS)

        x, y = params["x_y"]
        result = Image.new("RGBA", params["frame_size"])
        if frame:
            result.paste(frame, (0, 0))
        result.paste(qr_image, (x, y))

        buffered = io.BytesIO()
        result.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        return image_data_uri(img_str)

    def _get_qr_code_frame_generation_params(self, qr_method):
        """Hook for extension"""
        return None
