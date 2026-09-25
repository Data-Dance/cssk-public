# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which partners may be looked up in a company register, and by what.

Pinned because the distinction is invisible in the data: a contact inside a
company carries the company's IČO in exactly the same field the company does,
and the only thing separating them is where that number came from.

The bug this suite exists to prevent, in full: saving a person contact under a
company fired an enrichment with an EMPTY IČO — `company_registry` is in core's
`res.partner._commercial_fields()`, so the parent's number is copied down only
*after* create, which is after the inverse has already run. Finstat answers an
empty number with `HTTP 404 text/plain`, `.json()` raised, a broad `except`
swallowed it, and the user was told "no data returned" — indistinguishable from
a company the register does not hold. It also cost a billed API call each time.

The obvious fix — "only enrich companies" — is wrong, and test_sole_trader is
here to fail if anyone tries it.
"""
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestAutocompleteLookupKey(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.partner"].create({
            "name": "Zlaté Zrnko s.r.o.",
            "is_company": True,
            "company_registry": "50022814",
        })

    def test_a_company_is_looked_up_by_its_own_ico(self):
        self.assertEqual(self.company._autocomplete_lookup_key(), "50022814")

    def test_a_contact_inside_a_company_is_not(self):
        """The reported bug.

        The contact really does carry 50022814 — core copies it down as a
        commercial field — but it is the COMPANY's number, not the person's.
        Looking it up would fetch the company and overwrite the person's name,
        street and VAT with it.
        """
        contact = self.env["res.partner"].create({
            "name": "Jozef Mikulášik",
            "is_company": False,
            "parent_id": self.company.id,
        })
        self.assertEqual(
            contact.company_registry,
            self.company.company_registry,
            "core still syncs company_registry down; if this fails the "
            "premise of the guard has changed, not the guard",
        )
        self.assertEqual(contact._autocomplete_lookup_key(), "")

    def test_sole_trader(self):
        """A živnostník is a PERSON with a real IČO and no parent.

        So the guard cannot be `is_company`: that would silently stop enriching
        every sole trader in the database.
        """
        trader = self.env["res.partner"].create({
            "name": "Marek Topor",
            "is_company": False,
            "company_registry": "44123456",
        })
        self.assertEqual(trader._autocomplete_lookup_key(), "44123456")

    def test_partner_gid_belongs_to_the_record_even_inside_a_company(self):
        """Set only by the autocomplete dropdown, so it is always this record's
        own — and therefore usable where `company_registry` is not."""
        contact = self.env["res.partner"].create({
            "name": "Chosen from the dropdown",
            "is_company": False,
            "parent_id": self.company.id,
            "partner_gid": "36250481",
        })
        self.assertEqual(contact._autocomplete_lookup_key(), "36250481")

    def test_a_partner_with_nothing_to_search_by_is_skipped(self):
        partner = self.env["res.partner"].create({"name": "No number at all"})
        self.assertEqual(partner._autocomplete_lookup_key(), "")

    def test_the_key_is_stripped(self):
        """It is concatenated into a signing hash and posted as a form value;
        a stray space changes the hash and the register rejects the call."""
        self.company.company_registry = "  50022814 "
        self.assertEqual(self.company._autocomplete_lookup_key(), "50022814")


class TestImportEnrichTrigger(TransactionCase):
    """`import_enrich_company` is an import column, and its inverse must stay
    one. Its default puts it into every create, so an unguarded inverse turned
    every new company with an IČO into a register lookup."""

    def _spy_update(self):
        # A plain function, not a MagicMock: 19.0 resolves a field's inverse
        # by method and reads its __name__.
        calls = []

        def _update_partner_info(records):
            calls.append(records)

        return calls, patch.object(
            type(self.env["res.partner"]), "_update_partner_info", _update_partner_info
        )

    def test_saving_a_company_does_not_look_it_up(self):
        calls, spy = self._spy_update()
        with spy:
            self.env["res.partner"].create({
                "name": "Typed by hand s.r.o.",
                "is_company": True,
                "company_registry": "50022814",
            })
        self.assertFalse(calls)

    def test_an_import_column_does(self):
        calls, spy = self._spy_update()
        with spy:
            partner = self.env["res.partner"].create({
                "name": "Imported s.r.o.",
                "import_enrich_company": "50022814",
            })
        self.assertEqual(calls, [partner])
