from odoo import api, fields, models


class CSSKControlStatementVersion(models.Model):
    """A versioned control-statement template (KV DPH / KH DPH).

    Legislative changes ship as a *new version record* + a new QWeb template +
    a new XSD — never as new modules. Each version declares which section codes
    it emits and which concrete model implements each (``section_code_ids``).
    """

    _name = "cssk.control.statement.version"
    _description = "Control Statement Version (KV DPH / KH DPH template)"
    _order = "country_id, valid_from desc"

    name = fields.Char(required=True)  # e.g. "SK KV DPH 2025v1"
    country_id = fields.Many2one("res.country", required=True)
    active = fields.Boolean(default=True)
    valid_from = fields.Date(required=True)
    valid_to = fields.Date()

    section_code_ids = fields.One2many(
        "cssk.control.statement.section.code", "version_id"
    )
    # No ``statement_type_ids`` here any more: the submission types are scoped
    # by country, so a version does not own them. Reach them through
    # ``country_id`` — see ``cssk.control.statement.type``.

    # XML export configuration
    xml_template_ref_id = fields.Many2one(
        "ir.ui.view", string="XML template", required=True,
        domain="[('type', '=', 'qweb')]",
        help="QWeb template (ir.ui.view) that renders this version's "
        "statutory XML.",
    )
    xml_schema_data = fields.Binary(
        attachment=True, help="XSD used to validate the rendered XML."
    )
    xml_schema_filename = fields.Char()
    xml_root_element = fields.Char(
        required=True, help="Expected root element, e.g. 'KVDPH' / 'DPHKH1'."
    )

    # Threshold for the above/below split (B.3.x in SK, A.4/A.5 in CZ)
    threshold_value = fields.Monetary(
        currency_field="threshold_currency_id", required=True
    )
    threshold_currency_id = fields.Many2one("res.currency", required=True)

    allow_monthly = fields.Boolean(default=True)
    allow_quarterly = fields.Boolean(default=True)


class CSSKControlStatementSectionCode(models.Model):
    """Declares a section a version emits and the concrete model implementing
    it. The framework iterates these to populate a statement."""

    _name = "cssk.control.statement.section.code"
    _description = "Control Statement Section Code"
    _order = "version_id, sequence, code"

    version_id = fields.Many2one(
        "cssk.control.statement.version", required=True, ondelete="cascade"
    )
    code = fields.Char(required=True)  # 'A.1', 'A.5', 'B.3.1', 'C', ...
    name = fields.Char(required=True)
    section_model = fields.Char(
        required=True,
        help="Technical model name implementing this section, e.g. "
        "'l10n.sk.kv.dph.section.a1'.",
    )
    aggregation = fields.Selection(
        [
            ("detail", "Per row (above threshold)"),
            ("per_partner", "Aggregated per partner"),
            ("single", "Single aggregated line"),
            ("reconciliation", "Reconciliation lines (fixed)"),
        ],
        required=True,
    )
    threshold_behavior = fields.Selection(
        [
            ("above", "Only rows above threshold"),
            ("below", "Only rows below threshold"),
            ("all", "All rows"),
        ],
        default="all",
    )
    sequence = fields.Integer(default=10)


