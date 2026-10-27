import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# Odoo ColorList indices and their actual hex values:
#   0: No color
#   1: Red       #ee2d2d
#   2: Orange    #dc8534
#   3: Yellow    #e8bb1d
#   4: Cyan      #5794dd
#   5: Purple    #9f628f
#   6: Almond    #db8865
#   7: Teal      #41a9a2
#   8: Blue      #304be0
#   9: Raspberry #ee2f8a
#  10: Green     #61c36e
#  11: Violet    #9872e6

# Odoo pos.category.color (0-11) → VRP2 color ID (50-74)
ODOO_TO_VRP2_COLOR = {
    0: 66,   # no color → #c1c1c1 grey
    1: 50,   # red      → #eb1a1a red
    2: 51,   # orange   → #f7ba16 gold
    3: 52,   # yellow   → #f5ec00 yellow
    4: 55,   # cyan     → #23dde5 cyan
    5: 59,   # purple   → #712bc1 purple
    6: 63,   # almond   → #e3c295 tan
    7: 65,   # teal     → #2bd9a4 teal
    8: 57,   # blue     → #0089ff blue
    9: 60,   # raspberry→ #d800ff magenta
    10: 54,  # green    → #21b232 green
    11: 68,  # violet   → #abade2 lavender
}

# Reverse: VRP2 color ID → Odoo color index (best match)
VRP2_TO_ODOO_COLOR = {
    50: 1,   # #eb1a1a → red
    51: 2,   # #f7ba16 → orange
    52: 3,   # #f5ec00 → yellow
    53: 10,  # #b5e063 → green
    54: 10,  # #21b232 → green
    55: 4,   # #23dde5 → cyan
    56: 4,   # #10b9e2 → cyan
    57: 8,   # #0089ff → blue
    58: 8,   # #075291 → blue
    59: 5,   # #712bc1 → purple
    60: 9,   # #d800ff → raspberry
    61: 9,   # #a5177f → raspberry
    62: 0,   # #000000 → no color
    63: 6,   # #e3c295 → almond
    64: 10,  # #778019 → green (olive)
    65: 7,   # #2bd9a4 → teal
    66: 0,   # #c1c1c1 → no color
    67: 4,   # #cef0ff → cyan
    68: 11,  # #abade2 → violet
    69: 6,   # #e0c9c9 → almond
    70: 3,   # #e0d225 → yellow
    71: 7,   # #4d979a → teal
    72: 9,   # #f8e1f3 → raspberry
    73: 11,  # #ebe5fc → violet
    74: 3,   # #fefee7 → yellow
}


