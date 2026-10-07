"""Peppol settings moved from global parameters to the company.

Nothing changes for an existing database: a company whose partner has a
Peppol address could send before and still can (scope "any customer with a
Peppol address"), the auto-send flag applies to every company as it did, and
the purchase journal belongs to its own company. The parameters are left in
place, unread.

The company columns are set in SQL deliberately, and must stay that way.
``res.company.write()`` calls ``_set_category_defaults()``, which
``stock_account`` overrides to write an ``ir.default`` for
``product.category.property_valuation`` taken from the company's
``inventory_valuation``. That value is validated against the field's
selection, and an upgrade builds the registry one module at a time: this
migration runs after ``stock_account`` but before ``stock_account_method_a``,
which is what adds ``perpetual`` to the selection. So on a Method A database
an ORM write of ANY company field raises

    Invalid value for product.category.property_valuation: perpetual

and rolls the whole upgrade back -- after which this migration runs again and
fails again, so retrying never gets anywhere. Setting the columns directly
goes nowhere near that hook. Found on a customer database 2026-10-02 and
reproduced both ways on a scratch database with Method A installed: the ORM
version fails, this one upgrades cleanly and writes the same values. Not
covered by an automated test -- a migration runs outside the test framework
and the failure needs a real partial registry -- so do not "simplify" this
back to the ORM without rebuilding that scratch database.
"""

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"]
    auto_send = (ICP.get_param("peppol.auto_send") or "").lower() not in (
        "", "0", "false")

    # Every company, archived ones included, as the ORM loop did with
    # active_test=False: a column update sees no active filter at all.
    # A correlated subquery rather than UPDATE ... FROM res_partner: the join
    # form skips a company whose partner row is missing, where the ORM loop
    # resolved an empty partner and wrote False. COALESCE keeps that.
    cr.execute(
        """
        UPDATE res_company c
           SET peppol_send_enabled = COALESCE((
                   SELECT COALESCE(p.peppol_eas, '') <> ''
                          AND COALESCE(p.peppol_endpoint, '') <> ''
                     FROM res_partner p
                    WHERE p.id = c.partner_id), FALSE),
               peppol_auto_send = %s
        """,
        (auto_send,),
    )

    journal_id = ICP.get_param("peppol.purchase_journal_id")
    if journal_id and journal_id.isascii() and journal_id.isdigit():
        # No existence check needed: an id that is not a journal joins to no
        # company, and the statement then updates nothing.
        cr.execute(
            """
            UPDATE res_company
               SET peppol_purchase_journal_id = j.id
              FROM account_journal j
             WHERE j.id = %s
               AND j.company_id = res_company.id
            """,
            (int(journal_id),),
        )

    # The ORM has these companies cached from the reads above.
    env.invalidate_all()
