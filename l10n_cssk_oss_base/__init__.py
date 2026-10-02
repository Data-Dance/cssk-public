# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Add the Slovak 5 % mappings to companies core has already mapped.

    ``l10n_eu_oss`` maps a company when it is installed or when the accountant
    presses its button, so a company that was mapped BEFORE this module has
    OSS fiscal positions without the 5 % rows. Re-running the mapping is safe:
    core skips every domestic tax a fiscal position already maps, so the only
    effect is the rows that were missing. Companies that never used OSS are
    left alone — mapping them would create 26 fiscal positions nobody asked for.
    """
    oss_tag = env.ref("l10n_eu_oss.tag_oss", raise_if_not_found=False)
    if not oss_tag:
        return
    taxes = env["account.tax"].with_context(active_test=False).search([
        "|",
        ("invoice_repartition_line_ids.tag_ids", "in", oss_tag.ids),
        ("refund_repartition_line_ids.tag_ids", "in", oss_tag.ids),
    ])
    companies = taxes.company_id
    if companies:
        companies._map_eu_taxes()
        _logger.info(
            "l10n_cssk_oss_base: OSS tax mapping completed with the Slovak "
            "5 %% rate for %s company(ies)", len(companies))
