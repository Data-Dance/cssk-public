from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """CZ tax-authority seed data moved out of shared core into l10n_cz_statutory.
    Remove the old core-owned records (they are noupdate=1, so the normal data
    vacuum skips them). On a SK DB this also clears the CZ offices that core used
    to load there by mistake; on a CZ DB l10n_cz_statutory reseeds them."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    imd = env["ir.model.data"].search([
        ("module", "=", "l10n_cssk_core"),
        ("model", "=", "cssk.tax.authority"),
        ("name", "like", "cz_ufo_%"),
    ])
    offices = env["cssk.tax.authority"].browse(imd.mapped("res_id")).exists()
    partners = offices.mapped("partner_id")
    imd.unlink()
    offices.unlink()
    partners.filtered(lambda p: not p.parent_id and p.is_company).unlink()
