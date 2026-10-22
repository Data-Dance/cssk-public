# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.
"""SK UZPODv14 — official účtovná závierka podnikateľov (PÚ) XML export.

Builds the official ``dokument`` (Súvaha Úč POD 1 + Výkaz ziskov a strát Úč POD
2) and validates it against the official ``uzpod-2014.xsd``. CE-clean: every
row is summed directly from ``account.move.line`` using the flattened row→account
formulas in ``data/uzpod14_rows.py`` (mirrors the authoritative statutory
mapping). AKTÍVA rows carry Brutto/Korekcia/Netto; PASÍVA and VZS carry the net
for the current and prior period.
"""
import base64
import os
import re

from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

from .uzpod14_rows import CLAIMED_ANALYTICS, SUVAHA_AKTIVA, SUVAHA_PASIVA, VZS
from .uzpod14_kontroly import SUCET_BS, SUCET_PL

_XSD_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "uzpod-2014.xsd")

# Kapitálové účty A. Vlastného imania (r080) BEZ bežného výsledku hospodárenia —
# zjednotenie riadkov r081, r085, r086, r087, r090, r093, r097 (základné imanie,
# emisné ážio, ostatné kap. fondy, zákonné/štatutárne fondy, oceňovacie rozdiely,
# VH minulých rokov). Bežný VH (r100) sa pripočíta osobitne z pohybu tried 5/6.
# Účet 431 (VH v schvaľovaní) sa zámerne nemapuje — v otvorenej knihe stojí proti
# neuzavretému začiatočnému stavu tried 5/6 a obe sa z výkazu vypúšťajú spoločne.
_EQUITY_CAPITAL = (
    "-353000,-411000,-419000,-491000,-412000,-413000,-417000,-417100,-418000,"
    "-421000,-421100,-422000,-423000,-427000,-414000,-415000,-416000,-428000,-429000")


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
        [("draft", "Draft"), ("exported", "Exported"), ("submitted", "Submitted")],
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
        date_to (Súvaha); True = movement in [date_from, date_to] (VZS)."""
        self.ensure_one()
        domain = [
            ("parent_state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
            ("date", "<=", date_to),
        ]
        if period:
            domain.append(("date", ">=", date_from))
        groups = self.env["account.move.line"]._read_group(
            domain, ["account_id"], ["balance:sum"])
        out = {}
        for account, bal in groups:
            out[account.code] = out.get(account.code, 0.0) + (bal or 0.0)
        return out

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

    @staticmethod
    def _eval(acct, conds, balances, tag_codes=None):
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
        """
        tag_codes = tag_codes or {}
        total = 0.0
        for token in (acct or "").split(","):
            token = token.strip()
            if not token:
                continue
            sign = -1.0 if token.startswith("-") else 1.0
            token = token.lstrip("-")
            include = None
            exclude = set()
            if "&" in token or "!" in token:
                m = re.match(r"([0-9]+)(.*)", token)
                prefix = m.group(1)
                for op, name in re.findall(r"([&!])([A-Za-z0-9_]+)", m.group(2)):
                    if op == "&":
                        include = (include or set()) | tag_codes.get(name, set())
                    else:
                        exclude |= tag_codes.get(name, set())
            else:
                prefix = token
            # A synthetic-main token NNN000 absorbs every analytic of synthetic
            # NNN that isn't explicitly routed elsewhere (so 022000 picks up
            # 022001/022002); an explicit NNNxxx token matches its sub-tree only.
            is_main = len(prefix) == 6 and prefix.endswith("000")
            syn = prefix[:3]
            for code, bal in balances.items():
                if not code:
                    continue
                if include is not None and code not in include:
                    continue
                if code in exclude:
                    continue
                if is_main:
                    if code[:3] == syn and code[:6] not in CLAIMED_ANALYTICS:
                        total += sign * bal
                elif code.startswith(prefix):
                    total += sign * bal
        for low, high, mode, csign in (conds or []):
            net = sum(bal for code, bal in balances.items()
                      if code and low <= code < high)
            if mode == "sum" or (mode == "pos" and net > 0) or (mode == "neg" and net < 0):
                total += csign * net
        return total

    # ------------------------------------------------------------------
    # document build
    # ------------------------------------------------------------------
    def _num(self, parent, tag, value):
        el = etree.SubElement(parent, tag)
        el.text = str(int(float_round(value or 0.0, precision_digits=0)))
        return el

    def _txt(self, parent, tag, value):
        el = etree.SubElement(parent, tag)
        el.text = value or ""
        return el

    def _build_header(self, dokument):
        company = self.company_id
        partner = company.partner_id
        h = etree.SubElement(dokument, "hlavicka")
        dk = etree.SubElement(h, "datumK")
        self._txt(dk, "den", str(self.date_to.day))
        self._txt(dk, "mesiac", str(self.date_to.month))
        self._txt(dk, "rok", str(self.date_to.year))
        dic = (company.vat or "").strip()
        self._txt(h, "dic", dic[2:] if dic[:2].upper() == "SK" else dic)
        self._txt(h, "ico", company.company_registry or "")
        nace = (getattr(company, "l10n_sk_nace_code", "") or "").ljust(5, "0")
        sknace = etree.SubElement(h, "skNace")
        self._txt(sknace, "k1", nace[:2])
        self._txt(sknace, "k2", nace[2:4])
        self._txt(sknace, "k3", nace[4:5])
        # druh from statement_nature (one-hot riadna/mimoriadna/priebezna); an
        # opravná correction is still filed under its druh — the schema has no
        # corrective element, the opravná flag is submission-level (see
        # submission_type). Veľkostná trieda from size_class (mala xor velka).
        tu = etree.SubElement(h, "typUzavierky")
        for tag in ("riadna", "mimoriadna", "priebezna"):
            self._txt(tu, tag, "1" if tag == self.statement_nature else "0")
        for tag in ("mala", "velka"):
            self._txt(tu, tag, "1" if tag == self.size_class else "0")
        ob = etree.SubElement(h, "obdobie")
        for tag, d in (("od", self.date_from), ("do", self.date_to)):
            sub = etree.SubElement(ob, tag)
            self._txt(sub, "mesiac", str(d.month))
            self._txt(sub, "rok", str(d.year))
        pf, pt = self.date_from - relativedelta(years=1), self.date_to - relativedelta(years=1)
        pp = etree.SubElement(h, "bPredObdobie")
        for tag, d in (("od", pf), ("do", pt)):
            sub = etree.SubElement(pp, tag)
            self._txt(sub, "mesiac", str(d.month))
            self._txt(sub, "rok", str(d.year))
        ps = etree.SubElement(h, "prilozeneSucasti")
        self._txt(ps, "suvaha", "1")
        self._txt(ps, "vykazZiskovStrat", "1")
        self._txt(ps, "poznamky", "1" if self.poznamky_attached else "0")
        uj = etree.SubElement(h, "uctJednotka")
        om = etree.SubElement(uj, "obchMeno")
        # obchMeno / oznObchodReg require exactly 2 <riadok> lines
        self._txt(om, "riadok", (company.name or "")[:36])
        self._txt(om, "riadok", (company.name or "")[36:72])
        sid = etree.SubElement(uj, "sidlo")
        self._txt(sid, "ulica", partner.street or "")
        self._txt(sid, "cislo", "")
        self._txt(sid, "psc", (partner.zip or "").replace(" ", ""))
        self._txt(sid, "obec", partner.city or "")
        oor = etree.SubElement(sid, "oznObchodReg")
        self._txt(oor, "riadok", getattr(company, "trade_registry", "") or "")
        self._txt(oor, "riadok", "")
        self._txt(sid, "telefon", partner.phone or "")
        self._txt(sid, "fax", "")
        self._txt(sid, "email", partner.email or "")
        self._txt(h, "datZostavenia", fields.Date.context_today(self).strftime("%Y-%m-%d"))
        self._txt(h, "datSchvalenia", "")

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
        self.ensure_one()
        pf = self.date_from - relativedelta(years=1)
        pt = self.date_to - relativedelta(years=1)
        bs_cur = self._balances(self.date_from, self.date_to, False)
        bs_prev = self._balances(pf, pt, False)
        pl_cur = self._balances(self.date_from, self.date_to, True)
        pl_prev = self._balances(pf, pt, True)
        tags = self._tag_account_codes()  # VZS financial related-party split

        dokument = etree.Element("dokument")
        self._build_header(dokument)
        telo = etree.SubElement(dokument, "telo")
        suv = etree.SubElement(telo, "ucPod1Suvaha")
        # AKTÍVA r001..r078: s1 gross, s2 korekcia, s3 netto, s4 netto minulé
        for i, (g_acct, g_cond, a_acct, a_cond) in enumerate(SUVAHA_AKTIVA, start=1):
            r = etree.SubElement(suv, "r%03d" % i)
            g = self._eval(g_acct, g_cond, bs_cur)
            k = self._eval(a_acct, a_cond, bs_cur)
            gp = self._eval(g_acct, g_cond, bs_prev)
            kp = self._eval(a_acct, a_cond, bs_prev)
            self._num(r, "s1", g)
            self._num(r, "s2", k)
            self._num(r, "s3", g - k)
            self._num(r, "s4", gp - kp)
        # PASÍVA r079..r145: s5 netto, s6 netto minulé.
        #
        # r100 (A.VIII Výsledok hospodárenia za účtovné obdobie po zdanení) a jeho
        # medzisúčet r080 (A. Vlastné imanie) nesú BEŽNÝ výsledok hospodárenia,
        # počítaný priamo z POHYBU tried 5/6 (výnosy − náklady vrátane dane =
        # −(Σ trieda 5 + Σ trieda 6)) — NIE ako niekdajší súvahový dopočet (plug).
        # Pohyb (nie kumulatívny zostatok) sa použije preto, aby r100 == VZS r61 aj
        # vtedy, keď triedy 5/6 minulého roka ešte neboli uzavreté na účet 431
        # (rozpracovaná/otvorená hlavná kniha). SPOLU (r079) = čestný súčet
        # r080 + r101 + r141 — súvaha sedí z účtov, nie cez dopočet.
        # (Zodpovedá l10n_cz_fs riadku A.V, account_formula '-5,-6'.)
        result_cur = self._eval("-5,-6", [], pl_cur)
        result_prev = self._eval("-5,-6", [], pl_prev)
        s5, s6 = [], []
        for idx, (n_acct, n_cond) in enumerate(SUVAHA_PASIVA):
            rn = 79 + idx
            if rn == 100:  # A.VIII VH bežného obdobia = výsledok z tried 5/6
                cur, prev = result_cur, result_prev
            elif rn == 80:  # A. Vlastné imanie = kapitálové účty + bežný VH
                cur = self._eval(_EQUITY_CAPITAL, [], bs_cur) + result_cur
                prev = self._eval(_EQUITY_CAPITAL, [], bs_prev) + result_prev
            else:
                cur = self._eval(n_acct, n_cond, bs_cur)
                prev = self._eval(n_acct, n_cond, bs_prev)
            s5.append(cur)
            s6.append(prev)
        # SPOLU VLASTNÉ IMANIE A ZÁVÄZKY (r079) = r080 + r101 + r141
        s5[0] = s5[80 - 79] + s5[101 - 79] + s5[141 - 79]
        s6[0] = s6[80 - 79] + s6[101 - 79] + s6[141 - 79]
        for idx in range(len(SUVAHA_PASIVA)):
            r = etree.SubElement(suv, "r%03d" % (79 + idx))
            self._num(r, "s5", s5[idx])
            self._num(r, "s6", s6[idx])
        # VZS r01..r61: s1 bežné, s2 minulé (period movement)
        vz = etree.SubElement(telo, "ucPod2VykazZS")
        for k2, (n_acct, n_cond) in enumerate(VZS, start=1):
            r = etree.SubElement(vz, "r%02d" % k2)
            self._num(r, "s1", self._eval(n_acct, n_cond, pl_cur, tags))
            self._num(r, "s2", self._eval(n_acct, n_cond, pl_prev, tags))
        return etree.tostring(dokument, xml_declaration=True, encoding="UTF-8")

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
    # Výkaz ziskov a strát Úč POD 2-01), cross-checked against EE l10n_sk_reports:
    #   * AKTÍVA (r001 netto) = PASÍVA (r079 netto)         — bilančná rovnosť
    #   * netto = brutto − korekcia                          — stĺpcová kontrola
    #   * každý medzisúčtový riadok = súčet zložkových riadkov (SUCET_BS/PL)
    # A non-empty result means the XML would be XSD-valid but rejected/incorrect.
    _KONTROLY_EPS = 1.0  # whole-euro rounding tolerance

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
        return out

    def action_export_xml(self):
        self.ensure_one()
        self._ensure_not_submitted()
        xml_bytes = self._build_xml()
        self._validate(xml_bytes)
        violations = self.check_kontroly(xml_bytes)
        if violations:
            raise UserError(_(
                "UZPODv14 failed kontrolné pravidlá (XSD-valid but the výkaz "
                "would be rejected):\n%s") % "\n".join(
                "  • %s: %s" % (vio["desc"], vio["detail"]) for vio in violations))
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
