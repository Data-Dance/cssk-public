# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_cssk_payment_symbols.tools import end_to_end_id, remittance_suffix

#: The _prepare_field names the OCA credit transfer generator uses.
END_TO_END_FIELD = "End to End Identification"


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _l10n_cssk_sepa_placement(self):
        """Where this order's transfers carry the symbols, or ``none``."""
        if len(self) != 1 or self.payment_type != "outbound":
            return "none"
        if self.payment_method_id.code != "sepa_credit_transfer":
            return "none"
        return self.journal_id.l10n_cssk_sepa_symbol_placement or "none"

    @staticmethod
    def _l10n_cssk_payment_symbols(payment):
        """VS/KS/SS of one transfer (an ``account.payment`` of the order).

        Its payment lines share their symbols, since they are grouped by them;
        if they ever do not, nothing is written rather than one bill's symbols
        on a transfer that pays several.
        """
        lines = payment.payment_line_ids
        symbols = {}
        for key, field in (
            ("VS", "variable_symbol"),
            ("KS", "constant_symbol"),
            ("SS", "specific_symbol"),
        ):
            values = set(lines.mapped(field)) - {False, ""}
            if len(values) > 1:
                return {}
            if values:
                symbols[key] = values.pop()
        return symbols

    def _prepare_field(
        self, field_name, field_value, eval_ctx, max_size=0, gen_args=None
    ):
        if (
            field_name == END_TO_END_FIELD
            and self._l10n_cssk_sepa_placement() == "end_to_end"
            and eval_ctx.get("line")
        ):
            text = end_to_end_id(self._l10n_cssk_payment_symbols(eval_ctx["line"]))
            if text:
                field_value = repr(text)
        return super()._prepare_field(
            field_name, field_value, eval_ctx, max_size=max_size, gen_args=gen_args
        )

    def generate_remittance_info_block(self, parent_node, line, gen_args):
        res = super().generate_remittance_info_block(parent_node, line, gen_args)
        if self._l10n_cssk_sepa_placement() != "ustrd":
            return res
        suffix = remittance_suffix(self._l10n_cssk_payment_symbols(line))
        if not suffix:
            return res
        remittance = parent_node.findall("RmtInf")
        ustrd = remittance[-1].find("Ustrd") if remittance else None
        if ustrd is None:
            # a structured creditor reference (RF and the like): leave it alone
            return res
        text = (ustrd.text or "").strip() or "PLATBA"
        # Keep the symbols whole: shorten the free text, not the suffix, and
        # let OCA's own sanitizer see the result like any other field.
        ustrd.text = self._prepare_field(
            "Remittance Unstructured Information",
            repr(text[: max(0, 140 - len(suffix))] + suffix),
            {"line": line},
            140,
            gen_args=gen_args,
        )
        return res
