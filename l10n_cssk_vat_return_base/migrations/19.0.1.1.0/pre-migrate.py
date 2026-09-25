from odoo import SUPERUSER_ID, api

_TABLE = "cssk_vat_return_version"


def migrate(cr, version):
    """xml_template_ref (Char xmlid) -> xml_template_ref_id (Many2one ir.ui.view).
    Resolve each existing version's template xmlid to its view and store the id
    before the new required FK is enforced."""
    if not version:
        return
    cr.execute("""SELECT 1 FROM information_schema.columns
                  WHERE table_name = %s AND column_name = 'xml_template_ref'""",
               (_TABLE,))
    if not cr.fetchone():
        return  # legacy Char column already gone
    cr.execute("""SELECT 1 FROM information_schema.columns
                  WHERE table_name = %s AND column_name = 'xml_template_ref_id'""",
               (_TABLE,))
    if not cr.fetchone():
        cr.execute("ALTER TABLE %s ADD COLUMN xml_template_ref_id integer" % _TABLE)
    cr.execute("SELECT id, xml_template_ref FROM %s "
               "WHERE xml_template_ref_id IS NULL AND xml_template_ref IS NOT NULL"
               % _TABLE)
    rows = cr.fetchall()
    if not rows:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for vid, xmlid in rows:
        view = env.ref(xmlid, raise_if_not_found=False)
        if view:
            cr.execute("UPDATE %s SET xml_template_ref_id = %%s WHERE id = %%s"
                       % _TABLE, (view.id, vid))
