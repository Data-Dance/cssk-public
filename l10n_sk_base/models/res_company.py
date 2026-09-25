# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The company-side views of the partner's DIČ.

Both fields here are *views* of one value, ``res.partner.l10n_sk_dic``. Neither
stores a number of its own, which is the whole point: a company field that holds
its own copy is a company field that can disagree with the contact.

``income_tax_id``
    ``l10n_sk`` defines this as a plain stored ``Char`` on ``res.company`` only,
    so it cannot be recorded for a customer or a vendor. Odoo's own
    `PR #280178 <https://github.com/odoo/odoo/pull/280178>`_ repoints it at a
    partner field of exactly this name, and this mirrors that: same field, same
    target, so a database that later takes the upstream module finds the value
    already where it expects it. Kept ``store=True`` to leave the existing
    column in place.

``l10n_sk_dic``
    The name this repository already reads in ten DPPO report templates, the FS
    statement template, ``l10n_cssk_income_tax_base`` and the payroll
    declarations. Retained as a second view rather than swept, because renaming
    it across those readers risks missing one — and a missed reader is an empty
    ``<dic>`` in a statutory filing, which is the exact failure this module
    exists to stop. Both fields resolve to the same partner value, so they
    cannot diverge.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_sk_dic = fields.Char(
        string="DIČ",
        related="partner_id.l10n_sk_dic",
        readonly=False,
    )
    # OVERRIDE l10n_sk: a stored Char becomes a stored related on the partner.
    income_tax_id = fields.Char(
        string="DIČ",
        related="partner_id.l10n_sk_dic",
        store=True,
        readonly=False,
    )

    # -- the two views must never be handed different numbers ---------------
    # Both inverse onto partner_id.l10n_sk_dic, so a single call naming both
    # with different values is resolved by dict order — last one wins, silently,
    # on a statutory identifier. Nothing in this repository does it, but an
    # import or an RPC caller easily could. Refuse instead of guessing.

    @staticmethod
    def _l10n_sk_conflicting_dic(vals):
        pair = [vals[f] for f in ("l10n_sk_dic", "income_tax_id") if f in vals]
        return len(pair) == 2 and (pair[0] or "") != (pair[1] or "")

    def _l10n_sk_check_dic_vals(self, vals):
        if self._l10n_sk_conflicting_dic(vals):
            raise ValidationError(_(
                "'DIČ' was given two different values in one operation "
                "(%(a)s and %(b)s). Both fields are views of the same number; "
                "set one of them.",
                a=vals.get("l10n_sk_dic") or "-",
                b=vals.get("income_tax_id") or "-",
            ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._l10n_sk_check_dic_vals(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._l10n_sk_check_dic_vals(vals)
        return super().write(vals)
