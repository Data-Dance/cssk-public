# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fixtures shared by the country layers' OSS tests.

The base module has no chart and no form of its own, so the scenarios run in
``l10n_cz_oss`` and ``l10n_sk_oss`` on a real chart — core's OSS mapping reads
the chart's domestic taxes and tax groups, and a synthetic chart would test a
mapping nobody runs.
"""

import base64

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class OssReturnCommon(AccountTestInvoicingCommon):

    @classmethod
    def _oss_setup(cls, vat, version_xmlid):
        cls.company = cls.company_data["company"]
        cls.company.vat = vat
        cls.company._map_eu_taxes()
        cls.version = cls.env.ref(version_xmlid)
        cls.eur = cls.env.ref("base.EUR")
        # a database installed without demo data leaves EUR inactive
        cls.eur.active = True
        cls.goods = cls.env["product.product"].create(
            {"name": "OSS goods", "type": "consu"})
        cls.service = cls.env["product.product"].create(
            {"name": "OSS e-service", "type": "service"})

    @classmethod
    def _oss_fpos(cls, country):
        return cls.env["account.fiscal.position"].search([
            ("company_id", "=", cls.company.id),
            ("country_id", "=", country.id),
            ("auto_apply", "=", True),
            ("vat_required", "=", False),
            ("foreign_vat", "=", False),
        ], limit=1)

    @classmethod
    def _oss_tax(cls, country, amount):
        fpos = cls._oss_fpos(country)
        return cls.env["account.tax"].search([
            ("fiscal_position_ids", "in", fpos.ids),
            ("amount", "=", amount),
            ("type_tax_use", "=", "sale"),
        ], limit=1)

    def _consumer(self, country):
        return self.env["res.partner"].create({
            "name": "Consumer %s" % country.code,
            "country_id": country.id,
        })

    def _oss_invoice(self, country, price, rate, day, product=None,
                     currency=None):
        tax = self._oss_tax(country, rate)
        self.assertTrue(tax, "no OSS %s%% tax for %s" % (rate, country.code))
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "company_id": self.company.id,
            "partner_id": self._consumer(country).id,
            "invoice_date": day,
            "date": day,
            # l10n_cz defaults the tax point to TODAY, not the invoice date
            "taxable_supply_date": day,
            "fiscal_position_id": self._oss_fpos(country).id,
            "currency_id": (currency or self.eur).id,
            "invoice_line_ids": [Command.create({
                "product_id": (product or self.goods).id,
                "quantity": 1,
                "price_unit": price,
                "tax_ids": [Command.set(tax.ids)],
            })],
        })
        move.action_post()
        return move

    def _oss_refund(self, invoice, day):
        refund = invoice._reverse_moves([{
            "invoice_date": day, "date": day, "taxable_supply_date": day}])
        refund.action_post()
        return refund

    def _oss_return(self, year, quarter, compute=True):
        ret = self.env["cssk.oss.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "year": year,
            "quarter": str(quarter),
        })
        if compute:
            ret.action_compute_lines()
        return ret

    def _oss_xml(self, ret):
        return etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

    @staticmethod
    def _row(ret, code, rate, supply="goods"):
        return ret.line_ids.filtered(
            lambda ln: ln.member_state_id.code == code
            and abs(ln.vat_rate - rate) < 0.001 and ln.supply_type == supply)
