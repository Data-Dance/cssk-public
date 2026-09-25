# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A document says which Intrastat declaration reports it.

The reverse drill named the VAT return, the control statement, the EC sales
list and the financial statements, and stayed silent about Intrastat — which
an accountant reads as "no Intrastat obligation on this document" rather than
as "not implemented". Silence and absence look the same.
"""

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestIntrastatFootprint(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde DE", "country_id": cls.env.ref("base.de").id,
            "vat": "DE811907980",
        })

    def _invoice_line(self):
        move = self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0], post=True)
        return move.invoice_line_ids[:1]

    def _computation(self, declaration, line):
        """The link a real declaration generation would leave behind.

        `amount_company_currency` is not-null on the OCA model, so a bare link
        cannot be created — the fixture supplies the figure the generation
        would have computed. Nothing here re-derives eligibility: the point is
        to reproduce the STORED link, which is all the footprint reads.
        """
        return self.env["intrastat.product.computation.line"].create({
            "parent_id": declaration.id,
            "invoice_line_id": line.id,
            "amount_company_currency": abs(line.balance),
        })

    def _declaration(self, declaration_type="dispatches", state="draft"):
        declaration = self.env["intrastat.product.declaration"].create({
            "company_id": self.company.id,
            "year": "2026", "month": "06",
            "declaration_type": declaration_type,
            "action": "replace",
        })
        declaration.state = state
        return declaration

    def test_a_reported_line_names_its_declaration(self):
        """The link is READ from the declaration, not re-derived.

        What puts a line on a declaration is a goods movement across a border,
        decided by the declaration's own generation with the company's
        thresholds and exclusions in hand. Re-deciding it here would be a
        second reader of that question — the mistake three other contributors
        to this footprint made.
        """
        line = self._invoice_line()
        declaration = self._declaration()
        self._computation(declaration, line)
        footprint = line._cssk_statutory_footprint()
        intrastat = [fp for fp in footprint if fp["form"] == "Intrastat"]
        self.assertEqual(len(intrastat), 1, footprint)
        self.assertEqual(intrastat[0]["code"], "2026-06")
        self.assertIn("dispatches", intrastat[0]["name"])

    def test_the_state_is_named_because_draft_and_filed_differ(self):
        """A declaration nobody has sent is not the same answer as a filed one,
        and a footprint that named neither would read identically for both."""
        line = self._invoice_line()
        declaration = self._declaration(state="done")
        self._computation(declaration, line)
        name = [fp for fp in line._cssk_statutory_footprint()
                if fp["form"] == "Intrastat"][0]["name"]
        self.assertNotIn("Draft", name)
        self.assertTrue(name.strip().endswith(("Done", "done")) or "Done" in name,
                        "the declaration's own state label must appear: %s" % name)

    def test_no_declaration_yet_reports_nothing(self):
        """And that is honest rather than a gap.

        A document is not "on an Intrastat declaration" until one exists.
        Saying otherwise would be predicting an obligation rather than
        reporting one, and the drill's job is to report.
        """
        line = self._invoice_line()
        self.assertFalse(
            [fp for fp in line._cssk_statutory_footprint()
             if fp["form"] == "Intrastat"],
            "with no declaration generated there is nothing to report")

    def test_two_declarations_taking_one_line_are_both_named(self):
        """A corrected declaration does not replace the original as an answer.

        The line was reported in one and re-reported in the other, and an
        accountant chasing it needs both — the original is what was filed and
        the revision is what supersedes it.
        """
        line = self._invoice_line()
        first = self._declaration()
        second = self.env["intrastat.product.declaration"].create({
            "company_id": self.company.id,
            "year": "2026", "month": "06",
            "declaration_type": "dispatches",
            "action": "replace", "revision": 2,
        })
        for declaration in (first, second):
            self._computation(declaration, line)
        intrastat = [fp for fp in line._cssk_statutory_footprint()
                     if fp["form"] == "Intrastat"]
        self.assertEqual(len(intrastat), 2, intrastat)
