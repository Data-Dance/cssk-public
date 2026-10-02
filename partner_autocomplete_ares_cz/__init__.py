# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from . import models


def post_init_hook(env):
    env["partner.autocomplete.provider.ares_cz"]._ares_apply_default_mappings()
