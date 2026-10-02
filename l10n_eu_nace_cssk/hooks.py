# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def post_init_hook(env):
    """Tag the industries OCA's wizard imported before this module existed:
    they are NACE Rev. 2 (the only version it could import)."""
    env["res.partner.industry"]._nace_tag_legacy_rev2()
