# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK RLFO — Registračný list FO (registration of the SP relationship).

Filed to the Sociálna poisťovňa as the modern employee-only *hromadný* batch
(root ``spRegListZec``, ns ``http://socpoist.sk/xsd/rlzec2026``, shipped schema
``RLZEC-v2026.xsd``). It registers (prihláška) and de-registers (odhláška)
employees for social insurance.

Unlike MVP/VPP/ELDP this report is **NOT payslip-derived** — its data source is
the employee + the ``hr.version`` lifecycle: birth number, name, birth date, the
insurance start/end dates and the agreement type (which drives the ``typZec``
relationship code). It therefore reuses the base module only for the XML export
/ XSD-validate / filed-copy machinery; ``action_generate`` is overridden to
render from registration *events* instead of aggregating payslips.

Modelled events: ``PA`` (prihláška / registration) and ``OD`` (odhláška /
de-registration). ``ZM`` (zmena), ``PE`` (prerušenie) and ``ZP`` (zrušenie
prihlásenia) are not modelled yet.
"""
from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# employee agreement type -> default RLFO typZec relationship code
# (employee agreement type, income is regular) -> RLFO typZec relationship code
#
# The Sociálna poisťovňa distinguishes a dohoda with REGULAR monthly income
# from one with irregular income, because the two carry different insurance:
# an irregular-income dohodár pays old-age and disability only, with no
# sickness, unemployment or short-time contribution. The payslip rules key on
# exactly that, and the registration has to agree — telling SP the wrong
# relationship code gives the employee the wrong insurance scope from the day
# they are registered, not merely on one payslip.
AGREEMENT_TYP_ZEC = {
    ("none", True): "ZEC",      # Zamestnanec (employment is always regular)
    ("none", False): "ZEC",
    ("dovp", True): "ZECD1",    # DoVP - pravidelný príjem
    ("dovp", False): "ZECD1N",  # DoVP - nepravidelný príjem
    ("dopc", True): "ZECD2",    # DoPČ - pravidelný príjem
    ("dopc", False): "ZECD2N",  # DoPČ - nepravidelný príjem
}
DOHODA_CODES = ("ZECD1", "ZECD1N", "ZECD2", "ZECD2N")


class L10nSkRlfo(models.Model):
    _name = "l10n.sk.rlfo"
    _inherit = ["cssk.payroll.declaration.mixin", "mail.thread",
                "mail.activity.mixin"]
    _description = "SK RLFO natural-person registration batch"
    _order = "date_from desc, id desc"

    _report_code = "sk_rlfo"
    _country_code = "SK"
    _xml_name_fallback = "rlfo"

    event_ids = fields.One2many(
        "l10n.sk.rlfo.event", "rlfo_id", string="Registration events")
    events_count = fields.Integer(
        compute="_compute_events_count", string="Events")

    @api.depends("event_ids")
    def _compute_events_count(self):
        for rec in self:
            rec.events_count = len(rec.event_ids)

    # ------------------------------------------------------------------
    def _preflight(self):
        super()._preflight()
        for rec in self:
            company = rec.company_id
            vs = (company.l10n_sk_sp_vs or "").strip()
            if not (vs.isdigit() and len(vs) == 10):
                raise UserError(_(
                    "Company '%(company)s' needs a 10-digit Sociálna poisťovňa "
                    "identification number for the RLFO "
                    "<variabilnySymbol> element. Set 'Sociálna poisťovňa "
                    "variable symbol' on the company.",
                    company=company.display_name))
            if not rec._company_ico(company):
                raise UserError(_(
                    "Company '%(company)s' needs an 8-12 digit IČO (Company "
                    "Registry) for the RLFO <identifikator> element.",
                    company=company.display_name))
        return True

    @staticmethod
    def _digits(value):
        return "".join(ch for ch in (value or "") if ch.isdigit())

    def _company_ico(self, company):
        ico = self._digits(company.company_registry)
        return ico if 8 <= len(ico) <= 12 else False

    @staticmethod
    def _split_name(name):
        parts = (name or "").split()
        meno = parts[0] if parts else "-"
        priezvisko = parts[-1] if len(parts) > 1 else (parts[0] if parts else "-")
        return priezvisko[:36], meno[:24]

    @staticmethod
    def _fmt(d):
        return d.strftime("%d.%m.%Y") if d else False

    def _fo_osoba(self):
        user = self.env.user
        return {
            "zostavil": (user.name or "Odoo")[:30],
            "tel": (self.company_id.phone or "-")[:50] or "-",
            "mail": (self.company_id.email or user.email or "-")[:255] or "-",
        }

    # ------------------------------------------------------------------
    # Generate — render from lifecycle events, not payslips.
    # ------------------------------------------------------------------
    def action_generate(self):
        self.ensure_one()
        self._ensure_not_submitted()
        if self.state != "draft":
            raise UserError(_(
                "Reset the declaration to draft before regenerating it."))
        # RLFO bypasses the base action_generate. Resolve the requested period
        # here as well: today's API default may still point to an older form
        # with no end date even though a newer vintage exists.
        self.version_id = self._find_version(
            self._version_reference_date(), self.company_id.country_id)
        if not self.version_id:
            raise UserError(_(
                "No RLFO version is configured for this period. Check the "
                "shipped version data."))
        self._preflight()
        if not self.event_ids:
            raise UserError(_(
                "Add at least one registration event before generating the "
                "RLFO."))
        data = {"aggregate": {}, "per_employee": {}}
        xml_bytes = self._render_xml(data)
        self._validate_against_schema(xml_bytes)
        self._attach_xml(xml_bytes)
        self.state = "generated"
        self.message_post(body=_("RLFO generated and XSD-validated."))
        return True

    # 18.0's declaration base has no period vintages: it picks the version in
    # force TODAY when the record is created. These two are 19.0's base
    # helpers, kept here under the same names and semantics so that porting
    # the base later supersedes them without a behaviour change.
    def _version_reference_date(self):
        """The period's first day decides the vintage, not today."""
        self.ensure_one()
        return self.date_from

    def _find_version(self, on_date, country):
        """The RLFO form version in force on *on_date* (empty if none)."""
        Version = self.env["cssk.payroll.declaration.version"]
        if not on_date:
            return Version
        return Version.search([
            ("code", "=", self._report_code),
            ("country_id", "=", country.id),
            ("valid_from", "<=", on_date),
            "|", ("valid_to", "=", False), ("valid_to", ">=", on_date),
        ], order="valid_from desc", limit=1)

    def _render_xml(self, data):
        xml_bytes = super()._render_xml(data)
        if self.version_id != self.env.ref(
                "l10n_sk_hr_payroll_rlfo.rlfo_version_2027"):
            return xml_bytes
        old = "http://socpoist.sk/xsd/rlzec2026"
        new = "http://socpoist.sk/xsd/rlzec2027"
        root = etree.fromstring(xml_bytes)
        if etree.QName(root).namespace != old:
            raise UserError(_("Unexpected source namespace for RLZEC 2027."))
        # Existing PA/OD fields retain their element model in the new vintage.
        # Remap before action_generate's mandatory official-XSD validation.
        for node in root.iter():
            if isinstance(node.tag, str) and etree.QName(node).namespace == old:
                node.tag = etree.QName(new, etree.QName(node).localname)
        output = etree.Element(root.tag, nsmap={None: new}, attrib=dict(root.attrib))
        output.text = root.text
        output.extend(list(root))
        etree.cleanup_namespaces(output)
        return etree.tostring(output, encoding="UTF-8", xml_declaration=True)

    def _declaration_render_context(self, data):
        self.ensure_one()
        events = []
        for ev in self.event_ids.sorted("sequence"):
            employee = ev.employee_id
            rc = self._digits(employee.identification_id)
            if not (9 <= len(rc) <= 10):
                raise UserError(_(
                    "Employee '%(name)s' needs a 9-10 digit birth number "
                    "in the Identification No. field for the "
                    "RLFO.", name=employee.display_name))
            code = ev.typ_zec or "ZEC"
            if ev.typ_rl == "PA":
                if ev.owner50_status == "unknown":
                    raise UserError(_(
                        "Review statutory membership and at least 50%% ownership "
                        "for '%(name)s' before registering them.",
                        name=employee.display_name))
                if not (ev.ownership_evidence or "").strip():
                    raise UserError(_(
                        "Record the source of the reviewed ownership status "
                        "for '%(name)s'.", name=employee.display_name))
            if ev.typ_rl == "PA" and not ev.date_start:
                raise UserError(_(
                    "Registration for '%(name)s' needs an "
                    "insurance start date.", name=employee.display_name))
            if ev.typ_rl == "OD" and not (ev.date_start and ev.date_end):
                raise UserError(_(
                    "De-registration for '%(name)s' needs both the "
                    "insurance start and end dates.",
                    name=employee.display_name))
            priezvisko, meno = self._split_name(employee.name)
            events.append({
                "typ_rl": ev.typ_rl,
                "zam_s_ucastou": "true" if ev.owner50_status == "yes" else "false",
                "typ_zec": code,
                "is_dohoda": code in DOHODA_CODES,
                "is_zecn": code == "ZECN",
                "rc": rc,
                "priezvisko": priezvisko,
                "meno": meno,
                "dat_narodenia": self._fmt(employee.birthday),
                "dat_vznik_poist": self._fmt(ev.date_start),
                "dat_vzniku": self._fmt(ev.date_start),
                "dat_zaniku": self._fmt(ev.date_end),
            })
        return {
            "typ_doc": "RLZEC0001",
            "variabilny_symbol": self.company_id.l10n_sk_sp_vs,
            "ico": self._company_ico(self.company_id),
            "nazov": (self.company_id.name or "")[:144],
            "events": events,
            "fo": self._fo_osoba(),
            "datum_vystavenia": fields.Date.context_today(self).strftime(
                "%d.%m.%Y"),
        }


