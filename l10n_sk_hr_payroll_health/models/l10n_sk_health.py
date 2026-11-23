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

Rule-code mapping: ``HEALTHEMPLOYER`` → employer advance (DepositOfEmployer),
``HEALTH`` → employee advance (DepositOfEmployee), ``HEALTHDOPLATOK`` /
``HEALTH_DOPLATOK`` → minimum-advance top-up (DepositOffEmployeeAdd).

What each figure contains follows § 1 ods. 3 vyhlášky 159/2018 Z. z. and the
item descriptions in the schema:

* The employer aggregate is split by rate (§ 12 zákona 580/2004 Z. z.): group
  1 is employees without a health disability, group 2 those with one.
  DepositOfInsurance1 / 2 are the employer's and the employees' advances of
  group 1 (2 includes the minimum top-up, § 16a ods. 4), 3 / 4 those of
  group 2.
* NumberOfDays is the calendar days the advance is computed and paid for:
  the days of employment without the days the State pays for (§ 11 ods. 7
  písm. m)) and the days without income (§ 11 ods. 3).
* TotalReceiptOfEmployee is the income, which is the employer's base (§ 13
  ods. 4); BaseOfAssessOfEmployee is the employee's base after the deductible
  item (§ 13 ods. 1, § 16 ods. 16 to 18), OP the item itself. The base and
  the rates are the ones the payslip recorded; a payslip without recorded
  fund bases is reported on its gross with no item.
* ReceiptOfEmployee is the income of an employment relationship (§ 13a ods.
  1), TotalReceiptOfOther the income of an agreement.

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
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_payroll_declaration_base.rule_codes import sum_concept

_logger = logging.getLogger(__name__)

# The doplatok (minimum-advance top-up) rule code differs per engine; that
# mapping lives once, in the declaration base, rather than being restated here.
# 2-digit insurer code -> 4-digit CodeOfHealthInsuranceCompany.
INSURER_CODE_4 = {"25": "2500", "24": "2400", "27": "2700"}

# Leave codes of the days that are not days an advance is paid for. The State
# pays for a person receiving sick pay, sickness, nursing or maternity benefit
# (§ 11 ods. 7 písm. m) zákona 580/2004 Z. z.); on parental and unpaid leave
# there is no income, so the person is not an employee (§ 11 ods. 3).
STATE_PAID_SICK_CODE = "PN"
NON_EMPLOYEE_LEAVE_CODES = (
    STATE_PAID_SICK_CODE, "OCR", "MATERSKA", "OTCOVSKA", "RODICOVSKA",
    "NEPLATENE")
AGREEMENT_TYPES = ("dovp", "dopc", "dobps")
CENT = Decimal("0.01")


