# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

REPORT = "l10n_cssk_internal_document.action_report_internal_document"


@tagged("post_install", "-at_install")
class TestInternalDocument(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan = cls.env["account.analytic.plan"].create({"name": "Střediska"})
        cls.analytic = cls.env["account.analytic.account"].create({
            "name": "Sklad", "plan_id": cls.plan.id})
        cls.partner = cls.env["res.partner"].create({"name": "Dodavatel s.r.o."})

    def _entry(self, company=None, **values):
        company = company or self.env.company
        journal = self.env["account.journal"].search([
            ("company_id", "=", company.id), ("type", "=", "general")], limit=1)
        accounts = self.env["account.account"].search([
            ("company_ids", "in", company.id),
            ("account_type", "in", ("expense", "liability_current")),
        ])
        expense = accounts.filtered(lambda a: a.account_type == "expense")[:1]
        accrual = accounts.filtered(lambda a: a.account_type == "liability_current")[:1]
        return self.env["account.move"].with_company(company).create(dict({
            "move_type": "entry",
            "journal_id": journal.id,
            "date": "2026-06-30",
            "ref": "Dohadná položka – energie 06/2026",
            "line_ids": [
                Command.create({
                    "account_id": expense.id, "name": "Energie červen",
                    "debit": 1234.5, "partner_id": self.partner.id,
                    "analytic_distribution": {str(self.analytic.id): 100},
                }),
                Command.create({
                    "account_id": accrual.id, "name": "Energie červen",
                    "credit": 1234.5,
                }),
            ],
        }, **values))

    def _html(self, move):
        html, _format = self.env["ir.actions.report"]._render_qweb_html(REPORT, move.ids)
        return html.decode()

    def test_a_czech_entry_prints_the_statutory_requisites(self):
        self.env.company.account_fiscal_country_id = self.env.ref("base.cz")
        move = self._entry()
        move.action_post()
        html = self._html(move)
        for text in ("Interní doklad", move.name, "Obsah účetního případu",
                     "Dohadná položka", "Účastníci účetního případu",
                     "Dodavatel s.r.o.", "Peněžní částka", "Datum vyhotovení",
                     "Datum uskutečnění účetního případu", "Má dáti", "Dal",
                     "Sklad (100 %)",
                     "Podpisový záznam osoby odpovědné za účetní případ",
                     "Podpisový záznam osoby odpovědné za jeho zaúčtování"):
            self.assertIn(text, html)
        self.assertNotIn("NEZAÚČTOVÁNO", html)

    def test_the_person_who_posted_signs_for_the_booking(self):
        poster = self.env["res.users"].create({
            "name": "Účetní Nováková", "login": "novakova",
            "group_ids": [Command.set([self.env.ref("account.group_account_manager").id])],
            "company_id": self.env.company.id, "company_ids": [Command.set(self.env.company.ids)],
        })
        move = self._entry()
        # The test base class disables tracking, which also marks a record
        # created under it as untracked until the next precommit; tracking
        # values are only written at precommit, and the poster is read off one.
        self.env.cr.precommit.run()
        move.with_user(poster).with_context(
            tracking_disable=False, mail_notrack=False).action_post()
        self.env.cr.precommit.run()
        self.assertEqual(move._cssk_internal_document_poster(), poster.partner_id)
        self.assertIn("Účetní Nováková", self._html(move))

    def test_a_draft_says_it_is_not_booked(self):
        self.env.company.account_fiscal_country_id = self.env.ref("base.cz")
        move = self._entry()
        self.assertFalse(move._cssk_internal_document_poster())
        self.assertIn("NEZAÚČTOVÁNO", self._html(move))

    def test_a_slovak_company_prints_the_slovak_wording(self):
        self.env.company.account_fiscal_country_id = self.env.ref("base.sk")
        move = self._entry()
        move.action_post()
        html = self._html(move)
        for text in ("Interný doklad", "Obsah účtovného prípadu", "Peňažná suma",
                     "Dátum vyhotovenia", "Má dať",
                     "Podpisový záznam osoby zodpovednej za jeho zaúčtovanie"):
            self.assertIn(text, html)
        self.assertNotIn("Interní doklad", html)

    def test_the_content_falls_back_to_the_line_labels(self):
        move = self._entry(ref=False)
        self.assertEqual(move._cssk_internal_document_content(), "Energie červen")

    def test_the_amount_is_the_entry_total(self):
        self.assertAlmostEqual(self._entry()._cssk_internal_document_amount(), 1234.5)
