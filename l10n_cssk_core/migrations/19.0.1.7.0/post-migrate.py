import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.l10n_cssk_core.models.res_partner import REGISTRY_COUNTRIES
from odoo.addons.l10n_cssk_core.tools import is_valid_ico

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Report CZ/SK partners whose IČO does not pass the new check.

    This REPORTS and does not rewrite. A wrong company registry cannot be
    repaired by guessing -- the three real cases on the Data Dance base each
    held the company NAME, and the only correct value came from looking the
    company up in ARES. Writing something plausible over it would replace a
    visible error with an invisible one, on records that reach invoices.

    Nor does it archive or block anything: the constraint applies from here on
    to writes, so existing rows keep working until someone edits them, and the
    log below is what tells an administrator which ones to fix first.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    partners = env["res.partner"].with_context(active_test=False).search(
        [("company_registry", "!=", False)]
    )
    offenders = [
        p
        for p in partners
        if p.country_code in REGISTRY_COUNTRIES and not is_valid_ico(p.company_registry)
    ]
    if not offenders:
        _logger.info(
            "l10n_cssk_core: every CZ/SK company registry passes the IČO check."
        )
        return
    _logger.warning(
        "l10n_cssk_core: %s of %s CZ/SK partner(s) carry a company registry that "
        "is not a valid IČO. They are untouched and still readable; each will "
        "raise the next time that partner is written. Look each one up in the "
        "register (ARES for CZ, ORSF/RPO for SK) and correct it -- do not guess.",
        len(offenders),
        len(partners),
    )
    for partner in offenders:
        _logger.warning(
            "  res.partner(%s) %-40s %s = %r",
            partner.id,
            (partner.display_name or "")[:40],
            partner.country_code,
            partner.company_registry,
        )
