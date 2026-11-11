# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from lxml import etree

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBankFeedHeader(TransactionCase):

    def test_the_journal_form_has_the_feed_header(self):
        arch = self.env["account.journal"].get_view(view_type="form")["arch"]
        headers = etree.fromstring(arch).xpath("//header[@name='bank_feed']")
        self.assertEqual(len(headers), 1)
