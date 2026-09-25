# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The taxable supply date is reachable from the invoice and bill lists.

The extensions sit on core's BASE views, which is only enough if every primary
child actually inherits them. A core refactor that re-roots one of those children
would drop the column from that list and nothing else would notice, so each list
and search view the menus open is resolved here.
"""
from lxml import etree

from odoo.tests.common import TransactionCase


class TestInvoiceListTaxableSupplyDate(TransactionCase):
    LIST_VIEWS = (
        "account.view_invoice_tree",
        "account.view_out_invoice_tree",
        "account.view_out_credit_note_tree",
        "account.view_in_invoice_tree",
        "account.view_in_invoice_bill_tree",
        "account.view_in_invoice_refund_tree",
    )
    SEARCH_VIEWS = (
        "account.view_account_invoice_filter",
        "account.view_account_bill_filter",
    )

    def _arch(self, xmlid, view_type):
        view = self.env.ref(xmlid)
        arch = self.env["account.move"].get_views([(view.id, view_type)])["views"][view_type]["arch"]
        return etree.fromstring(arch)

    def test_list_views_offer_the_column(self):
        for xmlid in self.LIST_VIEWS:
            with self.subTest(view=xmlid):
                fields = self._arch(xmlid, "list").xpath("//field[@name='taxable_supply_date']")
                self.assertEqual(len(fields), 1)
                self.assertEqual(fields[0].get("optional"), "show")

    def test_search_views_filter_and_group_by_it(self):
        for xmlid in self.SEARCH_VIEWS:
            with self.subTest(view=xmlid):
                arch = self._arch(xmlid, "search")
                self.assertTrue(arch.xpath("//filter[@date='taxable_supply_date']"))
                self.assertTrue(arch.xpath(
                    "//filter[contains(@context, \"'group_by': 'taxable_supply_date'\")]"
                ))
