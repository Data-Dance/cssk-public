# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

TOKEN_READ = "r" * 64
TOKEN_WRITE = "w" * 64


class FioCommon(AccountTestInvoicingCommon):
    """A company with a Fio journal and a configured connection."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # The Fio orders in these tests are in CZK, and a currency that is not
        # active cannot be posted to ("You cannot validate a document with an
        # inactive currency"). The demo/validation databases these run against
        # need not have it on.
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.sudo().active = True
        cls.fio_bank = cls.env["res.bank"].sudo().create(
            {"name": "Fio banka, a.s.", "bic": "FIOBCZPP"}
        )
        cls.company_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ8020100000002111111111",
            "partner_id": cls.company.partner_id.id,
            "bank_id": cls.fio_bank.id,
            "company_id": cls.company.id,
        })
        cls.journal = cls.env["account.journal"].sudo().create({
            "name": "Fio", "type": "bank", "code": "FIOBK",
            "company_id": cls.company.id,
            "bank_account_id": cls.company_bank.id,
            # A Fio CZ account is kept in CZK, and the canned responses say so.
            # AccountTestInvoicingCommon's company is in USD, so without this
            # the journal and the bank genuinely disagree — which is exactly
            # what _fio_check_account_matches is there to refuse.
            "currency_id": cls.czk.id,
            # The tokens live on the journal: Fio binds one token to one
            # account, and the journal is Odoo's one record per bank account.
            "fio_token_read": TOKEN_READ,
            "fio_token_write": TOKEN_WRITE,
        })
        cls.supplier = cls.env["res.partner"].create({
            "name": "Dodavatel s.r.o.",
            "street": "Krátká 1",
            "city": "Praha",
            "country_id": cls.env.ref("base.cz").id,
        })
        cls.supplier_bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "2222233333/2010",
            "partner_id": cls.supplier.id,
            "company_id": cls.company.id,
            # Odoo refuses to batch a payment to an account that has not been
            # cleared for outgoing money ("Some recipient accounts do not allow
            # out payments"). A supplier account we are about to pay has been.
            "allow_out_payment": True,
        })