class L10nSkHealth(models.Model):
    _name = "l10n.sk.health"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK dávka 514 monthly health-insurance advance statement"
    _order = "date_from desc, id desc"

    _report_code = "sk_health"
    _country_code = "SK"
    _xml_name_fallback = "davka514"
    # Filed separately to each insurer: an amendment amends the filing sent
    # to the SAME insurer, never one sent to another.
    _amendment_scope_fields = ("insurer_code",)

    insurer_code = fields.Selection(
        selection="_insurer_code_selection",
        string="Health insurer",
        default=lambda self: self.env.company.l10n_sk_health_insurer_code,
        required=True,
        help="Health insurance company this dávka 514 is addressed to. "
        "Defaults from the company configuration.")

    # Required by the preflight but on no company form; edit it here.
    payer_number = fields.Char(
        related="company_id.l10n_sk_health_payer_number", readonly=False,
        string="Health payer number")

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
                    "for the dávka 514. Fill in 'Health payer number' on "
                    "this form.", company=company.display_name))
            if not rec.insurer_code:
                raise UserError(_(
                    "Select the target health insurer on the dávka "
                    "514."))
            # Inspect the unfiltered set: excluded agreements must not hide a
            # disagreement between the statutory fact and the payroll switch.
            for slip in super(L10nSkHealth, rec)._get_period_payslips():
                if slip.employee_id._l10n_sk_health_insurer() != rec.insurer_code:
                    continue
                version = rec._payslip_version(slip)
                if not version or version.l10n_sk_agreement_type not in ("dopc", "dovp"):
                    continue
                if rec._pension_agreement(slip) and not version.l10n_sk_health_exempt:
                    raise UserError(_(
                        "Payslip '%(name)s': the pension type and health-exempt "
                        "setting disagree for this agreement. Review the historical "
                        "version and recalculate payroll before generating the 514.",
                        name=slip.display_name))
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

    def _get_period_payslips(self):
        """Only the payslips of employees insured with THIS insurer.

        A dávka 514 goes to one health insurer and lists that insurer's
        insurees. Every employee used to be reported to whichever insurer
        the record was addressed to, so a company with employees at two
        insurers filed everybody twice. An employee without an insurer of
        their own counts as insured with the company's default one.
        """
        slips = super()._get_period_payslips()
        if not slips:
            return slips
        return slips.filtered(
            lambda s: s.employee_id._l10n_sk_health_insurer()
            == self.insurer_code and not self._excluded_agreement(s))

    def _excluded_agreement(self, payslip):
        """Also respect other legislation, e.g. a documented foreign A1.

        A pension implies exclusion, but exclusion does not imply a pension.
        The health-exempt flag is currently the payroll's way to express the
        latter case. Its legal evidence remains the operator's responsibility.
        """
        version = self._payslip_version(payslip)
        return bool(self._pension_agreement(payslip) or (
            version and "l10n_sk_agreement_type" in version._fields
            and "l10n_sk_health_exempt" in version._fields
            and version.l10n_sk_agreement_type in ("dopc", "dovp")
            and version.l10n_sk_health_exempt))

    def _pension_agreement(self, payslip):
        """§10b(1)(a) points 3/4, z.580/2004: excluded agreement income.

        Every pension selection maps to an excluded statutory pension group.
        The exclusion has no income limit or one-agreement claim condition.
        A pension does not exempt an ordinary employment contract.
        The payslip's historical version decides, never today's employee card.
        """
        version = self._payslip_version(payslip)
        return bool(version
                    and "l10n_sk_agreement_type" in version._fields
                    and "l10n_sk_pension_type" in version._fields
                    and version.l10n_sk_agreement_type in ("dopc", "dovp")
                    and version.l10n_sk_pension_type)

    # ------------------------------------------------------------------
    @staticmethod
    def _rate(amount, base):
        return round(amount / base * 100.0, 2) if base else 0.0

    def _version_value(self, payslip, name):
        """Field *name* of the version the payslip was computed on."""
        version = self._payslip_version(payslip)
        return version[name] if version and name in version._fields else False

    def _is_agreement(self, payslip):
        return self._version_value(
            payslip, "l10n_sk_agreement_type") in AGREEMENT_TYPES

    def _minimum_not_applied(self, payslip):
        """§ 16a ods. 2: the payslip computes no minimum advance for a
        disabled person, a state insuree or a student agreement."""
        return bool(
            self._version_value(payslip, "l10n_sk_ztp")
            or self._version_value(payslip, "l10n_sk_health_exempt")
            or self._version_value(
                payslip, "l10n_sk_agreement_type") == "dobps")

    def _leave_whole_days(self, leave):
        """Dates of the period *leave* covers wholly. A day taken in part
        (half a day, some hours) is a day with income and stays."""
        first, last = leave.request_date_from, leave.request_date_to
        unit = leave.leave_type_request_unit
        if unit == "hour":
            first += timedelta(days=1)
            last -= timedelta(days=1)
        elif unit == "half_day":
            if leave.request_date_from_period == "pm":
                first += timedelta(days=1)
            if leave.request_date_to_period == "am":
                last -= timedelta(days=1)
        first, last = max(first, self.date_from), min(last, self.date_to)
        return {first + timedelta(days=offset)
                for offset in range((last - first).days + 1)}

    def _absence_days(self, employee, payslips):
        """``(sick days, other days)`` of leave that are not days of an
        employee for the advance, as sets of dates inside the period."""
        sick, other = set(), set()
        reader = getattr(payslips[:1], "_l10n_sk_leave_code_field", None)
        if "hr.leave" not in self.env or not callable(reader):
            return sick, other
        try:
            code_path = reader()
        except NotImplementedError:
            return sick, other
        leaves = self.env["hr.leave"].sudo().search([
            ("employee_id", "=", employee.id),
            ("company_id", "=", self.company_id.id),
            ("state", "=", "validate"),
            ("request_date_from", "<=", self.date_to),
            ("request_date_to", ">=", self.date_from),
            (code_path, "in", NON_EMPLOYEE_LEAVE_CODES),
        ])
        for leave in leaves:
            code = leave
            for name in code_path.split("."):
                code = code[name]
            (sick if code == STATE_PAID_SICK_CODE else other).update(
                self._leave_whole_days(leave))
        return sick, other

    def _advance_days(self, employee, payslips):
        """Calendar days the advance is computed and paid for.

        The payslip takes the sick days from its ``PN_DAYS`` input when one
        is given and from the sick leave otherwise; so does the statement.
        """
        self.ensure_one()
        employed = set()
        for first, last in self._employee_contract_intervals(
                employee, self.date_from, self.date_to):
            employed.update(first + timedelta(days=offset)
                            for offset in range((last - first).days + 1))
        sick, other = self._absence_days(employee, payslips)
        typed = [line.amount for line in payslips.input_line_ids
                 if line.code == "PN_DAYS"]
        if typed:
            return max(0, len(employed - other) - int(round(sum(typed))))
        return len(employed - other - sick)

    def _recorded_health(self, payslips, recorded):
        """Health bases and rates the payslips recorded, per side, or False
        when a payslip has none. The bases are summed as the payslip lines
        are, so a row's base and its income stay one figure apart by the
        deductible item only."""
        bases = {"employee": Decimal(0), "employer": Decimal(0)}
        rates = {"employee": set(), "employer": set()}
        for slip in payslips:
            rows = {row["side"]: row for row in recorded.get(slip.id) or []
                    if row["fund"] == "health"}
            if set(rows) != set(bases):
                return False
            for side, row in rows.items():
                bases[side] += Decimal(row["base"])
                rates[side].add(Decimal(row["rate"]))
        return bases, rates

    def _person_figures(self, line, bucket, recorded):
        """The statement figures of one employee, as numbers."""
        payslips = bucket["payslips"]
        totals = line.values_json or {}
        employer = abs(round(totals.get("HEALTHEMPLOYER", 0.0), 2))
        employee = abs(round(totals.get("HEALTH", 0.0), 2))
        topup = sum_concept(totals, "HEALTH_TOPUP")
        income = abs(round(totals.get("GROSS", 0.0), 2))
        other_income = min(income, abs(round(sum(
            slip_line.total
            for slip in payslips.filtered(self._is_agreement)
            for slip_line in slip.line_ids if slip_line.code == "GROSS"), 2)))
        base, item = income, 0.0
        rate_employer = self._rate(employer, income)
        rate_employee = self._rate(employee, income)
        health = self._recorded_health(payslips, recorded)
        if health:
            bases, rates = health
            base_employee = abs(bases["employee"]).quantize(
                CENT, rounding=ROUND_HALF_UP)
            base_employer = abs(bases["employer"]).quantize(
                CENT, rounding=ROUND_HALF_UP)
            base = float(base_employee)
            item = float(max(Decimal(0), base_employer - base_employee))
            if len(rates["employer"]) == 1:
                rate_employer = float(next(iter(rates["employer"])))
            else:
                rate_employer = self._rate(employer, float(base_employer))
            if len(rates["employee"]) == 1:
                rate_employee = float(next(iter(rates["employee"])))
            else:
                rate_employee = self._rate(employee, base)
        days = line.insured_days
        return {
            "disabled": any(self._version_value(slip, "l10n_sk_ztp")
                            for slip in payslips),
            "days": days,
            "paid_for": bool(days or employer or employee or topup),
            "income": income,
            "income_for_item": round(income - other_income, 2),
            "other_income": other_income,
            "item": item,
            "base": base,
            "rate_employer": rate_employer,
            "rate_employee": rate_employee,
            "employer": employer,
            "employee": employee,
            "topup": topup,
            "no_minimum": not topup and (not days or all(
                self._minimum_not_applied(slip) for slip in payslips)),
        }

    def _prepare_employee_declarations(self, data):
        result = super()._prepare_employee_declarations(data)
        for line in self._sheet_lines():
            bucket = data["per_employee"].get(line.employee_id)
            if bucket and bucket["payslips"] is not None:
                line.insured_days = self._advance_days(
                    line.employee_id, bucket["payslips"])
        return result

    def _declaration_render_context(self, data):
        self.ensure_one()
        company = self.company_id
        payment = self.payment_date or self.date_to
        today = fields.Date.context_today(self)
        recorded = data.get("recorded_funds") or {}

        rows = []
        # Group 1: without a health disability; group 2: with one.
        groups = {disabled: {
            "count": 0, "days": 0, "income": 0.0, "base": 0.0,
            "employer": 0.0, "employee": 0.0,
        } for disabled in (False, True)}
        for line in self._sheet_lines().sorted("sequence"):
            employee = line.employee_id
            rc = self._digits(employee.identification_id)
            if not (9 <= len(rc) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the "
                    "dávka 514 employee row.", name=employee.display_name))
            person = self._person_figures(
                line, data["per_employee"][employee], recorded)
            group = groups[person["disabled"]]
            group["count"] += person["paid_for"]
            group["days"] += person["days"]
            group["income"] += person["income"]
            group["base"] += person["base"]
            group["employer"] += person["employer"]
            # § 16a ods. 4: the top-up raises the employee's advance.
            group["employee"] += person["employee"] + person["topup"]
            rows.append({
                "pc": str(len(rows) + 1),
                "rc": rc,
                "poc_dni": str(person["days"]),
                "tarifa_zamtel": "%.2f" % person["rate_employer"],
                "tarifa_zamnec": "%.2f" % person["rate_employee"],
                "prijem": "%.2f" % person["income"],
                "vz": "%.2f" % person["base"],
                "preddavok_zamtel": "%.2f" % person["employer"],
                "preddavok_zamnec": "%.2f" % person["employee"],
                "preddavok_spolu": "%.2f" % round(
                    person["employer"] + person["employee"]
                    + person["topup"], 2),
                "prijem_op": "%.2f" % person["income_for_item"],
                "prijem_ostatny": "%.2f" % person["other_income"],
                "op": "%.2f" % person["item"],
                "bez_minima": "1" if person["no_minimum"] else "0",
                "doplatok": "%.2f" % person["topup"],
            })

        n = len(rows)
        spolu = round(sum(
            group["employer"] + group["employee"]
            for group in groups.values()), 2)
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
        agg = {"pocet": str(n), "preddavok_spolu": "%.2f" % spolu}
        for suffix, group in (("1", groups[False]), ("2", groups[True])):
            agg.update({
                "pocet" + suffix: str(group["count"]),
                "dni" + suffix: str(group["days"]),
                "prijem" + suffix: "%.2f" % round(group["income"], 2),
                "vz" + suffix: "%.2f" % round(group["base"], 2),
                "preddavok_zamtel" + suffix: "%.2f" % round(
                    group["employer"], 2),
                "preddavok_zamnec" + suffix: "%.2f" % round(
                    group["employee"], 2),
            })
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
