# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Native official-form download. Financial values stay on the tax return."""
import hashlib
import json
import re

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open

from odoo.addons.l10n_cssk_core.tools import split_street, statutory_round
from .official_pdf import render_official_form

_FLAGS = (
    "currency_start", "currency_end", "nonresident", "controlled_transactions",
    "patent_exemption", "micro_taxpayer", "half_minimum", "minimum_exemption",
    "minimum_credit",
)


class DppoOfficialForm(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_form_layout = fields.Selection(related="version_id.l10n_sk_dppo_layout")
    l10n_sk_form_legal_code = fields.Char(string="Legal-form code")
    l10n_sk_form_nace = fields.Char(string="SK NACE for the form")
    l10n_sk_form_prepared_on = fields.Date(string="Declaration date")
    l10n_sk_form_discovered_on = fields.Date(string="Date the tax difference was discovered")
    l10n_sk_form_currency_start = fields.Boolean(string="Start special exchange-difference treatment")
    l10n_sk_form_currency_end = fields.Boolean(string="End special exchange-difference treatment")
    l10n_sk_form_nonresident = fields.Boolean(string="Limited tax liability")
    l10n_sk_form_controlled_transactions = fields.Boolean(string="Controlled transactions")
    l10n_sk_form_patent_exemption = fields.Boolean(string="Exemption under sections 13a/13b")
    l10n_sk_form_micro_taxpayer = fields.Boolean(string="Micro-taxpayer status")
    l10n_sk_form_half_minimum = fields.Boolean(string="Half minimum tax under section 46b(3)")
    l10n_sk_form_minimum_exemption = fields.Boolean(string="Minimum-tax exemption under section 46b(7)")
    l10n_sk_form_minimum_credit = fields.Boolean(string="Credit of prior minimum tax")
    l10n_sk_form_person_id = fields.Many2one(
        "res.partner", string="Person authorized to file", domain="[('is_company', '=', False)]")
    l10n_sk_form_person_first = fields.Char(string="Authorized person's first name")
    l10n_sk_form_person_last = fields.Char(string="Authorized person's surname")
    l10n_sk_form_person_relationship = fields.Char(string="Relationship to the legal entity")
    l10n_sk_form_title_before = fields.Char(string="Title before the person's name")
    l10n_sk_form_title_after = fields.Char(string="Title after the person's name")

    def _l10n_sk_dppo_pdf_supported_annex_rows(self):
        return set()

    def _l10n_sk_dppo_pdf_annex_payload(self):
        """Extend with typed, entered annex facts without a second tax ledger.

        The core adapter supports the complete native body and TablesA/B.
        Other nonzero claims must be accompanied by their entered form inputs;
        their concrete adapters extend this hook and validate their relations.
        """
        self.ensure_one()
        amounts = {line.code: line.value for line in self.line_ids}
        required = [code for code in ("r240", "r501", "r502", "r503",
                    "r710", "r920", "r1060", "r1070", "r1071", "r1072")
                    if amounts.get(code) and code not in self._l10n_sk_dppo_pdf_supported_annex_rows()]
        if required:
            raise UserError(_(
                "Enter and validate the related official annex inputs before "
                "printing these items: %s", ", ".join(required) or "Table I"))
        return {}

    def _l10n_sk_dppo_pdf_payload(self):
        self.ensure_one()
        self.check_access("read")
        self._cssk_check_not_legacy(_("printed"))
        if (self.country_id.code != "SK"
                or self.version_id.l10n_sk_dppo_layout != "2026"):
            raise UserError(_("Choose the published MF/014309/2026-721 paper form."))
        self._l10n_sk_dppo_check_form_applicability()
        if self.state not in ("preview", "exported") or not self.line_ids:
            raise UserError(_("Compute the return before printing its official form."))
        if self.currency_id.name != "EUR":
            raise UserError(_("The official Slovak form requires amounts in EUR."))
        if not self.date_from or self.date_from > self.date_to:
            raise UserError(_("Review the tax-period dates."))
        if not self.l10n_sk_form_prepared_on or self.l10n_sk_form_prepared_on < self.date_to:
            raise UserError(_("Enter a declaration date on or after the tax-period end."))
        if self.statement_type_id.code == "D" and not self.l10n_sk_form_discovered_on:
            raise UserError(_("Enter the actual discovery date for a supplementary return."))
        self._cssk_check_kontroly()
        hdr = self._l10n_sk_dppo_header()
        nace = self.l10n_sk_form_nace or "".join(hdr[key] for key in ("k1", "k2", "k3"))
        if not (re.fullmatch(r"[0-9]{10}", hdr["dic"])
                and re.fullmatch(r"[0-9]{8}|[0-9]{12}", hdr["ico"])
                and re.fullmatch(r"[0-9]{3}", self.l10n_sk_form_legal_code or "")
                and re.fullmatch(r"[0-9]{5}", nace)):
            raise UserError(_("Review DIČ, IČO, the three-digit legal-form code and five-digit SK NACE."))
        if not all((self.company_id.name, hdr["ulica"], hdr["obec"], hdr["psc"], hdr["stat"])):
            raise UserError(_("Complete the company's name and registered-office address."))
        person = self.l10n_sk_form_person_id
        if (not person or person.is_company
                or (person.company_id and person.company_id != self.company_id)
                or not all((self.l10n_sk_form_person_first, self.l10n_sk_form_person_last,
                            self.l10n_sk_form_person_relationship, person.street,
                            person.city, person.zip, person.country_id))):
            raise UserError(_("Enter the authorized person's contact, first name, surname, relationship and residence."))
        by = {line.code: line for line in self.line_ids}
        if any(line.is_overridden and self.currency_id.compare_amounts(line.value, line.manual_value)
               for line in self.line_ids):
            raise UserError(_("Recompute the return after changing a manual input."))
        definitions = {row.code: row for row in self.version_id.line_def_ids}
        if any(definitions[line.code].kind == "account" and not line.is_overridden
               and self.currency_id.compare_amounts(
                   self._eval_accounts(definitions[line.code].account_formula), line.value)
               for line in self.line_ids if line.code in definitions):
            raise UserError(_("Recompute the return after changing its posted ledger sources."))
        # Check the native derivation on virtual records, without changing a
        # posted provision or silently recomputing the accountant's saved return.
        trial = self.new({
            "company_id": self.company_id.id, "version_id": self.version_id.id,
            "date_from": self.date_from, "date_to": self.date_to,
            "l10n_sk_legacy_advance_relief": self.l10n_sk_legacy_advance_relief,
            "l10n_sk_legacy_advance_evidence": self.l10n_sk_legacy_advance_evidence,
            "line_ids": [(0, 0, {key: line[key] for key in
                          ("code", "value", "manual_value", "is_overridden")})
                         for line in self.line_ids],
        })
        trial._compute_tax_spine_2026()
        if any(self.currency_id.compare_amounts(line.value, by[line.code].value)
               for line in trial.line_ids):
            raise UserError(_("Recompute the return after changing a tax calculation input."))
        flags = {key: self["l10n_sk_form_" + key] for key in _FLAGS}
        if flags["half_minimum"] and flags["minimum_exemption"]:
            raise UserError(_("Choose either a half minimum tax or a minimum-tax exemption."))
        minimum = self._dppo_band_value(self.version_id.min_tax_bands, by["r560"].value)
        if self.date_from.year < 2026:
            minimum = min(minimum, 3840)
        minimum = statutory_round(minimum * self._period_months() / 12, 2)
        expected = 0 if flags["minimum_exemption"] else (
            statutory_round(minimum / 2, 2) if flags["half_minimum"] else minimum)
        if self.currency_id.compare_amounts(by["r810"].value, expected):
            raise UserError(_("The minimum-tax declaration must agree with the reviewed row 810 amount."))
        if bool(by["r920"].value) != bool(flags["minimum_credit"]):
            raise UserError(_("The prior minimum-tax credit declaration must agree with row 920."))
        extra = self._l10n_sk_dppo_pdf_annex_payload()
        derived = self.version_id._cssk_derived_codes()
        rows = {line.code: line.value for line in self.line_ids
                if line.value or line.is_overridden or line.code in derived
                or line.code in ("r100", "r560")}
        if self.l10n_sk_legacy_advance_relief:
            rows.pop("r1110", None)
        if not by["r920"].value:
            for code in ("r910", "r920", "r1000"):
                rows.pop(code, None)
        street, number = split_street(person)
        return {
            "header": {"dic": hdr["dic"], "ico": hdr["ico"],
                       "name": self.company_id.name, "legal_code": self.l10n_sk_form_legal_code,
                       "nace": nace, "street": hdr["ulica"], "number": hdr["cislo"],
                       "zip": hdr["psc"], "city": hdr["obec"], "country": hdr["stat"],
                       "phone": re.sub(r"\D", "", self.company_id.phone or ""),
                       "email": self.company_id.email or ""},
            "person": {"first": self.l10n_sk_form_person_first,
                       "last": self.l10n_sk_form_person_last,
                       "relationship": self.l10n_sk_form_person_relationship,
                       "title_before": self.l10n_sk_form_title_before or "",
                       "title_after": self.l10n_sk_form_title_after or "",
                       "street": street, "number": number, "zip": person.zip.replace(" ", ""),
                       "city": person.city, "country": person.country_id.name,
                       "phone": re.sub(r"\D", "", person.phone or ""), "email": person.email or ""},
            "date_from": str(self.date_from), "date_to": str(self.date_to),
            "prepared_on": str(self.l10n_sk_form_prepared_on),
            "discovered_on": str(self.l10n_sk_form_discovered_on) if self.l10n_sk_form_discovered_on else None,
            "statement_type": self.statement_type_id.code,
            "flags": flags, "rows": rows, "annex_count": 5, **extra,
        }

    def _l10n_sk_dppo_official_pdf(self):
        data = self._l10n_sk_dppo_pdf_payload()
        with file_open("l10n_sk_dppo/static/forms/DPPOv26.pdf", "rb") as source:
            template = source.read()
        with file_open("l10n_sk_dppo/static/forms/DPPOv26-layout.json") as source:
            layout = json.load(source)
        try:
            return render_official_form(template, layout, data)
        except ValueError as error:
            raise UserError(_("The official DPPO form cannot be printed: %s", str(error))) from error

    def action_export_official_pdf(self):
        self.ensure_one()
        self.check_access("write")
        raw = self._l10n_sk_dppo_official_pdf()
        checksum = hashlib.sha1(raw).hexdigest()
        Attachment = self.env["ir.attachment"]
        attachment = Attachment.search([
            ("res_model", "=", self._name), ("res_id", "=", self.id),
            ("checksum", "=", checksum), ("mimetype", "=", "application/pdf")], limit=1)
        if not attachment:
            attachment = Attachment.create({
                "name": "DPPO-MF014309-%s-%s.pdf" % (self.date_from, self.date_to),
                "raw": raw, "mimetype": "application/pdf",
                "res_model": self._name, "res_id": self.id,
                "description": "Published MF/014309/2026-721; unsigned native tax-return snapshot",
            })
            self.message_post(attachment_ids=attachment.ids)
        return {"type": "ir.actions.act_url",
                "url": "/web/content/%s?download=true" % attachment.id, "target": "self"}
