# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends("zip_id")
    def _compute_state_id(self):
        """A postcode whose city has no state clears the partner's state.

        Bratislava and Košice carry no okres: each spans several, and the post
        does not tell which part of the town a PSČ serves (Staré Mesto alone
        has codes in the 821, 831 and 841 series). base_location copies a
        city's state only when there is one, yet ``_check_zip`` insists the two
        are equal, so a partner whose okres came from an earlier PSČ could not
        be moved to Bratislava at all: "The state of the partner … differs
        from that in location …". The company form already copies the empty
        state in its onchange; this does the same for a partner.
        """
        res = super()._compute_state_id()
        for record in self:
            if record.zip_id and not record.zip_id.city_id.state_id:
                record.state_id = False
        return res
