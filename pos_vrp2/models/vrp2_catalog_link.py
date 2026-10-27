from odoo import api, fields, models


class Vrp2CatalogLink(models.Model):
    """Which VRP2 catalogue entry of which till stands for which Odoo record.

    One row per till and entry. A push updates the entries linked to its own
    till and deletes (categories) or deactivates (products) ONLY the entries
    it created there itself (``created_here``). Everything else on the
    register — entries typed in the VRP2 app, another till's, another
    database's — is left alone. The single ``vrp2_id`` / ``vrp2_code`` on the
    record could not say which till an id belonged to, so a push used to
    delete every remote entry it did not recognise.
    """

    _name = "vrp2.catalog.link"
    _description = "VRP2 catalogue entry of a till"

    config_id = fields.Many2one(
        "pos.config", string="Till", required=True, index=True,
        ondelete="cascade",
    )
    kind = fields.Selection(
        [("category", "Category"), ("service", "Product")],
        required=True,
    )
    res_id = fields.Integer(
        string="Odoo record", required=True, index=True,
        help="pos.category id for a category, product.template id for a "
        "product.",
    )
    remote_ref = fields.Char(
        string="VRP2 reference", required=True,
        help="categoryId for a category, the service code for a product.",
    )
    created_here = fields.Boolean(
        help="Created on the register by a push from this database. Only "
        "such entries are ever deleted or deactivated by a push.",
    )

    _record_uniq = models.Constraint(
        "UNIQUE (config_id, kind, res_id)",
        "An Odoo record is linked to one entry per till.",
    )
    _remote_uniq = models.Constraint(
        "UNIQUE (config_id, kind, remote_ref)",
        "A VRP2 entry is linked to one Odoo record per till.",
    )

    @api.model
    def _for(self, till, kind):
        """``{res_id: link}`` of one till's links of one kind."""
        links = self.search([("config_id", "=", till.id), ("kind", "=", kind)])
        return {link.res_id: link for link in links}