class CSSKControlStatementType(models.Model):
    """Submission type (riadny / opravný / dodatočný, řádné / opravné / následné).

    **Scoped by COUNTRY, not by version, and that is the whole point of this
    docstring.** The type is a property of the form family: Slovakia files
    R / O / D and Czechia files B / O / E, and neither set has moved.

    It used to hang off ``version_id``, which said the opposite — that a new
    vzor could bring new types — and the data disproved it. The Slovak three
    were declared identically on all four vzory, 2014 through 2025: twelve
    records expressing three facts, none of which changed in eleven years.

    The cost was not theoretical. Grouping a filing list by "Typ výkazu"
    yields one group per type RECORD, so every label repeated once per vzor in
    use — Riadny three times and Dodatočný three times on a 134-filing agenda,
    correct data reading as a duplication bug, and one row worse with every
    new vzor.

    Collapsing it also removes work rather than adding it: the statement only
    ever *domained* its type on the version, never derived the version through
    it, so the domain becomes a country match and nothing else changes.
    ``_is_dodatocne`` and all four report templates read ``fa_xml_value``,
    never the record's identity.

    If a future vzor ever does add a type or change an XML value, that is the
    moment to version them — not before.
    """

    _name = "cssk.control.statement.type"
    _description = "Control Statement Submission Type"
    # ``id`` last so ties are stable: without it two types of one
    # country at the same sequence order differently between reads.
    _order = "country_id, sequence, id"

    country_id = fields.Many2one("res.country", required=True, index=True)
    code = fields.Char(required=True)
    name = fields.Char(required=True)
    fa_xml_value = fields.Char(
        required=True, help="Value emitted in the statutory XML for this type."
    )
    sequence = fields.Integer(default=10)

    @api.model
    def _cssk_collapse_to_one_per_code(self, country, module, xmlid_by_code):
        """Reduce one country's types to a single row per code. Idempotent.

        Called from a COUNTRY module's pre-migration, and the location is the
        whole point. The first attempt ran this from ``l10n_cssk_kv_kh_base``'s
        post-migration and collapsed nothing: the surviving records are created
        by a country module's data file, and a country module DEPENDS on the
        base, so it loads afterwards. A post-migration in a base module cannot
        see records a dependent module has not created yet. It matched no pairs,
        logged "nothing to collapse", and exited 0 — leaving 15 records where
        there had been 12 and every filing on an orphan.

        Running it in the country module's PRE-migration inverts the problem
        instead of fighting it: the survivor is chosen from the rows that
        already exist, given the xmlid the data file is about to declare, and
        the load then UPDATES it rather than inserting a fourth.

        ``xmlid_by_code`` maps a type code to the local id its module declares
        for it. A code that is absent is collapsed but left without an xmlid.
        """
        Data = self.env["ir.model.data"]
        types = self.with_context(active_test=False).search(
            [("country_id", "=", country.id)], order="id")
        # ⚠️ Group to plain ids BEFORE anything is deleted, and re-browse per
        # code. The first version filtered the live `types` recordset inside
        # the loop, so the second iteration read `code` off rows the first had
        # already unlinked and raised MissingError — reliably, on the second
        # code, because the loop deletes as it goes. A recordset held across a
        # delete is stale by definition; ids are not.
        by_code = {}
        for record in types:
            by_code.setdefault(record.code, []).append(record.id)
        kept = removed = remapped = 0
        for code in sorted(by_code):
            same = self.browse(by_code[code]).exists()
            if not same:
                continue
            # Prefer whichever row already bears the xmlid this module
            # declares, and fall back to the oldest. Not cosmetic: on a
            # database that took the broken first attempt there are already
            # rows carrying these xmlids alongside the originals, and choosing
            # by id alone would delete the record an xmlid points at.
            claimed = self.browse()
            name = xmlid_by_code.get(code)
            if name:
                data = Data.search([("module", "=", module),
                                    ("name", "=", name)], limit=1)
                if data and data.res_id in same.ids:
                    claimed = same.filtered(lambda t: t.id == data.res_id)
            survivor = claimed[:1] or same[:1]
            rest = same - survivor
            kept += 1
            if rest:
                # Filings first: a delete before the remap takes them with it.
                moved = self.env["cssk.control.statement"].with_context(
                    active_test=False).search(
                        [("statement_type_id", "in", rest.ids)])
                if moved:
                    moved.statement_type_id = survivor.id
                    remapped += len(moved)
                removed += len(rest)
                rest.unlink()
            if not name:
                continue
            existing = Data.search([("module", "=", module),
                                    ("name", "=", name)], limit=1)
            if existing:
                # Point it at the survivor if it drifted; otherwise nothing to
                # do. Re-running this must be a no-op.
                if existing.res_id != survivor.id:
                    existing.res_id = survivor.id
                continue
            if Data.search_count([
                    ("model", "=", self._name), ("res_id", "=", survivor.id)]):
                continue
            Data.create({
                "module": module, "name": name, "model": self._name,
                "res_id": survivor.id, "noupdate": True,
            })
        return kept, removed, remapped
