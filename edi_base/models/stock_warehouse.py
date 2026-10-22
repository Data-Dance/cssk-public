from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    edi_gln = fields.Char(
        string="EDI GLN (Delivery Point)",
        help="Per-warehouse GLN override used as the Delivery Place (DP) "
        "party in outbound EDI messages. Falls back to the company GLN. "
        "Shared by all EDI providers.",
    )
