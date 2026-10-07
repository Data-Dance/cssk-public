from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ISDOC mandates a document <UUID>; persist the one we generate so a re-exported
    # proforma keeps a stable identifier.
    isdoc_uuid = fields.Char(string="ISDOC UUID", copy=False)

    def _export_isdoc_proforma(self):
        """ Return (xml_bytes, errors) for this order as an ISDOC proforma (DocumentType 4). """
        self.ensure_one()
        return self.env['account.edi.xml.isdoc']._export_order_proforma(self)
