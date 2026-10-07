# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK Poznámky k účtovnej závierke — Úč PODV 3-01 (malé účtovné jednotky).

The third statutory part of the SK účtovná závierka (Súvaha + VZS + Poznámky),
per Opatrenie MF/23378/2014-74. Unlike Súvaha/VZS it is ~90 % narrative/policy
text + a few small tables, so this is a structured-content + template model, not
a GL calculation. v1 renders a fileable **PDF** (QWeb); the narrative fields
default to the standard malá-UJ boilerplate so the accountant edits only the
exceptions. A structured POZv14 XML export is a follow-up.
"""
import base64

from odoo import api, fields, models, _

# Standard malá-UJ "nemá náplň" boilerplate so a clean filing needs no editing.
_DEF_ORGANY = ("Členom štatutárneho orgánu, dozorného orgánu ani iného orgánu "
               "účtovnej jednotky neboli v účtovnom období poskytnuté žiadne "
               "príjmy, preddavky, pôžičky ani iné plnenia.")
_DEF_OCENOVANIE = (
    "Majetok a záväzky sa oceňujú v súlade so zákonom č. 431/2002 Z. z. "
    "o účtovníctve: dlhodobý hmotný a nehmotný majetok obstaraný kúpou "
    "obstarávacou cenou, vytvorený vlastnou činnosťou vlastnými nákladmi; "
    "zásoby obstarávacou cenou / vlastnými nákladmi; pohľadávky menovitou "
    "hodnotou; peňažné prostriedky a ceniny menovitou hodnotou; záväzky "
    "menovitou hodnotou. Opravné položky ani rezervy účtovná jednotka "
    "netvorila, ak nie je nižšie uvedené inak.")
_DEF_ZMENY = ("V účtovnom období nedošlo k zmenám účtovných zásad a účtovných "
              "metód oproti predchádzajúcemu účtovnému obdobiu.")
_DEF_CL4 = ("Účtovná jednotka neeviduje goodwill, deriváty, vlastné akcie ani "
            "výnimočné náklady a výnosy. Záväzky so zostatkovou dobou splatnosti "
            "nad päť rokov a záväzky zabezpečené záložným právom sú uvedené nižšie "
            "(ak existujú).")
_DEF_CL5 = ("Účtovná jednotka neeviduje podmienený majetok ani podmienené záväzky, "
            "ostatné finančné povinnosti ani významné položky podsúvahových účtov.")
_DEF_CL6 = ("Po dni, ku ktorému sa zostavuje účtovná závierka, do dňa jej "
            "zostavenia nenastali udalosti osobitného významu, ktoré by si "
            "vyžadovali úpravu alebo zverejnenie v poznámkach.")
_DEF_CL7 = ("Účtovná jednotka nemá výlučné práva ani povolenia, nepatrí do "
            "osobitnej kategórie priemyselnej výroby a nemá osobitné finančné "
            "vzťahy s orgánmi verejnej moci nad rámec bežných daňových povinností.")


class L10nSkPoznamkyOdpisLine(models.Model):
    _name = "l10n.sk.poznamky.odpis.line"
    _description = "Notes — depreciation-schedule line"
    _order = "sequence, id"

    poznamky_id = fields.Many2one("l10n.sk.poznamky", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    nazov = fields.Char("Skupina / účet majetku", required=True)
    doba_rokov = fields.Float("Doba odpisovania (roky)")
    sadzba = fields.Float("Ročná sadzba (%)")


class L10nSkPoznamky(models.Model):
    _name = "l10n.sk.poznamky"
    _description = "SK Notes to the financial statements (Úč PODV 3-01)"
    _order = "date_to desc, id desc"

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    submission_type = fields.Selection(
        [("radna", "Regular"), ("opravna", "Corrective")],
        default="radna", required=True, copy=False)
    state = fields.Selection(
        [("draft", "Draft"), ("generated", "Generated")],
        default="draft", readonly=True, copy=False)
    pdf_attachment_id = fields.Many2one("ir.attachment", readonly=True, copy=False)

    # --- Čl. I — Všeobecné informácie ---
    cinnost = fields.Text("Opis hospodárskej činnosti")
    schvalenie_date = fields.Date("Dátum schválenia predchádzajúcej závierky")
    pravny_dovod = fields.Selection(
        [("riadna", "Regular"), ("mimoriadna", "Extraordinary")],
        string="Legal basis for preparation", default="riadna")
    je_konsolidovana = fields.Boolean(
        "Je súčasťou konsolidovaného celku", default=False)
    zamestnanci_bezne = fields.Integer("Priemerný prepočítaný počet zamestnancov (bežné)")
    zamestnanci_predch = fields.Integer("… (predchádzajúce obdobie)")
    zamestnanci_veduci = fields.Integer("Z toho vedúci zamestnanci")

    # --- Čl. II — Orgány ---
    cl2_organy = fields.Text("Orgány — príjmy a výhody", default=_DEF_ORGANY)

    # --- Čl. III — Účtovné zásady a metódy ---
    going_concern = fields.Boolean("Nepretržité pokračovanie v činnosti", default=True)
    cl3_zmeny_metod = fields.Text("Zmeny účtovných zásad a metód", default=_DEF_ZMENY)
    cl3_ocenovanie = fields.Text("Spôsob oceňovania majetku a záväzkov", default=_DEF_OCENOVANIE)
    odpis_line_ids = fields.One2many(
        "l10n.sk.poznamky.odpis.line", "poznamky_id", string="Depreciation schedule")
    ddhm_prah = fields.Monetary("Prah DDHM", default=1700.0)
    dnm_prah = fields.Monetary("Prah DNM", default=2400.0)

    # --- Čl. IV — Položky VZS ---
    cl4 = fields.Text("Informácie k položkám výkazu ziskov a strát", default=_DEF_CL4)
    zavazky_nad_5_rokov = fields.Monetary("Záväzky so splatnosťou nad 5 rokov")
    zavazky_zabezpecene = fields.Monetary("Záväzky zabezpečené záložným právom")

    # --- Čl. V / VI / VII ---
    cl5 = fields.Text("Iné aktíva a iné pasíva", default=_DEF_CL5)
    cl6 = fields.Text("Udalosti po dni, ku ktorému sa zostavuje závierka", default=_DEF_CL6)
    cl7 = fields.Text("Ostatné informácie", default=_DEF_CL7)

    @api.depends("date_to", "submission_type")
    def _compute_name(self):
        for rec in self:
            suffix = _("(corrective)") if rec.submission_type == "opravna" else ""
            rec.name = "Poznámky %s%s" % (
                rec.date_to or "", (" " + suffix) if suffix else "")

    def action_populate_odpis(self):
        """Fill the odpisový plán from the company's posted assets (group by the
        depreciation duration). Best-effort: durations come from each asset's
        ``method_number`` (years); rate = 100 / years."""
        self.ensure_one()
        Asset = self.env.get("account.asset")
        self.odpis_line_ids.unlink()
        if Asset is None:
            return
        assets = Asset.search([("company_id", "=", self.company_id.id)])
        period_months = {"month": 1, "quarter": 3, "year": 12}
        groups = {}
        for a in assets:
            # method_number = number of depreciations; method_period = its length
            months = (a.method_number or 0) * period_months.get(a.method_period, 1)
            years = round(months / 12.0, 2) if months else 0.0
            cls = a.tax_class_id.name if "tax_class_id" in a._fields and a.tax_class_id else _("Majetok")
            groups.setdefault((cls, years), True)
        lines = []
        for (cls, years), _v in sorted(groups.items()):
            lines.append((0, 0, {
                "nazov": cls,
                "doba_rokov": years,
                "sadzba": round(100.0 / years, 2) if years else 0.0,
            }))
        self.odpis_line_ids = lines

    def action_generate_pdf(self):
        """Render the Poznámky as a PDF and store it on the record."""
        self.ensure_one()
        report = self.env.ref("l10n_sk_fs.action_report_l10n_sk_poznamky")
        pdf, _ext = report._render_qweb_pdf("l10n_sk_fs.report_l10n_sk_poznamky", self.ids)
        att = self.env["ir.attachment"].create({
            "name": "%s.pdf" % (self.name or "Poznamky"),
            "type": "binary",
            "datas": base64.b64encode(pdf),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
        })
        self.pdf_attachment_id = att.id
        self.state = "generated"
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % att.id,
            "target": "self",
        }
