# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_taxes(self):
        """No VAT on the instalments of a lease that is a supply of goods.

        Under § 8 ods. 1 písm. c) zákona 222/2004 a finančný prenájom whose
        contract passes ownership at the latest with the final instalment is a
        supply of GOODS: the whole VAT falls due ONCE, on the day the asset is
        handed over, from the entire agreed price — and the lessee receives one
        invoice for it. The instalments that follow are repayments of that
        liability, not further supplies.

        The engine assigns taxes from the product and the fiscal position, which
        for the ordinary purchase products used on a lease means the standard
        rate. Left alone, every instalment would carry VAT that was already paid
        and deducted at handover, i.e. the same supply taxed many times over.

        A lease treated as a supply of SERVICES is the opposite case — the
        service is progressively delivered, so each instalment is taxed. That is
        the engine's own behaviour and is left untouched.

        Whether a given contract is one or the other is a judgement recorded on
        the lease: since 1. 1. 2025 the test is economic substance, not the
        wording of the contract (C-164/16 Mercedes-Benz).
        """
        taxes = super()._get_computed_taxes()
        loan = self.move_id.loan_id
        if (
            loan
            and loan.l10n_sk_vat_treatment == "goods"
            and loan.company_id.chart_template == "sk"
        ):
            return self.env["account.tax"]
        return taxes
