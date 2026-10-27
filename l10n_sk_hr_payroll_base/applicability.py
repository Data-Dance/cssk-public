# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Which entitlements and contributions apply to which Slovak employment form.

Slovak payroll runs four employment forms side by side — a pracovný pomer and
the three dohody — and they differ in what is owed and what is earned. Until
now that knowledge lived inside each salary rule's condition, spread across two
engine-specific rule files of several hundred lines each. It is a small table
pretending to be thirty scattered predicates, and it behaved like one: "does
§ 120 apply to dohody?" is a single fact, and it was answered correctly in the
contract warning and incorrectly in the payslip rule, one commit apart, because
nowhere could you read the answer as a whole. A dohodár on €400 was topped up
to €915 for two days.

So it is a table. Adding an employment form means adding a column and being
forced to answer every row, rather than remembering which thirty conditions to
revisit.

Deliberately free of Odoo imports: it is a statement of law, and should read
and diff as one.
"""

# --- employment forms -------------------------------------------------------
# The values of ``hr.version.l10n_sk_agreement_type``. EMPLOYMENT is a
# pracovný pomer; the rest are dohody (§§ 223-228a Zákonníka práce).
EMPLOYMENT = "none"
DOVP = "dovp"          # § 226 dohoda o vykonaní práce
DOPC = "dopc"          # § 228a dohoda o pracovnej činnosti
DOBPS = "dobps"        # § 227 dohoda o brigádnickej práci študentov

AGREEMENTS = (DOVP, DOPC, DOBPS)
ALL_FORMS = (EMPLOYMENT,) + AGREEMENTS
# --- pension status -----------------------------------------------------------
# The values of ``hr.version.l10n_sk_pension_type``: the pension the worker has
# been granted (priznaný). Empty means none. Three provisions of zákon 461/2003
# key off it, each with its own list, so they are kept apart rather than folded
# into one "pensioner" flag:
OLD_AGE = "old_age"                    # starobný dôchodok
EARLY_OLD_AGE = "early_old_age"        # predčasný starobný dôchodok
DISABILITY_OVER_70 = "disability_over_70"  # invalidný, pokles > 70 %
DISABILITY = "disability"              # invalidný, pokles do 70 %
DISABILITY_AT_AGE = "disability_at_age"    # invalidný + dovŕšený dôchodkový vek
SERVICE_AT_AGE = "service_at_age"      # výsluhový + dovŕšený dôchodkový vek
DISABILITY_SERVICE = "disability_service"  # invalidný výsluhový dôchodok

PENSION_TYPES = (OLD_AGE, EARLY_OLD_AGE, DISABILITY_OVER_70, DISABILITY,
                 DISABILITY_AT_AGE, SERVICE_AT_AGE, DISABILITY_SERVICE)

# § 4 ods. 1 písm. b): a DoVP/DoPČ holder with any of these pensions is not a
# zamestnanec for sickness, pension-and-unemployment purposes; § 4 ods. 2
# písm. a) and písm. b) bod 2 bring them back for PENSION insurance only.
AGREEMENT_PENSIONS = PENSION_TYPES
# § 19 ods. 3 písm. b): poistenie v nezamestnanosti "sa nevzťahuje na fyzickú
# osobu, ktorej bol priznaný starobný dôchodok, predčasný starobný dôchodok
# alebo invalidný dôchodok z dôvodu poklesu … o viac ako 70 % a fyzickú osobu,
# ktorá má priznaný invalidný dôchodok a dovŕšila dôchodkový vek" — on every
# employment form.
NO_UNEMPLOYMENT_PENSIONS = (OLD_AGE, EARLY_OLD_AGE, DISABILITY_OVER_70,
                            DISABILITY_AT_AGE)
# § 128 ods. 3 (ods. 4 in the versions up to 2025): invalidné poistenie is not
# paid by a poistenec after a starobný or predčasný starobný dôchodok, nor by a
# výsluhový pensioner who reached dôchodkový vek — and not by the employer for
# them either. On every employment form.
NO_DISABILITY_PENSIONS = (OLD_AGE, EARLY_OLD_AGE, SERVICE_AT_AGE)

# Forms whose holder can be a zamestnanec for sickness and unemployment
# insurance at all. § 4 ods. 1 písm. a) zákona 461/2003 takes the DoBPŠ
# student out of that definition outright; with a regular income they are a
# zamestnanec for PENSION insurance only (§ 4 ods. 2 písm. b) bod 1).
SICKNESS_FORMS = (EMPLOYMENT, DOVP, DOPC)

# --- the table --------------------------------------------------------------
# concept -> {
#   "forms":   employment forms it applies to,
#   "regular": True  -> only with a regular (pravidelný) income,
#              False -> only with an irregular income,
#              None  -> regardless,
#   "not_for_pensions": {form: pension types} for which the row does NOT
#              apply on that form (absent = the pension status is irrelevant),
#   "why":     the statutory hook, so a reader can check the row,
# }
APPLICABILITY = {
    # --- social insurance funds -------------------------------------------
    # Old-age and disability are owed by everyone, on every form.
    "PENSION_INSURANCE": {
        "forms": ALL_FORMS, "regular": None,
        "why": "zák. 461/2003 — starobné poistenie, owed on every form.",
    },
    "DISABILITY_INSURANCE": {
        "forms": ALL_FORMS, "regular": None,
        "not_for_pensions": {form: NO_DISABILITY_PENSIONS for form in ALL_FORMS},
        "why": "zák. 461/2003 — invalidné poistenie, owed on every form, "
        "except after a starobný / predčasný starobný dôchodok or a výsluhový "
        "dôchodok at dôchodkový vek (§ 128 ods. 3).",
    },
    # Sickness, unemployment and the short-time contribution follow the
    # REGULARITY of the income, not the kind of agreement. Both DoVP and DoPČ
    # can lawfully be agreed either way; keying these off the agreement type
    # under-charged every monthly-paid DoVP. The one form-based exception is
    # the DoBPŠ, excluded by § 4 ods. 1 písm. a) whatever its regularity.
    "SICKNESS_INSURANCE": {
        "forms": SICKNESS_FORMS, "regular": True,
        "not_for_pensions": {DOVP: AGREEMENT_PENSIONS, DOPC: AGREEMENT_PENSIONS},
        "why": "zák. 461/2003 § 4 ods. 1 — nemocenské poistenie only for a "
        "zamestnanec s pravidelným príjmom, \"okrem fyzickej osoby v právnom "
        "vzťahu na základe dohody o brigádnickej práci študentov\" (písm. a)), "
        "nor for a DoVP/DoPČ holder with a dôchodok (písm. b)).",
    },
    "UNEMPLOYMENT_INSURANCE": {
        "forms": SICKNESS_FORMS, "regular": True,
        "not_for_pensions": {
            EMPLOYMENT: NO_UNEMPLOYMENT_PENSIONS,
            # § 19 ods. 1: only a zamestnanec who is sickness-insured, so a
            # dohodár with any dôchodok (§ 4 ods. 1 písm. b)) is out too.
            DOVP: AGREEMENT_PENSIONS,
            DOPC: AGREEMENT_PENSIONS,
        },
        "why": "zák. 461/2003 § 4 ods. 1 and § 19 — poistenie v "
        "nezamestnanosti only with a regular income, DoBPŠ excluded by "
        "písm. a), the pensions of § 19 ods. 3 písm. b) excluded on every "
        "form.",
    },
    # § 128 ods. 1 písm. g): the employer pays it "za zamestnanca v pracovnom
    # pomere" — never for a dohoda, whatever the regularity. For a dohodár the
    # employer pays the FULL unemployment rate instead (§ 136 písm. b) bod 2).
    "SHORTTIME_CONTRIBUTION": {
        "forms": (EMPLOYMENT,), "regular": None,
        "why": "zák. 461/2003 § 128 ods. 1 písm. g) — poistné na "
        "financovanie podpory platí zamestnávateľ za zamestnanca v pracovnom "
        "pomere.",
    },
    # --- entitlements ------------------------------------------------------
    "MIN_WAGE_CLAIM": {
        "forms": (EMPLOYMENT,), "regular": None,
        "why": "§ 120 sets minimálne mzdové nároky for a pracovný pomer. A "
        "dohodár has no stupeň náročnosti and is entitled to the minimum "
        "HOURLY wage under zák. 663/2007 instead.",
    },
    "HOLIDAY_ENTITLEMENT": {
        "forms": (EMPLOYMENT,), "regular": None,
        "why": "§ 100 — dovolenka belongs to a pracovný pomer; work "
        "agreements carry no vacation entitlement, so no náhrada za dovolenku.",
    },
    "SICKNESS_COMPENSATION": {
        "forms": SICKNESS_FORMS, "regular": True,
        "not_for_pensions": {DOVP: AGREEMENT_PENSIONS, DOPC: AGREEMENT_PENSIONS},
        "why": "Náhrada príjmu pri PN presupposes sickness insurance, which "
        "only a regular income carries.",
    },
}

# Rows deliberately NOT in the table, with the reason. Named rather than merely
# absent, so the gap is not mistaken for an oversight and filled in on a guess.
NEEDS_LEGAL_CONFIRMATION = {
    "WAGE_SURCHARGES": "The Saturday, Sunday and night surcharges (§§ 122a, "
    "122b and 123 ZP) are extended to dohodári by § 223 ods. 2 ZP, which lists "
    "§ 122a ods. 1 až 3, § 122b ods. 1 až 3 and § 123 ods. 1 a 2 (but not the "
    "§ 121 overtime or § 122 holiday pay). The rules already apply them to "
    "every form; encoding the row is the surcharges family's call.",
    "MEAL_ENTITLEMENT": "§ 152 sits in the seventh part of the Labour Code, "
    "which § 223 ods. 2 does NOT extend to dohody (it lists the sixth part, "
    "ochrana práce). Whether a dohodár is entitled to stravovanie therefore "
    "needs a practitioner's confirmation before it is encoded.",
}

def applies(concept, form, income_regular=True, pension=None):
    """Whether *concept* applies to *form* with the given income regularity
    and pension status (one of ``PENSION_TYPES``, or a falsy value for none).

    Raises on an unknown concept. Returning a default would make a typo look
    like a legal answer, and every caller here is deciding whether to charge
    or pay somebody.
    """
    try:
        row = APPLICABILITY[concept]
    except KeyError:
        hint = NEEDS_LEGAL_CONFIRMATION.get(concept)
        raise KeyError(
            "No applicability row for %r.%s" % (
                concept,
                " It is listed as needing legal confirmation: %s" % hint
                if hint else " Add one to APPLICABILITY, or to "
                "NEEDS_LEGAL_CONFIRMATION with a reason.",
            )
        )
    if pension and pension not in PENSION_TYPES:
        raise KeyError("Unknown pension type %r." % (pension,))
    if form not in row["forms"]:
        return False
    if pension and pension in row.get("not_for_pensions", {}).get(form, ()):
        return False
    if row["regular"] is None:
        return True
    return bool(income_regular) is row["regular"]
