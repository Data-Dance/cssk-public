# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A domain written as a string on a field is evaluated by the web client,
where a many2one is its id and nothing more. ``company_id.partner_id.id`` or
``country_id.code`` on the value side therefore evaluates to nothing, and the
picker raises "Invalid domain representation" the moment it is opened. The
server never evaluates the string, so no install and no ORM test sees it."""

import ast

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

# Names the client does give attributes to.
_DOTTED_OK = {"parent", "context", "datetime", "time", "relativedelta",
              "context_today", "current_date"}
_PREFIXES = ("l10n_cssk", "l10n_sk", "l10n_cz", "nop_", "edi_", "cssk_")


def dotted_values(domain):
    """The ``name.attr`` expressions a domain string dereferences."""
    found = []
    for node in ast.walk(ast.parse(domain.strip(), mode="eval")):
        if not isinstance(node, ast.Attribute):
            continue
        root = node
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(root, ast.Name) and root.id not in _DOTTED_OK:
            found.append(ast.unparse(node))
    return found


@tagged("post_install", "-at_install")
class TestFieldDomains(TransactionCase):

    def test_detector(self):
        self.assertEqual(
            dotted_values("[('country_code', '=', country_id.code)]"),
            ["country_id.code"])
        self.assertFalse(dotted_values(
            "[('partner_id.country_id.code', '=', country_code),"
            " ('company_id', '=', parent.company_id),"
            " ('id', 'in', context.get('ids', []))]"))

    def test_company_pickers_filter_by_fiscal_country(self):
        company = self.env["res.company"].create({
            "name": "SK domain co", "country_id": self.env.ref("base.sk").id})
        self.assertEqual(company.l10n_cssk_fiscal_country_code, "SK")
        for name in ("l10n_cssk_tax_authority_id", "l10n_cssk_person_type_id"):
            self.assertEqual(
                company._fields[name].domain,
                "[('country_code', '=', l10n_cssk_fiscal_country_code)]")

    def test_no_string_domain_dereferences_a_many2one(self):
        bad = []
        for model in self.env.values():
            for name, field in model._fields.items():
                domain = getattr(field, "domain", None)
                if not isinstance(domain, str):
                    continue
                if not (field._module or "").startswith(_PREFIXES):
                    continue
                for expr in dotted_values(domain):
                    bad.append(f"{model._name}.{name}: {expr}")
        self.assertFalse(bad, "\n".join(sorted(set(bad))))
