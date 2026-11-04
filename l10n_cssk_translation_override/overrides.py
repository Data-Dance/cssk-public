# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Where the override catalogues live, and how code translations reach them.

Layout: ``i18n_override/<target_module>/<lang>.po``, one file per overridden
module and language, in Odoo's own .po format (copy the entry from the target's
.pot, keep its ``#. module:`` and occurrence lines, write our msgstr). One file
serves both kinds of term, because each Odoo loader ignores the other's rows:

* field, selection, menu, action and view terms (``model:`` / ``model_terms:``
  occurrences) are written into the database by ``ir.module.module`` -- see
  ``models/ir_module.py``;
* code terms (``_()``, ``_lt``, JS/OWL; ``code:`` occurrences, with the
  ``#. odoo-python`` / ``#. odoo-javascript`` comment Odoo filters on) never go
  through the database. Odoo reads them from the module's OWN ``i18n/`` folder
  only (``CodeTranslations._get_code_translations``), so the only way in is to
  wrap that function, which is what this file does.
"""

import logging
import os

from odoo.tools import translate
from odoo.tools.misc import file_open
from odoo.tools.translate import CodeTranslations, get_base_langs

_logger = logging.getLogger(__name__)

#: Directories searched for ``<target_module>/<lang>.po``. A list so tests can
#: add a fixture directory; production ships only the first.
OVERRIDE_DIRS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n_override")]


def override_po_paths(module_name, lang):
    """Override catalogues for one module and language, base language first
    (``sk`` then ``sk_SK``), so a regional file wins, as in Odoo's own loader."""
    for root in OVERRIDE_DIRS:
        for base in get_base_langs(lang):
            path = os.path.join(root, module_name, base + ".po")
            if os.path.isfile(path):
                yield path


def all_override_po_paths(lang, only=None):
    """Every override catalogue for *lang*, or only those of the target
    modules in *only*."""
    for root in OVERRIDE_DIRS:
        if not os.path.isdir(root):
            continue
        for module_name in sorted(os.listdir(root)):
            if only is not None and module_name not in only:
                continue
            for base in get_base_langs(lang):
                path = os.path.join(root, module_name, base + ".po")
                if os.path.isfile(path):
                    yield path


def install_code_translation_patch():
    """Merge our catalogues over each module's own code translations.

    Idempotent. The patch is process-wide: ``code_translations`` is one cache
    per server process, keyed by (module, lang) and not by database, so once
    this module is loaded for any database the code terms apply to all of
    them. Odoo never invalidates that cache, so a changed catalogue needs a
    restart; the web client's translation hash follows the content, so
    browsers pick the new terms up by themselves.
    """
    current = CodeTranslations.__dict__["_get_code_translations"].__func__
    if getattr(current, "_cssk_override", False):
        return
    original = current

    def _get_code_translations(module_name, lang, filter_func):
        translations = original(module_name, lang, filter_func)
        for path in override_po_paths(module_name, lang):
            try:
                with file_open(path, mode="rb") as fileobj:
                    translations.update(
                        CodeTranslations._read_code_translations_file(fileobj, filter_func)
                    )
            except OSError:
                _logger.exception("cannot read translation override %s", path)
        return translations

    _get_code_translations._cssk_override = True
    _get_code_translations._cssk_original = original
    CodeTranslations._get_code_translations = staticmethod(_get_code_translations)
    reset_code_translation_cache()


def reset_code_translation_cache():
    """Drop what was cached before the patch (or before a fixture changed)."""
    translate.code_translations.python_translations.clear()
    translate.code_translations.web_translations.clear()
