# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_cz_fu_code = fields.Char(
        string="Tax office code (FÚ)",
        help="1-4 digit numeric code of the locally competent tax office "
        "from the ÚFO register — the annual tax settlement "
        "<VetaD c_ufo_cil> attribute.")
    l10n_cz_vyuctovani_typ_ds = fields.Selection(
        [("F", "F — natural person"),
         ("P", "P — legal entity"),
         ("L", "L — payer's cashier")],
        string="Filing subject type",
        default="P",
        help="Type of the filing subject — the annual tax settlement "
        "<VetaP typ_ds> attribute.")
    l10n_cz_zuj_code = fields.Char(
        related="partner_id.l10n_cz_zuj_code", readonly=False)
    l10n_cz_zuj_name = fields.Char(
        related="partner_id.l10n_cz_zuj_name", readonly=False)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Příloha č. 1 k Vyúčtování (VetaB c_obce_zuj / naz_obce_zuj): employees
    # are counted per municipality of their place of work, identified by the
    # ZÚJ code of the Finanční správa's "Obce ZUJ" register. Kept on the
    # address, so a branch office's work address carries its own.
    l10n_cz_zuj_code = fields.Char(
        string="Municipality code (ZÚJ)", size=6,
        help="6-digit code of the municipality (základní územní jednotka) "
        "this address lies in, from the Finanční správa register Obce ZUJ. "
        "Used in Příloha č. 1 of the annual tax settlement for employees "
        "whose place of work is this address.")
    l10n_cz_zuj_name = fields.Char(
        string="Municipality name (ZÚJ)",
        help="Name of the municipality exactly as in the Obce ZUJ register.")
