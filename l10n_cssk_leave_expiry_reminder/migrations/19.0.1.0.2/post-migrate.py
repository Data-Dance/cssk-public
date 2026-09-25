"""Backfill the netted amount into the noupdate mail template.

``expiring_carryover_days`` is the GROSS carried-over balance; days taken
since the carryover date are only deducted when the expiration date itself
arrives. The template quoted the raw field, so an employee who had already
used part of the carried days was emailed too large a figure. Point it at
``_l10n_cssk_expiry_amount_and_unit()`` instead, which nets it — and, while
we are here, take the day/hour wording from the same helper rather than
hardcoding "day(s)".

Only the untouched original markup is rewritten; a deployment that reworded
the template keeps its own body. ``body_html`` is translatable, so every
installed language is fixed, not just the one the migration runs in.
"""

import re

from odoo import SUPERUSER_ID, api

TEMPLATE_XMLID = "l10n_cssk_leave_expiry_reminder.mail_template_leave_expiry"

# The gross-amount <span>, followed by the hardcoded unit word. The whitespace
# between them is matched loosely so re-indentation does not defeat the match.
OLD_BODY_RE = re.compile(
    r"""<span style="font-weight: bold;" t-out="'%g' % object\.expiring_carryover_days">"""
    r"""(?P<placeholder>.*?)</span>\s*day\(s\) of""",
    re.DOTALL,
)
NEW_BODY = (
    '<span style="font-weight: bold;" '
    't-out="object._l10n_cssk_expiry_amount_and_unit()[0]">\\g<placeholder>'
    '</span>\n        '
    '<t t-out="object._l10n_cssk_expiry_amount_and_unit()[1]">day(s)</t> of'
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = env.ref(TEMPLATE_XMLID, raise_if_not_found=False)
    if not template:
        return
    for lang, _name in env["res.lang"].get_installed():
        localised = template.with_context(lang=lang)
        body = localised.body_html
        if not body:
            continue
        new_body = OLD_BODY_RE.sub(NEW_BODY, body)
        if new_body != body:
            localised.body_html = new_body
