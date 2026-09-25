
from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_statutory_footprint(self):
        res = super()._cssk_statutory_footprint()
        code = self.account_id.code or ""
        if not code:
            return res
        defs = self.env["cssk.income.tax.line.def"].search(
            [("kind", "=", "account")] + self._cssk_footprint_version_domain())
        seen = set()
        matcher = self.env["cssk.income.tax.return"]
        for ldef in defs:
            if not self._dppo_formula_matches(matcher, ldef, code):
                continue
            if ldef.code in seen:
                continue
            seen.add(ldef.code)
            res.append({"form": _("Income tax return (DPPO)"),
                        "code": ldef.code, "name": ldef.name,
                        "res_model": "cssk.income.tax.return"})
        return res

    @staticmethod
    def _dppo_formula_matches(matcher, ldef, code):
        """Does this row's formula claim this account?

        Asked through the shared matcher rather than a local regex, so the
        reverse direction cannot answer a different question from the figures.
        The old ``re.findall(r"[0-9]+")`` differed in a way that is latent
        rather than theoretical: a non-numeric analytic token — ``131ved``,
        which the core matcher's docstring names — yields the prefix ``131``
        and claims the whole synthetic, where ``startswith`` on the token
        claims only that account. No such token is in the DPPO data today.

        ``claimed`` is None because ``cssk.income.tax._eval_accounts`` passes
        no claimed set, so the residual mechanism is off for this form and
        every token is a plain prefix. If that ever changes, BOTH readers have
        to change together — and the way to make that structural rather than
        remembered is the one used in ``l10n_cssk_fs_base``: put the answer on
        the VERSION, where the footprint can reach it too.
        """
        for raw in (ldef.account_formula or "").split(","):
            _neg, prefix, _inc, _exc = matcher._cssk_split_token(raw, None)
            if prefix and matcher._cssk_code_matches(code, prefix, None):
                return True
        return False
