# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK UZPODv14 — official účtovná závierka podnikateľov (PÚ) XML export.

The filing record of the official ``dokument`` (Súvaha Úč POD 1 + Výkaz ziskov
a strát Úč POD 2): its header choices, its state, its corrective filings. The
document itself is rendered by the Úč POD ``cssk.fs.statement`` of the same
period (``_build_xml``), so what is filed is what the accountant reviewed —
overrides and manual rows included — and there is one generator, not two. It
is validated against the official ``uzpod-2014.xsd`` and the kontrolné pravidlá
below. The row tables in ``uzpod14_rows.py`` remain the mapping the statement's
version is generated from, and still drive the coverage diagnostic and
``vzs_before_tax``.
"""
import base64
import logging
import os

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .uzpod14_rows import CLAIMED_ANALYTICS, SUVAHA_AKTIVA, SUVAHA_PASIVA, TWO_SIDED, VZS
from .uzpod14_kontroly import SUCET_BS, SUCET_PL

_logger = logging.getLogger(__name__)

_XSD_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "uzpod-2014.xsd")

# Účet 431 (VH v schvaľovaní) sa zámerne nemapuje — v OTVORENEJ knihe stojí proti
# neuzavretému začiatočnému stavu tried 5/6 a obe sa z výkazu vypúšťajú spoločne.
#
# POZOR, tento predpoklad neplatí vždy. Platí len vtedy, keď sa triedy 5/6
# na 431 ešte neuzavreli. Ak sa uzávierka KAŽDÝ rok vykonala (a jej zápisy sú
# vylúčené cez l10n_cssk_closing_journal_ids), potom na 431 nestojí protistrana
# v triedach 5/6 — je to skutočný zostatok vlastného imania, nahromadený
# výsledok minulých rokov, ktorý valné zhromaždenie nikdy neschválilo a
# nerozdelilo na 428/429. Overené na reálnej migrácii: 3 630 289,70 EUR
# nahromadených za roky 2014–2022, ktoré do súvahy nevstúpili.
#
# Bežný výsledok sa NEZDVOJÍ ani v tomto prípade: r100 sa počíta z POHYBU tried
# 5/6 a uzávierkový zápis bežného roka je vylúčený, takže r100 a zostatok 431 sú
# disjunktné. Napriek tomu sa 431 nemapuje automaticky — nenulový zostatok na
# prechodnom účte je ZISTENIE (neschválená závierka), nie chyba mapovania, a
# jeho preklasifikovanie softvérom by problém zakrylo. Vypisuje ho kontrola
# BS_UNMAPPED; zaradenie do riadku patrí účtovníkovi a poučeniu k Úč POD 1.


class L10nSkUzpod(models.Model):
    _name = "l10n.sk.uzpod"
    _description = "SK Annual Statements (UZPODv14)"
    _inherit = ["mail.thread", "cssk.statutory.submission.mixin"]
    _order = "date_to desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection(
        [("draft", "Draft"), ("exported", "Exported"),
         ("submitted", "Submitted"),
         # Terminal and off the workflow — see cssk.statutory.submission.mixin.
         ("legacy", "Historical filing")],
        default="draft", tracking=True)
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)

    # Opravná účtovná závierka. The UZPODv14 body schema (uzpod-2014.xsd) has NO
    # corrective element — its typUzavierky is a fixed sequence of
    # riadna/mimoriadna/priebezna + mala/velka. A correction is still filed with
    # druh = riadna; the "opravná" nature is a RÚZ submission document-type, so it
    # rides the record + filing metadata (filename / log / link to the corrected
    # statement) and the e-filing envelope, NOT the XSD-validated body (adding a
    # non-schema element would fail validation).
    submission_type = fields.Selection(
        [("radna", "Regular"), ("opravna", "Corrective")],
        default="radna", required=True, copy=False, tracking=True,
        help="Regular = original filing; Corrective = a corrective financial "
             "statement of an already-submitted one for the same period (RÚZ "
             "document type 'opravná'; the body XML stays druh=riadna).")
    original_return_id = fields.Many2one(
        "l10n.sk.uzpod", string="Opravuje", readonly=True, copy=False,
        help="The originally-filed UZPODv14 this corrective statement corrects.")
    amendment_ids = fields.One2many(
        "l10n.sk.uzpod", "original_return_id", string="Opravné podania")
    size_class = fields.Selection(
        [("mala", "Malá účtovná jednotka"), ("velka", "Veľká účtovná jednotka")],
        string="Veľkostná trieda", required=True, default="mala",
        help="Veľkostná trieda účtovnej jednotky podľa § 2 ods. 5 až 8 zákona "
             "č. 431/2002 Z. z. o účtovníctve (kritériá: celková suma majetku, "
             "čistý obrat a priemerný prepočítaný počet zamestnancov za dve po "
             "sebe idúce účtovné obdobia). Mandatory in the UZPODv14 header "
             "(mikro jednotky file UZMIKv14, not UZPODv14).")
    statement_nature = fields.Selection(
        [("riadna", "Riadna"), ("mimoriadna", "Mimoriadna"),
         ("priebezna", "Priebežná")],
        string="Druh závierky", required=True, default="riadna",
        help="Druh účtovnej závierky (§ 17/18 zákona o účtovníctve): riadna "
             "(k poslednému dňu účtovného obdobia), mimoriadna (iný deň — "
             "napr. vstup do likvidácie), priebežná (v priebehu obdobia).")
    poznamky_attached = fields.Boolean(
        "Poznámky priložené", default=False,
        help="Set when the Notes (Úč PODV 3-01) are filed with this statement; "
             "drives the header prilozeneSucasti/poznamky flag (see l10n.sk.poznamky).")

    @api.depends("company_id", "date_to", "submission_type")
    def _compute_name(self):
        for rec in self:
            rec.name = "UZPODv14 %s — %s%s" % (
                rec.company_id.country_id.code or "SK", rec.date_to or "",
                " (opravná)" if rec.submission_type == "opravna" else "")

    # ------------------------------------------------------------------
    # account summation
    # ------------------------------------------------------------------
    def _balances(self, date_from, date_to, period):
        """Return {account_code: balance}. ``period`` False = cumulative to
        date_to (Súvaha); True = movement in [date_from, date_to] (VZS).

        This used to run its own ``_read_group`` with a hand-copied domain
        identical to the shared one. It now goes through
        ``_cssk_account_balance_map`` in ``l10n_cssk_core`` — the same query
        every other statutory statement reads. That is not only de-duplication:
        the company's year-end closing/reopening journals are excluded there,
        and a filing that kept its own copy of the query would have quietly
        gone on including the close/reopen entries while the on-screen preview
        excluded them."""
        self.ensure_one()
        return self._cssk_account_balance_map(
            date_from if period else None, date_to)

    # VZS financial-income/cost related-party split (Úč POD 2 lines IX/X/XI/N).
    # A company that has financial flows with prepojené/podielové entities tags
    # the relevant accounts; otherwise everything stays "ostatné" (no setup).
    _PL_SPLIT_TAGS = ("IX_1", "IX_2", "X_1", "X_2", "XI_1", "N_1")

    def _tag_account_codes(self):
        """{tag_key: set(account_codes)} for the related-party split tags."""
        out = {}
        Account = self.env["account.account"]
        for key in self._PL_SPLIT_TAGS:
            tag = self.env.ref("l10n_sk_fs.account_tag_pl_%s" % key,
                               raise_if_not_found=False)
            out[key] = (set(Account.search([("tag_ids", "in", tag.id)]).mapped("code"))
                        if tag else set())
        return out

    def _eval(self, acct, conds, balances, tag_codes=None):
        """Plain signed account-prefix sum + conditional domain terms.

        A conditional term ``[low, high, mode, sign]`` adds ``sign × net`` where
        ``net`` is the sum of accounts with ``low <= code < high``, but only when
        the net is positive (``pos``) or negative (``neg``) — the sum_if_pos /
        sum_if_neg split that routes tax accounts to the receivable or payable
        row by balance sign.

        A token may carry **account-tag filters** for the VZS financial
        related-party split: ``665&IX_1`` keeps only accounts tagged ``IX_1``,
        ``665!IX_1!IX_2`` excludes them (so the *ostatné* leaf = everything not
        tagged prepojené/podielová, hence the full amount when nothing is
        tagged). ``tag_codes`` maps a tag key to the set of account codes that
        carry it.

        Delegates to the shared matcher in ``l10n_cssk_core`` — the same code
        path the FS preview and the income-tax return use — so the figures an
        accountant checks on screen and the figures written into the filed XML
        can no longer drift apart. ``CLAIMED_ANALYTICS`` is passed as
        ``claimed``, which is what turns the synthetic-absorb rule on here and
        leaves it off for callers whose row definitions do not expect it.

        ``TWO_SIDED`` gates the accounts the form names on both sides (316,
        336, 373, 398, 481) on their own balance sign, as the on-screen
        statement always did. The export used not to, so a deferred tax ASSET
        on 481000 was filed on r052 and, negated, on r117 as well.
        """
        return self._cssk_eval_formula(
            acct, balances, conds=conds, default_sign=1.0,
            claimed=CLAIMED_ANALYTICS, tag_codes=tag_codes or {},
            two_sided=TWO_SIDED)

    def _cssk_uzpod_cells(self):
        """Every ``(formula, conds)`` cell of Súvaha and VZS, for the coverage
        diagnostic. AKTÍVA rows are 4-tuples (gross, gross_conds, adjustment,
        adjustment_conds); PASÍVA and VZS rows are 2-tuples."""
        cells = []
        for row in SUVAHA_AKTIVA:
            cells.append((row[0], row[1]))
            cells.append((row[2], row[3]))
        for row in SUVAHA_PASIVA:
            cells.append((row[0], row[1]))
        for row in VZS:
            cells.append((row[0], row[1]))
        return cells

    def _cssk_unmapped_report(self, balances):
        """``[(code, balance)]`` for accounts this statement maps to no row.

        Account 431 is expected here and is not a gap: in an open ledger it
        stands against the not-yet-closed opening balance of classes 5/6, and
        both are left out of the statement together — r100 takes the year's
        result from the MOVEMENT of 5/6 instead, so that it equals VZS r61 even
        when last year was never closed. Mapping 431 onto a PASÍVA row on top
        of that books the result twice.

        Účtová trieda 7 sa vynecháva. Trieda 7 sú závierkové a podsúvahové účty
        (701/702/710/711 a podsúvahové 75x–79x s vyrovnávacím účtom 799) — na
        súvahu ani do VZS nepatria z definície, nie preto, že by nám chýbal
        riadok. Overené: oficiálna štruktúra neodkazuje ani na
        jediný účet triedy 7. Bez tohto filtra sa podsúvahové páry (napr.
        722/799, 751/772), ktoré sa navzájom rušia na nulu, hlásia ako chýbajúce
        mapovanie a topia skutočné nálezy v šume. Prvá číslica = účtová trieda
        je v CZ/SK osnove záväzná a modul sa na ňu spolieha aj inde (r100 =
        pohyb tried 5/6). Účty typované ``off_balance`` sa vynechávajú rovnako
        — l10n_sk tak typuje 701/702/710/711."""
        off_balance = {
            code for code, account in self._cssk_account_by_code().items()
            if account.account_type == "off_balance"
        }
        probe = {
            code: balance for code, balance in balances.items()
            if not (code or "").startswith("7") and code not in off_balance
        }
        return self._cssk_unmapped_codes(
            probe, self._cssk_uzpod_cells(),
            claimed=CLAIMED_ANALYTICS, tag_codes=self._tag_account_codes())

    def _cssk_account_by_code(self):
        """``{code: account}`` for this company — lets the diagnostic spot
        account TYPES the Súvaha must ignore whatever the row mapping says."""
        accounts = self.env["account.account"].search(
            [("company_ids", "in", self.company_id.ids)])
        return {a.code: a for a in accounts if a.code}

    # ------------------------------------------------------------------
    # document build — through the statement, the one generator
    # ------------------------------------------------------------------
    def _l10n_sk_statement(self):
        """The Úč POD statement this record files.

        The latest one for the same company, period and submission type
        (riadna / opravná) that is not cancelled, a live statement before a
        historical filing. When there is none, one is created and computed:
        a filing record without its statement has nothing to file. A draft or
        preview statement is recomputed first, so the file reads the ledger as
        it stands — overrides survive a recompute; an exported or submitted
        statement is filed exactly as it was exported."""
        self.ensure_one()
        version = self.env.ref("l10n_sk_fs.uzpod_v14")
        Statement = self.env["cssk.fs.statement"]
        candidates = Statement.search([
            ("company_id", "=", self.company_id.id),
            ("version_id", "=", version.id),
            ("date_from", "=", self.date_from),
            ("date_to", "=", self.date_to),
            ("submission_type", "=", self.submission_type),
            ("state", "!=", "cancelled"),
        ], order="id desc")
        statement = (candidates.filtered(lambda st: st.state != "legacy")
                     or candidates)[:1]
        if not statement:
            statement = Statement.create({
                "company_id": self.company_id.id,
                "version_id": version.id,
                "date_from": self.date_from,
                "date_to": self.date_to,
                "l10n_sk_size_class": self.size_class,
                "l10n_sk_statement_nature": self.statement_nature,
                "l10n_sk_poznamky_attached": self.poznamky_attached,
                "submission_type": self.submission_type,
            })
        if statement.state in ("draft", "preview"):
            statement.action_compute_lines()
        return statement

    def vzs_before_tax(self):
        """VZS r56 — *Výsledok hospodárenia za účtovné obdobie pred zdanením*.

        Computed from the same P&L movement that fills the výkaz; equals DPPO
        r100 (the income-tax return starts from this accounting result). Used by
        the VZS→DPPO cross-form reconciliation.
        """
        self.ensure_one()
        pl = self._balances(self.date_from, self.date_to, True)
        acct, cond = VZS[55]  # 0-based index 55 == r56 == sk_pl_before_tax
        return self._eval(acct, cond, pl)

    def _build_xml(self):
        """The UZPODv14 document, rendered by the statement's template with
        this record's header choices. There is no second generator."""
        self.ensure_one()
        return self._l10n_sk_statement().with_context(l10n_sk_uzpod_header={
            "size_class": self.size_class,
            "statement_nature": self.statement_nature,
            "poznamky_attached": self.poznamky_attached,
        })._render_xml()

    def _validate(self, xml_bytes):
        schema = etree.XMLSchema(etree.parse(_XSD_PATH))
        root = etree.fromstring(xml_bytes)
        try:
            schema.assertValid(root)
        except etree.DocumentInvalid as exc:
            raise UserError(_("UZPODv14 XML failed schema validation:\n%s") % exc)

    # ------------------------------------------------------------------
    # kontrolné pravidlá (content checks the XSD cannot do)
    # ------------------------------------------------------------------
    # The schema only checks structure (XSD-valid != portal-accepted). These
    # rules enforce the statutory content invariants of the účtovná závierka
    # (Opatrenie MF SR č. MF/23377/2014-74, prílohy — Súvaha Úč POD 1-01 a
    # Výkaz ziskov a strát Úč POD 2-01):
    #   * AKTÍVA (r001 netto) = PASÍVA (r079 netto)         — bilančná rovnosť
    #   * netto = brutto − korekcia                          — stĺpcová kontrola
    #   * každý medzisúčtový riadok = súčet zložkových riadkov (SUCET_BS/PL)
    # A non-empty result means the XML would be XSD-valid but rejected/incorrect.
    _KONTROLY_EPS = 1.0  # whole-euro rounding tolerance
    # Below this an unmapped account is not worth naming: the výkaz is filed in
    # whole euros, so a few cents stranded on a rounding account says nothing.
    # Deliberately far below any balance that could move a statutory row —
    # the point is to catch the 473,762 sitting on an unmapped 131, not to be
    # quiet. A company whose 431 is properly approved out to 428/429 shows
    # nothing here; one carrying eight years of it shows the whole balance.
    _UNMAPPED_MATERIALITY = 100.0

    def _kontroly_values(self, xml_bytes):
        """{(section_key, r_int, s_tag): float} for both výkazy."""
        root = etree.fromstring(xml_bytes)
        vals = {}
        for tag, key in (("ucPod1Suvaha", "suvaha"), ("ucPod2VykazZS", "vzs")):
            sec = root.find(".//%s" % tag)
            if sec is None:
                continue
            for r in sec:
                rnum = int(r.tag.lstrip("r"))
                for s in r:
                    vals[(key, rnum, s.tag)] = float(s.text or 0.0)
        return vals

    def check_kontroly(self, xml_bytes=None):
        """Run the UZPODv14 kontrolné pravidlá against the generated document.

        Returns a list of ``{code, desc, detail}`` violations (empty = clean).
        """
        self.ensure_one()
        if xml_bytes is None:
            xml_bytes = self._build_xml()
        return self._cssk_uzpod_violations(xml_bytes)

    def _cssk_uzpod_violations(self, xml_bytes):
        """The rules themselves, shared with the statement's export: they
        need only the document and this record's company and period, so a
        ``new()`` record serves the statement as well."""
        v = self._kontroly_values(xml_bytes)
        eps = self._KONTROLY_EPS
        out = []

        def g(key, rnum, s):
            return v.get((key, rnum, s), 0.0)

        # 1. bilančná rovnosť: AKTÍVA (r001 netto) = PASÍVA (r079 netto)
        akt, pas = g("suvaha", 1, "s3"), g("suvaha", 79, "s5")
        if abs(akt - pas) > eps:
            out.append({"code": "BS_BALANCE",
                        "desc": "AKTÍVA (r001) = PASÍVA (r079)",
                        "detail": "%.0f != %.0f" % (akt, pas)})
        # 1b. obe strany nulové = bilancia síce "sedí" (0 = 0), ale účtovná
        # jednotka v PÚ má vždy nejaké aktíva — nulové súčty signalizujú výpadok
        # mapovania účtov (napr. analytické účty nezachytené v riadkoch súvahy).
        if abs(akt) <= eps and abs(pas) <= eps:
            out.append({"code": "BS_ZERO",
                        "desc": "AKTÍVA aj PASÍVA sú nulové — pravdepodobne "
                                "výpadok mapovania účtov na riadky súvahy",
                        "detail": "AKTÍVA=%.0f PASÍVA=%.0f" % (akt, pas)})
        # 2. stĺpcová kontrola: netto (s3) = brutto (s1) − korekcia (s2), AKTÍVA
        for rn in range(1, 79):
            b, k, n = g("suvaha", rn, "s1"), g("suvaha", rn, "s2"), g("suvaha", rn, "s3")
            if abs((b - k) - n) > eps:
                out.append({"code": "BS_NETTO",
                            "desc": "netto = brutto − korekcia (r%03d)" % rn,
                            "detail": "%.0f − %.0f != %.0f" % (b, k, n)})
        # 3. medzisúčty Súvaha: parent netto = Σ component netto
        for parent, kids in SUCET_BS:
            col = "s3" if parent <= 78 else "s5"
            tot = sum(g("suvaha", c, col) for c in kids)
            if abs(g("suvaha", parent, col) - tot) > eps:
                out.append({"code": "BS_SUCET",
                            "desc": "r%03d = Σ r%s" % (parent, kids),
                            "detail": "%.0f != %.0f" % (g("suvaha", parent, col), tot)})
        # 4. medzisúčty VZS: parent (s1 bežné) = Σ component
        for parent, kids in SUCET_PL:
            tot = sum(g("vzs", c, "s1") for c in kids)
            if abs(g("vzs", parent, "s1") - tot) > eps:
                out.append({"code": "PL_SUCET",
                            "desc": "VZS r%02d = Σ r%s" % (parent, kids),
                            "detail": "%.0f != %.0f" % (g("vzs", parent, "s1"), tot)})
        # 5. Účty, ktoré nesadli do žiadneho riadku súvahy ani VZS.
        #
        # Diagnostika, nie blokácia (severity=warning): bilančnú nerovnosť už
        # blokuje BS_BALANCE. Zmyslom je povedať PREČO — bez toho účtovník vidí
        # len "AKTÍVA != PASÍVA o 3 630 289" a nemá kde začať. Presne takto sa
        # sedem syntetík (078, 131, 261, 325, 395, 461, 474) stratilo zo súvahy
        # bez jediného varovania, kým sa výkaz neporovnal s pôvodným systémom.
        #
        # Účet 431 sa tu objaví vždy, keď na ňom niečo zostáva — a to je
        # správne. 431 (výsledok v schvaľovaní) je prechodný účet; nenulový
        # zostatok k súvahovému dňu znamená, že valné zhromaždenie výsledok
        # neschválilo a nerozdelilo na 428/429. To je zistenie pre účtovníka,
        # nie chyba mapovania, ktorú by mal softvér potichu preklasifikovať.
        bs_now = self._balances(self.date_from, self.date_to, False)
        unmapped = [(code, bal) for code, bal in self._cssk_unmapped_report(bs_now)
                    if abs(bal) > self._UNMAPPED_MATERIALITY]
        if unmapped:
            out.append({
                "code": "BS_UNMAPPED",
                "severity": "warning",
                "desc": "Účty nezachytené v žiadnom riadku výkazu",
                "detail": "; ".join(
                    "%s %.0f" % (code, bal) for code, bal in unmapped[:15])
                + ("; …(%d ďalších)" % (len(unmapped) - 15)
                   if len(unmapped) > 15 else ""),
            })
        return out

    def action_export_xml(self):
        self.ensure_one()
        self._ensure_not_submitted()
        xml_bytes = self._build_xml()
        self._validate(xml_bytes)
        violations = self.check_kontroly(xml_bytes)
        # Severity-aware, matching the shared contract in
        # cssk.statutory.submission.mixin._cssk_enforce_kontroly: only 'error'
        # blocks. Every rule that predates this carries no severity key and so
        # still defaults to 'error' — blocking behaviour for them is unchanged.
        # Warnings are diagnostics (BS_UNMAPPED) that must reach the accountant
        # without refusing a statement whose totals are sound.
        errors = [v for v in violations if v.get("severity", "error") == "error"]
        if errors:
            raise UserError(_(
                "UZPODv14 failed kontrolné pravidlá (XSD-valid but the výkaz "
                "would be rejected):\n%s") % "\n".join(
                "  • %s: %s" % (vio["desc"], vio["detail"]) for vio in errors))
        for vio in violations:
            if vio not in errors:
                _logger.warning("UZPODv14 %s — %s: %s",
                                self.display_name, vio["desc"], vio["detail"])
        att = self.env["ir.attachment"].create({
            "name": "UZPODv14%s-%s.xml" % (
                "-opravna" if self.submission_type == "opravna" else "",
                self.date_to or ""),
            "res_model": self._name, "res_id": self.id,
            "datas": base64.b64encode(xml_bytes), "mimetype": "application/xml"})
        self.xml_attachment_id = att.id
        self.state = "exported"

    # ------------------------------------------------------------------
    # Amendment (opravná účtovná závierka)
    # ------------------------------------------------------------------
    def action_create_amendment(self):
        """The shared mixin copies the original into a fresh draft and links
        original_return_id; here we flag the copy Opravná. The amended statement
        re-exports from the corrected accounting (full restatement — UZPODv14 has
        no difference rows). The corrective marker is submission-level metadata
        (filename + link + log), not a body element (see submission_type)."""
        action = super().action_create_amendment()
        amendment = (
            self.browse(action.get("res_id"))
            if isinstance(action, dict) else self.browse())
        if amendment and amendment.exists():
            amendment.submission_type = "opravna"
        return action
