"""Backfill the rendering language on the noupdate mail templates —
without it a template renders in the SENDING USER's language instead of
the recipient's."""

from odoo import SUPERUSER_ID, api

TEMPLATE_LANGS = {
    "l10n_cssk_leave_expiry_reminder.mail_template_leave_expiry":
        "{{ object.employee_id.user_id.lang or object.employee_id.lang }}",
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, lang_expr in TEMPLATE_LANGS.items():
        template = env.ref(xmlid, raise_if_not_found=False)
        if template and not template.lang:
            template.lang = lang_expr
