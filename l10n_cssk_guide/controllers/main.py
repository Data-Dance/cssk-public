# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import html
import json
import os
import re
from urllib.parse import urlencode

from markupsafe import Markup

import odoo.addons
from odoo import http
from odoo.http import request
from odoo.modules.module import Manifest
from odoo.tools.misc import file_open

FILENAME = {"en": "index.html", "sk": "index_sk.html", "cs": "index_cs.html"}
COUNTRIES = ("all", "cz", "sk")

# tools/gen_module_docs.py stamps a guide page's <head> with these; a page
# without a topic is not part of the guide (another vendor's, or a short page
# of a family, reached from the family's guide).
META_RE = re.compile(r'<meta name="cssk-guide-(topic|order|country)" content="([^"]*)">')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
SUMMARY_RE = re.compile(r'<p class="cssk-summary">(.*?)</p>', re.S)
# The stamp, the title and the summary all sit before the facts table.
HEAD_BYTES = 16384

# Pages per addons path. What is on disk changes only with a restart (a
# module copied into a running server is not served until then either).
_PAGES = {}


def read_page(path):
    """The guide entry of one generated page, or None when it is not one."""
    with open(path, encoding="utf8") as fh:
        head = fh.read(HEAD_BYTES)
    meta = dict(META_RE.findall(head))
    if "topic" not in meta:
        return None
    title = TITLE_RE.search(head)
    summary = SUMMARY_RE.search(head)
    try:
        order = int(meta.get("order") or 0)
    except ValueError:
        # one hand-edited page must not take the whole guide down
        order = 0
    return {
        "topic": meta["topic"],
        "order": order,
        "country": meta.get("country") or "both",
        "title": html.unescape(title.group(1)) if title else "",
        "summary": html.unescape(summary.group(1)) if summary else "",
    }


def guide_pages():
    """{module: {lang: entry}} for every guide page on the addons path."""
    key = tuple(odoo.addons.__path__)
    if key not in _PAGES:
        pages = {}
        for manifest in Manifest.all_addon_manifests():
            desc = os.path.join(manifest.path, "static", "description")
            entries = {}
            for lang, fname in FILENAME.items():
                path = os.path.join(desc, fname)
                if os.path.isfile(path):
                    entry = read_page(path)
                    if entry:
                        entry["version"] = manifest.version
                        entries[lang] = entry
            if "en" in entries:
                pages[manifest.name] = entries
        _PAGES[key] = pages
    return _PAGES[key]


def guide_data():
    with file_open("l10n_cssk_guide/data/guide.json") as fh:
        return json.load(fh)


class CsskGuide(http.Controller):

    @http.route("/cssk/guide", type="http", auth="user", readonly=True)
    def guide(self, lang=None, country=None, **kw):
        # auth="user" admits portal users too; the guide is for the back office
        if not request.env.user._is_internal():
            raise request.not_found()
        data = guide_data()
        langs = data["langs"]
        if lang not in langs:
            user_lang = (request.env.user.lang or "")[:2]
            lang = user_lang if user_lang in langs else "en"
        if country not in COUNTRIES:
            code = (request.env.company.country_id.code or "").lower()
            country = code if code in COUNTRIES else "all"
        labels = data["labels"][lang]

        installed = set(request.env["ir.module.module"].sudo().search(
            [("state", "=", "installed")]).mapped("name"))
        by_topic = {}
        for name, entries in guide_pages().items():
            page_lang = lang if lang in entries else "en"
            entry = entries[page_lang]
            if country != "all" and entry["country"] not in (country, "both"):
                continue
            by_topic.setdefault(entries["en"]["topic"], []).append({
                "name": name,
                "title": entry["title"] or name,
                "summary": entry["summary"],
                "country": entry["country"],
                "version": entry["version"],
                "url": f"/{name}/static/description/{FILENAME[page_lang]}",
                "installed": name in installed,
                "order": entries["en"]["order"],
            })
        topics = []
        for topic in data["topics"]:
            rows = sorted(by_topic.get(topic["key"], []),
                          key=lambda r: (not r["installed"], r["order"]))
            topics.append({
                "key": topic["key"],
                "title": topic["title"][lang],
                "intro": topic["intro"][lang],
                "rows": rows,
            })

        def url(**params):
            return "/cssk/guide?" + urlencode(
                {"lang": params.get("lang", lang),
                 "country": params.get("country", country)})

        with file_open(f"l10n_cssk_guide/data/start_{lang}.html") as fh:
            # Generated by tools/gen_module_docs.py from guide/<lang>.md
            start_html = Markup(fh.read())
        return request.render("l10n_cssk_guide.guide_page", {
            "doctype": Markup("<!DOCTYPE html>"),
            # not "lang": the renderer's own key, the user's language
            "guide_lang": lang,
            "start": data["start"][lang],
            "start_html": start_html,
            "labels": labels,
            "topics": topics,
            "lang_links": [(data["lang_names"][code],
                            None if code == lang else url(lang=code))
                           for code in langs],
            "country_links": [(labels[code], url(country=code), code == country)
                              for code in COUNTRIES],
        })
