# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Účtovná závierka (VZS) → DPPO cross-form reconciliation.

The income-tax return starts from the accounting result: DPPO r100 ("výsledok
hospodárenia pred zdanením", account_formula 5,6,-591,-592,-595,-596) equals
VZS r56 (the same result before income tax — both exclude daň z príjmov
591/592/595 and prevod podielov 596). This is an EXACT tie — a mismatch means
the two filings disagree on the accounting result (a manual r100 override or a
different obdobie), so it is an error, not info.

It lives in this bridge rather than next to the KV/SV/DP reconciliations in
``l10n_sk_datadance`` because it is the only one of the four that needs modules
the umbrella deliberately does not depend on.
"""
from odoo import _, api, models


class L10nSkDphReconciliation(models.TransientModel):
    _inherit = "l10n.sk.dph.reconciliation"

    @api.model
    def reconcile_vzs_dppo(self, uzpod, dppo):
        """Return ``{block, label, left, right, diff, status}`` (``left`` = VZS,
        ``right`` = DPPO r100)."""
        vzs = uzpod.vzs_before_tax()
        r100 = next((l.value for l in dppo.line_ids if l.code == "r100"), 0.0)
        diff = vzs - r100
        return [{
            "block": "vzs_r100", "left": vzs, "right": r100, "diff": diff,
            "status": "ok" if abs(diff) <= self._RECON_TOL else "mismatch",
            "label": _("Výsledok hospodárenia pred zdanením (VZS r56 = DPPO r100)")}]

    @api.model
    def check_kontroly_vzs_dppo(self, uzpod, dppo):
        out = []
        for row in self.reconcile_vzs_dppo(uzpod, dppo):
            if row["status"] == "mismatch":
                out.append({
                    "code": "VZSDPPO_RECON", "severity": "error",
                    "desc": row["label"],
                    "detail": "VZS %.2f != DPPO r100 %.2f (rozdiel %.2f) — "
                              "skontrolujte obdobie alebo manuálnu úpravu r100"
                              % (row["left"], row["right"], row["diff"])})
        return out
