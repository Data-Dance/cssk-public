# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

_logger = logging.getLogger(__name__)

DEFAULT_HOURLY_BUDGET = 60


def post_init_hook(env):
    """Give companies that already existed the default hourly budget.

    A column added by an install is NULL on existing rows, which an Integer
    field reads as 0 — and zero budget means no lookups. Without this, every
    company that predates the install would silently refuse to capture
    anything, with the field's own default sitting right there in the form.
    """
    companies = env["res.company"].sudo().search(
        [("l10n_sk_ekasa_hourly_budget", "<=", 0)])
    if companies:
        companies.write({"l10n_sk_ekasa_hourly_budget": DEFAULT_HOURLY_BUDGET})
        _logger.info(
            "l10n_sk_ekasa_receipt: set the default hourly lookup budget on "
            "%s existing compan%s",
            len(companies), "y" if len(companies) == 1 else "ies")
