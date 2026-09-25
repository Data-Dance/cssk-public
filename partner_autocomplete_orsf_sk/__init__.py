# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from . import models


def post_init_hook(env):
    """Point the field mappings at the standard SK fields that exist.

    A sibling module installed *after* this one brings fields that no mapping
    knows about yet; the settings button re-runs this for that case.
    """
    env["partner.autocomplete.provider.orsf_sk"]._orsf_apply_default_mappings()
