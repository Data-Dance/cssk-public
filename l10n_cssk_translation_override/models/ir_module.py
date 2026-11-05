# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import os
import time

from psycopg2.extras import Json

from odoo import api, models
from odoo.tools import split_every
from odoo.tools.translate import TranslationImporter

from ..overrides import all_override_po_paths, reset_code_translation_cache

_logger = logging.getLogger(__name__)
MODULE = "l10n_cssk_translation_override"


class SourceCheckedImporter(TranslationImporter):
    """Write a record field's translation only where the record's English
    still IS the msgid.

    Odoo's importer writes a plain field translation (a menu, group or
    category name) by xmlid and never looks at the source text. That is wrong
    as soon as another module renames the record in English: OCA
    ``account_usability`` turns ``account.menu_finance`` from "Invoicing" into
    "Accounting", and an entry for "Invoicing" -> "Fakturácia" would put the
    old name back under the new one. So every candidate is kept per source
    text, and at save time the one whose msgid equals the record's current
    ``en_US`` wins; a record with no matching candidate is left as it is.
    Several catalogues may therefore carry the same xmlid (the module that
    defines the record and the module that renames it), in any load order.

    A RENAMED record is one whose xmlid belongs to another module than the
    catalogue's target (``i18n_override/account_usability/`` carrying
    ``account.menu_finance``). Its matching entry is written even when the
    record is ``noupdate`` (``base.module_category_accounting_accounting``
    is): whatever translation it holds was made for the English it had
    before the rename, so keeping it is never right.

    View terms (``model_terms``) need none of this: Odoo already matches
    them term by term against the current English.
    """

    def __init__(self, cr, verbose=True):
        super().__init__(cr, verbose=verbose)
        # {(model, field, xmlid): {lang: {source: translation}}}
        self._cssk_candidates = {}
        # {(model, field, xmlid, lang, source)} that came from a renaming catalogue
        self._cssk_renamed = set()
        # {(model, field, xmlid): current en_US}, filled at save time
        self._cssk_english = {}
        self._cssk_target = None

    def load_file(self, filepath, lang, xmlids=None, module=None):
        # i18n_override/<target>/<lang>.po
        self._cssk_target = os.path.basename(os.path.dirname(filepath))
        try:
            return super().load_file(filepath, lang, xmlids=xmlids, module=module)
        finally:
            self._cssk_target = None

    def _load(self, reader, lang, xmlids=None):
        rows = list(reader)
        for row in rows:
            if row.get("type") != "model" or not row.get("value") or not row.get("src"):
                continue
            # the rows super()._load keeps as plain field translations, no others
            model = self.env.get(row.get("imd_model"))
            field = model._fields.get(row["name"].split(",")[1]) if model is not None else None
            if field is None or field.translate is not True or not field.store:
                continue
            key = (row["imd_model"], row["name"].split(",")[1], f"{row['module']}.{row['imd_name']}")
            self._cssk_candidates.setdefault(key, {}).setdefault(lang, {})[row["src"]] = row["value"]
            if self._cssk_target and row["module"] != self._cssk_target:
                self._cssk_renamed.add((*key, lang, row["src"]))
        return super()._load(iter(rows), lang, xmlids)

    def save(self, overwrite=False, force_overwrite=False):
        self._cssk_keep_matching_sources()
        # Force only where the WINNING entry came from a renaming catalogue: if
        # the renaming module is gone, the record's own entry wins and the
        # usual noupdate rule applies to it.
        renamed = []
        for model, by_field in self.model_translations.items():
            for field, by_xmlid in by_field.items():
                for xmlid, translations in by_xmlid.items():
                    english = self._cssk_english.get((model, field, xmlid))
                    forced = {
                        lang: value for lang, value in translations.items()
                        if (model, field, xmlid, lang, english) in self._cssk_renamed
                    }
                    if forced:
                        renamed.append((model, field, xmlid, forced))
        res = super().save(overwrite=overwrite, force_overwrite=force_overwrite)
        if overwrite or force_overwrite:
            for model, field, xmlid, translations in renamed:
                module, name = xmlid.split(".", 1)
                self.cr.execute(
                    f"""UPDATE "{self.env[model]._table}" m
                           SET "{field}" = m."{field}" || %s::jsonb
                          FROM ir_model_data imd
                         WHERE imd.model = %s AND imd.module = %s AND imd.name = %s
                           AND m.id = imd.res_id""",
                    [Json(translations), model, module, name],
                )
            if renamed:
                self.env.invalidate_all()
        return res

    def _cssk_keep_matching_sources(self):
        cr = self.cr
        for model_name, by_field in self.model_translations.items():
            table = self.env[model_name]._table
            for field_name, by_xmlid in by_field.items():
                if not by_xmlid:
                    continue
                english = {}
                for chunk in split_every(cr.IN_MAX, list(by_xmlid)):
                    cr.execute(
                        f"""SELECT imd.module || '.' || imd.name, m."{field_name}"->>'en_US'
                              FROM ir_model_data imd
                              JOIN "{table}" m ON m.id = imd.res_id
                             WHERE imd.model = %s
                               AND (imd.module, imd.name) IN %s""",
                        [model_name, tuple(tuple(x.split(".", 1)) for x in chunk)],
                    )
                    english.update(cr.fetchall())
                for xmlid in list(by_xmlid):
                    candidates = self._cssk_candidates.get((model_name, field_name, xmlid), {})
                    current = english.get(xmlid)
                    self._cssk_english[(model_name, field_name, xmlid)] = current
                    translations = by_xmlid[xmlid]
                    for lang in list(translations):
                        value = candidates.get(lang, {}).get(current)
                        if value is None:
                            del translations[lang]
                        else:
                            translations[lang] = value
                    if not translations:
                        del by_xmlid[xmlid]


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def _load_module_terms(self, modules, langs, overwrite=False):
        """Re-apply our overrides after every load of module terms.

        Everything that writes translations into the database goes through
        here: installing or upgrading any module (``loading.py`` calls
        ``_update_translations`` per module), activating a language, and
        Settings > Languages with or without "Overwrite Existing Terms". Odoo
        loads a module's catalogue with ``overwrite=False`` by default, so the
        value already in the database wins; ours therefore has to be written
        with ``overwrite=True``, and written again after anything that may
        have replaced it. A target module installed after this one gets its
        overrides when its own terms are loaded.
        """
        super()._load_module_terms(modules, langs, overwrite=overwrite)
        # Installing N modules calls this once per module; re-applying every
        # catalogue each time would parse all of them N times. Only the
        # modules just loaded can have lost an override; our own load (and
        # a language install, which passes every module) applies them all.
        only = None if MODULE in (modules or ()) else set(modules or ())
        self._cssk_apply_translation_overrides(langs, only=only)
        # The catalogues may have changed with the module being loaded; drop
        # this worker's cached code terms so it reads them again. Other
        # workers keep theirs until they restart, as for any Odoo module.
        reset_code_translation_cache()
        # Records created by code (warehouse operation types and routes) get
        # their names here. During a module install the registry is not
        # ready, and the records being named may not exist yet: defer to
        # _register_hook, as account defers its chart translations.
        if self.env.registry.ready:
            self._cssk_translate_code_named_records(langs)
        else:
            pending = getattr(self.env.registry, "_cssk_pending_code_named_langs", set())
            pending.update(langs or ())
            self.env.registry._cssk_pending_code_named_langs = pending

    def _register_hook(self):
        super()._register_hook()
        pending = getattr(self.env.registry, "_cssk_pending_code_named_langs", None)
        if pending:
            del self.env.registry._cssk_pending_code_named_langs
            # Not now: account's own _register_hook runs after this one (its
            # class comes later in the MRO) and only then loads the chart of
            # a new database, creating the journals whose payment methods we
            # name. Just before the commit, every hook has run.
            langs = sorted(pending)
            self.env.cr.precommit.add(
                lambda: self.env["ir.module.module"]._cssk_translate_code_named_records(langs))

    @api.model
    def _cssk_apply_translation_overrides(self, langs, only=None):
        """Write the field / view terms of every override catalogue.

        ``overwrite=True`` and never ``force_overwrite``: records marked
        ``noupdate`` (mail templates and other data a user is expected to edit)
        keep their translation. Entries whose target module, model or xmlid is
        absent are skipped by the importer, so no target is a dependency. A
        record field's entry applies only while the record's English equals
        its msgid (see ``SourceCheckedImporter``).
        """
        started = time.monotonic()
        importer = SourceCheckedImporter(self.env.cr, verbose=False)
        loaded = 0
        for lang in langs or ():
            if lang == "en_US":
                continue
            for path in all_override_po_paths(lang, only=only):
                _logger.debug("loading translation override %s for %s", path, lang)
                importer.load_file(path, lang)
                loaded += 1
        if loaded:
            importer.save(overwrite=True)
            _logger.info("applied %d translation override catalogue(s) for %s in %.2fs",
                         loaded, ", ".join(langs), time.monotonic() - started)
