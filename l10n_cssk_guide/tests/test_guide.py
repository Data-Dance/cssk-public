# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import re
import tempfile

from odoo.modules.module import Manifest, get_module_path
from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.l10n_cssk_guide.controllers.main import guide_pages, read_page


@tagged("post_install", "-at_install")
class TestGuidePage(HttpCase):

    def setUp(self):
        super().setUp()
        self.authenticate("admin", "admin")

    def get(self, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        response = self.url_open(f"/cssk/guide?{query}")
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_lists_installed_core_under_its_topic(self):
        text = self.get(lang="en", country="all")
        self.assertIn("<h1>Czech and Slovak Localization — User Guide</h1>", text)
        self.assertIn('id="start"', text)
        # l10n_cssk_core's row (the start page links it too), marked installed
        row = re.search(r'<tr data-country="both">\s*<td>\s*<a [^>]*'
                        r'/l10n_cssk_core/static/description/index.html.*?</tr>',
                        text, re.S)
        self.assertTrue(row, "no row for l10n_cssk_core")
        self.assertIn('class="cssk-state cssk-on"', row.group(0))
        # with its technical name and the version on disk
        self.assertIn("<code>l10n_cssk_core</code>", row.group(0))
        version = Manifest.for_addon("l10n_cssk_core").version
        self.assertIn(f'<td class="cssk-version">{version}</td>', row.group(0))
        # and a module that is on disk but not installed is listed as such
        if get_module_path("l10n_cz_kh", display_warning=False):
            row = re.search(r'<tr data-country="cz">\s*<td>\s*<a [^>]*'
                            r'/l10n_cz_kh/static/description/index.html.*?</tr>',
                            text, re.S)
            self.assertTrue(row, "no row for l10n_cz_kh")
            self.assertNotIn("cssk-on", row.group(0))
        # every topic of guide/topics.yaml is a heading
        for key in ("start", "vat", "statements", "partners", "banking",
                    "edi", "assets", "pos", "payroll"):
            self.assertIn(f'id="{key}"', text)

    def test_country_filter(self):
        if not (get_module_path("l10n_cz_base", display_warning=False)
                and get_module_path("l10n_sk_base", display_warning=False)):
            self.skipTest("needs both country bases on the addons path")
        czech = self.get(lang="en", country="cz")
        slovak = self.get(lang="en", country="sk")
        both = self.get(lang="en", country="all")
        self.assertIn("/l10n_cz_base/static/description/", czech)
        self.assertNotIn("/l10n_sk_base/static/description/", czech)
        self.assertIn("/l10n_sk_base/static/description/", slovak)
        self.assertNotIn("/l10n_cz_base/static/description/", slovak)
        # shared modules are shown either way
        for text in (czech, slovak, both):
            self.assertIn("/l10n_cssk_core/static/description/", text)

    def test_language(self):
        slovak = self.get(lang="sk", country="all")
        self.assertIn('lang="sk"', slovak)
        self.assertIn("Prvé kroky", slovak)
        # a module documented in Slovak links its Slovak page
        self.assertIn("/l10n_cssk_core/static/description/index_sk.html", slovak)
        czech = self.get(lang="cs", country="cz")
        self.assertIn("První kroky", czech)
        self.assertIn("/l10n_cssk_core/static/description/index_cs.html", czech)

    def test_defaults_follow_company_country(self):
        self.env.company.country_id = self.env.ref("base.sk")
        text = self.get()
        self.assertIn('lang="en"', text)
        self.assertNotIn("/l10n_cz_base/static/description/", text)

    def test_not_for_portal_users(self):
        portal = self.env["res.users"].create({
            "name": "Guide Portal", "login": "guide_portal",
            "password": "guide_portal_pw",
            "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
        })
        self.assertFalse(portal._is_internal())
        self.authenticate("guide_portal", "guide_portal_pw")
        response = self.url_open("/cssk/guide")
        self.assertEqual(response.status_code, 404)

    def test_needs_login(self):
        self.logout()
        response = self.url_open("/cssk/guide", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("/web/login", response.headers["Location"])


class TestGuideScan(TransactionCase):

    def test_read_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "index.html")
            with open(path, "w", encoding="utf8") as fh:
                fh.write(
                    "<html><head><title>A &amp; B</title>\n"
                    '<meta name="cssk-guide-topic" content="vat">\n'
                    '<meta name="cssk-guide-order" content="7">\n'
                    '<meta name="cssk-guide-country" content="sk">\n'
                    '</head><body><p class="cssk-summary">It &lt;works&gt;</p>')
            self.assertEqual(read_page(path), {
                "topic": "vat", "order": 7, "country": "sk",
                "title": "A & B", "summary": "It <works>"})
            # a page without the stamp is not part of the guide
            with open(path, "w", encoding="utf8") as fh:
                fh.write("<html><head><title>Other</title></head></html>")
            self.assertIsNone(read_page(path))
            # a malformed order does not break the page
            with open(path, "w", encoding="utf8") as fh:
                fh.write('<title>X</title><meta name="cssk-guide-topic" content="vat">'
                         '<meta name="cssk-guide-order" content="first">')
            self.assertEqual(read_page(path)["order"], 0)

    def test_family_pages_are_not_listed(self):
        # a short page of a family carries no topic: only its family's guide
        # is listed. l10n_cssk_guide's own page carries one.
        pages = guide_pages()
        self.assertIn("l10n_cssk_guide", pages)
        self.assertIn("l10n_cssk_core", pages)
        for name, entries in pages.items():
            self.assertIn(entries["en"]["topic"], {
                "start", "vat", "statements", "partners", "banking", "edi",
                "assets", "pos", "payroll"}, name)

    def test_menu(self):
        menu = self.env.ref("l10n_cssk_guide.menu_cssk_guide")
        self.assertEqual(menu.parent_id, self.env.ref("account.menu_finance_configuration"))
        self.assertEqual(menu.action.url, "/cssk/guide")
