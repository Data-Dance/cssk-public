import ast

# (model, table) name fields changed translate=True -> False. Odoo 19 does NOT
# reset ir_model_fields.translate nor convert the jsonb column on that change, so
# the column keeps being recreated as jsonb and reads return the raw {'en_US':..}
# dict. Reset the IR flag to non-translatable AND flatten the column to plain text.
PAIRS = [('cssk.fs.statement.line.def', 'cssk_fs_statement_line_def')]


def migrate(cr, version):
    if not version:
        return
    for model, tbl in PAIRS:
        cr.execute("UPDATE ir_model_fields SET translate = NULL "
                   "WHERE model = %s AND name = 'name'", (model,))
        cr.execute("SELECT data_type FROM information_schema.columns "
                   "WHERE table_name = %s AND column_name = 'name'", (tbl,))
        r = cr.fetchone()
        if r and r[0] == "jsonb":
            cr.execute("ALTER TABLE %s ALTER COLUMN name TYPE varchar "
                       "USING name->>'en_US'" % tbl)
    cr.execute("SELECT id, name FROM cssk_fs_statement_line WHERE name LIKE '%en_US%'")
    for lid, nm in cr.fetchall():
        try:
            v = ast.literal_eval(nm)
            if isinstance(v, dict):
                cr.execute("UPDATE cssk_fs_statement_line SET name = %s WHERE id = %s",
                           (v.get("en_US") or next(iter(v.values())), lid))
        except Exception:
            pass
