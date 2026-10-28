# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Czech hooks on the statement VERSION: its rozsah and its tag map."""

from odoo import fields, models


class CSSKFsVersion(models.Model):
    _inherit = "cssk.fs.statement.version"

    # Vyhláška 500/2002 Sb., § 3a: the Rozvaha and the Výkaz zisku a ztráty
    # each come in a plný and a zkrácený rozsah, and which one a unit files is
    # decided per statement (an obchodní společnost files the VZZ in full even
    # where its Rozvaha may be abridged, § 3a odst. 2 vs odst. 3 písm. a).
    # Each rozsah is its own version because the zkrácený one is not merely a
    # view of the plný one: its leaves are the plný rozsah's subtotals, and a
    # subtotal can carry a manual override (a comparative figure in the first
    # year kept in Odoo) only where it is a leaf.
    l10n_cz_fs_scope = fields.Selection(
        [("full", "Full (plný rozsah)"),
         ("abridged", "Abridged (zkrácený rozsah)")],
        string="Scope (rozsah)",
        help="Czech statements only (vyhláška č. 500/2002 Sb., § 3a). The "
             "full scope carries every item of přílohy 1 and 2; the abridged "
             "one only the items marked with letters and Roman numerals "
             "(plus C.II.1 and C.II.2 of the Rozvaha). The DPPDP9 return "
             "files its výkazy in the rozsah of the linked statements.")

    def _cssk_tag_codes(self):
        """The plný-rozsah VZZ splits rows by account TAG, not by code.

        IV./V. both live on účet 665, and IV.1, V.1, VI.1 and J.1 separate
        income and cost with an ovládaná nebo ovládající osoba from the rest;
        E.1.2 / E.2 / E.3 split 559 by what the opravná položka is made to.
        No account of the směrná osnova tells these apart, so the rows read
        account tags (``-665&IV_1``) and the "ostatní" row takes what is not
        tagged (``-665!IV_1!V_1!V_2``) — the whole amount where nothing is.

        Every Czech version gets the map; only formulas containing ``&`` or
        ``!`` ever read it, and the zkrácený versions, the cash flow and the
        changes in equity contain none.
        """
        self.ensure_one()
        if self.country_id.code != "CZ":
            return super()._cssk_tag_codes()
        return self.env["account.account"]._l10n_cz_fs_tag_codes()
