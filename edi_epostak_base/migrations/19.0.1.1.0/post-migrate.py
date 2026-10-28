"""The ePošťák firm moved from a global parameter to the company.

One account served one company per database until now: the one the inbound
cron ran as. That company gets the firm, so the database behaves as before;
a second company is given its own in its settings. The parameter is left in
place, unread.

Set in SQL deliberately, as in ``edi_grit_base/migrations/19.0.1.2.0``: an ORM
write of a company field goes through ``_set_category_defaults()``, which
``stock_account`` overrides, and on a Method A database mid-upgrade that
raises and takes the upgrade with it.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    firm_id = env["ir.config_parameter"].get_param("epostak.firm_id")
    if not firm_id:
        return
    cron = env.ref("edi_epostak_base.cron_epostak_get_messages",
                   raise_if_not_found=False)
    company = (cron.user_id.company_id if cron else None) or env.ref(
        "base.main_company", raise_if_not_found=False)
    if not company:
        return
    cr.execute(
        "UPDATE res_company SET epostak_firm_id = %s"
        " WHERE id = %s AND COALESCE(epostak_firm_id, '') = ''",
        (firm_id, company.id),
    )
    env.invalidate_all()
