# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Who files: the ``VetaP`` of every Czech EPO VAT submission.

DPHDP3, the kontrolní hlášení and the souhrnné hlášení share one ``VetaP``
(údaje o daňovém subjektu). Their templates used to carry the DIČ, the office
and the company name with ``typ_ds="P"`` hard-coded, so a natural person could
not file at all, and none of them said who signed, who compiled the filing or
that a tax adviser was filing for the client. Built here once, from the
company, so the three forms cannot drift apart.

Attribute sizes are the XSD's (dphdp3_epo2.xsd / dphkh1_epo2.xsd /
dphshv_epo2.xsd agree on every one used here).
"""

import re

from odoo import api, fields, models

#: ``zast_kod`` — typ podepisující osoby, from the EPO code list in the XSD.
#: 4b is for a natural person, 4c for a legal entity; the rest apply to both.
EPO_REPRESENTATIVE_CODES = [
    ("1", "1 – zákonný zástupce nebo opatrovník"),
    ("2", "2 – ustanovený zástupce"),
    ("3", "3 – společný zástupce, společný zmocněnec"),
    ("4a", "4a – obecný zmocněnec"),
    ("4b", "4b – daňový poradce nebo advokát (fyzická osoba)"),
    ("4c", "4c – právnická osoba vykonávající daňové poradenství"),
    ("5a", "5a – osoba spravující pozůstalost"),
    ("5b", "5b – zástupce osoby spravující pozůstalost"),
    ("6a", "6a – dědic po skončení řízení o pozůstalosti"),
    ("6b", "6b – zástupce dědice po skončení řízení o pozůstalosti"),
    ("7b", "7b – zástupce právního nástupce právnické osoby"),
]

# "Diabasová 1141/11", "Příhon 943", "Nám. Míru 12a": street, číslo
# popisné, optional číslo orientační.
_STREET_RE = re.compile(r"^(?P<street>.*?\D)\s*(?P<pop>\d{1,6})(?:\s*/\s*(?P<orient>\w{1,4}))?\s*$")


class ResCompany(models.Model):
    _inherit = "res.company"

    # -- natural-person filer (typ_ds = F) --------------------------------
    l10n_cz_epo_title = fields.Char(
        string="Titul", size=10,
        help="Academic title of a natural-person taxpayer, as filed (VetaP/titul).")
    l10n_cz_epo_first_name = fields.Char(
        string="Jméno", size=30,
        help="First name of a natural-person taxpayer (VetaP/jmeno). Used when "
        "the company's person type is a natural person.")
    l10n_cz_epo_last_name = fields.Char(
        string="Příjmení", size=36,
        help="Surname of a natural-person taxpayer (VetaP/prijmeni).")

    # -- oprávněná osoba (legal entity) ------------------------------------
    l10n_cz_epo_signatory_first_name = fields.Char(
        string="Oprávněná osoba – jméno", size=20,
        help="The natural person entitled to sign for a legal entity "
        "(VetaP/opr_jmeno).")
    l10n_cz_epo_signatory_last_name = fields.Char(
        string="Oprávněná osoba – příjmení", size=36)
    l10n_cz_epo_signatory_position = fields.Char(
        string="Oprávněná osoba – vztah k právnické osobě", size=40,
        help="E.g. 'jednatel' (VetaP/opr_postaveni).")

    # -- sestavil ----------------------------------------------------------
    l10n_cz_epo_preparer_first_name = fields.Char(
        string="Sestavil – jméno", size=20,
        help="Who compiled the filing (VetaP/sest_jmeno).")
    l10n_cz_epo_preparer_last_name = fields.Char(string="Sestavil – příjmení", size=36)
    l10n_cz_epo_preparer_phone = fields.Char(string="Sestavil – telefon", size=14)

    # -- zástupce / podepisující osoba -------------------------------------
    l10n_cz_epo_agent_partner_id = fields.Many2one(
        "res.partner", string="Zástupce",
        help="Who files on the taxpayer's behalf — typically a tax adviser. "
        "A company partner files as a legal entity (zast_typ P, name and IČO), "
        "a person as a natural person (zast_typ F, name and surname). Leave "
        "empty when the taxpayer files itself.")
    l10n_cz_epo_agent_code = fields.Selection(
        EPO_REPRESENTATIVE_CODES, string="Typ zástupce",
        help="Kód podepisující osoby (VetaP/zast_kod).")
    l10n_cz_epo_agent_registration_number = fields.Char(
        string="Evidenční číslo zástupce", size=36,
        help="Registration number of a natural-person adviser, e.g. the "
        "Komora daňových poradců number (VetaP/zast_ev_cislo). A natural-"
        "person representative needs this or a date of birth.")
    l10n_cz_epo_agent_birth_date = fields.Date(
        string="Datum narození zástupce",
        help="VetaP/zast_dat_nar, for a natural-person representative "
        "without an evidenční číslo.")

    l10n_cz_epo_natural_person = fields.Boolean(
        compute="_compute_l10n_cz_epo_natural_person",
        help="The filer is a natural person (typ_ds F), from the person type.")

    # ------------------------------------------------------------------
    def _l10n_cz_typ_platce(self, date):
        """DPHDP3 ``VetaD/typ_platce`` on ``date``: P plátce, I identifikovaná
        osoba, N neplátce (§ 108). A VAT payer unless a module that records the
        company's VAT status says otherwise (``l10n_cz_vat_status``)."""
        self.ensure_one()
        return "P"

    @api.depends("l10n_cssk_person_type_id.is_legal_entity")
    def _compute_l10n_cz_epo_natural_person(self):
        for company in self:
            company.l10n_cz_epo_natural_person = (
                company._l10n_cz_epo_is_natural_person())

    def _l10n_cz_epo_is_natural_person(self):
        self.ensure_one()
        person_type = self.l10n_cssk_person_type_id
        return bool(person_type) and not person_type.is_legal_entity

    @staticmethod
    def _l10n_cz_epo_clip(value, size):
        value = (value or "").strip()
        return value[:size] if value else None

    def _l10n_cz_epo_address(self):
        """``ulice`` / ``c_pop`` / ``c_orient`` / ``naz_obce`` / ``psc``.

        Uses ``base_address_extended``'s split fields when they are there,
        else splits ``street`` on its trailing house number. A street that
        does not end in a number goes out whole as ``ulice``, with no number:
        a wrong číslo popisné is worse than none.
        """
        self.ensure_one()
        partner = self.partner_id
        street = pop = orient = None
        if "street_name" in partner._fields and partner.street_name:
            street = partner.street_name
            number = (partner.street_number or "").strip()
            if number.isdigit() and len(number) <= 6:
                pop = number
            orient = (partner.street_number2 or "").strip() or None
        elif partner.street:
            match = _STREET_RE.match(partner.street.strip())
            if match:
                street = match.group("street").strip().rstrip(",")
                pop = match.group("pop")
                orient = match.group("orient")
            else:
                street = partner.street
        zip_code = re.sub(r"\s+", "", partner.zip or "")
        return {
            "ulice": self._l10n_cz_epo_clip(street, 38),
            "c_pop": pop,
            "c_orient": self._l10n_cz_epo_clip(orient, 4),
            "naz_obce": self._l10n_cz_epo_clip(partner.city, 48),
            "psc": zip_code[:10] or None,
        }

    def _l10n_cz_epo_vetap(self, exclude=()):
        """The ``VetaP`` attributes for a DPH filing, empty ones left out.

        ``exclude`` names attributes the form's XSD does not have — the
        souhrnné hlášení carries no ``email`` and no ``c_telef``.
        """
        self.ensure_one()
        clip = self._l10n_cz_epo_clip
        vat = self.vat or ""
        dic = vat[2:] if vat[:2].upper() == "CZ" else vat
        natural = self._l10n_cz_epo_is_natural_person()
        attrs = {
            "dic": dic,
            "c_ufo": self.l10n_cssk_tax_authority_id.submission_code or "",
            "c_pracufo": self.l10n_cz_tax_office_id.workplace_code or None,
            "typ_ds": "F" if natural else "P",
        }
        if natural:
            attrs.update({
                "titul": clip(self.l10n_cz_epo_title, 10),
                "jmeno": clip(self.l10n_cz_epo_first_name, 30),
                "prijmeni": clip(self.l10n_cz_epo_last_name, 36),
            })
        else:
            attrs.update({
                "zkrobchjm": clip(self.name, 255),
                "opr_jmeno": clip(self.l10n_cz_epo_signatory_first_name, 20),
                "opr_prijmeni": clip(self.l10n_cz_epo_signatory_last_name, 36),
                "opr_postaveni": clip(self.l10n_cz_epo_signatory_position, 40),
            })
        attrs.update(self._l10n_cz_epo_address())
        phone = re.sub(r"[^\d+]", "", self.phone or "")
        attrs.update({
            "c_telef": phone[:14] or None,
            "email": clip(self.email, 255),
            "sest_jmeno": clip(self.l10n_cz_epo_preparer_first_name, 20),
            "sest_prijmeni": clip(self.l10n_cz_epo_preparer_last_name, 36),
            "sest_telef": clip(
                re.sub(r"[^\d+]", "", self.l10n_cz_epo_preparer_phone or ""), 14),
        })
        attrs.update(self._l10n_cz_epo_representative())
        attrs = {k: v for k, v in attrs.items() if k not in exclude}
        return {k: v for k, v in attrs.items() if v not in (None, False, "")} | {
            # Required by every XSD even when empty: the preflight names a
            # missing office; an empty DIČ fails the pattern loudly.
            "dic": attrs["dic"], "c_ufo": attrs["c_ufo"],
            "typ_ds": attrs["typ_ds"],
        }

    def _l10n_cz_epo_representative(self):
        self.ensure_one()
        rep = self.l10n_cz_epo_agent_partner_id
        if not rep:
            return {}
        clip = self._l10n_cz_epo_clip
        vals = {"zast_kod": self.l10n_cz_epo_agent_code or None}
        if rep.is_company:
            ico = re.sub(r"\D", "", rep.company_registry or "")
            vals.update({
                "zast_typ": "P",
                "zast_nazev": clip(rep.name, 255),
                "zast_ic": ico[:10] or None,
            })
        else:
            first, _sep, last = (rep.name or "").strip().rpartition(" ")
            vals.update({
                "zast_typ": "F",
                "zast_jmeno": clip(first, 20),
                "zast_prijmeni": clip(last or rep.name, 36),
                "zast_ev_cislo": clip(self.l10n_cz_epo_agent_registration_number, 36),
                "zast_dat_nar": self.l10n_cz_epo_agent_birth_date.strftime("%d.%m.%Y")
                if self.l10n_cz_epo_agent_birth_date else None,
            })
        return vals
