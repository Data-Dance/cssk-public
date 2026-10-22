from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """``cssk.tax.authority`` is gaining delegation inheritance to ``res.partner``
    (``_inherits``). Existing offices have no partner yet — create one per office
    (carrying its name + country) and link it before the required ``partner_id``
    FK is enforced by the new model definition."""
    if not version:
        return  # fresh install: the seed data creates the partners itself
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'cssk_tax_authority' AND column_name = 'partner_id'
    """)
    if not cr.fetchone():
        cr.execute("ALTER TABLE cssk_tax_authority ADD COLUMN partner_id integer")
    cr.execute("""
        SELECT id, name, country_code FROM cssk_tax_authority
        WHERE partner_id IS NULL
    """)
    rows = cr.fetchall()
    if not rows:
        return
    # Apps installed on this DB (purchase_stock, account) add NOT NULL columns to
    # res_partner whose fields aren't in the registry yet during this
    # pre-migration, so the ORM INSERT omits them. Give those columns a DB-level
    # default so the partner INSERT succeeds (matches each field's Python default).
    for col, default in (("group_rfq", "default"),
                         ("group_on", "default"),
                         ("autopost_bills", "ask")):
        cr.execute("""SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'res_partner' AND column_name = %s
                      AND is_nullable = 'NO' AND column_default IS NULL""", (col,))
        if cr.fetchone():
            cr.execute(
                "ALTER TABLE res_partner ALTER COLUMN %s SET DEFAULT '%s'"
                % (col, default))
    env = api.Environment(cr, SUPERUSER_ID, {})
    for office_id, name, country_code in rows:
        # the old name column was translatable (jsonb {lang: value}); take the
        # source / any available value as the (non-translatable) partner name.
        if isinstance(name, dict):
            name = name.get("en_US") or next(iter(name.values()), None)
        country = env["res.country"].search([("code", "=", country_code)], limit=1)
        partner = env["res.partner"].create({
            "name": name or "Tax office",
            "country_id": country.id,
            "is_company": True,
        })
        cr.execute(
            "UPDATE cssk_tax_authority SET partner_id = %s WHERE id = %s",
            (partner.id, office_id),
        )
