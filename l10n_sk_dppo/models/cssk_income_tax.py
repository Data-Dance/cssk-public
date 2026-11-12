# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK DPPO dodatočné priznanie — auto-fill the difference rows.

Per the DPPOv25 poučenie (§ II, oddiel Dodatočné daňové priznanie), each
"posledná známa" row repeats a source row from the previous return and each
"rozdiel" row is (this − previous). The poučenie's sign rules for the daň /
daňová strata transitions collapse exactly to ``current − previous``:

  posledná známa  rozdiel   zdroj (source)
    r1120          r1130    r1050  — daň / minimálna daň
    r1140          r1150    r400   — daňová strata
    r1160          r1170    r1060  — daň z osobitného základu § 17f
    r1180          r1190    r1070  — daň z osobitného základu § 51e
    r1191          r1192    r1071  — daň z osobitného základu § 51ea

DPPO is a FULL restatement, so ``original_return_id`` holds the previous full
values and this chains correctly across repeated dodatočné priznania (the prior
amendment's r1050/r400/… are its restated totals — no snapshot needed, unlike KV).
"""

import re
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_core.tools import split_street, statutory_round

# (posledná_známa_row, rozdiel_row, source_row)
_DODATOCNE_DIFF = [
    ("r1120", "r1130", "r1050"),
    ("r1140", "r1150", "r400"),
    ("r1160", "r1170", "r1060"),
    ("r1180", "r1190", "r1070"),
    ("r1191", "r1192", "r1071"),
]


# The rows the SK tax spine DERIVES. Declared once, and ``put()`` refuses a
# code that is not here — so this cannot quietly fall behind the spine the way
# a hand-kept list would. Every one of them is ``kind='manual'`` in the version
# data, which is the whole reason the set has to be stated somewhere: ``kind``
# names where a row's INPUT comes from, not whether we overwrite it.
# III. časť tables held as return lines: a06 = tabuľka A, riadok 6.
_TABLE_CODE = re.compile(r"[ab]\d\d")

_SPINE_ROWS = frozenset(
    {
        "r200",
        "r300",
        "r301",
        "r310",
        "r400",
        "r500",
        "r510",
        "r550",
        "r600",
        "r700",
        "r800",
        "r810",
        "r820",
        "r830",
        "r900",
        "r1050",
        "r1080",
        "r1100",
        "r1101",
    }
)

_SPINE_ROWS_2026 = (_SPINE_ROWS - {"r310"}) | {
    "r315",
    "r910",
    "r1000",
    "r1040",
    "r1110",
}


class CSSKIncomeTaxVersion(models.Model):
    """The SK layer's answer to "which rows does this engine derive?"."""

    _inherit = "cssk.income.tax.version"

    l10n_sk_dppo_layout = fields.Selection(
        [("legacy", "Earlier published layout"), ("2026", "MF/014309/2026-721")],
        string="DPPO form layout",
        default="legacy",
        required=True,
    )
    l10n_sk_dppo_publication = fields.Selection(
        [
            ("xml", "Published XML schema"),
            ("paper", "Published form; XML schema pending"),
        ],
        string="DPPO form publication",
        default="xml",
        required=True,
    )

    def _cssk_derived_codes(self):
        """The tax spine's write-set, intersected with what the vzor defines.

        Older vzory do not carry every row the spine can write — r830 exists
        on 2013-2015 and 2024+ and nowhere else, r810/r820 vanish across
        2020-2022 with the daňová licencia — so the answer is per version, not
        a constant. Non-SK versions inherit the base's empty set.
        """
        self.ensure_one()
        if (self.country_id.code or "").upper() != "SK":
            return super()._cssk_derived_codes()
        # Row310 is a NEW accountant input (§17k); the subtotal moved315.
        spine = _SPINE_ROWS_2026 if self.l10n_sk_dppo_layout == "2026" else _SPINE_ROWS
        return set(self.line_def_ids.mapped("code")) & spine


class CSSKIncomeTaxReturn(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_legacy_advance_relief = fields.Boolean(
        string="Legacy section 35/35a relief: leave row 1110 blank"
    )
    l10n_sk_legacy_advance_evidence = fields.Text(
        string="Legacy advance-tax relief evidence"
    )

    def _l10n_sk_check_advance_relief(self):
        self.ensure_one()
        if self.l10n_sk_legacy_advance_relief:
            relief = self.line_ids.filtered(lambda row: row.code == "r610").value
            advance = self.line_ids.filtered(lambda row: row.code == "r1110").value
            if (
                relief <= 0
                or advance
                or not (self.l10n_sk_legacy_advance_evidence or "").strip()
            ):
                raise UserError(
                    _(
                        "Review the legacy section 35/35a relief, its evidence and the blank row 1110."
                    )
                )

    l10n_sk_dppo_filing_deadline = fields.Date(
        string="Applicable legal filing deadline",
        help="The legal deadline including an effective extension, when it "
        "differs from the ordinary three-calendar-month deadline. "
        "This is not the actual filing date.",
    )
    l10n_sk_dppo_applicable_version_ids = fields.Many2many(
        "cssk.income.tax.version",
        string="Applicable DPPO form versions",
        compute="_compute_sk_applicable_versions",
    )
    version_id = fields.Many2one(
        domain="[('id', 'in', l10n_sk_dppo_applicable_version_ids)]"
    )

    def _l10n_sk_dppo_requires_2026_form(self):
        """MF014310 uses the legal DEADLINE, independently of period start.

        For the ordinary return, the end of the third calendar month is
        sufficient to decide this2026-12-31 cutoff (a working Thursday).
        An effective extension is an explicit stored taxpayer fact. The
        actual day of filing must never replace that legal deadline.
        """
        self.ensure_one()
        if not self.date_to:
            return False
        deadline = self.l10n_sk_dppo_filing_deadline or (
            self.date_to + relativedelta(months=3, day=31)
        )
        return deadline > date(2026, 12, 31)

    @api.depends("company_id", "date_from", "date_to", "l10n_sk_dppo_filing_deadline")
    def _compute_sk_applicable_versions(self):
        Version = self.env["cssk.income.tax.version"].with_context(active_test=False)
        for ret in self:
            country = ret.company_id.account_fiscal_country_id
            domain = [("country_id", "=", country.id)]
            if not (ret.date_from and ret.date_to and country):
                ret.l10n_sk_dppo_applicable_version_ids = False
                continue
            if country.code == "SK" and ret._l10n_sk_dppo_requires_2026_form():
                # The new form's ordinary-period valid_from is not a second
                # legal condition on the announcement's deadline criterion.
                domain += [("l10n_sk_dppo_layout", "=", "2026")]
            else:
                domain += [
                    ("valid_from", "<=", ret.date_to),
                    "|",
                    ("valid_to", "=", False),
                    ("valid_to", ">=", ret.date_from),
                ]
                if country.code == "SK":
                    domain += [("l10n_sk_dppo_layout", "!=", "2026")]
            ret.l10n_sk_dppo_applicable_version_ids = Version.search(domain)

    def _l10n_sk_dppo_check_form_applicability(self):
        """Shared by the paper adapter and XML eligibility checks."""
        for ret in self:
            if (ret.country_id.code or "").upper() != "SK":
                continue
            new_form = ret.version_id.l10n_sk_dppo_layout == "2026"
            if ret._l10n_sk_dppo_requires_2026_form() != new_form:
                raise UserError(
                    _(
                        "The selected DPPO form does not cover the applicable "
                        "legal filing deadline. Select the published form for "
                        "that deadline, including any effective extension."
                    )
                )
        return True

    def _cssk_preflight_export(self):
        self._l10n_sk_dppo_check_form_applicability()
        for ret in self:
            version = ret.version_id
            if (
                (ret.country_id.code or "").upper() == "SK"
                and version.l10n_sk_dppo_layout != "2026"
                and (
                    ret.date_to < version.valid_from
                    or (version.valid_to and ret.date_from > version.valid_to)
                )
            ):
                raise UserError(
                    _(
                        "The selected DPPO form does not cover this tax period. "
                        "Select its applicable published version before XML export."
                    )
                )
            if ret.version_id.l10n_sk_dppo_publication == "paper":
                raise UserError(
                    _(
                        "The published DPPO form can be calculated, but its "
                        "official XML schema is not installed. Install the "
                        "published electronic version before XML export."
                    )
                )
        return super()._cssk_preflight_export()

    # Codes the spine writes — present in every official DPPO form version.
    # Guard marker: a version missing any of them is NOT the DPPO form (a
    # custom/minimal SK version), and running the spine on it would clobber
    # its aggregates with zeros computed from nonexistent rows.
    _SK_DPPO_SPINE_CODES = frozenset(
        {
            "r200",
            "r300",
            "r301",
            "r310",
            "r400",
            "r500",
            "r510",
            "r550",
            "r600",
            "r700",
            "r800",
            "r810",
            "r820",
            "r1050",
        }
    )

    def _is_sk_dppo_form_version(self):
        self.ensure_one()
        codes = set(self.version_id.line_def_ids.mapped("code"))
        return self._SK_DPPO_SPINE_CODES.issubset(codes)

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx["hdr"] = self._l10n_sk_dppo_header()
        ctx["values_tab"] = self._l10n_sk_dppo_table_values()
        return ctx

    def _l10n_sk_dppo_table_rows(self):
        """The Table A/B lines of this return (codes ``a01``…, ``b01``…)."""
        return self.line_ids.filtered(
            lambda line: _TABLE_CODE.fullmatch(line.code or "")
        )

    def _l10n_sk_dppo_table_values(self):
        """``{code: "123.45"}`` for the Table A/B cells the XML carries.

        A row nobody touched is left OUT, so the template files it empty —
        "U daňovníka sa vypĺňajú len tie tabuľky III. časti, ktoré vecne
        súvisia s údajmi jeho priznania" (poučenie, III. časť). A row the
        accountant set, even to 0, and a row with a value are filed.
        """
        self.ensure_one()
        return {
            line.code: "%.2f" % line.value
            for line in self._l10n_sk_dppo_table_rows()
            if line.is_overridden or round(line.value, 2)
        }

    def _l10n_sk_dppo_header(self):
        """The company-derived DPPO ``hlavicka`` values, for every vzor.

        * ``dic`` — the Slovak DIČ (``l10n_sk_dic``); the IČ DPH only as a
          fallback and without its "SK", which is not part of a DIČ.
        * ``k1``/``k2``/``k3`` — SK NACE from ``partner_nace`` when installed
          and filled; the schema makes them mandatory digits, so "0" otherwise.
        * ``pravna_forma`` — the register's wording from
          ``l10n_sk_trade_registry`` when installed.
        * ``cislo`` — the house number split off ``street`` (never the
          second address line, unless that is only a number).
        * ``datum_vyhlasenia`` — the day the return is exported.

        What the data model does not hold (oprávnená osoba, the § 50
        prijímateľ, tables A–K) is left empty for the filer.
        """
        self.ensure_one()
        company = self.company_id
        partner = company.partner_id
        dic = (
            (company.l10n_sk_dic if "l10n_sk_dic" in company._fields else "") or ""
        ).strip()
        if not dic:
            dic = (company.vat or "").replace(" ", "")
            if dic[:2].upper() == "SK":
                dic = dic[2:]
        nace = re.sub(
            r"\D",
            "",
            (partner.nace_code or "") if "nace_code" in partner._fields else "",
        )
        if nace:
            nace = nace.ljust(5, "0")
            k1, k2, k3 = nace[:2], nace[2:4], nace[4:5]
        else:
            k1 = k2 = k3 = "0"
        legal_form = ""
        for holder in (company, partner):
            if "l10n_sk_legal_form" in holder._fields:
                legal_form = holder.l10n_sk_legal_form or ""
                if legal_form:
                    break
        street, number = split_street(partner)
        return {
            "dic": dic,
            "ico": (company.company_registry or "").replace(" ", ""),
            "pravna_forma": legal_form,
            "k1": k1,
            "k2": k2,
            "k3": k3,
            "ulica": street,
            "cislo": number,
            "psc": (partner.zip or "").replace(" ", ""),
            "obec": partner.city or "",
            "stat": partner.country_id.name or "",
            "datum_vyhlasenia": fields.Date.context_today(self).strftime("%d.%m.%Y"),
        }

    def action_compute_lines(self):
        res = super().action_compute_lines()
        if self.country_id.code == "SK" and self._is_sk_dppo_form_version():
            self._compute_tax_spine()
            if self.original_return_id:
                self._fill_dodatocne_differences()
        return res

    # ------------------------------------------------------------------
    # Tax spine  (r100 -> daň), authoritatively from the DPPOv25 eForm
    # ------------------------------------------------------------------
    # Exact arithmetic from form.622.html (vypocet_r* / inliner*):
    #   r310 = r301+r302+r303+r304+r305+r306 - r307 + r308
    #   r400 = r310 - r320 - r330
    #   r500 = max(0, r400 - r410)              (0 if r400 <= 0)
    #   r510 = r500 - r501 - r502 - r503        (odpočet § 30c výskum a vývoj)
    #   r550 = sadzba dane (§ 15) by úhrn zdaniteľných príjmov r560
    #   r600 = r510 × r550/100                  (daň; 0 if r510 <= 0)
    #   r700 = max(0, r600 - r610)              (úľava na dani)
    #   r800 = r700 - r710                       (zápočet zahraničnej dane)
    #   r810 = minimálna daň (§ 46b) by r560, prorated by months
    #   r820 = r810 if r810 > r800 else 0
    # The judgment items (r301–r308 pripočítateľné/odpočítateľné, r320/r330,
    # r410 odpočet straty, r501–r503, r560 úhrn príjmov, r610/r710) stay manual.
    # The min-tax zápočet carry-forward (r830–r1000, cross-year table) stays
    # manual; r1050 defaults to max(daň, minimálna daň) for the common case.
    # Any row the accountant overrides (is_overridden) is left untouched.

    # The § 15 rate schedule and the § 46b minimum-tax schedule are STATUTORY
    # DATA that changes with the law, not with the code — they live on the
    # version record (cssk.income.tax.version.rate_bands / min_tax_bands,
    # populated by data/dppo_version*_data.xml per form year) as ordered
    # [upper_bound_inclusive, value] pairs keyed on r560, the last band with a
    # null upper bound. A version without bands raises loudly: silently
    # applying a wrong rate is worse than stopping the computation.

    def _dppo_version_bands(self, field_name, label):
        self.ensure_one()
        bands = self.version_id[field_name] or []
        if not bands or not bands[-1] or bands[-1][0] is not None:
            raise UserError(
                _(
                    "DPPO version '%(version)s' carries no usable %(label)s "
                    "(field '%(field)s'): expected an ordered list of "
                    "[upper_bound, value] pairs whose last band has a null upper "
                    "bound. Fill the bands on the version record (they are "
                    "noupdate data — on an existing database reload the "
                    "l10n_sk_dppo version data). Refusing to guess a statutory "
                    "rate.",
                    version=self.version_id.display_name,
                    label=label,
                    field=field_name,
                )
            )
        return bands

    @staticmethod
    def _dppo_band_value(bands, r560, conditions=None):
        """Value of the first band that covers r560 and whose condition holds.

        A band is ``[upper_bound, value]`` — inclusive bound, null last band
        catches everything above — or ``[upper_bound, value, condition]``,
        where the condition names a fact about the taxpayer that turnover
        cannot express. § 46b's daňová licencia needs it: 480 € and 960 € sit
        at the SAME turnover bound and are told apart by whether the taxpayer
        was a platiteľ DPH on the last day of the period.

        Unknown conditions never match, so a band nobody can evaluate is
        skipped rather than silently applied.
        """
        conditions = conditions or {}
        for band in bands:
            upper, value = band[0], band[1]
            if upper is not None and r560 > upper:
                continue
            if len(band) > 2 and not conditions.get(band[2]):
                continue
            return value

    def check_kontroly(self):
        """Tables A/B against the rows they feed, and § 30 ods. 1.

        The table check is an error (see ``_l10n_sk_dppo_table_kontroly``).
        The § 30 ods. 1 check concerns the loss deduction against the base.

        A warning rather than an error, and silent up to 100 000 € of income:
        a mikrodaňovník may deduct up to the whole base, and that status also
        depends on facts the return does not hold. The 50 % limit took effect
        for periods from 2020.
        """
        self.ensure_one()
        out = []
        values = {line.code: line.value for line in self.line_ids}
        r400 = values.get("r400") or 0.0
        r410 = values.get("r410") or 0.0
        limit = statutory_round(r400 * 0.5, 2)
        if (self.country_id.code or "").upper() == "SK":
            out += self._l10n_sk_dppo_table_kontroly()
        if (
            self.date_from.year >= 2020
            and r410 > limit + 0.005
            and (values.get("r560") or 0.0) > 100000.0
        ):
            out.append(
                {
                    "code": "DPPO_LOSS_50",
                    "severity": "warning",
                    "desc": _("Loss deduction above 50 % of the tax base"),
                    "detail": _(
                        "r410 is %(loss).2f but § 30 ods. 1 písm. b) allows "
                        "%(limit).2f unless the company is a mikrodaňovník.",
                        loss=r410,
                        limit=limit,
                    ),
                }
            )
        return out

    def _l10n_sk_dppo_table_kontroly(self):
        """An overridden row must still agree with the table it is derived from.

        r130 is the úhrn of tabuľka A and r150/r250 the difference of
        tabuľka B, and the eForm refuses a priznanie where they disagree
        ("'r.130': má byť suma rovná sume uvedenej v tabuľke A na riadku 17",
        vypocet_r130_C0). Every row derived from a table is an ``aggregate``
        line, so the check reads the formulas instead of naming rows — the
        same code serves both table layouts, and the úhrn rows themselves
        (a17, b06) are held to their own formulas the same way.

        Only where the table carries something: a return that types r150
        straight onto the main row and leaves tabuľka B empty is how it was
        filed before the tables existed here, and stays valid.
        """
        self.ensure_one()
        lines = {line.code: line for line in self.line_ids}
        values = {code: line.value for code, line in lines.items()}
        defs = {d.code: d for d in self.version_id.line_def_ids}
        filled = {
            letter
            for letter in "ab"
            if any(
                round(line.value, 2) or line.is_overridden
                for code, line in lines.items()
                if code[:1] == letter
                and _TABLE_CODE.fullmatch(code)
                and defs.get(code)
                and defs[code].kind != "aggregate"
            )
        }
        out = []
        for code, line in lines.items():
            ldef = defs.get(code)
            if not (line.is_overridden and ldef and ldef.kind == "aggregate"):
                continue
            names = self._aggregate_dependencies(ldef.aggregate_formula)
            letters = {n[:1] for n in names if _TABLE_CODE.fullmatch(n)}
            if not letters or not letters & filled:
                continue
            expected = self._eval_aggregate(ldef.aggregate_formula, values)
            if (
                abs(statutory_round(expected, 2) - statutory_round(line.value, 2))
                < 0.005
            ):
                continue
            out.append(
                {
                    "code": "DPPO_TABLE_%s" % code.upper(),
                    "severity": "error",
                    "desc": _("%(code)s disagrees with its table", code=code),
                    "detail": _(
                        "%(code)s is overridden to %(value).2f, but %(formula)s "
                        "over the table gives %(expected).2f. Correct the table "
                        "or remove the override.",
                        code=code,
                        value=line.value,
                        formula=ldef.aggregate_formula,
                        expected=expected,
                    ),
                }
            )
        return out

    def _cssk_check_kontroly(self):
        self.ensure_one()
        self._cssk_enforce_kontroly()
        return True

    def _dppo_rate(self, r560):
        """Sadzba dane % (§ 15) by úhrn zdaniteľných príjmov r560 — statutory
        schedule read from the version record (rate_bands)."""
        return self._dppo_band_value(
            self._dppo_version_bands("rate_bands", _("§ 15 rate bands")), r560
        )

    def _period_months(self):
        df, dt = self.date_from, self.date_to
        if not dt or dt < df:
            return 12
        return (dt.year - df.year) * 12 + (dt.month - df.month) + 1

    def _dppo_is_vat_payer(self):
        """Platiteľ DPH k poslednému dňu zdaňovacieho obdobia (§ 46b ods. 2).

        Read from ``l10n_sk_vat_registration`` when it is installed, because
        that module records the registration and the date it took effect —
        which is what the statute asks about, a status on one specific day.

        Without it, falls back to whether the company carries a VAT number at
        all. That is an APPROXIMATION and it errs downwards: a registered
        company with no ``vat`` on its record lands in the 480 band instead of
        960. Install ``l10n_sk_vat_registration`` on any agenda where the
        licencia is actually computed.
        """
        self.ensure_one()
        partner = self.company_id.partner_id
        if "l10n_sk_vat_payer_since" in partner._fields:
            since = partner.l10n_sk_vat_payer_since
            if since:
                return since <= self.date_to
            if partner.l10n_sk_vat_registration_category:
                return bool(partner.l10n_sk_is_full_vat_payer)
            # Category never recorded: the module knows nothing, so it must
            # not decide "not a payer" — fall back as if it were absent.
        return bool(self.company_id.vat)

    def _dppo_min_tax(self, r560):
        """Minimálna daň / daňová licencia (§ 46b) — the band amount from the
        version record (min_tax_bands), prorated by months. Polovičná sadzba
        (ods. 3), neplatenie and oslobodenie (ods. 7) are accountant overrides.

        ⚠️ The licencia vzory (2014-2019) have **no r560**. That row arrived
        with the 2020 form, for the § 15 reduced-rate test, so the older
        tlačivo carries no turnover figure at all and the band has nothing on
        the form to key on. We fall back to the same basis the later form uses
        for r560 — class 6 revenue, which is literally r560's own
        ``account_formula`` — rather than to nothing, because a silent 0,00
        here means "no licencia owed", which is the wrong answer for almost
        every taxpayer.

        That is a reading, not a citation: the older poučenie does not define
        ročný obrat by reference to a row, because it has none to point at.
        Override r810 where the taxpayer's obrat differs from class 6.
        """
        self.ensure_one()
        if self._dppo_licencia_abolished():
            return 0.0
        if "r560" not in set(self.version_id.line_def_ids.mapped("code")):
            r560 = self._eval_accounts("6")
        if r560 <= 0:
            return 0.0
        payer = self._dppo_is_vat_payer()
        base = self._dppo_band_value(
            self._dppo_version_bands("min_tax_bands", _("§ 46b minimum-tax bands")),
            r560,
            {"vat_payer": payer, "not_vat_payer": not payer},
        )
        months = self._period_months()
        return base if months == 12 else statutory_round(base / 12.0 * months, 2)

    def _dppo_licencia_abolished(self):
        """Whether § 52zk says this period owes no daňová licencia at all.

        § 52zk zák. 595/2003 Z. z. (prechodné ustanovenie k úpravám účinným
        od 1. januára 2018): "Ustanovenie § 46b v znení účinnom do
        31. decembra 2017 sa naposledy uplatní za zdaňovacie obdobie končiace
        31. decembra 2017, a ak je zdaňovacím obdobím hospodársky rok, za
        zdaňovacie obdobie končiace v priebehu kalendárneho roka 2018."

        The 2018 and 2019 vzory still print the licencia rows — the zápočet of
        an earlier licencia (§ 46b ods. 5) runs on after 2017, and a
        hospodársky rok ending in 2018 still pays one — so their version
        records keep the bands. Whether a band applies is a fact about the
        PERIOD, not about the vzor, and it is decided here.

        Only the licencia-era vzory (before the 2020 form) are gated: the
        minimálna daň from 2024 is a different § 46b and has its own vzory.
        """
        self.ensure_one()
        version_from = self.version_id.valid_from
        if not version_from or version_from >= date(2020, 1, 1):
            return False
        end = self.date_to
        if not end or end <= date(2017, 12, 31):
            return False
        # A hospodársky rok is a twelve-month period that is not the calendar
        # year, so it cannot end on 31 December.
        hospodarsky_rok = (end.month, end.day) != (12, 31)
        return not (hospodarsky_rok and end.year == 2018)

    def _compute_tax_spine(self):
        self.ensure_one()
        if self.version_id.l10n_sk_dppo_layout == "2026":
            return self._compute_tax_spine_2026()
        by = {line.code: line for line in self.line_ids}

        def g(code):
            line = by.get(code)
            return line.value if line else 0.0

        def put(code, value):
            # The guard is what keeps _SPINE_ROWS honest: a row the spine
            # learns to write, and nobody adds here, fails on the next
            # compute rather than silently dropping out of
            # ``_cssk_derived_codes`` and out of every comparison built on it.
            # A raise, not an assert: `python -O` strips asserts, and a guard
            # that disappears under a flag is not a guard.
            if code not in _SPINE_ROWS:
                raise ValueError(
                    "the SK tax spine writes %s but _SPINE_ROWS does not list "
                    "it — add it there, or _cssk_derived_codes() will hide the "
                    "row from every comparator built on it" % code
                )
            line = by.get(code)
            if line and not line.is_overridden:
                line.value = value

        # Base cascade (DPPOv24/v25 eForm vypocet_r200/_r300/_r301):
        #   r200 = pripočítateľné položky  = r110+r130+r140+r150+r170+r180
        #   r300 = odpočítateľné položky    = r210+r220+…+r290
        #   r301 = všeobecný základ dane    = r100 + r200 − r300
        # i.e. the accounting result (r100) flows into the base — the user enters
        # the individual judgment rows (r110…r290), not r301 itself. (The eForm
        # adds ± r.11 tabuľky H transfer-pricing úprava; model that as an r301
        # override when it applies.)
        # The 2013-2017 vzory also carry r120 (pokuty/úroky z omeškania
        # under § 17 ods. 19 as in force to 2014, § 52 ods. 12 príjmy, studies)
        # and r160 (§ 17 ods. 17 kurzové rozdiely), both in the "zvyšujúce"
        # block that r200 totals (DPPOv15/v17 poučenie, riadky 110 až 180).
        # g() is 0 for a vzor without them, so one formula serves every vzor.
        r200 = statutory_round(
            g("r110")
            + g("r120")
            + g("r130")
            + g("r140")
            + g("r150")
            + g("r160")
            + g("r170")
            + g("r180"),
            2,
        )
        put("r200", r200)
        r300 = statutory_round(
            g("r210")
            + g("r220")
            + g("r230")
            + g("r240")
            + g("r250")
            + g("r260")
            + g("r270")
            + g("r280")
            + g("r290"),
            2,
        )
        put("r300", r300)
        r301 = statutory_round(g("r100") + r200 - r300, 2)
        put("r301", r301)

        r310 = statutory_round(
            g("r301")
            + g("r302")
            + g("r303")
            + g("r304")
            + g("r305")
            + g("r306")
            - g("r307")
            + g("r308"),
            2,
        )
        put("r310", r310)
        r400 = statutory_round(r310 - g("r320") - g("r330"), 2)
        put("r400", r400)
        r500 = max(0.0, statutory_round(r400 - g("r410"), 2)) if r400 > 0 else 0.0
        put("r500", r500)
        r510 = statutory_round(r500 - g("r501") - g("r502") - g("r503"), 2)
        put("r510", r510)
        rate = self._dppo_rate(g("r560"))
        put("r550", rate)
        r600 = statutory_round(r510 * rate / 100.0, 2) if r510 > 0 else 0.0
        put("r600", r600)
        r700 = max(0.0, statutory_round(r600 - g("r610"), 2)) if r600 > 0 else 0.0
        put("r700", r700)
        r800 = statutory_round(r700 - g("r710"), 2)
        put("r800", r800)
        r810 = self._dppo_min_tax(g("r560"))
        put("r810", r810)
        # KLADNÝ ROZDIEL — and WHICH ROW carries it depends on the vzor,
        # because the form reused the number. Verified against the pinned FS SR
        # schemas: 2017/2018/2019 define r800/r810/r820 and NO r830, while
        # 2013-2015 and 2024+ define r830 as well.
        #
        #   licencia era, no r830   -> r820 is the rozdiel
        #   r830 present            -> r830 is the rozdiel, r820 is other
        #
        # Finančná správa's own usmernenie (20. 12. 2018) prints the licencia
        # vzor's captions and its worked example: r800 600, r810 960,
        # r820 360 — i.e. r810 − r800, not r810. This branch used to write
        # r810 into r820 on every vintage, which was right for the minimálna
        # daň forms and wrong for the three licencia ones.
        rozdiel = max(0.0, statutory_round(r810 - r800, 2))
        # Daň-na-úhradu cascade (DPPOv25 poučenie r830/r900/r1050/r1080/r1100/r1101).
        # r830 = kladný rozdiel medzi minimálnou daňou (r810) a daňou (r800) — the
        #        carry-forwardable min-tax surplus (§ 46b ods. 5).
        if "r830" in {d.code for d in self.version_id.line_def_ids}:
            put("r820", r810 if r810 > r800 else 0.0)
            put("r830", rozdiel)
        else:
            put("r820", rozdiel)
        # r900 = suma na účely určenia výšky preddavkov: the minimum tax when the
        #        payer actually pays it (override for § 46b ods. 3/7 halving/
        #        exemption, or to add r840, in those cases).
        if r810 > r800:
            put("r900", r810)
        # r1050 = daň pred úpravou o preddavky na daň alebo minimálna daň.
        r1050 = max(r800, r810)
        put("r1050", r1050)
        # r1080 = celková daň = súčet riadkov 1050 + 1060 + 1070 + 1071.
        r1080 = statutory_round(r1050 + g("r1060") + g("r1070") + g("r1071"), 2)
        put("r1080", r1080)
        # r1100 = daň (min. daň) na úhradu, nedoplatok (+) = r1080 − preddavky
        #         (r1040); nula ak ≤ 5 €. r1101 = daňový preplatok (−).
        settle = statutory_round(r1080 - g("r1040"), 2)
        put("r1100", settle if settle > 5.0 else 0.0)
        put("r1101", settle if settle < 0.0 else 0.0)

    def _compute_tax_spine_2026(self):
        """Published MF/014309/2026-721, pages2–5 and its official guidance.

        The input row310 now means §17k, while the subtotal moved315 and
        the sports input306 shifted the vehicle/CFC rows. Reusing the older
        spine would overwrite a real adjustment. Read every effective row
        after writing it: reviewed exemptions and other accountant overrides
        must flow to downstream rows, including the bookable tax1050.
        """
        self.ensure_one()
        by = {line.code: line for line in self.line_ids}

        def g(code):
            return by[code].value if code in by else 0.0

        def put(code, amount):
            if code not in _SPINE_ROWS_2026:
                raise ValueError("Undeclared published2026 DPPO derived row: %s" % code)
            line = by[code]
            if not line.is_overridden:
                line.value = statutory_round(amount, 2)
            return line.value

        put(
            "r200",
            sum(g(code) for code in ("r110", "r130", "r140", "r150", "r170", "r180")),
        )
        put("r300", sum(g("r%s" % code) for code in range(210, 300, 10)))
        put("r301", g("r100") + g("r200") - g("r300"))
        put(
            "r315",
            sum(g("r%s" % code) for code in range(301, 308))
            - g("r308")
            + g("r309")
            + g("r310"),
        )
        put("r400", g("r315") - g("r320") - g("r330"))
        put("r500", max(0.0, g("r400") - g("r410")))
        put("r510", max(0.0, g("r500") - g("r501") - g("r502") - g("r503")))
        put("r550", self._dppo_rate(g("r560")))
        put("r600", max(0.0, g("r510")) * g("r550") / 100.0)
        put("r700", max(0.0, g("r600") - g("r610")))
        put("r800", max(0.0, g("r700") - g("r710")))
        # A zero turnover does not itself exempt an ordinary taxpayer.
        # §46b(7) exemptions/halving remain explicit reviewed row810 inputs.
        minimum = self._dppo_band_value(
            self._dppo_version_bands("min_tax_bands", _("§ 46b minimum-tax bands")),
            g("r560"),
        )
        # §46b(2)(e) applies to periods STARTING from1.1.2026. A fiscal
        # period2025/26 may use the new form, but retains the older ceiling.
        if self.date_from < date(2026, 1, 1):
            minimum = min(minimum, 3840.0)
        put("r810", minimum * self._period_months() / 12.0)
        put("r820", g("r810") if g("r810") > g("r800") else 0.0)
        put("r830", max(0.0, g("r810") - g("r800")))
        put("r900", g("r820"))
        put("r910", max(0.0, g("r800") - g("r810")))
        if g("r920") < 0 or statutory_round(g("r920") - g("r910"), 2) > 0:
            raise UserError(
                _(
                    "The reviewed prior minimum-tax credit (row920) must be "
                    "nonnegative and cannot exceed row910. Review Table K."
                )
            )
        put("r1000", max(0.0, g("r800") - g("r920")) if g("r920") else 0.0)
        put(
            "r1050",
            g("r1000")
            if g("r1000") > 0
            else (g("r900") if g("r810") > g("r800") else g("r800")),
        )
        put("r1040", g("r1010") + g("r1020") + g("r1030"))
        put(
            "r1080",
            sum(g(code) for code in ("r1050", "r1060", "r1070", "r1071", "r1072")),
        )
        settlement = statutory_round(g("r1080") - g("r1090") - g("r1040"), 2)
        put("r1100", settlement if settlement > 5 else 0.0)
        put("r1101", min(0.0, settlement))
        # Published guidance, page12: use r500 BEFORE deductions501-503,
        # subtract610, irrespective of minimum tax or withholding credits.
        put(
            "r1110",
            0
            if self.l10n_sk_legacy_advance_relief
            else g("r500") * g("r550") / 100.0 - g("r610"),
        )
        self._l10n_sk_check_advance_relief()

    def _fill_dodatocne_differences(self):
        """Fill the 'posledná známa' rows from the previous return and the
        'rozdiel' rows as (this − previous). Manual overrides are respected."""
        self.ensure_one()
        prev = {line.code: line.value for line in self.original_return_id.line_ids}
        by_code = {line.code: line for line in self.line_ids}
        for known, diff, src in _DODATOCNE_DIFF:
            prev_val = prev.get(src, 0.0)
            cur_val = by_code[src].value if src in by_code else 0.0
            if known in by_code and not by_code[known].is_overridden:
                by_code[known].value = prev_val
            if diff in by_code and not by_code[diff].is_overridden:
                by_code[diff].value = cur_val - prev_val
