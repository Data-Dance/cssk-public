# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Translate records whose name Odoo creates from a code message.

Creating a warehouse gives its operation types and routes names such as
``_('Receipts')`` or ``'%s: %s' % (warehouse, _('Receive in 1 step (stock)'))``,
evaluated in the language of whoever created it. On a database set up in
English (a hosted tenant is), those records have an English name only, so a
Slovak or Czech user sees "Receipts" on the Inventory dashboard however
complete the catalogues are: no .po entry points at a record that was made by
code. This fills the missing language from the code translations, ours
included.

Only a language that is missing, or still equal to the English name, is
written, so a name someone translated or changed by hand is kept.
"""

import json
import logging
import re

from odoo import api, models
from odoo.tools.translate import code_translations

_logger = logging.getLogger(__name__)

#: (model, field) pairs that Odoo fills from code messages. Models that are
#: not installed are skipped.
CODE_NAMED_FIELDS = [
    ("stock.picking.type", "name"),
    ("stock.route", "name"),
    ("stock.rule", "name"),
    ("account.journal", "name"),
    ("pos.payment.method", "name"),
    ("account.tax.group", "name"),
]
#: Names no catalogue carries, as (pattern, {lang: replacement}). A chart's
#: tax groups are translated from its own ``name@<lang>`` columns only, so a
#: Czech company's "VAT 21%" has Czech and no Slovak: a Slovak user of a
#: Czech company sees English in every order and invoice total.
NAME_PATTERNS = [
    (re.compile(r"^VAT (\d+(?:[.,]\d+)?) ?%$"), {"sk_SK": r"DPH \1%", "cs_CZ": r"DPH \1%"}),
]
#: (model, field, source) where Odoo copies the source record's translatable
#: field into a plain Char of the same name.
COPIED_NAMES = [
    ("account.payment.method.line", "name", "payment_method_id"),
]
#: "<warehouse or code>: <message>", the shape of warehouse route names.
PREFIXED = re.compile(r"^(?P<prefix>[^:]{1,40}): (?P<term>.+)$")


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def _cssk_code_terms(self, lang):
        """{english: translation} over the Python code terms of every
        installed module, with our overrides merged in by the code patch."""
        installed = self.sudo().search([("state", "=", "installed")]).mapped("name")
        terms = {}
        for module in installed:
            try:
                terms.update(code_translations.get_python_translations(module, lang))
            except Exception:  # noqa: BLE001 - one unreadable catalogue must not stop the rest
                _logger.exception("cannot read code translations of %s for %s", module, lang)
        return {k: v for k, v in terms.items() if v and v != k}

    @api.model
    def _cssk_translate_code_named_records(self, langs=None, fields_list=None):
        """Fill missing translations of code-named records; return the count.

        Written as a jsonb merge rather than through the ORM: when en_US is not
        an active language (a Slovak-only tenant), Odoo writes en_US along with
        any other language, so translating into Slovak would replace the
        English source, and Czech, matched against that source next, would
        never be found. The English name stays the key every language is
        derived from.
        """
        langs = [lang for lang in (langs or [code for code, _n in self.env["res.lang"].get_installed()])
                 if lang != "en_US"]
        if not langs:
            return 0
        terms = {}
        done = 0
        for model_name, field_name in fields_list or CODE_NAMED_FIELDS:
            if model_name not in self.env:
                continue
            Model = self.env[model_name].sudo().with_context(active_test=False)
            field = Model._fields.get(field_name)
            if not field or field.translate is not True or not field.store:
                continue
            for lang in langs:
                if lang not in terms:
                    terms[lang] = self._cssk_code_terms(lang)
            self.env.flush_all()
            self.env.cr.execute(
                f'SELECT id, "{field_name}" FROM "{Model._table}" WHERE "{field_name}" IS NOT NULL'
            )
            updates = []
            for res_id, values in self.env.cr.fetchall():
                en = values.get("en_US")
                if not en:
                    continue
                # Only a genuine English name is matched. A database set up
                # without English stores the creating language in the en_US
                # slot ("Balenie"); mapping that back to an English source is
                # ambiguous (one Slovak word translates several English
                # messages) and produced wrong Czech ("Pack" became "Sada"),
                # so such records keep their name.
                source = en
                new = {}
                for lang in langs:
                    current = values.get(lang)
                    if current and current != en:
                        continue
                    value = terms[lang].get(source)
                    if value is None:
                        for pattern, replacements in NAME_PATTERNS:
                            if lang in replacements and pattern.match(source):
                                value = pattern.sub(replacements[lang], source)
                                break
                    if value is None:
                        match = PREFIXED.match(source)
                        if match and match["term"] in terms[lang]:
                            value = f"{match['prefix']}: {terms[lang][match['term']]}"
                    if value and value != current:
                        new[lang] = value
                if new:
                    updates.append((res_id, new))
            for res_id, new in updates:
                self.env.cr.execute(
                    f'UPDATE "{Model._table}" SET "{field_name}" = "{field_name}" || %s::jsonb WHERE id = %s',
                    (json.dumps(new), res_id),
                )
                done += len(new)
            if updates:
                Model.invalidate_model([field_name])
        done += self._cssk_localize_copied_names(langs)
        if done:
            _logger.info("translated %d code-named record name(s)", done)
        return done

    @api.model
    def _cssk_localize_copied_names(self, langs):
        """Rename untranslatable copies of a translatable name; return the count.

        A journal's payment method line stores ``payment_method_id.name`` in a
        plain Char, copied in the language of whoever created the journal,
        usually English. Every payment's label is built from it ("Manual
        Payment: INV/2026/00001"), so a Slovak company's bank lines read
        English however complete the catalogues are. One value serves the whole
        company, so it follows the company's language. Only a name still equal
        to the source's English is replaced: a name someone chose is kept.
        """
        done = 0
        for model_name, field_name, source_field in COPIED_NAMES:
            if model_name not in self.env:
                continue
            records = self.env[model_name].sudo().with_context(active_test=False).search([])
            for record in records:
                lang = record.company_id.partner_id.lang
                source = record[source_field]
                if not source or lang not in langs:
                    continue
                english = source.with_context(lang="en_US")[field_name]
                local = source.with_context(lang=lang)[field_name]
                if record[field_name] == english and local and local != english:
                    record[field_name] = local
                    done += 1
        return done

    @api.model
    def _cron_cssk_translate_code_named_records(self):
        """Daily: records created since (a new company's warehouse) get theirs too."""
        self._cssk_translate_code_named_records()
