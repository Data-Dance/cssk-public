import re

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
        for ldef in defs:
            prefixes = re.findall(r"[0-9]+",
                                  (ldef.account_formula or "").replace("-", " "))
            if not any(code.startswith(p) for p in prefixes):
                continue
            if ldef.code in seen:
                continue
            seen.add(ldef.code)
            res.append({"form": _("Income tax return (DPPO)"),
                        "code": ldef.code, "name": ldef.name})
        return res