class PosCategory(models.Model):
    _inherit = "pos.category"

    vrp2_id = fields.Integer(
        string="VRP2 Category ID",
        readonly=True,
        copy=False,
        help="Server-side category ID in VRP2 (categoryId).",
    )
    vrp2_short_name = fields.Char(
        string="VRP2 Short Name",
        help="Short name for VRP2 tabs (max ~3 chars). "
        "Auto-generated from name if not set.",
    )
    vrp2_order = fields.Integer(
        string="VRP2 Order",
        readonly=True,
        copy=False,
        help="Display order in VRP2 (set by server).",
    )

    # ------------------------------------------------------------------
    # Pull: VRP2 → Odoo
    # ------------------------------------------------------------------

    @api.model
    def _vrp2_pull(self, register):
        """Pull all categories from VRP2 and upsert as top-level pos.category.

        Each pulled entry is linked to this till (not ``created_here``: it was
        on the register first, so no push will ever delete it).

        Returns the count of categories synced.
        """
        client = self.env["vrp2.client"]
        Link = self.env["vrp2.catalog.link"]
        company = register.company_id
        resp = client._get_category_list(register)
        categories = resp.get("categories", [])
        by_remote = {
            link.remote_ref: link
            for link in Link._for(register, "category").values()
        }

        synced = 0
        for cat_data in categories:
            vrp2_id = cat_data.get("id")
            if not vrp2_id:
                continue

            link = by_remote.get(str(vrp2_id))
            existing = self.browse(link.res_id).exists() if link else self.browse()
            if not existing:
                existing = self.search([("vrp2_id", "=", vrp2_id)], limit=1)

            color_data = cat_data.get("color", {})
            vrp2_color_id = color_data.get("id") or 66
            odoo_color = VRP2_TO_ODOO_COLOR.get(vrp2_color_id, 0)

            vals = {
                "name": cat_data.get("name", ""),
                "vrp2_id": vrp2_id,
                "vrp2_short_name": cat_data.get("shortName") or False,
                "vrp2_order": cat_data.get("order", 0),
                "color": odoo_color,
                "parent_id": False,
            }

            if existing:
                existing.write(vals)
            else:
                existing = self.create(vals)
            if link:
                link.res_id = existing.id
            else:
                stale = Link._for(register, "category").get(existing.id)
                if stale:
                    stale.remote_ref = str(vrp2_id)
                else:
                    Link.create({
                        "config_id": register.id, "kind": "category",
                        "res_id": existing.id, "remote_ref": str(vrp2_id),
                    })
            synced += 1

        _logger.info(
            "VRP2 category pull for %s: %d categories",
            company.display_name,
            synced,
        )
        return synced

    @api.model
    def _vrp2_intended(self, register):
        """The top-level categories this till sells from."""
        intended = self.search([("parent_id", "=", False)])
        if register.limit_categories and register.iface_available_categ_ids:
            roots = self.browse()
            for categ in register.iface_available_categ_ids:
                while categ.parent_id:
                    categ = categ.parent_id
                roots |= categ
            intended &= roots
        return intended

    # ------------------------------------------------------------------
    # Push: Odoo → VRP2  (bulk — single API call)
    # ------------------------------------------------------------------

    @api.model
    def _vrp2_push(self, register):
        """Push this till's top-level POS categories to VRP2 in one bulk call.

        If vrp2_short_name is not set, it is auto-generated from the first
        2 chars of the name. Color is derived from pos.category.color.

        Deletes from VRP2 only a category that THIS till's pushes created
        there (see ``vrp2.catalog.link``) and whose Odoo category is gone or
        no longer offered on the till. A category made in the VRP2 app, by
        another till or by another database is never deleted.

        Returns (created, updated, deleted) counts.
        """
        client = self.env["vrp2.client"]
        Link = self.env["vrp2.catalog.link"]
        company = register.company_id

        # 1. The categories this till offers
        intended = self._vrp2_intended(register)

        # Auto-fill vrp2_short_name where missing
        for cat in intended:
            if not cat.vrp2_short_name:
                name = cat.name or ""
                cat.vrp2_short_name = name[:2].upper() or "XX"

        # 2. Current VRP2 state
        resp = client._get_category_list(register)
        remote_cats = resp.get("categories", [])
        remote_ids = {c["id"] for c in remote_cats if c.get("id")}

        links = Link._for(register, "category")
        # A link whose entry is gone from the register (deleted in the app)
        # is dropped: the category is created again rather than addressed by
        # a dead id.
        for res_id, link in list(links.items()):
            if int(link.remote_ref) not in remote_ids:
                link.unlink()
                del links[res_id]
        linked_remote = {int(link.remote_ref) for link in links.values()}
        # Adopt the id from before per-till links: the category's own vrp2_id,
        # when this register has it and no other record claims it. Adopted,
        # not created here — so never deleted.
        for cat in intended:
            if cat.id not in links and cat.vrp2_id in remote_ids \
                    and cat.vrp2_id not in linked_remote:
                links[cat.id] = Link.create({
                    "config_id": register.id, "kind": "category",
                    "res_id": cat.id, "remote_ref": str(cat.vrp2_id),
                })
                linked_remote.add(cat.vrp2_id)

        # 3. Build setCategories
        set_categories = []
        for order, cat in enumerate(intended, start=1):
            vrp2_color = ODOO_TO_VRP2_COLOR.get(cat.color or 0, 66)
            entry = {
                "order": order,
                "name": cat.name,
                "shortName": cat.vrp2_short_name,
                "colorId": vrp2_color,
            }
            if cat.id in links:
                entry["categoryId"] = int(links[cat.id].remote_ref)
            set_categories.append(entry)

        # 4. deleteCategories — only what this till created and no longer offers
        doomed = [
            link for res_id, link in links.items()
            if res_id not in intended.ids
        ]
        delete_categories = [
            {"categoryId": int(link.remote_ref)}
            for link in doomed if link.created_here
        ]

        if not set_categories and not delete_categories:
            return 0, 0, 0

        data = {
            "setCategories": set_categories,
            "deleteCategories": delete_categories,
        }
        resp = client._set_category(register, data)

        # 5. Record what the register answered
        created = 0
        updated = 0
        resp_cats = resp.get("categories", []) if resp else []
        resp_by_id = {rc.get("id"): rc for rc in resp_cats if rc.get("id")}
        resp_by_name = {}
        for rc in resp_cats:
            if rc.get("id") not in linked_remote:
                resp_by_name.setdefault(rc.get("name"), rc)

        for cat in intended:
            link = links.get(cat.id)
            if link:
                rc = resp_by_id.get(int(link.remote_ref))
                if rc:
                    cat.vrp2_order = rc.get("order", 0)
                updated += 1
            else:
                rc = resp_by_name.pop(cat.name, None)
                if rc and rc.get("id"):
                    Link.create({
                        "config_id": register.id, "kind": "category",
                        "res_id": cat.id, "remote_ref": str(rc["id"]),
                        "created_here": True,
                    })
                    cat.vrp2_id = rc["id"]
                    cat.vrp2_order = rc.get("order", 0)
                    created += 1

        deleted = len(delete_categories)
        if doomed:
            gone = [int(link.remote_ref) for link in doomed if link.created_here]
            if gone:
                self.search([("vrp2_id", "in", gone)]).write(
                    {"vrp2_id": False, "vrp2_order": False})
            for link in doomed:
                link.unlink()

        _logger.info(
            "VRP2 category push for %s: %d created, %d updated, %d deleted",
            company.display_name,
            created,
            updated,
            deleted,
        )
        return created, updated, deleted
