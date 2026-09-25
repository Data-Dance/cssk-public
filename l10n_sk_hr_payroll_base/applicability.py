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

# --- the table --------------------------------------------------------------
# concept -> {
#   "forms":   employment forms it applies to,
#   "regular": True  -> only with a regular (pravidelný) income,
#              False -> only with an irregular income,
#              None  -> regardless,
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
        "why": "zák. 461/2003 — invalidné poistenie, owed on every form.",
    },
    # Sickness, unemployment and the short-time contribution follow the
    # REGULARITY of the income, not the kind of agreement. Both DoVP and DoPČ
    # can lawfully be agreed either way; keying these off the agreement type
    # under-charged every monthly-paid DoVP.
    "SICKNESS_INSURANCE": {
        "forms": ALL_FORMS, "regular": True,
        "why": "zák. 461/2003 § 4 — nemocenské poistenie only for a "
        "zamestnanec s pravidelným príjmom.",
    },
    "UNEMPLOYMENT_INSURANCE": {
        "forms": ALL_FORMS, "regular": True,
        "why": "zák. 461/2003 § 4 — poistenie v nezamestnanosti only with a "
        "regular income.",
    },
    "SHORTTIME_CONTRIBUTION": {
        "forms": ALL_FORMS, "regular": True,
        "why": "Financovanie podpory v čase skrátenej práce follows the "
        "sickness/unemployment set.",
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
        "forms": ALL_FORMS, "regular": True,
        "why": "Náhrada príjmu pri PN presupposes sickness insurance, which "
        "only a regular income carries.",
    },
}

# Rows deliberately NOT in the table, with the reason. Named rather than merely
# absent, so the gap is not mistaken for an oversight and filled in on a guess.
NEEDS_LEGAL_CONFIRMATION = {
    "WAGE_SURCHARGES": "The 2023 amendment is understood to have extended the "
    "§§ 122a-122c surcharges to dohodári, but that is belief rather than "
    "checked law, so the rules currently apply them to every form without a "
    "table row asserting it. Confirm with a practitioner before encoding.",
    "MEAL_ENTITLEMENT": "Likewise for the § 152 meal entitlement of dohodári "
    "working more than four hours.",
}


def applies(concept, form, income_regular=True):
    """Whether *concept* applies to *form* with the given income regularity.

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
    if form not in row["forms"]:
        return False
    if row["regular"] is None:
        return True
    return bool(income_regular) is row["regular"]
