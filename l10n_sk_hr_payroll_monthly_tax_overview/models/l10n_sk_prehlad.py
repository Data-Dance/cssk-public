# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK Prehľad — o zrazených a odvedených preddavkoch na daň (monthly).

Filed monthly to the Finančná správa (tax administrator) under § 39 ods. 9
zákona 595/2003 Z. z.  Unlike the MVP/social overview, the Prehľad is
**employer-aggregate only** (no per-employee annex) — every figure is a
company-level sum for the reporting month.

Line mapping (from the official PREHLADv-poucenie), amounts summed across the
company's payslips for the period:

======  ==============================================  ======================
Line    Meaning                                          Source (rule codes)
======  ==============================================  ======================
r00     úhrn zúčt. a vypl. zdaniteľných príjmov          Σ GROSS
r01     úhrn zrazených preddavkov na daň (bez bonusu)    Σ INCOMETAX19+25 / INCOMETAX
r04     úhrn r. 1 až 3                                   = r01 (r02, r03 = 0)
r05     daňový bonus § 33 vyplatený                      Σ CHILD_BONUS
r08     odvodová povinnosť (r4 − r5 − r6 − r7)           r01 − CHILD_BONUS
rA/rB   rekapitulácia daňového bonusu § 33               Σ CHILD_BONUS
======  ==============================================  ======================

The monthly income-tax advance is emitted as INCOMETAX19+INCOMETAX25 by the
``hr_payroll`` engine and as a single INCOMETAX line by the ``payroll``
engine; ``_tax_advance`` handles both.  r02/r03 (ročné zúčtovanie corrections),
r06/r07 (zamestnanecká prémia, § 33a úroky bonus) and the III. časť žiadosti
have no monthly rule source and are left empty / zero.
"""
from odoo import _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import sum_concept

# The rule codes carrying the income-tax advance differ per engine (Enterprise
# splits it into 19 %/25 % bands, the OCA engine emits one line). That mapping
# lives once, in the declaration base, rather than being restated here.
# Daňový bonus (§ 33) paid to employees.
BONUS_CODE = "CHILD_BONUS"


class L10nSkPrehlad(models.Model):
    _name = "l10n.sk.prehlad"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK monthly overview of withheld tax advances"
    _order = "date_from desc, id desc"

    _report_code = "sk_prehlad"
    # The FS Prehľad wire format carries a riadny/opravný pair and nothing
    # else — no dodatočný, no storno — so only those two are offered.
    _supported_correction_types = ("regular", "corrective")
    _country_code = "SK"
    _xml_name_fallback = "prehlad"

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_dic(self, company):
        return self._digits(company.l10n_sk_dic)

    def _preflight(self):
        super()._preflight()
        for rec in self:
            dic = rec._company_dic(rec.company_id)
            if not (dic.isdigit() and len(dic) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit DIČ (tax "
                    "identification number) for the monthly tax overview <dic> "
                    "element. Set 'DIČ' on the company.",
                    company=rec.company_id.display_name))
        return True

    # ------------------------------------------------------------------
    def _tax_advance(self, agg):
        """Withheld monthly income-tax advance before the daňový bonus."""
        return sum_concept(agg, "INCOME_TAX")

    def _declaration_render_context(self, data):
        self.ensure_one()
        agg = data["aggregate"]
        company = self.company_id
        payment = self.payment_date or self.date_to

        r00 = abs(round(agg.get("GROSS", 0.0), 2))
        r01 = self._tax_advance(agg)
        bonus = abs(round(agg.get(BONUS_CODE, 0.0), 2))
        r04 = r01
        r05 = min(bonus, r04)  # § 33 bonus capped at the advance for r05/r08
        r08 = round(r04 - r05, 2)

        # bank IBAN (first account of the company partner), for III. časť
        iban = ""
        banks = company.partner_id.bank_ids
        if banks:
            iban = (banks[0].acc_number or "").replace(" ", "")[:34]

        prehlad = {
            "dic": self._company_dic(company),
            # Riadny and opravný are mutually exclusive flags in the FS wire
            # format; both used to be hardcoded, so the form could only ever
            # emit a regular Prehľad.
            "riadny": "0" if self.is_correction else "1",
            "opravny": "1" if self.is_correction else "0",
            "mesiac": str(int(self.month)),
            "rok": str(int(self.year)),
            # PO identification
            "nazov": (company.name or "")[:255],
            "pravna_forma": (company.l10n_sk_legal_form())
            if hasattr(company, "l10n_sk_legal_form") else "",
            # sídlo
            "ulica": (company.street or "")[:255],
            "cislo": (company.street2 or "")[:20],
            "psc": self._digits(company.zip)[:5],
            "obec": (company.city or "")[:255],
            "stat": (company.country_id.code or "SK"),
            "tel": (company.phone or "")[:30],
            "email": (company.email or "")[:255],
            # I. časť — preddavky na daň
            "r00": "%.2f" % r00,
            "r01_datum": payment.strftime("%d.%m.%Y") if payment else "",
            "r01_suma": "%.2f" % r01,
            "r04": "%.2f" % r04,
            "r05": "%.2f" % r05,
            "r08": "%.2f" % r08,
            # II. časť — rekapitulácia daňového bonusu § 33
            "rA": "%.2f" % bonus,
            "rB": "%.2f" % r05,
            "rC": "%.2f" % round(bonus - r05, 2),
            # III. časť — žiadosti (not requested by default)
            "iban": iban,
            # vyhotovil
            "zostavil": (self.env.user.name or "Odoo Payroll")[:255],
            "datum_vyhotovenia": fields.Date.context_today(self).strftime(
                "%d.%m.%Y"),
        }
        return {"p": prehlad}
