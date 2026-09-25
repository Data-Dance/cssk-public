# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK VPP — Výkaz poistného a príspevkov (dohody / irregular income).

Filed to the Sociálna poisťovňa (ns http://socpoist.sk/xsd/vpp2026). VPP is the
*dohoda* counterpart of the MVP monthly statement: it reports social insurance
for employees with **irregular income** (nepravidelný príjem) — typically work
agreements (dohody: DoVP / DoPČ) — and for regular income paid after the
insurance relationship ended / after an invalid termination.

Same shape as MVP (an aggregate ``poistne`` summary + a full per-employee
annex), so it reuses the exact fund → rule-code mapping. It differs from MVP in
that it is **scoped to dohoda contracts** (``l10n_sk_agreement_type`` in
``dovp``/``dopc``), its header carries ``cisloVykazu`` (MM99RRRR) and
``obdobieVyplPrijmov`` (MMRRRR) instead of ``denVyplaty``, and the annex row
carries an ``obdobie`` attribute and the employee-side ``vzZec*`` bases.

Fund → rule-code mapping (identical to MVP), employer = ``*Zamtel``,
employee = ``*Zamnec``:

======  ================================  =====================  ==================
Fund    Meaning                           Employer (Zamtel)      Employee (Zamnec)
======  ================================  =====================  ==================
np      nemocenské (sickness)             SICKEMPLOYER           SICK
sp      starobné + SDS (old-age)          PENSIONEMPLOYER        PENSION
ip      invalidné (disability)            DISABILITYEMPLOYER     DISABILITY
pvn     v nezamestnanosti (unemployment)  UNEMPLOYMENTEMPLOYER   UNEMPLOYMENT
up      úrazové (accident)                ACCIDENT               — (unused)
gp      garančné (guarantee)              GUARANTEEEMPLOYER      — (unused)
rfs     rezervný fond solidarity          RESERVEFUNDEMPLOYER    — (unused)
======  ================================  =====================  ==================

``spoluPoistne`` ← ``SOCIALEMPLOYERTOTAL`` + ``SOCIALEMPLOYEETOTAL``.
"""
from odoo import _, fields, models
from odoo.exceptions import UserError

# fund element -> (employer rule code, employee rule code or None)
FUND_MAP = [
    ("np", "SICKEMPLOYER", "SICK"),
    ("sp", "PENSIONEMPLOYER", "PENSION"),
    ("ip", "DISABILITYEMPLOYER", "DISABILITY"),
    ("pvn", "UNEMPLOYMENTEMPLOYER", "UNEMPLOYMENT"),
    ("up", "ACCIDENT", None),
    ("gp", "GUARANTEEEMPLOYER", None),
    ("rfs", "RESERVEFUNDEMPLOYER", None),
]

# dohoda agreement type -> VPP typZec relationship code. VPP reports irregular
# income, so the "nepravidelný príjem" (…N) variants are used by default.
AGREEMENT_TYP_ZEC = {
    "dovp": "ZECD1N",  # DoVP (dohoda o vykonaní práce) - nepravidelný príjem
    "dopc": "ZECD2N",  # DoPČ (dohoda o pracovnej činnosti) - nepravidelný príjem
}


class L10nSkVpp(models.Model):
    _name = "l10n.sk.vpp"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK VPP insurance statement for work agreements"
    _order = "date_from desc, id desc"

    _report_code = "sk_vpp"
    _country_code = "SK"
    _xml_name_fallback = "vpp"

    # ------------------------------------------------------------------
    # Scope: only dohoda payslips (irregular income) feed the VPP.
    # ------------------------------------------------------------------
    def _get_period_payslips(self):
        slips = super()._get_period_payslips()
        if not slips:
            return slips
        Employee = self.env["hr.employee"]
        if "l10n_sk_agreement_type" not in Employee._fields:
            # No SK payroll engine field -> nothing qualifies as a dohoda.
            return slips.browse()
        return slips.filtered(
            lambda s: s.employee_id.l10n_sk_agreement_type in ("dovp", "dopc"))

    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            vs = (company.l10n_sk_sp_vs or "").strip()
            if not (vs.isdigit() and len(vs) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit Sociálna poisťovňa "
                    "variable symbol for the VPP <variabilnySymbol> element. "
                    "Set 'Sociálna poisťovňa variable symbol' on the company.",
                    company=company.display_name))
            if not rec._company_ico(company):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-12 digit IČO "
                    "(Company Registry) for the VPP <identifikator> element.",
                    company=company.display_name))
        return True

    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_ico(self, company):
        ico = self._digits(company.company_registry)
        return ico if 8 <= len(ico) <= 12 else False

    def _fo_osoba(self):
        """The natural person fulfilling SP obligations (mzdová účtovníčka)."""
        user = self.env.user
        parts = (user.name or "Payroll Odoo").split()
        meno = parts[0] if parts else "Odoo"
        priezvisko = parts[-1] if len(parts) > 1 else "Payroll"
        return {
            "priezvisko": priezvisko[:36] or "Payroll",
            "meno": meno[:24] or "Odoo",
            "tel": (self.company_id.phone or "-")[:50] or "-",
            "mail": (self.company_id.email or user.email or "-")[:255] or "-",
            "zostavil": (user.name or "Odoo")[:30],
        }

    def _declaration_render_context(self, data):
        self.ensure_one()
        agg = data["aggregate"]

        def a(code):
            return abs(round(agg.get(code, 0.0), 2))

        funds = {}
        for elem, er_code, ee_code in FUND_MAP:
            funds[elem] = {
                "zamtel": "%.2f" % a(er_code),
                "zamnec": ("%.2f" % a(ee_code)) if ee_code else None,
            }
        spolu = "%.2f" % (a("SOCIALEMPLOYERTOTAL") + a("SOCIALEMPLOYEETOTAL"))

        annex = self._build_annex()
        fo = self._fo_osoba()
        m, y = int(self.month), int(self.year)
        return {
            "typ_doc": "VPP00001",
            "cislo_vykazu": "%02d99%04d" % (m, y),
            "obdobie_vypl_prijmov": "%02d%04d" % (m, y),
            "typ_vykazu": "R",
            "variabilny_symbol": self.company_id.l10n_sk_sp_vs,
            "ico": self._company_ico(self.company_id),
            "nazov": (self.company_id.name or "")[:144],
            "funds": funds,
            "spolu_poistne": spolu,
            "annex": annex,
            "fo": fo,
            "datum_vystavenia": fields.Date.context_today(self).strftime(
                "%d.%m.%Y"),
        }

    def _build_annex(self):
        """Per-employee annex rows (pre-formatted for the QWeb template)."""
        self.ensure_one()
        obdobie = "%02d%04d" % (int(self.month), int(self.year))
        rows = []
        pc = 0
        for line in self._sheet_lines().sorted("sequence"):
            pc += 1
            employee = line.employee_id
            rc = self._digits(employee.identification_id)
            if not (9 <= len(rc) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the VPP "
                    "per-employee annex.", name=employee.display_name))
            typ_zec = AGREEMENT_TYP_ZEC.get(
                employee.l10n_sk_agreement_type or "", "ZECN")
            totals = line.values_json or {}

            def t(code):
                return "%.2f" % abs(round(totals.get(code, 0.0), 2))

            vz = "%.2f" % abs(round(line.vz_base, 2))
            rows.append({
                "pc": pc,
                "obdobie": obdobie,
                "rc": rc,
                "poc_dni": line.insured_days,
                "typ_zec": typ_zec,
                "vynimka_vz": "0",
                "vz": vz,
                "poc_hodin": "%.2f" % abs(round(line.worked_hours, 2)),
                "np_zamtel": t("SICKEMPLOYER"),
                "np_zamnec": t("SICK"),
                "sp_zamtel": t("PENSIONEMPLOYER"),
                "sp_zamnec": t("PENSION"),
                "ip_zamtel": t("DISABILITYEMPLOYER"),
                "ip_zamnec": t("DISABILITY"),
                "pvn_zamtel": t("UNEMPLOYMENTEMPLOYER"),
                "pvn_zamnec": t("UNEMPLOYMENT"),
                "up_zamtel": t("ACCIDENT"),
                "gp_zamtel": t("GUARANTEEEMPLOYER"),
                "rfs_zamtel": t("RESERVEFUNDEMPLOYER"),
            })
        return rows
