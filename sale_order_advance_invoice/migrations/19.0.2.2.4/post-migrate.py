"""Backfill the rendering language on the noupdate mail templates —
without it a template renders in the SENDING USER's language instead of
the recipient's."""

from odoo import SUPERUSER_ID, api

TEMPLATE_LANGS = {
    "sale_order_advance_invoice.email_template_edi_advance_invoice":
        "{{ object.partner_id.lang }}",
    "sale_order_advance_invoice.mail_template_advance_invoice_confirmation":
        "{{ object.partner_id.lang }}",
    "sale_order_advance_invoice.mail_template_advance_invoice_payment_executed":
        "{{ object.partner_id.lang }}",
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, lang_expr in TEMPLATE_LANGS.items():
        template = env.ref(xmlid, raise_if_not_found=False)
        if template and not template.lang:
            template.lang = lang_expr
