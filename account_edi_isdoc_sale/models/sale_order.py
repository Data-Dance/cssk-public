from odoo import _, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ISDOC mandates a document <UUID>; persist the one we generate so a re-exported
    # proforma keeps a stable identifier.
    isdoc_uuid = fields.Char(string="ISDOC UUID", copy=False)

    def _export_isdoc_proforma(self):
        """ Return (xml_bytes, errors) for this order as an ISDOC proforma (DocumentType 4). """
        self.ensure_one()
        return self.env['account.edi.xml.isdoc']._export_order_proforma(self)

    def action_isdoc_download_proforma(self):
        """ Download the order as an ISDOC proforma (Action → Download ISDOC Proforma).

        Kept as the order's attachment ``<name>.isdoc``, replaced on every
        download, so it always matches the order as it now stands. """
        self.ensure_one()
        if self.state == 'cancel':
            raise UserError(_("A cancelled order cannot be exported as an ISDOC proforma."))
        raw, errors = self._export_isdoc_proforma()
        if errors:
            raise UserError("\n".join(sorted(errors)))
        filename = f"{self.name.replace('/', '_')}.isdoc"
        Attachment = self.env['ir.attachment']
        attachment = Attachment.search([
            ('res_model', '=', self._name), ('res_id', '=', self.id), ('name', '=', filename),
        ], limit=1)
        if attachment:
            attachment.write({'raw': raw, 'mimetype': 'application/xml'})
        else:
            attachment = Attachment.create({
                'name': filename, 'raw': raw, 'mimetype': 'application/xml',
                'res_model': self._name, 'res_id': self.id,
            })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'download',
        }
