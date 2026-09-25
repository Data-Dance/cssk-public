# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Give every Czech company the statutory rate provider on install.

    A hook rather than an XML record because the provider is company-scoped and
    there is no way to write "one per Czech company" as data — and because
    ``_load_data`` rewrites what it loads on every upgrade, which would revert
    the currency list a user had adjusted.
    """
    created = env["res.currency.rate.provider"]._cz_ensure_default_provider()
    _logger.info("currency_rate_update_cz: post_init created %d provider(s).",
                 len(created))
