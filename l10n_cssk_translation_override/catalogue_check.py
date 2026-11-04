# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Check override catalogues against the target modules' own templates.

Pure Python (polib, plus lxml for the target's XML), so it runs both inside the module's tests and from
``tools/check_translation_overrides.py`` with no database.

An override that no longer matches its target fails SILENTLY at runtime: the
importer finds no record (renamed xmlid) or no term (changed source text), and
Odoo's text stays on screen. This check is what turns that into an error.
"""

import glob
import os
import re

import polib

CODE_COMMENTS = ("odoo-python", "odoo-javascript")
LANG_FILES = {"sk.po": "sk_SK", "cs.po": "cs_CZ"}


def target_templates(module_path, module_name):
    """The catalogue that defines the target's terms: its .pot, else any .po."""
    pot = os.path.join(module_path, "i18n", module_name + ".pot")
    if os.path.isfile(pot):
        return [pot]
    return sorted(glob.glob(os.path.join(module_path, "i18n", "*.po")))


def _index(paths):
    """{msgid: (set of occurrences, set of extracted comments)} over *paths*."""
    index = {}
    for path in paths:
        for entry in polib.pofile(path):
            if entry.obsolete or not entry.msgid:
                continue
            occ, com = index.setdefault(entry.msgid, (set(), set()))
            occ.update(o for o, _line in entry.occurrences)
            com.update(c.strip() for c in entry.comment.splitlines())
    return index


RECORD_OCC = re.compile(r"^model:([\w.]+),(\w+):(\w+\.[\w.]+)$")


def redefined_records(module_path, module_name):
    """{(model, field, xmlid): english} for the records of OTHER modules that
    *module_name*'s XML files rename in English.

    Odoo exports such a value under the renaming module's own name
    (``account_usability.menu_finance`` for ``account.menu_finance``), an
    xmlid that does not exist, so the target's template can never translate
    it. An override entry may target the real xmlid instead; this is what it
    is checked against.
    """
    from lxml import etree

    found = {}
    for root, dirs, files in os.walk(module_path):
        dirs[:] = [d for d in dirs if d not in ("static", "tests", "i18n", "migrations")]
        for fname in files:
            if not fname.endswith(".xml"):
                continue
            try:
                tree = etree.parse(os.path.join(root, fname))
            except etree.XMLSyntaxError:
                continue
            for rec in tree.iter("record", "menuitem"):
                xmlid = rec.get("id") or ""
                if "." not in xmlid or xmlid.split(".", 1)[0] == module_name:
                    continue
                if rec.tag == "menuitem":
                    if rec.get("name"):
                        found[("ir.ui.menu", "name", xmlid)] = rec.get("name")
                    continue
                for field in rec.iter("field"):
                    if field.get("ref") or field.get("eval") or len(field) or not (field.text or "").strip():
                        continue
                    found[(rec.get("model"), field.get("name"), xmlid)] = field.text.strip()
    return found


def _is_redefined(occ, msgid, redefined):
    m = RECORD_OCC.match(occ)
    return bool(m) and redefined.get(m.groups()) == msgid


def check_catalogue(path, find_module):
    """Return (problems, checked) for one override file.

    *find_module(name)* returns the target's directory or None. A target that
    cannot be found is reported as a problem only by the caller's choice, via
    the returned ``checked`` flag being False.
    """
    problems = []
    target = os.path.basename(os.path.dirname(path))
    fname = os.path.basename(path)
    po = polib.pofile(path)
    if fname not in LANG_FILES:
        problems.append(f"{path}: file name must be one of {sorted(LANG_FILES)}")
    lang = po.metadata.get("Language")
    if fname in LANG_FILES and lang not in (LANG_FILES[fname], LANG_FILES[fname][:2]):
        problems.append(f"{path}: Language header {lang!r}, expected {LANG_FILES[fname]}")
    module_path = find_module(target)
    index = _index(target_templates(module_path, target)) if module_path else None
    redefined = redefined_records(module_path, target) if module_path else {}
    for entry in po:
        if entry.obsolete:
            continue
        where = f"{path}:{entry.linenum} {entry.msgid[:50]!r}"
        modules = re.findall(r"^module[s]?: (\w+)", entry.comment, re.M)
        if modules != [target]:
            problems.append(f"{where}: needs exactly '#. module: {target}'")
        if not entry.msgstr:
            problems.append(f"{where}: empty msgstr")
        if "fuzzy" in entry.flags:
            problems.append(f"{where}: fuzzy (Odoo would load it as live text)")
        if not entry.occurrences:
            problems.append(f"{where}: no occurrence line")
        is_code = any(o.startswith("code:") for o, _l in entry.occurrences)
        comments = {c.strip() for c in entry.comment.splitlines()}
        if is_code and not comments & set(CODE_COMMENTS):
            problems.append(f"{where}: code term without '#. odoo-python' / "
                            f"'#. odoo-javascript' is never loaded")
        if index is None:
            continue
        if entry.occurrences and all(_is_redefined(o, entry.msgid, redefined) for o, _l in entry.occurrences):
            continue  # a record another module defines, renamed in English by the target
        known = index.get(entry.msgid)
        if not known:
            problems.append(f"{where}: msgid not in {target}'s template (stale or mistyped)")
            continue
        occurrences, target_comments = known
        for occ, _line in entry.occurrences:
            if occ not in occurrences and not _is_redefined(occ, entry.msgid, redefined):
                problems.append(f"{where}: occurrence {occ} not in {target}'s template")
        # Adding the marker a stale template lacks is fine (and necessary);
        # claiming the OTHER kind of code term is not.
        for c, other in (CODE_COMMENTS, CODE_COMMENTS[::-1]):
            if c in comments and other in target_comments and c not in target_comments:
                problems.append(f"{where}: '{c}' but the target's term is '{other}'")
    return problems, index is not None


def shipped_catalogues(root):
    return sorted(glob.glob(os.path.join(root, "*", "*.po")))
