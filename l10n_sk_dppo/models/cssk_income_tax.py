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
from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_core.tools import statutory_round

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
_SPINE_ROWS = frozenset({
    "r200", "r300", "r301", "r310", "r400", "r500", "r510", "r550",
    "r600", "r700", "r800", "r810", "r820", "r830", "r900",
    "r1050", "r1080", "r1100", "r1101",
})


class CSSKIncomeTaxVersion(models.Model):
    """The SK layer's answer to "which rows does this engine derive?"."""

    _inherit = "cssk.income.tax.version"

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
        return {code for code in self.line_def_ids.mapped("code")
                if code in _SPINE_ROWS}


class CSSKIncomeTaxReturn(models.Model):
    _inherit = "cssk.income.tax.return"

    # Codes the spine writes — present in every official DPPO form version.
    # Guard marker: a version missing any of them is NOT the DPPO form (a
    # custom/minimal SK version), and running the spine on it would clobber
    # its aggregates with zeros computed from nonexistent rows.
    _SK_DPPO_SPINE_CODES = frozenset({
        "r200", "r300", "r301", "r310", "r400", "r500", "r510",
        "r550", "r600", "r700", "r800", "r810", "r820", "r1050",
    })

    def _is_sk_dppo_form_version(self):
        self.ensure_one()
        codes = set(self.version_id.line_def_ids.mapped("code"))
        return self._SK_DPPO_SPINE_CODES.issubset(codes)

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
            raise UserError(_(
                "DPPO version '%(version)s' carries no usable %(label)s "
                "(field '%(field)s'): expected an ordered list of "
                "[upper_bound, value] pairs whose last band has a null upper "
                "bound. Fill the bands on the version record (they are "
                "noupdate data — on an existing database reload the "
                "l10n_sk_dppo version data). Refusing to guess a statutory "
                "rate.",
                version=self.version_id.display_name, label=label,
                field=field_name))
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

    def _dppo_rate(self, r560):
        """Sadzba dane % (§ 15) by úhrn zdaniteľných príjmov r560 — statutory
        schedule read from the version record (rate_bands)."""
        return self._dppo_band_value(
            self._dppo_version_bands("rate_bands", _("§ 15 rate bands")),
            r560)

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
            return bool(partner.l10n_sk_is_full_vat_payer)
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
        if "r560" not in set(self.version_id.line_def_ids.mapped("code")):
            r560 = self._eval_accounts("6")
        if r560 <= 0:
            return 0.0
        payer = self._dppo_is_vat_payer()
        base = self._dppo_band_value(
            self._dppo_version_bands(
                "min_tax_bands", _("§ 46b minimum-tax bands")),
            r560,
            {"vat_payer": payer, "not_vat_payer": not payer},
        )
        months = self._period_months()
        return base if months == 12 else statutory_round(
            base / 12.0 * months, 2)

    def _compute_tax_spine(self):
        self.ensure_one()
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
                    "row from every comparator built on it" % code)
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
        r200 = statutory_round(g("r110") + g("r130") + g("r140") + g("r150")
                               + g("r170") + g("r180"), 2)
        put("r200", r200)
        r300 = statutory_round(g("r210") + g("r220") + g("r230") + g("r240")
                               + g("r250") + g("r260") + g("r270") + g("r280")
                               + g("r290"), 2)
        put("r300", r300)
        r301 = statutory_round(g("r100") + r200 - r300, 2)
        put("r301", r301)

        r310 = statutory_round(g("r301") + g("r302") + g("r303") + g("r304")
                               + g("r305") + g("r306") - g("r307")
                               + g("r308"), 2)
        put("r310", r310)
        r400 = statutory_round(r310 - g("r320") - g("r330"), 2)
        put("r400", r400)
        r500 = (max(0.0, statutory_round(r400 - g("r410"), 2))
                if r400 > 0 else 0.0)
        put("r500", r500)
        r510 = statutory_round(r500 - g("r501") - g("r502") - g("r503"), 2)
        put("r510", r510)
        rate = self._dppo_rate(g("r560"))
        put("r550", rate)
        r600 = statutory_round(r510 * rate / 100.0, 2) if r510 > 0 else 0.0
        put("r600", r600)
        r700 = (max(0.0, statutory_round(r600 - g("r610"), 2))
                if r600 > 0 else 0.0)
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
