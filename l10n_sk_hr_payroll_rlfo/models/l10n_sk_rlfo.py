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

Modelled events: ``PA`` (prihláška / registration), ``OD`` (odhláška /
de-registration) and ``ZM`` (zmena) for ONE kind of change only: the
agreement's odvodová odpočítateľná položka (OOP) under § 227a zákona 461/2003
Z. z., which the employer reports under § 231 ods. 1 písm. e). ``PE``
(prerušenie), ``ZP`` (zrušenie prihlásenia) and every other change are not
modelled.
"""
from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# (employee agreement type, income is regular) -> RLFO typZec relationship code
#
# The Sociálna poisťovňa distinguishes a dohoda with REGULAR monthly income
# from one with irregular income, because the two carry different insurance:
# an irregular-income dohodár pays old-age and disability only, with no
# sickness, unemployment or short-time contribution. That is the same fact the
# payslip rules key on (see l10n_sk_hr_payroll_base.applicability), and the
# registration has to agree with it — telling SP the wrong relationship code
# gives the employee the wrong insurance scope from the day they are
# registered, not merely on one payslip.
AGREEMENT_TYP_ZEC = {
    ("none", True): "ZEC",      # Zamestnanec (employment is always regular)
    ("none", False): "ZEC",
    ("dovp", True): "ZECD1",    # DoVP - pravidelný príjem
    ("dovp", False): "ZECD1N",  # DoVP - nepravidelný príjem
    ("dopc", True): "ZECD2",    # DoPČ - pravidelný príjem
    ("dopc", False): "ZECD2N",  # DoPČ - nepravidelný príjem
    # DoBPŠ had no entry and fell back to ZEC, registering a student as an
    # employee in a pracovný pomer with the full insurance scope.
    ("dobps", True): "ZECD3",   # DoBPŠ - pravidelný príjem
    ("dobps", False): "ZECD3N",  # DoBPŠ - nepravidelný príjem
}
DOHODA_CODES = ("ZECD1", "ZECD1N", "ZECD2", "ZECD2N", "ZECD3", "ZECD3N")
# § 227a ods. 1: the OOP on the ground of maternity, paternity or parental
# leave exists on a DoVP and a DoPČ only. A DoBPŠ holder has the right without
# any such ground.
PARENTAL_OOP_CODES = ("ZECD1", "ZECD1N", "ZECD2", "ZECD2N")


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
    # The company field is required for every Sociálna poisťovňa filing but
    # appears on no company form (several modules declare it, and one view
    # per module would show the input several times). Edit it here instead.
    sp_vs = fields.Char(
        related="company_id.l10n_sk_sp_vs", readonly=False,
        string="Sociálna poisťovňa variable symbol",
        help="10-digit number the Sociálna poisťovňa assigned to the "
        "company. It is stored on the company and shared by every Sociálna "
        "poisťovňa filing (MVP, VPP, ELDP, RLFO).")

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
                    "<variabilnySymbol> element. Fill in 'Sociálna "
                    "poisťovňa variable symbol' on this form.",
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

    def _oop_values(self, ev, code, is_2027):
        """The agreement-OOP elements of one event, checked.

        ``datOznUplatnOop`` / ``datOznUkoncUplatnOop`` are accepted by the
        Sociálna poisťovňa for the agreement codes only (its description of
        the RLZEC 2023 changes). ``uplatnOopMdOdRd`` and
        ``datSkonceniaMdOdRd`` exist from RLZEC 2027, with the OOP of a
        parent on leave (§ 227a in the wording from 1 January 2027).
        """
        name = ev.employee_id.display_name
        registering = ev.typ_rl == "PA"
        changing = ev.typ_rl == "ZM"
        claimed = (registering or changing) and ev.oop_notified_date
        ended = changing and ev.oop_end_notified_date
        parental = (registering or changing) and ev.oop_parental
        leave_end = changing and ev.parental_leave_end
        if changing and not (claimed or ended or leave_end):
            raise UserError(_(
                "The change for '%(name)s' reports nothing: fill in the date "
                "the OOP claim or its end was notified, or the end of the "
                "leave.", name=name))
        if (claimed or ended or parental or leave_end) and code not in DOHODA_CODES:
            raise UserError(_(
                "The OOP of '%(name)s' can be reported on an agreement only "
                "(relationship types ZECD1 to ZECD3N).", name=name))
        if (parental or leave_end) and code not in PARENTAL_OOP_CODES:
            raise UserError(_(
                "The OOP on the ground of maternity, paternity or parental "
                "leave exists on a DoVP or DoPČ only; '%(name)s' has another "
                "relationship type.", name=name))
        if (parental or leave_end) and not is_2027:
            raise UserError(_(
                "The OOP on the ground of maternity, paternity or parental "
                "leave ('%(name)s') is reported on the RLZEC 2027 form: set "
                "the batch to January 2027 or later.", name=name))
        if parental and not claimed:
            raise UserError(_(
                "The event of '%(name)s' marks the OOP as claimed on the "
                "ground of leave but has no date the claim was notified.",
                name=name))
        if claimed and ended and ended < claimed:
            raise UserError(_(
                "For '%(name)s' the end of the OOP claim is notified before "
                "the claim itself.", name=name))
        return {
            "dat_ozn_uplatn_oop": self._fmt(claimed),
            "dat_ozn_ukonc_uplatn_oop": self._fmt(ended),
            "uplatn_oop_md_od_rd": bool(parental),
            "dat_skoncenia_md_od_rd": self._fmt(leave_end),
        }

    def _declaration_render_context(self, data):
        self.ensure_one()
        events = []
        is_2027 = self.version_id == self.env.ref(
            "l10n_sk_hr_payroll_rlfo.rlfo_version_2027")
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
            if ev.typ_rl == "ZM" and not ev.date_change:
                raise UserError(_(
                    "The change for '%(name)s' needs the date it applies "
                    "from.", name=employee.display_name))
            oop = self._oop_values(ev, code, is_2027)
            # Last word = surname, the rest = first name(s); separate first /
            # last name fields win when hr_employee_firstname provides them.
            meno, priezvisko = self._split_person_name(employee)
            meno, priezvisko = (meno or "-")[:24], (priezvisko or "-")[:36]
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
                "dat_uplatnenia": self._fmt(ev.date_change),
                **oop,
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
         ("OD", "De-registration"),
         ("ZM", "Change (agreement OOP)")],
        string="Event type", required=True, default="PA")
    typ_zec = fields.Selection(
        [("ZEC", "ZEC — employee, regular income"),
         ("ZECN", "ZECN — employee, irregular income"),
         ("ZECD1", "ZECD1 — DoVP, regular income"),
         ("ZECD1N", "ZECD1N — DoVP, irregular income"),
         ("ZECD2", "ZECD2 — DoPČ, regular income"),
         ("ZECD2N", "ZECD2N — DoPČ, irregular income"),
         ("ZECD3", "ZECD3 — DoBPŠ, regular income"),
         ("ZECD3N", "ZECD3N — DoBPŠ, irregular income")],
        string="Relationship type (typZec)",
        compute="_compute_typ_zec", store=True, readonly=False)
    date_start = fields.Date(
        string="Insurance start (datVznikPoist)",
        help="Date the social-insurance relationship arises (registration) / "
        "the original start reported with a de-registration.")
    date_end = fields.Date(
        string="Insurance end (datZaniku)",
        help="Date the social-insurance relationship ends (de-registration).")
    date_change = fields.Date(
        string="Change applies from (datUplatnenia)",
        help="For a change: the day the reported change takes effect.")
    oop_notified_date = fields.Date(
        string="OOP claim notified (datOznUplatnOop)",
        compute="_compute_oop_defaults", store=True, readonly=False,
        help="The day the employee told the employer in writing that the "
        "odvodová odpočítateľná položka is claimed on this agreement "
        "(§ 227a ods. 2 písm. a) zákona 461/2003 Z. z.) and, for a parent on "
        "leave, also proved the leave. Reported with a registration or a "
        "change, no later than the next working day.")
    oop_end_notified_date = fields.Date(
        string="OOP end notified (datOznUkoncUplatnOop)",
        help="For a change: the day the employee told the employer that the "
        "OOP is no longer claimed on this agreement (§ 227a ods. 2 písm. b)).")
    oop_parental = fields.Boolean(
        string="OOP on the ground of leave (uplatnOopMdOdRd)",
        compute="_compute_oop_defaults", store=True, readonly=False,
        help="The OOP is claimed by a person on maternity, paternity or "
        "parental leave. DoVP and DoPČ only, RLZEC 2027 and later.")
    parental_leave_end = fields.Date(
        string="Leave ends (datSkonceniaMdOdRd)",
        help="For a change: the last day of the maternity, paternity or "
        "parental leave the OOP was claimed on. RLZEC 2027 and later.")
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
            version = emp.version_id if emp else False
            if version and hasattr(version, "l10n_sk_income_is_regular"):
                regular = version.l10n_sk_income_is_regular()
            elif version and "l10n_sk_income_regular" in version._fields:
                regular = bool(version.l10n_sk_income_regular)
            ev.typ_zec = AGREEMENT_TYP_ZEC.get((agr, regular), "ZEC")

    @api.depends("employee_id")
    def _compute_oop_defaults(self):
        """Propose the OOP facts recorded on the contract, where it has them.

        The fields belong to the Slovak payroll modules, which this module
        does not depend on, so they are probed.
        """
        for ev in self:
            version = ev.employee_id.version_id if ev.employee_id else False
            claimed = bool(
                version
                and "l10n_sk_agreement_oop_reason" in version._fields
                and version.l10n_sk_agreement_oop
                and (version.l10n_sk_agreement_type or "none") != "none")
            ev.oop_notified_date = (
                claimed and version.l10n_sk_agreement_oop_notified)
            ev.oop_parental = bool(
                claimed and version.l10n_sk_agreement_oop_reason == "parental")
