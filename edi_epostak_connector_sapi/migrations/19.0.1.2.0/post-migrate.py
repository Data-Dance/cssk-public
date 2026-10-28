"""The ePošťák credentials moved from global parameters to the company.

One account served one company per database until now: the one the inbound
cron ran as. That company gets the credentials, and the inbound health its
mailbox recorded, so the database behaves as before; a second company is
given its own in its settings. The parameters are left in place, unread.

The company columns are set in SQL deliberately; see
``edi_epostak_base/migrations/19.0.1.1.0``.
"""

from odoo import SUPERUSER_ID, api

PARAMS = {
    "epostak_sandbox_client_id": "epostak.sapi.sandbox.client_id",
    "epostak_sandbox_client_secret": "epostak.sapi.sandbox.client_secret",
    "epostak_prod_client_id": "epostak.sapi.prod.client_id",
    "epostak_prod_client_secret": "epostak.sapi.prod.client_secret",
}

#: Inbound health, now kept per company as "<param>.<company id>".
HEALTH = (
    "epostak.inbound.last_poll",
    "epostak.inbound.last_ok",
    "epostak.inbound.last_error",
    "epostak.inbound.last_count",
    "epostak.inbound.fail_streak",
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"]
    cron = env.ref("edi_epostak_base.cron_epostak_get_messages",
                   raise_if_not_found=False)
    company = (cron.user_id.company_id if cron else None) or env.ref(
        "base.main_company", raise_if_not_found=False)
    if not company:
        return

    for param in HEALTH:
        value = ICP.get_param(param)
        if value and not ICP.get_param("%s.%s" % (param, company.id)):
            ICP.set_param("%s.%s" % (param, company.id), value)

    values = {field: ICP.get_param(param) for field, param in PARAMS.items()}
    values = {field: value for field, value in values.items() if value}
    if not values:
        return
    # The column names are PARAMS' own keys, never anything from the database,
    # so composing the SET clause from them introduces nothing injectable.
    assignments = ", ".join("%s = %%s" % field for field in values)
    cr.execute(
        "UPDATE res_company SET " + assignments
        # A company that already has credentials of its own keeps all of them.
        + " WHERE id = %s"
        " AND COALESCE(epostak_sandbox_client_id, '') = ''"
        " AND COALESCE(epostak_prod_client_id, '') = ''",
        (*values.values(), company.id),
    )
    env.invalidate_all()
