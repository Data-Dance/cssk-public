# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Entered supporting facts for the native foreign/minimum-tax credit rows.

These are official-form inputs, not another tax ledger. Accountants retain
the treaty calculation and filed/paid source evidence; the native return owns
the tax, provision and correction lifecycle.
"""

import math

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.addons.l10n_cssk_core.tools import statutory_round


def _amounts(record, names):
    values = [record[name] for name in names]
    if any(
        not math.isfinite(value) or value < 0 or statutory_round(value, 2) != value
        for value in values
    ):
        raise UserError(_("Enter finite, nonnegative credit amounts in whole cents."))
    return values


class DppoTablesEK(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_table_e_ids = fields.One2many(
        "l10n.sk.dppo.table.e.line",
        "return_id",
        copy=True,
        string="Table E - foreign tax credit",
    )
    l10n_sk_table_k_ids = fields.One2many(
        "l10n.sk.dppo.table.k.line",
        "return_id",
        copy=True,
        string="Table K - prior minimum-tax credits",
    )

    def write(self, values):
        if {"l10n_sk_table_e_ids", "l10n_sk_table_k_ids"} & values.keys():
            self._l10n_sk_form_inputs_editable()
        return super().write(values)

    def _l10n_sk_dppo_pdf_supported_annex_rows(self):
        return super()._l10n_sk_dppo_pdf_supported_annex_rows() | {"r710", "r920"}

    def _l10n_sk_table_ek_payload(self, *, compare_row=True):
        self.ensure_one()
        self.check_access("read")
        rows = {line.code: line.value for line in self.line_ids}
        foreign = [
            line._form_payload()
            for line in self.l10n_sk_table_e_ids.sorted(
                lambda line: (line.country_id.code, line.id)
            )
        ]
        e = {}
        if foreign:
            base = max(0, rows.get("r400", 0))
            if not base:
                raise UserError(_("Table E requires a positive native row 400."))
            ordinary = statutory_round(sum(line["base"] for line in foreign), 2)
            hybrid = statutory_round(sum(line["hybrid"] for line in foreign), 2)
            ordinary_rate = min(100, statutory_round(ordinary / base * 100, 2))
            hybrid_rate = min(
                100 - ordinary_rate, statutory_round(hybrid / base * 100, 2)
            )
            ordinary_cap = statutory_round(rows["r700"] * ordinary_rate / 100, 2)
            hybrid_cap = statutory_round(rows["r700"] * hybrid_rate / 100, 2)
            paid = statutory_round(sum(line["tax"] for line in foreign), 2)
            cap = statutory_round(ordinary_cap + hybrid_cap, 2)
            e = {
                "rows": [
                    base,
                    ordinary,
                    ordinary_rate,
                    ordinary_cap,
                    hybrid,
                    hybrid_rate,
                    hybrid_cap,
                    paid,
                    cap,
                    min(paid, cap),
                ],
                "items": foreign,
            }
        credit_e = e["rows"][-1] if e else 0
        # Row 910 depends on the foreign credit. Evaluate its lawful capacity
        # before applying either row, so a combined apply is atomic.
        capacity = max(0, rows.get("r700", 0) - credit_e - rows.get("r810", 0))
        items = [
            line._form_payload()
            for line in self.l10n_sk_table_k_ids.sorted(
                lambda line: (line.date_from, line.date_to, line.id)
            )
        ]
        if len(items) > 4:
            raise UserError(_("The published Table K has four source-period rows."))
        for previous, current in zip(items, items[1:]):
            if previous["date_to"] >= current["date_from"]:
                raise UserError(
                    _("Table K source periods must not overlap or be duplicated.")
                )
        total = statutory_round(sum(line["claimed"] for line in items), 2)
        if self.currency_id.compare_amounts(total, capacity) > 0:
            raise UserError(
                _(
                    "Table K current claims cannot exceed the tax above the current minimum tax."
                )
            )
        if compare_row and (
            self.currency_id.compare_amounts(credit_e, rows.get("r710", 0))
            or self.currency_id.compare_amounts(total, rows.get("r920", 0))
        ):
            raise UserError(
                _("Apply the reviewed Tables E/K and recompute native rows 710/920.")
            )
        return {"table_e": e, "table_k": {"items": items, "total": total}}

    def action_apply_table_ek_credits(self):
        self.ensure_one()
        with self.env.cr.savepoint():
            self._l10n_sk_form_inputs_editable()
            if self.version_id.l10n_sk_dppo_layout != "2026" or not self.line_ids:
                raise UserError(
                    _(
                        "Compute the published paper-form return before applying Tables E/K."
                    )
                )
            data = self._l10n_sk_table_ek_payload(compare_row=False)
            for code, amount in (
                ("r710", data["table_e"].get("rows", [0])[-1]),
                ("r920", data["table_k"]["total"]),
            ):
                self.line_ids.filtered(lambda row: row.code == code).write(
                    {"is_overridden": True, "manual_value": amount}
                )
            self.l10n_sk_form_minimum_credit = bool(data["table_k"]["total"])
            result = self.action_compute_lines()
            self._l10n_sk_table_ek_payload()
            return result

    def action_post_provision(self):
        self.ensure_one()
        if self.version_id.l10n_sk_dppo_layout == "2026":
            self._l10n_sk_table_ek_payload()
        return super().action_post_provision()

    def _l10n_sk_dppo_pdf_annex_payload(self):
        result = super()._l10n_sk_dppo_pdf_annex_payload()
        result.update(self._l10n_sk_table_ek_payload())
        descriptions = [item["note"] for item in result["table_e"].get("items", [])]
        descriptions += [
            item["note"] for item in result["table_k"]["items"] if item["expired"]
        ]
        if descriptions:
            result["notes"] = "\n".join(
                filter(None, [result.get("notes"), *descriptions])
            )
        result["fx_annex"] = "\n".join(
            item["fx_note"]
            for item in result["table_e"].get("items", [])
            if item["fx_note"]
        )
        return result


class DppoTableELine(models.Model):
    _name = "l10n.sk.dppo.table.e.line"
    _description = "DPPO Table E country tax-credit source"
    _inherit = "l10n.sk.dppo.form.input.mixin"
    _check_company_auto = True

    country_id = fields.Many2one("res.country", required=True, string="Foreign country")
    foreign_base = fields.Monetary(
        required=True, string="Eligible foreign net tax base"
    )
    hybrid_base = fields.Monetary(string="Eligible net hybrid income")
    eligible_tax = fields.Monetary(required=True, string="Treaty-eligible tax in EUR")
    tax_currency_id = fields.Many2one(
        "res.currency", required=True, string="Source tax currency"
    )
    source_tax = fields.Float(
        required=True, digits=(16, 2), string="Paid/estimated source tax"
    )
    eur_rate = fields.Float(
        required=True, digits=(16, 8), default=1, string="EUR per source-currency unit"
    )
    fx_evidence = fields.Text(string="Section 31 conversion evidence")
    tax_status = fields.Selection(
        [("paid", "Paid foreign tax"), ("estimated", "Estimate under section 45(2)")],
        required=True,
        default="paid",
        string="Foreign tax source",
    )
    paid_on = fields.Date(string="Foreign tax payment date")
    foreign_date_from = fields.Date(string="Foreign tax-period start")
    foreign_date_to = fields.Date(string="Foreign tax-period end")
    evidence = fields.Text(
        required=True, string="Reviewed income, treaty and tax evidence"
    )

    def _form_payload(self):
        self.ensure_one()
        self.check_access("read")
        base, hybrid, tax, source = _amounts(
            self, ("foreign_base", "hybrid_base", "eligible_tax", "source_tax")
        )
        if (
            not self.country_id
            or self.country_id.code == "SK"
            or not (self.evidence or "").strip()
            or not self.tax_currency_id
        ):
            raise UserError(
                _(
                    "Retain a foreign country and reviewed treaty, net-income and tax evidence for Table E."
                )
            )
        if not math.isfinite(self.eur_rate) or self.eur_rate <= 0:
            raise UserError(_("Enter a positive finite EUR conversion rate."))
        if self.tax_currency_id.name == "EUR":
            if self.eur_rate != 1:
                raise UserError(_("EUR source tax requires a conversion rate of one."))
        elif not (self.fx_evidence or "").strip():
            raise UserError(
                _("Retain the section 31 foreign-tax conversion calculation.")
            )
        converted = statutory_round(source * self.eur_rate, 2)
        if self.currency_id.compare_amounts(tax, converted) > 0:
            raise UserError(
                _("Treaty-eligible tax cannot exceed the converted source tax.")
            )
        if self.tax_status == "paid":
            if not self.paid_on or (
                self.return_id.l10n_sk_form_prepared_on
                and self.paid_on > self.return_id.l10n_sk_form_prepared_on
            ):
                raise UserError(
                    _(
                        "Retain a foreign tax payment date no later than the declaration date."
                    )
                )
        elif self.tax_status == "estimated":
            if (
                not self.foreign_date_from
                or not self.foreign_date_to
                or self.foreign_date_from > self.foreign_date_to
                or (
                    self.foreign_date_from == self.return_id.date_from
                    and self.foreign_date_to == self.return_id.date_to
                )
            ):
                raise UserError(
                    _(
                        "Section 45(2) estimates require a different, evidenced foreign tax period."
                    )
                )
        else:
            raise UserError(_("Review the foreign tax source status."))
        note = _(
            "Table E %(country)s: net base %(base).2f EUR; hybrid %(hybrid).2f EUR; treaty tax %(tax).2f EUR; source %(source).2f %(currency)s (%(status)s).",
            country=self.country_id.code,
            base=base,
            hybrid=hybrid,
            tax=tax,
            source=source,
            currency=self.tax_currency_id.name,
            status=self.tax_status,
        )
        fx_note = ""
        if self.tax_currency_id.name != "EUR":
            fx_note = _(
                "%(country)s — section 31 conversion: %(source).2f %(currency)s × %(rate).8f EUR = %(converted).2f EUR; eligible %(tax).2f EUR. %(evidence)s",
                country=self.country_id.code,
                source=source,
                currency=self.tax_currency_id.name,
                rate=self.eur_rate,
                converted=converted,
                tax=tax,
                evidence=self.fx_evidence,
            )
        return {
            "base": base,
            "hybrid": hybrid,
            "tax": tax,
            "note": note,
            "fx_note": fx_note,
        }


class DppoTableKLine(models.Model):
    _name = "l10n.sk.dppo.table.k.line"
    _description = "DPPO Table K paid minimum-tax source period"
    _inherit = "l10n.sk.dppo.form.input.mixin"
    _check_company_auto = True

    date_from = fields.Date(required=True, string="Source tax-period start")
    date_to = fields.Date(required=True, string="Source tax-period end")
    minimum_tax = fields.Monetary(required=True, string="Original minimum tax")
    credit_amount = fields.Monetary(
        required=True, string="Original positive minimum-tax difference"
    )
    prior_claimed = fields.Monetary(string="Credited in prior periods")
    claimed = fields.Monetary(string="Credit claimed in this return")
    subsequent_period_number = fields.Selection(
        [(str(number), str(number)) for number in range(1, 4)],
        required=True,
        string="Subsequent tax-period ordinal",
        help="Count tax periods, including short periods, rather than calendar years.",
    )
    paid_amount = fields.Monetary(
        required=True, string="Original minimum tax actually paid"
    )
    paid_on = fields.Date(required=True, string="Minimum-tax payment date")
    evidence = fields.Text(
        required=True,
        string="Reviewed filed return, payment and intervening-period evidence",
    )

    def _form_payload(self):
        self.ensure_one()
        self.check_access("read")
        minimum, credit, prior, claimed, paid = _amounts(
            self,
            ("minimum_tax", "credit_amount", "prior_claimed", "claimed", "paid_amount"),
        )
        if (
            not self.date_from
            or not self.date_to
            or self.date_from > self.date_to
            or self.date_to >= self.return_id.date_from
            or self.date_from.year < 2024
        ):
            raise UserError(
                _(
                    "Table K requires a prior, non-overlapping minimum-tax period starting in 2024 or later."
                )
            )
        ordinal = self.subsequent_period_number
        immediately_follows = (self.return_id.date_from - self.date_to).days == 1
        if (
            ordinal not in ("1", "2", "3")
            or immediately_follows != (ordinal == "1")
            or (ordinal == "1" and prior)
        ):
            raise UserError(
                _(
                    "Review the first, second or third subsequent tax period for Table K."
                )
            )
        if (
            not credit
            or credit > minimum
            or paid < minimum
            or self.currency_id.compare_amounts(prior + claimed, credit) > 0
        ):
            raise UserError(
                _(
                    "Table K needs a positive eligible difference, a fully paid original minimum tax and claims within that difference."
                )
            )
        if (
            not self.paid_on
            or self.paid_on < self.date_from
            or (
                self.return_id.l10n_sk_form_prepared_on
                and self.paid_on > self.return_id.l10n_sk_form_prepared_on
            )
            or not (self.evidence or "").strip()
        ):
            raise UserError(
                _(
                    "Retain the filed minimum-tax calculation, actual payment date and intervening-period credit evidence."
                )
            )
        residual = statutory_round(credit - prior - claimed, 2)
        expired = residual if ordinal == "3" else 0
        return {
            "date_from": str(self.date_from),
            "date_to": str(self.date_to),
            "credit": credit,
            "prior": prior,
            "claimed": claimed,
            "remaining": 0 if expired else residual,
            "expired": expired,
            "note": _(
                "Table K %(start)s–%(end)s: %(expired).2f EUR expires after the third subsequent tax period.",
                start=self.date_from,
                end=self.date_to,
                expired=expired,
            ),
        }
