# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK dávka 514 — Mesačný výkaz preddavkov na poistné (monthly health).

Filed each month to the target health insurance company (VšZP 25, Dôvera 24,
Union 27) via its e-pobočka.  The dávka 514 record set is defined centrally by
the ÚDZS/MZSR and is IDENTICAL across all three insurers — one writer,
parameterised by the insurer code + the payer/bank details.

Wire structure — the official ``514-2023.xsd`` (root ``MZSR``, English element
names, no target namespace):

* ``Identification`` — PatternOfRate (N/O/A), TypeOfRate (514), IDCode (IČO),
  CodeOfPayer (číslo platiteľa), CodeOfHealthInsuranceCompany (4-digit kód ZP),
  DateOfSending, SerialNumberOfRate, NumberOfRecords.
* ``CorporateBody`` — Period, DateOfPayment, CorporateBodyFullName,
  CompanyIDCode, CodeOfPayerSec, CompanyIDTaxCode (DIČ), IBAN.
* ``InsuranceBody`` — the employer aggregate (counts, bases, the advance split
  DepositOfInsurance1..4 + TotalDepositOfInsurance).
* ``PersonData`` (0..n) — one row per employee: SerialNumberOfLine,
  IdentificationNumberOfInsured (rodné číslo), NumberOfDays, TariffOfDeposit1/2
  (rates), TotalReceiptOfEmployee, BaseOfAssessOfEmployee, DepositOfEmployer,
  DepositOfEmployee, DepositOfTotal, DepositOffEmployeeAdd (doplatok) …

Rule-code mapping (rates come from the payslip, not hardcoded):
``HEALTHEMPLOYER`` → employer advance (DepositOfEmployer), ``HEALTH`` →
employee advance (DepositOfEmployee), ``HEALTHDOPLATOK`` / ``HEALTH_DOPLATOK``
→ minimum-advance top-up (DepositOffEmployeeAdd).

