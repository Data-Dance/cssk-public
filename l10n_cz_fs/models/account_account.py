# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The account tags that split VZZ rows no account code can tell apart."""

from odoo import _, api, models
from odoo.exceptions import ValidationError

#: Tag key -> xmlid suffix. The key is what a row formula names
#: (``-665&IV_1``); see data/cz_fs_split_tags.xml for what each one means.
SPLIT_TAGS = ("E_1_2", "E_2", "IV_1", "V_1", "V_2", "VI_1", "J_1")


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model
    def _l10n_cz_fs_split_tags(self):
        """``{key: account.account.tag}`` for the tags that exist."""
        out = {}
        for key in SPLIT_TAGS:
            tag = self.env.ref("l10n_cz_fs.account_tag_vzz_%s" % key,
                               raise_if_not_found=False)
            if tag:
                out[key] = tag
        return out

    @api.model
    def _l10n_cz_fs_tag_codes(self):
        """``{key: {account codes}}`` — the map a ``&`` / ``!`` token reads.

        The code an account is matched by is company-dependent, so every
        company's code of a tagged account is collected: the version that
        reads this map has no company of its own, and a statement of either
        company must see its own code in the set.
        """
        tags = self._l10n_cz_fs_split_tags()
        out = {key: set() for key in SPLIT_TAGS}
        if not tags:
            return out
        accounts = self.sudo().with_context(active_test=False).search(
            [("tag_ids", "in", [t.id for t in tags.values()])])
        for account in accounts:
            for key, tag in tags.items():
                if tag in account.tag_ids:
                    for company in account.company_ids:
                        code = account.with_company(company).code
                        if code:
                            out[key].add(code)
        return out

    @api.constrains("tag_ids")
    def _check_l10n_cz_fs_one_split_tag(self):
        """One account, one VZZ row. Two split tags on one account would put
        its balance on two sibling rows — IV.1 and V.1, say — and the výkaz
        would report it twice while every total still looked plausible."""
        tags = self._l10n_cz_fs_split_tags()
        if not tags:
            return
        tag_ids = {t.id for t in tags.values()}
        for account in self:
            carried = account.tag_ids.filtered(lambda t: t.id in tag_ids)
            if len(carried) > 1:
                raise ValidationError(_(
                    "Account %(account)s carries %(tags)s. Each of these tags "
                    "moves the account's balance to its own row of the Výkaz "
                    "zisku a ztráty, so an account can carry only one of "
                    "them.",
                    account=account.display_name,
                    tags=", ".join(carried.mapped("name"))))
