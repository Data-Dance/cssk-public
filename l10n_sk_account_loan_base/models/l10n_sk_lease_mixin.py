# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

# Doba odpisovania per odpisová skupina, § 26 ods. 1 zákona 595/2003.
SK_DEPRECIATION_YEARS = {
    "1": 4,
    "2": 6,
    "3": 8,
    "4": 12,
    "5": 20,
    "6": 40,
}

# § 2 písm. s) bod 1: finančným prenájmom je obstaranie hmotného majetku s
# dojednaným právom kúpy, pri ktorom doba trvania nájmu je najmenej 60 % doby
# odpisovania. (The former "and at least three years" condition was dropped.)
SK_MIN_LEASE_SHARE = 0.60


def sk_min_lease_months(group):
    """Minimum lease term in months for the arrangement to be finančný prenájom."""
    years = SK_DEPRECIATION_YEARS.get(group)
    if not years:
        return 0
    return int(round(years * 12 * SK_MIN_LEASE_SHARE))


class L10nSkLeaseMixin(models.AbstractModel):
    _name = "l10n.sk.lease.mixin"
    _description = "Slovak finančný prenájom — statutory qualifiers"

    # An AbstractModel, so this lives in the engine-neutral base and both
    # bridges can mix it into their own account.loan without the base ever
    # touching an engine (asserted by tools/check_module_parity.py).

    l10n_sk_vat_treatment = fields.Selection(
        [
            ("goods", "Dodanie tovaru (§ 8 ods. 1 písm. c)"),
            ("service", "Dodanie služby"),
        ],
        string="Režim DPH",
        default="goods",
        help="Finančný prenájom je DODANÍM TOVARU, ak zo zmluvy vyplýva prevod "
             "vlastníctva najneskôr zaplatením poslednej splátky — vtedy daňová "
             "povinnosť vzniká RAZ, dňom odovzdania predmetu nájmu, z celej "
             "dohodnutej ceny.\n\n"
             "Inak ide o DODANIE SLUŽBY a daň sa uplatňuje z každej splátky.\n\n"
             "Od 1. 1. 2025 sa posudzuje ekonomická podstata, nie znenie zmluvy: "
             "rozhoduje, či je uplatnenie opcie pre nájomcu jedinou ekonomicky "
             "racionálnou voľbou (v nadväznosti na C-164/16 Mercedes-Benz).",
    )
    l10n_sk_depreciation_group = fields.Selection(
        [(key, _("Odpisová skupina %s (%s rokov)", key, years))
         for key, years in sorted(SK_DEPRECIATION_YEARS.items())],
        string="Odpisová skupina predmetu",
        help="Slúži len na overenie 60 % podmienky. Samotné odpisovanie je od "
             "1. 1. 2015 bežné — lízingové odpisy boli zrušené zákonom 333/2014, "
             "takže prenajatý majetok sa odpisuje počas doby odpisovania v "
             "príslušnej odpisovej skupine (§ 26 ods. 8).",
    )
    l10n_sk_lease_months = fields.Integer(
        string="Doba trvania nájmu (mesiace)",
        compute="_compute_l10n_sk_lease_months",
        help="Dopĺňa bridge podľa polí konkrétneho enginu.",
    )
    l10n_sk_lease_term_warning = fields.Char(
        string="Lease term warning",
        compute="_compute_l10n_sk_lease_term_warning",
    )

    def _compute_l10n_sk_lease_months(self):
        # Each engine bridge overrides this from its own duration fields.
        for record in self:
            record.l10n_sk_lease_months = 0

    @api.depends("l10n_sk_depreciation_group", "l10n_sk_lease_months")
    def _compute_l10n_sk_lease_term_warning(self):
        for record in self:
            warning = False
            required = sk_min_lease_months(record.l10n_sk_depreciation_group)
            if required and record.l10n_sk_lease_months:
                if record.l10n_sk_lease_months < required:
                    warning = _(
                        "Doba trvania nájmu je %(actual)s mesiacov, čo je menej "
                        "ako zákonné minimum %(required)s mesiacov (60 %% doby "
                        "odpisovania). Nejde o finančný prenájom podľa § 2 písm. "
                        "s) — daňový režim bude iný.",
                        actual=record.l10n_sk_lease_months,
                        required=required,
                    )
            record.l10n_sk_lease_term_warning = warning