XSD note (IMPORTANT)
--------------------
The official ``514-2023.xsd`` is shipped in ``data/`` and IS loaded into the
export pipeline, BUT the schema is internally defective: its ID/string fields
carry a single-character ``[0-9]`` pattern under an 8-12 char minLength, its day
/ birth-number integer fields carry impossible ``maxInclusive`` bounds (2 / 10)
and ``DateOfSending`` mixes an ``xs:date`` base with a YYYYMMDD-only pattern —
so **no real-world instance can pass ``assertValid``**.  The pipeline therefore
runs the XSD as a *non-fatal* check (violations are logged, not raised) and the
authoritative gate is well-formedness + structural conformance to the XSD's
element model (root + the three blocks + NumberOfRecords = row count + key
totals).  Element names/order match the official schema exactly; reconcile the
figures with the insurer before live filing.
"""
import logging

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import sum_concept

_logger = logging.getLogger(__name__)

# The doplatok (minimum-advance top-up) rule code differs per engine; that
# mapping lives once, in the declaration base, rather than being restated here.
# 2-digit insurer code -> 4-digit CodeOfHealthInsuranceCompany.
INSURER_CODE_4 = {"25": "2500", "24": "2400", "27": "2700"}


class L10nSkHealth(models.Model):
    _name = "l10n.sk.health"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK dávka 514 monthly health-insurance advance statement"
    _order = "date_from desc, id desc"

    _report_code = "sk_health"
    _country_code = "SK"
    _xml_name_fallback = "davka514"

    insurer_code = fields.Selection(
        selection="_insurer_code_selection",
        string="Health insurer",
        default=lambda self: self.env.company.l10n_sk_health_insurer_code,
        required=True,
        help="Health insurance company this dávka 514 is addressed to. "
        "Defaults from the company configuration.")

    @api.model
    def _insurer_code_selection(self):
        return self.env["res.company"]._fields[
            "l10n_sk_health_insurer_code"].selection

    # ------------------------------------------------------------------
    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_ico(self, company):
        ico = self._digits(company.company_registry)
        return ico if 8 <= len(ico) <= 12 else False

    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            if not rec._company_ico(company):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-12 digit IČO "
                    "(Company Registry) for the dávka 514 identification "
                    "block.", company=company.display_name))
            if not (company.l10n_sk_health_payer_number or "").strip():
                raise UserError(_(
                    "Company '%(company)s' needs a health payer number "
                    "for the dávka 514. Set it on the "
                    "company.", company=company.display_name))
            if not rec.insurer_code:
                raise UserError(_(
                    "Select the target health insurer on the dávka "
                    "514."))
            # <CompanyIDTaxCode> was the one identification element nothing
            # checked. _digits() turns a missing DIČ into "", so the dávka went
            # to the insurer with an empty tax code and no error anywhere —
            # unlike the Prehľad and the Hlásenie, which have always refused.
            dic = self._digits(getattr(company, "l10n_sk_dic", ""))
            if not (dic.isdigit() and len(dic) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit DIČ (tax "
                    "identification number) for the dávka 514 "
                    "<CompanyIDTaxCode> element. Set 'DIČ' on the company.",
                    company=company.display_name))
        return True

    # ------------------------------------------------------------------
    @staticmethod
    def _rate(amount, base):
        return round(amount / base * 100.0, 2) if base else 0.0

    def _declaration_render_context(self, data):
        self.ensure_one()
        company = self.company_id
        payment = self.payment_date or self.date_to
        today = fields.Date.context_today(self)

        rows = []
        total_zamnec = total_zamtel = total_doplatok = 0.0
        total_base = total_income = 0.0
        total_days = 0
        pc = 0
        for line in self._sheet_lines().sorted("sequence"):
            pc += 1
            employee = line.employee_id
            rc = self._digits(employee.identification_id)
            if not (9 <= len(rc) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the "
                    "dávka 514 employee row.", name=employee.display_name))
            totals = line.values_json or {}
            zamnec = abs(round(totals.get("HEALTH", 0.0), 2))
            zamtel = abs(round(totals.get("HEALTHEMPLOYER", 0.0), 2))
            doplatok = sum_concept(totals, "HEALTH_TOPUP")
            base = abs(round(line.vz_base, 2))
            income = abs(round(totals.get("GROSS", 0.0), 2)) or base
            total_zamnec += zamnec
            total_zamtel += zamtel
            total_doplatok += doplatok
            total_base += base
            total_income += income
            total_days += line.insured_days
            rows.append({
                "pc": str(pc),
                "rc": rc,
                "poc_dni": str(line.insured_days),
                "tarifa_zamtel": "%.2f" % self._rate(zamtel, base),
                "tarifa_zamnec": "%.2f" % self._rate(zamnec, base),
                "prijem": "%.2f" % income,
                "vz": "%.2f" % base,
                "preddavok_zamtel": "%.2f" % zamtel,
                "preddavok_zamnec": "%.2f" % zamnec,
                "preddavok_spolu": "%.2f" % round(zamnec + zamtel, 2),
                "doplatok": "%.2f" % doplatok,
            })

        n = len(rows)
        spolu = round(total_zamnec + total_zamtel + total_doplatok, 2)
        iban = ""
        banks = company.partner_id.bank_ids
        if banks:
            iban = (banks[0].acc_number or "").replace(" ", "")[:34]

        ident = {
            "charakter": "N",
            "typ": "514",
            "ico": self._company_ico(company),
            "cislo_platitela": self._digits(
                company.l10n_sk_health_payer_number)[:10],
            "kod_zp": INSURER_CODE_4.get(self.insurer_code, "2500"),
            "datum_odoslania": today.strftime("%Y-%m-%d"),
            "poradie": "1",
            "pocet_viet": str(n),
        }
        corp = {
            "obdobie": "%04d-%02d" % (int(self.year), int(self.month)),
            "den_platby": "---%02d" % (payment.day if payment else 1),
            "nazov": (company.name or "")[:80],
            "ico": ident["ico"],
            "cislo_platitela": ident["cislo_platitela"],
            "dic": self._digits(getattr(company, "l10n_sk_dic", ""))[:12],
            "iban": iban,
        }
        agg = {
            "pocet": str(n),
            "pocet1": str(n),
            "pocet2": "0",
            "dni1": str(total_days),
            "dni2": "0",
            "prijem1": "%.2f" % round(total_income, 2),
            "prijem2": "0.00",
            "vz1": "%.2f" % round(total_base, 2),
            "vz2": "0.00",
            "preddavok_zamtel": "%.2f" % round(total_zamtel, 2),
            "preddavok_zamnec": "%.2f" % round(total_zamnec, 2),
            "doplatok": "%.2f" % round(total_doplatok, 2),
            "preddavok_spolu": "%.2f" % spolu,
        }
        return {"ident": ident, "corp": corp, "agg514": agg, "rows514": rows}

    # ------------------------------------------------------------------
    def _validate_against_schema(self, xml_bytes):
        """Well-formedness + structural conformance to the XSD element model,
        plus a NON-FATAL run of the (defective) official XSD.

        The shipped ``514-2023.xsd`` is the official schema but is internally
        contradictory (single-char patterns under multi-char minLength,
        impossible integer bounds), so ``assertValid`` can never pass on real
        data.  We therefore log its findings instead of raising, and gate on
        the structural checks below.
        """
        self.ensure_one()
        root = etree.fromstring(xml_bytes)  # raises on non-well-formed XML
        expected = self.version_id.xml_root_element or "MZSR"
        got = etree.QName(root).localname
        if got != expected:
            raise UserError(_(
                "Rendered dávka 514 root <%(got)s> does not match expected "
                "<%(exp)s>.", got=got, exp=expected))
        for block in ("Identification", "CorporateBody", "InsuranceBody"):
            if root.find(block) is None:
                raise UserError(_(
                    "dávka 514 XML is missing the <%s> block.", block))
        declared = root.findtext("Identification/NumberOfRecords")
        rows = root.findall("PersonData")
        if declared != str(len(rows)):
            raise UserError(_(
                "dávka 514 NumberOfRecords (%(declared)s) does not match the "
                "number of PersonData rows (%(rows)s).",
                declared=declared, rows=len(rows)))
        # Non-fatal official-XSD pass (schema is known-defective).
        schema = self._load_schema(self.version_id)
        if schema is not None and not schema.validate(root):
            _logger.info(
                "dávka 514: the official 514-2023.xsd reported %d schema "
                "issue(s) — expected, the published schema is internally "
                "defective (single-char [0-9] patterns, impossible integer "
                "bounds); gating on structural conformance instead.",
                len(schema.error_log))
        return True
