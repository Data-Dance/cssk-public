# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK-specific hooks on the shared financial-statement framework.

Both hooks hang off the VERSION rather than the statement, because the
reverse-drill footprint reads them too and a hook the reverse direction
cannot reach is how the two came to disagree about which row an account
feeds.
"""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import float_round

from .uzpod14_rows import CLAIMED_ANALYTICS


class CSSKFsVersion(models.Model):
    _inherit = "cssk.fs.statement.version"

    def _cssk_tag_codes(self):
        """Úč POD 2 splits IX/X/XI/N by account TAG, not by code.

        Ten VZS rows separate financial income and cost with a prepojená
        účtovná jednotka from the rest, and no account code distinguishes
        them. The filed export (``l10n.sk.uzpod``) already resolves this from
        the same six tags, and the on-screen statement has to agree with what
        gets filed — so it reads the same map rather than keeping a second one.

        Only the UZPODv14 version uses the grammar; for every other version
        the map is harmless, because a formula with no ``&`` or ``!`` never
        consults it.

        On the VERSION, not the statement. The reverse drill reads it from an
        EMPTY ``cssk.fs.statement`` recordset, where ``self.version_id`` is
        empty and its country code is False — so a statement-level override
        would fall through to ``super()`` and silently answer None, which is
        the failure it exists to prevent.
        """
        self.ensure_one()
        if self.country_id.code != "SK":
            return super()._cssk_tag_codes()
        return self.env["l10n.sk.uzpod"]._tag_account_codes()

    def _cssk_claimed_codes(self):
        """Which analytics a main account may NOT absorb, from one source.

        UZPODv14's rows name specific chart codes, so ``022000`` has to take
        022001 and 022002 with it or those balances reach no row at all — but
        it must not take 311110, which r043 routes to a line of its own. The
        set of accounts "another row names" is the whole content of that rule,
        and the filed export computes it in
        ``uzpod14_rows._claimed_analytics``. Read it from there rather than
        re-deriving from the version's formulas: three codes (255100, 473100,
        479100) are named only by TOTAL rows, which this version renders as
        aggregates, so a re-derivation cannot see them and their balances
        would land on a different row on screen than in the filed XML.

        Overridden on the VERSION and not on the statement, because the
        reverse-drill footprint reads it from here too. On the statement it
        would answer the forward direction only, and the two would disagree
        about which row an account feeds — which is the drift this whole
        arrangement exists to prevent.

        Every other version — the CZ statements, the SK cash flow and changes
        in equity — is written in group prefixes where '022' already covers
        its analytics, and keeps the framework's own answer.
        """
        self.ensure_one()
        uzpod = self.env.ref("l10n_sk_fs.uzpod_v14", raise_if_not_found=False)
        if uzpod and self == uzpod:
            return CLAIMED_ANALYTICS
        return super()._cssk_claimed_codes()


class CSSKFsStatement(models.Model):
    """The Úč POD statement is the ONE source of the filed UZPODv14 XML.

    There used to be two generators: this statement's QWeb export and the
    ``l10n.sk.uzpod`` builder, each with its own header and its own reading
    of the rows. They agreed on the netto figures and disagreed on everything
    else — the export hardcoded SK NACE 00.00.0, malá / riadna and no
    poznámky, filed brutto and korekcia as 0 on the totals, and ran none of
    the kontrolné pravidlá — while the builder ignored the accountant's
    overrides and the manual rows. The statement is what the accountant
    reviews, so it is what gets filed; ``l10n.sk.uzpod`` now renders through
    it, and the header and the content checks live here."""

    _inherit = "cssk.fs.statement"

    l10n_sk_is_uzpod = fields.Boolean(
        string="Úč POD statement", compute="_compute_l10n_sk_is_uzpod")
    l10n_sk_size_class = fields.Selection(
        [("mala", "Malá účtovná jednotka"), ("velka", "Veľká účtovná jednotka")],
        string="Veľkostná trieda", default="mala", copy=True,
        help="Veľkostná trieda účtovnej jednotky podľa § 2 ods. 5 až 8 zákona "
             "č. 431/2002 Z. z. o účtovníctve. Mandatory in the UZPODv14 header "
             "(mikro jednotky file UZMIKv14, not UZPODv14).")
    l10n_sk_statement_nature = fields.Selection(
        [("riadna", "Riadna"), ("mimoriadna", "Mimoriadna"),
         ("priebezna", "Priebežná")],
        string="Druh závierky", default="riadna", copy=True,
        help="Druh účtovnej závierky (§ 17/18 zákona o účtovníctve).")
    l10n_sk_poznamky_attached = fields.Boolean(
        "Poznámky priložené", copy=True,
        help="Set when the Notes (Úč PODV 3-01) are filed with this statement; "
             "drives the header prilozeneSucasti/poznamky flag.")

    @api.depends("version_id")
    def _compute_l10n_sk_is_uzpod(self):
        version = self.env.ref("l10n_sk_fs.uzpod_v14", raise_if_not_found=False)
        for st in self:
            st.l10n_sk_is_uzpod = bool(version) and st.version_id == version

    # ------------------------------------------------------------------
    # header
    # ------------------------------------------------------------------
    def _l10n_sk_uzpod_header(self, size_class=None, statement_nature=None,
                              poznamky_attached=None):
        """The UZPODv14 ``hlavicka`` values. The keyword arguments let
        ``l10n.sk.uzpod`` file its own header choices over the same rows."""
        self.ensure_one()
        company = self.company_id
        partner = company.partner_id
        dic = ((company.l10n_sk_dic if "l10n_sk_dic" in company._fields
                else "") or company.vat or "").strip()
        if dic[:2].upper() == "SK":
            dic = dic[2:]
        # SK NACE: division, group+class, subclass (k1 k2 k3).
        nace = ((partner.nace_code if "nace_code" in partner._fields else "")
                or "").replace(".", "").ljust(5, "0")
        size = size_class or self.l10n_sk_size_class or "mala"
        nature = statement_nature or self.l10n_sk_statement_nature or "riadna"
        poznamky = (self.l10n_sk_poznamky_attached if poznamky_attached is None
                    else poznamky_attached)
        prior_from = self.date_from - relativedelta(years=1)
        prior_to = self.date_to - relativedelta(years=1)
        name = company.name or ""
        return {
            "den": str(self.date_to.day),
            "mesiac": str(self.date_to.month),
            "rok": str(self.date_to.year),
            "dic": dic,
            "ico": company.company_registry or "",
            "k1": nace[:2], "k2": nace[2:4], "k3": nace[4:5],
            "druh": {tag: "1" if tag == nature else "0"
                     for tag in ("riadna", "mimoriadna", "priebezna")},
            "velkost": {tag: "1" if tag == size else "0"
                        for tag in ("mala", "velka")},
            "obdobie": [(d.month, d.year) for d in (self.date_from, self.date_to)],
            "predobdobie": [(d.month, d.year) for d in (prior_from, prior_to)],
            "poznamky": "1" if poznamky else "0",
            # obchMeno / oznObchodReg require exactly 2 <riadok> lines
            "meno": [name[:36], name[36:72]],
            "ulica": partner.street or "",
            "psc": (partner.zip or "").replace(" ", ""),
            "obec": partner.city or "",
            "register": [getattr(company, "trade_registry", "") or "", ""],
            "telefon": partner.phone or "",
            "email": partner.email or "",
            # The day the statement is compiled, written as the other
            # Finančná správa forms of this repository write their dates.
            "zostavena": fields.Date.context_today(self).strftime("%d.%m.%Y"),
        }

    def _l10n_sk_uzpod_cells(self):
        """``{code: {g, k, n, p}}`` — brutto, korekcia, netto and prior netto
        of every row, in WHOLE EUROS, as the form is completed.

        Rounding each cell on its own does not survive the portal's
        kontrolné pravidlá: a total is checked against the sum of the rounded
        rows beneath it, and over a few dozen rows independent rounding drifts
        past a euro. So only the leaves are rounded — brutto and korekcia, with
        netto = brutto − korekcia — and every total is its own formula over
        its children's ROUNDED figures. The screen keeps the cents."""
        self.ensure_one()
        lines = {line.code: line for line in self.line_ids}
        cells = {}

        def whole(value):
            return int(float_round(value or 0.0, precision_digits=0))

        for ldef in self._cssk_eval_order():
            line = lines.get(ldef.code)
            if not line:
                continue
            if ldef.kind == "aggregate":
                cells[ldef.code] = {
                    col: int(round(self._eval_aggregate(
                        ldef.aggregate_formula,
                        {c: v[col] for c, v in cells.items()}) or 0))
                    for col in ("g", "k", "n", "p")
                }
            else:
                g, k = whole(line.gross_value), whole(line.correction_value)
                cells[ldef.code] = {"g": g, "k": k, "n": g - k,
                                    "p": whole(line.prior_value)}
        return cells

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self.l10n_sk_is_uzpod:
            header = self.env.context.get("l10n_sk_uzpod_header") or {}
            ctx["uzpod"] = self._l10n_sk_uzpod_header(**header)
            ctx["cells"] = self._l10n_sk_uzpod_cells()
        return ctx

    # ------------------------------------------------------------------
    # kontrolné pravidlá
    # ------------------------------------------------------------------
    def _cssk_check_kontroly(self):
        self.ensure_one()
        if self.l10n_sk_is_uzpod:
            self._cssk_enforce_kontroly()
        return super()._cssk_check_kontroly()

    def check_kontroly(self, xml_bytes=None):
        """The UZPODv14 rules (bilančná rovnosť, netto = brutto − korekcia,
        medzisúčty, unmapped accounts) on the document this statement files."""
        self.ensure_one()
        if not self.l10n_sk_is_uzpod:
            parent = getattr(super(), "check_kontroly", None)
            return parent(xml_bytes) if parent else []
        if xml_bytes is None:
            xml_bytes = self._render_xml()
        return self.env["l10n.sk.uzpod"].new({
            "company_id": self.company_id.id,
            "date_from": self.date_from,
            "date_to": self.date_to,
        })._cssk_uzpod_violations(xml_bytes)
