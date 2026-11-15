# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from . import models


def post_init_hook(env):
    """Tell an ARES provider that is already installed about our fields.

    ``partner_autocomplete_ares_cz`` points its mappings at these fields when
    it is installed or upgraded. Installed first, it has no later occasion to
    notice them, so this module says so itself. No dependency either way: with
    no ARES provider in the database there is nothing to tell.
    """
    provider = env.get("partner.autocomplete.provider.ares_cz")
    if provider is not None and hasattr(provider, "_ares_apply_default_mappings"):
        provider._ares_apply_default_mappings()
