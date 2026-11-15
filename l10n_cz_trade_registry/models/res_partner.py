# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Register coordinates and the § 435 občanského zákoníku statement.

§ 435 odst. 1 zákona č. 89/2012 Sb. requires every entrepreneur to state the
name and seat on business documents (*obchodní listiny*) and in information
made available to the public by remote access. One entered in the obchodní
rejstřík adds the entry "včetně oddílu a vložky"; one entered in another
veřejný rejstřík states that entry; one entered in no public register states
the entry in another evidence. Odoo's ``l10n_cz`` holds one free-text
``res.company.trade_registry`` for it, typed once by hand and never looked at
again.

This module keeps the three register coordinates as data and composes the
statement from them, so it can be refreshed from the register instead of
retyped.

The statement itself is statutory Czech and stays in the source untranslated,
per the repository's convention for legal wording that must appear verbatim on
a document.
"""

import re

from odoo import api, fields, models

# "C 12345" -> oddíl "C", vložka "12345". The veřejný rejstřík writes the
# oddíl (one to three letters: A, B, C, Dr, Pr, L, N, U, S, O, …) and then the
# vložka number. Anything in another shape — a živnostenský úřad's číslo
# jednací, say — fails to match and is printed whole.
SPISOVA_ZNACKA_RE = re.compile(r"^\s*([A-Za-zÀ-ž]{1,3})\s*(\d+)\s*$")

# The six veřejné rejstříky of § 1 odst. 1 zákona č. 304/2013 Sb., as the
# register names them. All six are kept by a rejstříkový soud and all six file
# an entry under oddíl and vložka, so these are the names for which the
# "vedený … soudem, oddíl, vložka" wording is the register's own.
PUBLIC_REGISTERS = (
    "obchodní rejstřík",
    "spolkový rejstřík",
    "nadační rejstřík",
    "rejstřík ústavů",
    "rejstřík společenství vlastníků jednotek",
    "rejstřík obecně prospěšných společností",
)

# The statement names the court in the instrumental ("vedený Krajským soudem
# v Brně"). The rejstříkové soudy are the krajské soudy and the Městský soud v
# Praze, and their official names already carry the seat in the locative
# ("v Brně", "v Praze"), so the prefix is all that declines.
COURT_INSTRUMENTAL_PREFIXES = (
    ("městský soud ", "Městským soudem "),
    ("krajský soud ", "Krajským soudem "),
)

# The register's status vocabulary. Codes follow ARES's `StavZdroje` codelist
# (AKTIVNI, POZASTAVENY, ZANIKLY, HISTORICKY); the labels are its Czech.
REGISTER_STATUSES = [
    ("active", "Aktivní"),
    ("suspended", "Pozastavený"),
    ("dissolved", "Zaniklý"),
    ("historical", "Historický"),
]
ARES_STATUS_CODES = {
    "aktivni": "active",
    "pozastaveny": "suspended",
    "zanikly": "dissolved",
    "historicky": "historical",
}
CZECH_STATUS_WORDS = {
    "aktivní": "active",
    "aktivní subjekt": "active",
    "pozastavený": "suspended",
    "pozastavená": "suspended",
    "zaniklý": "dissolved",
    "zaniklá": "dissolved",
    "zaniklý subjekt": "dissolved",
    "historický": "historical",
    "historický subjekt": "historical",
}
# Statuses that mean "do not treat this subject as trading". A pozastavená
# živnost is not dead, but invoicing one is still worth a second look.
NOT_TRADING_STATUSES = ("dissolved", "historical", "suspended")

COORDINATES = (
    "l10n_cz_register_name",
    "l10n_cz_register_office",
    "l10n_cz_register_number",
)


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_cz_register_name = fields.Char(
        string="Rejstřík",
        help="The register the subject is entered in, as the register itself "
        "names it — e.g. Obchodní rejstřík, Spolkový rejstřík, or "
        "Živnostenský rejstřík for a sole trader entered in no public "
        "register.",
    )
    l10n_cz_register_office = fields.Char(
        string="Rejstříkový soud",
        help="The court keeping the entry — e.g. Městský soud v Praze, "
        "Krajský soud v Brně. For an entry outside the public registers, the "
        "authority that keeps it.",
    )
    l10n_cz_register_number = fields.Char(
        string="Spisová značka",
        help="Oddíl and vložka as the register writes them — e.g. C 12345.",
    )
    l10n_cz_established_on = fields.Date(
        string="Datum vzniku",
        help="Date the subject came into existence, per the register.",
    )
    l10n_cz_register_status = fields.Selection(
        selection=REGISTER_STATUSES,
        string="Stav v rejstříku",
        help="What the register says about the subject's existence. A subject "
        "shown as zaniklý no longer trades, whatever the contact record says.",
    )
    l10n_cz_dissolved_on = fields.Date(
        string="Datum zániku",
        help="Date the subject ceased to exist, per the register.",
    )
    l10n_cz_register_checked_on = fields.Datetime(
        string="Register checked",
        help="When the register was last read for this partner. A status is "
        "only as good as its date.",
    )
    l10n_cz_activity_ids = fields.One2many(
        "l10n.cz.register.activity",
        "partner_id",
        string="Předmět podnikání a činnosti",
    )
    l10n_cz_history_ids = fields.One2many(
        "l10n.cz.register.history", "partner_id", string="Historie"
    )
    l10n_cz_register_inactive = fields.Boolean(
        string="Not trading",
        compute="_compute_l10n_cz_register_inactive",
        store=True,
        help="True when the register shows the subject as zaniklý, historický "
        "or pozastavený.",
    )
    l10n_cz_trade_registry_statement = fields.Char(
        string="§ 435 statement",
        compute="_compute_l10n_cz_trade_registry_statement",
        store=True,
        readonly=False,
        help="The entry § 435 občanského zákoníku requires on business "
        "documents. Composed from the register coordinates; overwrite it "
        "freely — an edit sticks until the coordinates change again.",
    )

    @api.depends("l10n_cz_register_status")
    def _compute_l10n_cz_register_inactive(self):
        for partner in self:
            partner.l10n_cz_register_inactive = (
                partner.l10n_cz_register_status in NOT_TRADING_STATUSES
            )

    @api.model
    def _l10n_cz_parse_register_status(self, status_code, status=None):
        """Map a register status onto the selection.

        ARES gives a code from its ``StavZdroje`` codelist (``AKTIVNI``,
        ``ZANIKLY``, …); other sources give the Czech word. Anything
        unrecognised returns False. That includes ARES's ``NEEXISTUJICI`` —
        "this source holds no such subject" is a fact about the source, not a
        status of the subject — and its bookkeeping codes ``BUDOUCI`` and
        ``LOGICKY_SMAZANY``.
        """
        valid = dict(REGISTER_STATUSES)
        code = (status_code or "").strip().lower()
        if code in valid:
            return code
        if code in ARES_STATUS_CODES:
            return ARES_STATUS_CODES[code]
        word = (status or "").strip().lower()
        return CZECH_STATUS_WORDS.get(word, False)

    def _l10n_cz_register_warning(self):
        """One sentence about why this partner should not be traded with."""
        self.ensure_one()
        if not self.l10n_cz_register_inactive:
            return ""
        label = dict(REGISTER_STATUSES).get(self.l10n_cz_register_status, "")
        when = self.l10n_cz_dissolved_on
        detail = f" ({when})" if when else ""
        checked = self.l10n_cz_register_checked_on
        asof = f" Ověřeno v rejstříku {checked.date()}." if checked else ""
        # Worded around the status rather than the subject, so that no
        # participle has to agree with a legal form the module cannot know.
        return (
            f"{self.display_name}: stav subjektu v rejstříku je "
            f"„{label.lower()}“{detail}.{asof}"
        )

    @api.depends(*COORDINATES)
    def _compute_l10n_cz_trade_registry_statement(self):
        for partner in self:
            partner.l10n_cz_trade_registry_statement = (
                partner._l10n_cz_compose_trade_registry() or False
            )

    def write(self, vals):
        res = super().write(vals)
        # A company's register coordinates are usually edited on the company
        # form, but nothing stops someone editing the partner behind it — and
        # then the printed statement would quietly go stale, which is the
        # exact failure this module exists to prevent.
        if (set(COORDINATES) | {"l10n_cz_trade_registry_statement"}) & set(vals):
            companies = self.env["res.company"].sudo().search(
                [("partner_id", "in", self.ids)]
            )
            if companies:
                companies._l10n_cz_sync_trade_registry()
        return res

    def _l10n_cz_compose_trade_registry(self):
        """Build the § 435 statement, or "" when there is nothing to say.

        Czech would normally say "zapsaná / zapsaný / zapsané v obchodním
        rejstříku …", and the participle follows the grammatical gender of
        the legal form: společnost, spolek, družstvo. The module does not know
        the legal form, so the statement is built around the register instead
        — "Obchodní rejstřík vedený Městským soudem v Praze, oddíl C, vložka
        12345" — where the only agreement is with *rejstřík* itself.

        Deliberately conservative beyond that: a register or an authority the
        tables do not recognise passes through as written, joined by commas. A
        slightly stiff statement is a much better failure than a confidently
        wrong one on a statutory document.
        """
        self.ensure_one()
        register = (self.l10n_cz_register_name or "").strip()
        office = (self.l10n_cz_register_office or "").strip()
        number = (self.l10n_cz_register_number or "").strip()
        if not register and not office and not number:
            return ""

        public = register.lower() in PUBLIC_REGISTERS
        court = ""
        lowered = office.lower()
        for prefix, instrumental in COURT_INSTRUMENTAL_PREFIXES:
            if lowered.startswith(prefix):
                court = instrumental + office[len(prefix):]
                break

        if register:
            head = register[0].upper() + register[1:]
        else:
            head = ""
        if public and court:
            # "vedený" agrees with rejstřík, the head noun of all six names.
            head = f"{head} vedený {court}"
        elif office:
            head = f"{head}, {office}" if head else office

        if not number:
            return head

        # "oddíl / vložka" is the vocabulary of the veřejné rejstříky. Another
        # evidence numbers its entries its own way, and labelling the parts of
        # such a number would put words on a statutory document that the
        # authority issuing it does not use.
        match = SPISOVA_ZNACKA_RE.match(number)
        by_court = public or (not register and court)
        if match and by_court:
            tail = f"oddíl {match.group(1)}, vložka {match.group(2)}"
        elif by_court:
            tail = f"spisová značka {number}"
        else:
            tail = f"číslo zápisu: {number}"
        return f"{head}, {tail}" if head else tail[0].upper() + tail[1:]
