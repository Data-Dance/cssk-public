# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Register coordinates and the § 3a Obchodného zákonníka statement.

§ 3a ods. 1 requires every business document (invoice, order, letter, website)
to name the register the subject is entered in, together with the oddiel and
vložka. Odoo's ``l10n_sk`` holds one free-text ``res.company.trade_registry``
for that sentence, typed once by hand — which is how a company ends up still
printing *Okresný súd Bratislava I* years after the registrový súd for
Bratislava became *Mestský súd Bratislava III* on 1. 6. 2023.

This module keeps the three register coordinates as data and composes the
sentence from them, so it can be refreshed from the register instead of retyped.

The sentence itself is statutory Slovak and stays in the source untranslated,
per the repository's convention for legal wording that must appear verbatim on
a document.
"""

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# "Sro/3586/B" -> oddiel "Sro", vložka "3586/B". ORSR writes the oddiel first,
# then the vložka number, then the court's letter. A subject in the
# Živnostenský register carries a number in another shape entirely, which is
# why a failure to match falls back to printing the number whole.
REGISTER_NUMBER_RE = re.compile(r"^\s*([A-Za-zÀ-ž]+)\s*/\s*(.+?)\s*$")

# Slovak puts the register in the locative and the keeping authority in the
# genitive. Both follow from a short list of fixed prefixes, and the place name
# keeps its nominative form the way the register itself writes it
# ("Okresného súdu Žilina").
REGISTER_LOCATIVE = {
    "obchodný register": "Obchodnom registri",
    "živnostenský register": "Živnostenskom registri",
    "register nadácií": "Registri nadácií",
    "register občianskych združení": "Registri občianskych združení",
    "register neziskových organizácií": "Registri neziskových organizácií",
}
OFFICE_GENITIVE_PREFIXES = (
    ("mestský súd ", "Mestského súdu "),
    ("okresný súd ", "Okresného súdu "),
    ("krajský súd ", "Krajského súdu "),
    ("okresný úrad ", "Okresného úradu "),
)

# The register's status vocabulary. Codes follow ORSF's `statusCode`; the
# labels are the register's own Slovak, which is also what it puts in `status`.
REGISTER_STATUSES = [
    ("active", "Aktívna"),
    ("suspended", "Pozastavená"),
    ("dissolved", "Zrušená"),
    ("deleted", "Vymazaná"),
    ("unknown", "Neznámy"),
]
SLOVAK_STATUS_WORDS = {
    "aktívna": "active",
    "aktívny": "active",
    "pozastavená": "suspended",
    "pozastavený": "suspended",
    "zrušená": "dissolved",
    "zrušený": "dissolved",
    "vymazaná": "deleted",
    "vymazaný": "deleted",
}
# Statuses that mean "do not treat this subject as trading". A pozastavená
# živnosť is not dead, but invoicing one is still worth a second look.
NOT_TRADING_STATUSES = ("dissolved", "deleted", "suspended")


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_sk_register_name = fields.Char(
        string="Register",
        help="The register the subject is entered in, as the register itself "
        "names it — e.g. Obchodný register, Živnostenský register.",
    )
    l10n_sk_register_office = fields.Char(
        string="Registrový súd",
        help="The authority keeping the entry — e.g. Mestský súd Bratislava III, "
        "or the Okresný úrad for a živnostník.",
    )
    l10n_sk_register_number = fields.Char(
        string="Číslo zápisu",
        help="Oddiel and vložka as the register writes them — e.g. Sro/3586/B.",
    )
    l10n_sk_nace = fields.Char(
        string="SK NACE",
        help="Statistical classification of the main activity. Not the same "
        "as a predmet podnikania: NACE says what the subject is counted as, "
        "a predmet podnikania is what it is authorised to do.",
    )
    l10n_sk_legal_form = fields.Char(
        string="Právna forma",
        help="As the register words it — spoločnosť s ručením obmedzeným, "
        "akciová spoločnosť, and so on.",
    )
    l10n_sk_size_category = fields.Char(
        string="Veľkostná kategória",
        help="Employee band from the register (e.g. 1 000–1 999 zamestnancov).",
    )
    l10n_sk_established_on = fields.Date(
        string="Dátum vzniku",
        help="Date the subject was entered in the register.",
    )
    l10n_sk_register_status = fields.Selection(
        selection=REGISTER_STATUSES,
        string="Stav v registri",
        help="What the register says about the subject's existence. A subject "
        "shown as zrušená no longer trades, whatever the contact record says.",
    )
    l10n_sk_dissolved_on = fields.Date(
        string="Dátum zániku",
        help="Date the subject was struck from the register.",
    )
    l10n_sk_register_checked_on = fields.Datetime(
        string="Register checked",
        help="When the register was last read for this partner. A status is "
        "only as good as its date.",
    )
    l10n_sk_activity_ids = fields.One2many(
        "l10n.sk.register.activity", "partner_id", string="Predmety podnikania"
    )
    l10n_sk_filing_ids = fields.One2many(
        "l10n.sk.register.filing", "partner_id", string="Účtovné závierky"
    )
    l10n_sk_history_ids = fields.One2many(
        "l10n.sk.register.history", "partner_id", string="História"
    )
    l10n_sk_has_suspended_activity = fields.Boolean(
        string="Suspended activity",
        compute="_compute_l10n_sk_activity_signals",
        store=True,
        help="At least one predmet podnikania is under an open-ended "
        "suspension — the subject is active but may not do that work.",
    )
    l10n_sk_last_filing_period = fields.Char(
        string="Posledná závierka",
        compute="_compute_l10n_sk_filing_signals",
        store=True,
        help="Most recent accounting period filed to RÚZ.",
    )
    l10n_sk_filing_years_overdue = fields.Integer(
        string="Roky bez závierky",
        compute="_compute_l10n_sk_filing_signals",
        store=True,
        help="Full years between the last filed period and the one that "
        "should have been filed by now. Zero when up to date, and zero when "
        "nothing is known.",
    )
    l10n_sk_register_inactive = fields.Boolean(
        string="Not trading",
        compute="_compute_l10n_sk_register_inactive",
        store=True,
        help="True when the register shows the subject as zrušená, vymazaná "
        "or pozastavená.",
    )
    l10n_sk_trade_registry_statement = fields.Char(
        string="§ 3a statement",
        compute="_compute_l10n_sk_trade_registry_statement",
        store=True,
        readonly=False,
        help="The sentence § 3a Obchodného zákonníka requires on business "
        "documents. Composed from the register coordinates; overwrite it "
        "freely — an edit sticks until the coordinates change again.",
    )

    @api.depends(
        "l10n_sk_activity_ids.suspended_from", "l10n_sk_activity_ids.suspended_to"
    )
    def _compute_l10n_sk_activity_signals(self):
        for partner in self:
            partner.l10n_sk_has_suspended_activity = any(
                a.suspended_from and not a.suspended_to
                for a in partner.l10n_sk_activity_ids
            )

    @api.depends("l10n_sk_filing_ids.period")
    def _compute_l10n_sk_filing_signals(self):
        # A závierka for year N is filed during N+1, so by any date in year Y
        # the latest period that can be expected is Y-1.
        expected = fields.Date.context_today(self).year - 1
        for partner in self:
            years = [
                int(p)
                for p in partner.l10n_sk_filing_ids.mapped("period")
                if p and p.isdigit()
            ]
            partner.l10n_sk_last_filing_period = str(max(years)) if years else False
            partner.l10n_sk_filing_years_overdue = (
                max(0, expected - max(years)) if years else 0
            )

    @api.depends("l10n_sk_register_status")
    def _compute_l10n_sk_register_inactive(self):
        for partner in self:
            partner.l10n_sk_register_inactive = (
                partner.l10n_sk_register_status in NOT_TRADING_STATUSES
            )

    @api.model
    def _l10n_sk_parse_register_status(self, status_code, status=None):
        """Map a register status onto the selection.

        ORSF gives both a canonical ``statusCode`` and the Slovak word; older
        payloads and other sources give only the word. Anything unrecognised
        returns False rather than ``unknown``, because "we did not understand
        the answer" and "the register says it does not know" are different
        facts and only one of them is the register's.
        """
        valid = dict(REGISTER_STATUSES)
        code = (status_code or "").strip().lower()
        if code in valid:
            return code
        word = (status or "").strip().lower()
        return SLOVAK_STATUS_WORDS.get(word, False)

    def action_l10n_sk_refresh_register(self):
        """Ask ORSF to re-read this company from the source registers.

        ORSF's copy is sometimes incomplete — register coordinates null while
        the RPO and FS data is all there — and that looks exactly like a
        mapping failure on our side. The refresh is asynchronous: the data
        turns up about a minute later, so this says "come back", it does not
        re-read.
        """
        self.ensure_one()
        provider = self.env.get("partner.autocomplete.provider.orsf_sk")
        if provider is None:
            raise UserError(_("The ORSF provider module is not installed."))
        ico = provider._orsf_normalise_ico(
            self.company_registry or self.partner_gid
        )
        if not ico:
            raise UserError(
                _("%s has no IČO to look up.", self.display_name)
            )
        accepted, message = provider._orsf_refresh(ico)
        if accepted:
            self.env.user._bus_send("simple_notification", {
                "type": "success",
                "title": _("Refresh requested"),
                "message": _(
                    "ORSF is re-reading IČO %(ico)s from the source registers. "
                    "It takes about a minute — run Update again after that.",
                    ico=ico,
                ),
            })
        else:
            self.env.user._bus_send("simple_notification", {
                "type": "warning",
                "title": _("Refresh not accepted"),
                "message": message or _("ORSF declined the refresh."),
            })
        return True

    def _l10n_sk_register_warning(self):
        """One sentence about why this partner should not be traded with."""
        self.ensure_one()
        if not self.l10n_sk_register_inactive:
            return ""
        label = dict(REGISTER_STATUSES).get(self.l10n_sk_register_status, "")
        when = self.l10n_sk_dissolved_on
        detail = f" ({when})" if when else ""
        checked = self.l10n_sk_register_checked_on
        asof = f" Overené v registri {checked.date()}." if checked else ""
        return (
            f"{self.display_name} je v registri vedená ako "
            f"{label.lower()}{detail}.{asof}"
        )

    @api.depends(
        "l10n_sk_register_name",
        "l10n_sk_register_office",
        "l10n_sk_register_number",
        "is_company",
    )
    def _compute_l10n_sk_trade_registry_statement(self):
        for partner in self:
            partner.l10n_sk_trade_registry_statement = (
                partner._l10n_sk_compose_trade_registry() or False
            )

    def write(self, vals):
        res = super().write(vals)
        # A company's register coordinates are usually edited on the company
        # form, but nothing stops someone editing the partner behind it — and
        # then the printed sentence would quietly go stale, which is the exact
        # failure this module exists to prevent.
        if {
            "l10n_sk_register_name",
            "l10n_sk_register_office",
            "l10n_sk_register_number",
            "l10n_sk_trade_registry_statement",
            "is_company",
        } & set(vals):
            companies = self.env["res.company"].sudo().search(
                [("partner_id", "in", self.ids)]
            )
            if companies:
                companies._l10n_sk_sync_trade_registry()
        return res

    def _l10n_sk_compose_trade_registry(self):
        """Build the § 3a sentence, or "" when there is nothing to say.

        Deliberately conservative: anything the declension tables do not
        recognise passes through as the register wrote it. A slightly stiff
        sentence is a much better failure than a confidently wrong one on a
        statutory document.
        """
        self.ensure_one()
        register = (self.l10n_sk_register_name or "").strip()
        office = (self.l10n_sk_register_office or "").strip()
        number = (self.l10n_sk_register_number or "").strip()
        if not register and not office and not number:
            return ""

        # "Zapísaná" agrees with spoločnosť, "Zapísaný" with a živnostník.
        head = "Zapísaná" if self.is_company else "Zapísaný"

        if register:
            head = f"{head} v {REGISTER_LOCATIVE.get(register.lower(), register)}"
        if office:
            lowered = office.lower()
            for prefix, genitive in OFFICE_GENITIVE_PREFIXES:
                if lowered.startswith(prefix):
                    office = genitive + office[len(prefix) :]
                    break
            head = f"{head} {office}" if register else f"{head}, {office}"

        if not number:
            return head

        # "oddiel / vložka" is the Obchodný register's own vocabulary. A
        # Živnostenský register number can contain a slash too, and labelling
        # its parts that way would put words on a statutory document that the
        # register issuing it does not use.
        match = REGISTER_NUMBER_RE.match(number)
        if match and register.lower() == "obchodný register":
            return f"{head}, oddiel: {match.group(1)}, vložka č.: {match.group(2)}"
        return f"{head}, číslo zápisu: {number}"