class L10nSkRlfoEvent(models.Model):
    _name = "l10n.sk.rlfo.event"
    _description = "SK RLFO registration event"
    _order = "rlfo_id, sequence, id"

    rlfo_id = fields.Many2one(
        "l10n.sk.rlfo", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    employee_id = fields.Many2one("hr.employee", required=True)
    typ_rl = fields.Selection(
        [("PA", "Registration"),
         ("OD", "De-registration")],
        string="Event type", required=True, default="PA")
    typ_zec = fields.Selection(
        [("ZEC", "ZEC — employee, regular income"),
         ("ZECN", "ZECN — employee, irregular income"),
         ("ZECD1", "ZECD1 — DoVP, regular income"),
         ("ZECD1N", "ZECD1N — DoVP, irregular income"),
         ("ZECD2", "ZECD2 — DoPČ, regular income"),
         ("ZECD2N", "ZECD2N — DoPČ, irregular income")],
        string="Relationship type (typZec)",
        compute="_compute_typ_zec", store=True, readonly=False)
    date_start = fields.Date(
        string="Insurance start (datVznikPoist)",
        help="Date the social-insurance relationship arises (registration) / "
        "the original start reported with a de-registration.")
    date_end = fields.Date(
        string="Insurance end (datZaniku)",
        help="Date the social-insurance relationship ends (de-registration).")
    owner50_status = fields.Selection(
        [("unknown", "Not reviewed"),
         ("no", "Not a statutory member with at least 50% ownership"),
         ("yes", "Statutory member with at least 50% ownership")],
        string="Statutory owner 50%+", required=True, default="unknown",
        copy=False,
        help="Historical fact for this registration (§ 231(1)(o), z. 461/2003). "
             "A generic guarantee-insurance exemption does not prove it.")
    ownership_evidence = fields.Char(
        string="Ownership evidence", copy=False,
        help="Reference to the reviewed statutory membership/ownership "
             "evidence and its effective date.")

    def write(self, vals):
        if {"owner50_status", "ownership_evidence"} & vals.keys():
            if any(event.rlfo_id.state != "draft" for event in self):
                raise UserError(_(
                    "Reset the registration batch to draft before changing "
                    "its ownership evidence."))
        return super().write(vals)

    @api.depends("employee_id")
    def _compute_typ_zec(self):
        for ev in self:
            agr, regular = "none", True
            emp = ev.employee_id
            if emp and "l10n_sk_agreement_type" in emp._fields:
                agr = emp.l10n_sk_agreement_type or "none"
            # 18.0 keeps the payroll fields on hr.contract, not hr.version.
            contract = emp.contract_id if emp else False
            if contract and "l10n_sk_income_regular" in contract._fields:
                regular = bool(contract.l10n_sk_income_regular)
            ev.typ_zec = AGREEMENT_TYP_ZEC.get((agr, regular), "ZEC")
