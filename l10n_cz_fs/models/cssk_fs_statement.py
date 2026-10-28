# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class CSSKFsStatement(models.Model):
    _inherit = "cssk.fs.statement"

    @api.model
    def default_get(self, fields_list):
        """New lands on the PLNÝ rozsah where both are on offer.

        Both versions of the Rozvaha and of the VZZ are valid for the same
        period, so the framework's "newest valid_from" pick is a tie. The
        plný rozsah is the one every unit may file (vyhláška 500/2002 Sb.,
        § 3a odst. 1 and 3), and the VZZ in plný rozsah is the one every
        obchodní společnost must file (§ 3a odst. 3 písm. a). The zkrácený
        rozsah stays one click away in the Version field.

        Only the framework's own pick is swapped: a version the caller asked
        for (``default_version_id``) is the caller's decision.
        """
        res = super().default_get(fields_list)
        if self.env.context.get("default_version_id"):
            return res
        version = self.env["cssk.fs.statement.version"].browse(
            res.get("version_id")).exists()
        if (version and version.country_id.code == "CZ"
                and version.l10n_cz_fs_scope == "abridged"
                and res.get("date_from") and res.get("date_to")):
            full = version.with_context(active_test=False).search([
                ("country_id", "=", version.country_id.id),
                ("statement_kind", "=", version.statement_kind),
                ("l10n_cz_fs_scope", "=", "full"),
                ("valid_from", "<=", res["date_to"]),
                "|", ("valid_to", "=", False),
                ("valid_to", ">=", res["date_from"]),
            ], order="valid_from desc, id desc", limit=1)
            if full:
                res["version_id"] = full.id
        return res
