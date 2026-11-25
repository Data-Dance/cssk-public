# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Věta UZ: the request to hand the závěrka to the sbírka listin (§ 21b)."""

import base64

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from .test_cz_dppo_vykazy import TestCzDppoVykazy

PDF = b"%PDF-1.4 priloha ucetni zaverky"


@tagged("post_install", "-at_install")
class TestCzDppoRegistry(TestCzDppoVykazy):

    def _file(self, name, content=PDF):
        return self.env["ir.attachment"].create(
            {"name": name, "raw": content})

    def _linked_return(self, **vals):
        self._ledger()
        self.company.partner_id.nace_code = "62101"
        bs = self._statement(self.bs_version)
        pl = self._statement(self.pl_version)
        return self._return(l10n_cz_fs_balance_sheet_id=bs.id,
                            l10n_cz_fs_profit_loss_id=pl.id, **vals)

    def _root(self, ret):
        ret.action_export_xml()     # validates against the bundled XSD
        return etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

    def test_no_request_no_record(self):
        root = self._root(self._linked_return())
        self.assertIsNone(root.find(".//VetaUZ"))
        self.assertIsNone(root.find(".//Prilohy"))
        self.assertIsNone(root.find(".//VetaD").get("pril_uz"))

    def test_the_request_states_its_scope(self):
        """§ 21b odst. 3: the filing says in what scope the závěrka goes to
        the rejstříkový soud."""
        notes = self._file("priloha_2025.pdf")
        ret = self._linked_return(
            l10n_cz_registry_request=True,
            l10n_cz_registry_email="ucetni@example.com",
            l10n_cz_uz_not_approved=True,
            l10n_cz_notes_attachment_ids=[(6, 0, notes.ids)])
        root = self._root(ret)
        request = root.find(".//VetaUZ")
        self.assertEqual(dict(request.attrib), {
            "pr11_rozv": "A", "pr11_vzz": "A", "pr11_puz": "A",
            "pr11_ppt": "N", "pr11_pzvk": "N", "pr11_uzmus": "N",
            "pr11_email": "ucetni@example.com"})
        head = root.find(".//VetaD")
        self.assertEqual(head.get("pril_uz"), "1")
        self.assertEqual(head.get("neschval_uz"), "A")
        self.assertIsNone(head.get("neaudit_uz"))
        self.assertIsNone(head.get("p_ptok"))
        files = root.findall(".//Prilohy/PredepsanaPriloha")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].get("kod"), "PP_OPISPUV")
        self.assertEqual(files[0].get("cislo"), "1")
        self.assertEqual(files[0].get("jm_souboru"), "priloha_2025.pdf")
        self.assertEqual(files[0].get("kodovani"), "base64")
        self.assertEqual(base64.b64decode(files[0].text), PDF)
        # the request sits after the výkazy and before the files
        tags = [el.tag for el in root.find("DPPDP9")]
        self.assertLess(tags.index("VetaUD"), tags.index("VetaUZ"))
        self.assertEqual(tags[-1], "Prilohy")

    def test_a_small_unit_leaves_the_vzz_out(self):
        ret = self._linked_return(l10n_cz_registry_request=True,
                                  l10n_cz_registry_profit_loss=False)
        request = self._root(ret).find(".//VetaUZ")
        self.assertEqual(request.get("pr11_rozv"), "A")
        self.assertEqual(request.get("pr11_vzz"), "N")
        self.assertIsNone(request.get("pr11_email"))

    def test_files_are_numbered_across_kinds(self):
        ret = self._linked_return(
            l10n_cz_registry_request=True,
            l10n_cz_notes_attachment_ids=[(6, 0, self._file("p.pdf").ids)],
            l10n_cz_cash_flow_attachment_ids=[
                (6, 0, self._file("cf.xlsx", b"PK cash").ids)],
            l10n_cz_equity_attachment_ids=[
                (6, 0, (self._file("e1.pdf") + self._file("e2.pdf")).ids)])
        root = self._root(ret)
        files = root.findall(".//Prilohy/PredepsanaPriloha")
        self.assertEqual([f.get("cislo") for f in files],
                         ["1", "2", "3", "4"])
        self.assertEqual([f.get("kod") for f in files],
                         ["PP_OPISPUV", "PP_PTOK", "PP_ZVKAP", "PP_ZVKAP"])
        head = root.find(".//VetaD")
        self.assertEqual((head.get("pril_uz"), head.get("p_ptok"),
                          head.get("p_zvkap")), ("1", "1", "2"))
        request = root.find(".//VetaUZ")
        self.assertEqual((request.get("pr11_ppt"), request.get("pr11_pzvk")),
                         ("A", "A"))

    def test_the_files_go_without_a_request_too(self):
        """The příloha is part of the závěrka attached to the return (§ 18)
        whether or not the registry is asked."""
        ret = self._linked_return(
            l10n_cz_notes_attachment_ids=[(6, 0, self._file("p.pdf").ids)])
        root = self._root(ret)
        self.assertIsNone(root.find(".//VetaUZ"))
        self.assertEqual(len(root.findall(".//PredepsanaPriloha")), 1)
        self.assertEqual(root.find(".//VetaD").get("pril_uz"), "1")

    def test_a_request_needs_the_statements_it_names(self):
        ret = self._return(l10n_cz_registry_request=True)
        with self.assertRaisesRegex(UserError, "no statements are linked"):
            ret.action_export_xml()

    def test_a_request_for_nothing_is_refused(self):
        ret = self._linked_return(l10n_cz_registry_request=True,
                                  l10n_cz_registry_balance_sheet=False,
                                  l10n_cz_registry_profit_loss=False)
        with self.assertRaisesRegex(UserError, "names nothing"):
            ret.action_export_xml()

    def test_a_bad_email_is_refused(self):
        ret = self._linked_return(l10n_cz_registry_request=True,
                                  l10n_cz_registry_email="ucetni(at)firma")
        with self.assertRaisesRegex(UserError, "not a valid e-mail"):
            ret.action_export_xml()

    def test_a_file_type_epo_does_not_take_is_refused(self):
        ret = self._linked_return(
            l10n_cz_notes_attachment_ids=[
                (6, 0, self._file("priloha.odt").ids)])
        with self.assertRaisesRegex(UserError, "cannot be filed"):
            ret.action_export_xml()

    def test_the_size_limit_is_checked(self):
        big = self._file("big.pdf", b"x" * 1024)
        ret = self._linked_return(
            l10n_cz_notes_attachment_ids=[(6, 0, big.ids)])
        self.patch(type(ret), "_L10N_CZ_E_PRILOHA_LIMIT", 1000)
        with self.assertRaisesRegex(UserError, "10 240 kB"):
            ret.action_export_xml()

    def test_a_missing_priloha_is_said_not_refused(self):
        ret = self._linked_return(l10n_cz_registry_request=True)
        before = len(ret.message_ids)
        ret.action_export_xml()
        self.assertGreater(len(ret.message_ids), before)

    def test_uploaded_files_are_bound_to_the_return(self):
        """The widget uploads with no record; such a file is readable by
        its uploader only."""
        loose = self.env["ir.attachment"].create({
            "name": "p.pdf", "raw": PDF,
            "res_model": "cssk.income.tax.return", "res_id": 0})
        ret = self._return()
        ret.l10n_cz_notes_attachment_ids = [(4, loose.id)]
        self.assertEqual(loose.res_id, ret.id)
        self.assertEqual(loose.res_model, "cssk.income.tax.return")

    def test_another_user_s_loose_file_is_not_adopted(self):
        """Binding runs with sudo; it must not hand a colleague's unbound
        upload to whoever writes its id into the field."""
        other = self.env["res.users"].create({
            "name": "Other", "login": "other-dppo",
            "group_ids": [(6, 0, self.env.ref("base.group_user").ids)]})
        loose = self.env["ir.attachment"].with_user(other).create({
            "name": "secret.pdf", "raw": PDF})
        ret = self._return()
        ret.l10n_cz_notes_attachment_ids = [(4, loose.id)]
        self.assertFalse(loose.sudo().res_id)

    def test_the_file_name_is_a_bare_name(self):
        ret = self._linked_return(l10n_cz_notes_attachment_ids=[
            (6, 0, self._file("C:\\zaverka\\pri\tloha.pdf").ids)])
        priloha = self._root(ret).find(".//PredepsanaPriloha")
        self.assertEqual(priloha.get("jm_souboru"), "priloha.pdf")

    def test_a_copy_does_not_carry_the_files(self):
        ret = self._return(
            l10n_cz_notes_attachment_ids=[(6, 0, self._file("p.pdf").ids)])
        self.assertFalse(ret.copy().l10n_cz_notes_attachment_ids)
