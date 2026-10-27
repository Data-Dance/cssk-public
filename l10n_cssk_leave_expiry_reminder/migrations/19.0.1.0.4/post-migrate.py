"""Drop the claim that unused leave is forfeited from the noupdate records.

The email and the activity told the employee the leave would be forfeited, and
the Czech and Slovak translations called it ``propadá`` / ``prepadá``. Neither
labour code lets annual leave lapse (CZ § 218 zákoníku práce, SK § 113
Zákonníka práce); the date is only when the accrual plan removes the
carried-over days from the balance in Odoo.

The template and the activity type are ``noupdate``, so the corrected data
file and catalogues do not reach an installed database. Only the untouched
original wording is rewritten, per installed language; a deployment that
reworded the template keeps its own text.
"""

from odoo import SUPERUSER_ID, api

TEMPLATE_XMLID = "l10n_cssk_leave_expiry_reminder.mail_template_leave_expiry"
ACTIVITY_XMLID = "l10n_cssk_leave_expiry_reminder.mail_activity_type_expiring_leave"

BODY = {
    "        Please schedule this time off before then, otherwise it will be forfeited.\n": (
        "        Please agree with your manager when you will take this time off before then.\n"
        "        Annual leave does not lapse under the Labour Code; this is the date the\n"
        "        time-off plan removes it from your balance in Odoo.\n"
    ),
    "        Naplánujte si prosím tuto dovolenou do té doby, jinak propadne.\n": (
        "        Domluvte se prosím s vedoucím, kdy tuto dovolenou do té doby vyčerpáte.\n"
        "        Podle zákoníku práce dovolená nepropadá; k tomuto datu ji plán volna\n"
        "        odebere z vašeho zůstatku v Odoo.\n"
    ),
    "        Naplánujte si prosím túto dovolenku dovtedy, inak prepadne.\n": (
        "        Dohodnite sa, prosím, s vedúcim, kedy túto dovolenku dovtedy vyčerpáte.\n"
        "        Podľa Zákonníka práce dovolenka neprepadá; k tomuto dátumu ju plán voľna\n"
        "        odoberie z vášho zostatku v Odoo.\n"
    ),
}
SUBJECT = {
    "Vaše dovolená propadá dne": "Vaše převedená dovolená vyprší dne",
    "Vaša dovolenka prepadá dňa": "Vaša prenesená dovolenka vyprší dňa",
}
ACTIVITY = {
    "name": {
        "Propadající dovolená": "Vypršující dovolená",
        "Prepadajúca dovolenka": "Vypršiavajúca dovolenka",
    },
    "summary": {
        "Převedená dovolená brzy propadne": "Převedená dovolená brzy vyprší",
        "Prenesená dovolenka čoskoro prepadne": "Prenesená dovolenka čoskoro vyprší",
    },
}


def _replace(text, mapping):
    for old, new in mapping.items():
        text = text.replace(old, new)
    return text


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    langs = [code for code, _name in env["res.lang"].get_installed()]
    template = env.ref(TEMPLATE_XMLID, raise_if_not_found=False)
    activity = env.ref(ACTIVITY_XMLID, raise_if_not_found=False)
    for lang in langs:
        if template:
            localised = template.with_context(lang=lang)
            body = localised.body_html or ""
            new_body = _replace(body, BODY)
            if new_body != body:
                localised.body_html = new_body
            subject = localised.subject or ""
            new_subject = _replace(subject, SUBJECT)
            if new_subject != subject:
                localised.subject = new_subject
        if activity:
            localised = activity.with_context(lang=lang)
            for field, mapping in ACTIVITY.items():
                value = localised[field] or ""
                if value in mapping:
                    localised[field] = mapping[value]
