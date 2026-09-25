# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""KV DPH ↔ DPH priznanie cross-form reconciliation (porovnanie KV a DP).

The kontrolný výkaz and the daňové priznanie are built from the same tax-tagged
move lines, so their daň totals are related — but **not** by a clean equality:
the priznanie legitimately contains daň the KV never reports (dodania pre
nezdaniteľné osoby / B2C, zjednodušené vydané doklady, dovoz self-assessment
without a KV invoice, pomerné odpočítanie koeficientom). FS SR performs this
matching on its side and the exact machine väzby are not published; what *is*
structurally certain is the direction — every KV daň figure is a **subset** of
the corresponding priznanie aggregate (KV ⊆ DP). So this reconciliation:

* ties each KV block to the priznanie rows it must be contained in,
* reports the gap (DP − KV) as expected non-KV content (informačné), and
* flags **KV > DP** beyond tolerance as a likely tagging error (upozornenie) —
  you cannot report more daň in the KV than the priznanie totals.

Sources: zákon č. 222/2004 Z. z. § 78a (KV) a § 78/§ 79 (priznanie); the
DPHv25 / KVDPHv17 poučenia for the block semantics. This is an advisory
porovnanie, not a hard filing gate. It assumes full deduction (odpočítaná daň =
suma dane), consistent with the current KV export (koeficient krátenie TODO).
"""
from odoo import _, api, models

# DPH priznanie row groups (DPHv25). Values are positive daň in our return.
_DP_OUTPUT = ["r02", "r02a", "r04"]                       # tuzemská výstupná daň
_DP_SELF = ["r06", "r06a", "r08", "r10", "r10a", "r10b",  # prenos / nadobudnutie
            "r12", "r12a", "r12b", "r12c", "r12d", "r12e"]
_DP_DEDUCT = ["r18_total", "r18a_total", "r19_total"]      # odpočítanie dane


class L10nSkDphReconciliation(models.TransientModel):
    _name = "l10n.sk.dph.reconciliation"
    _description = "SK cross-form reconciliation (KV↔DP, SV↔DP, DP↔účtovníctvo)"

    _RECON_TOL = 0.5  # absolute € tolerance on the period aggregate

    #: Row ``status`` → ``cssk.filing.discrepancy.kind``. The distinction that
    #: matters is between a gap that is WRONG and a gap that is expected:
    #: ``subset`` (DP > KV) is structurally normal and ``info`` (VAT base vs
    #: účtová trieda 60) was never a control. Painting either as a difference
    #: sends an accountant chasing a number that is doing what it should.
    _RECON_KIND = {
        "ok": "ok",
        "mismatch": "amount",
        "over": "amount",
        "subset": "expected",
        "info": "info",
    }

    @api.model
    def recon_kind(self, status):
        return self._RECON_KIND.get(status, "amount")

    @api.model
    def _sum(self, records, field):
        return sum(records.mapped(field)) if records else 0.0

    @api.model
    def _aggregate_kv(self, kv):
        """{output, self_assessed, deduction} daň totals from the KV sections."""
        s = kv._collect_sections_by_code()
        return {
            # výstupná daň: vydané faktúry (A.1) + opravy výstupu (C.1)
            "output": self._sum(s.get("A.1"), "tax_amount")
            + self._sum(s.get("C.1"), "tax_amount"),
            # samozdanenie: prenos DP / nadobudnutie (B.1)
            "self_assessed": self._sum(s.get("B.1"), "tax_amount"),
            # odpočítaná daň: B.2 + B.3.1 + B.3.2 + opravy odpočtu (C.2)
            "deduction": self._sum(s.get("B.2"), "tax_amount")
            + self._sum(s.get("B.3.1"), "total_tax_amount")
            + self._sum(s.get("B.3.2"), "total_tax_amount")
            + self._sum(s.get("C.2"), "tax_amount"),
        }

    @api.model
    def _aggregate_dp(self, vat_return):
        vals = {line.code: line.value for line in vat_return.line_ids}
        g = lambda codes: sum(vals.get(c, 0.0) for c in codes)
        return {
            "output": g(_DP_OUTPUT),
            "self_assessed": g(_DP_SELF),
            "deduction": g(_DP_DEDUCT),
        }

    @api.model
    def reconcile(self, kv, vat_return):
        """Return a list of reconciliation rows comparing the two statements.

        Each row: ``{block, label, kv, dp, diff, status}`` where ``status`` is
        ``ok`` (|diff| ≤ tol), ``subset`` (DP > KV — expected non-KV content),
        or ``over`` (KV > DP — likely a tagging error).
        """
        akv, adp = self._aggregate_kv(kv), self._aggregate_dp(vat_return)
        blocks = [
            ("output", _("Výstupná daň — tuzemské dodania (A.1+C.1 ⊆ r02+r02a+r04)")),
            ("self_assessed", _("Samozdanenie — prenos/nadobudnutie (B.1 ⊆ r06+r08+r10+r12)")),
            ("deduction", _("Odpočítaná daň (B.2+B.3+C.2 ⊆ r18+r18a+r19 súčty)")),
        ]
        rows = []
        for key, label in blocks:
            kv_v, dp_v = akv[key], adp[key]
            diff = kv_v - dp_v
            tol = max(self._RECON_TOL, abs(dp_v) * 0.001)
            if abs(diff) <= tol:
                status = "ok"
            elif diff > 0:
                status = "over"      # KV > DP — impossible, flag it
            else:
                status = "subset"    # DP > KV — legitimate non-KV content
            rows.append({"block": key, "label": label, "kv": kv_v,
                         "dp": dp_v, "diff": diff, "status": status})
        return rows

    @api.model
    def check_kontroly(self, kv, vat_return):
        """Reconciliation violations as ``[{code, severity, desc, detail}]``.

        Only ``over`` rows are reported (KV exceeds the priznanie — structurally
        impossible, so a real tagging error); ``subset`` gaps are expected.
        """
        out = []
        for row in self.reconcile(kv, vat_return):
            if row["status"] == "over":
                out.append({
                    "code": "KVDP_RECON", "severity": "warning",
                    "desc": row["label"],
                    "detail": "KV %.2f > priznanie %.2f (rozdiel %.2f) — "
                              "skontrolujte zatriedenie/označenie plnení"
                              % (row["kv"], row["dp"], row["diff"])})
        return out

    # ------------------------------------------------------------------
    # Súhrnný výkaz ↔ DPH priznanie
    # ------------------------------------------------------------------
    # The súhrnný výkaz reports intra-EU supplies by kód plnenia. Only kód 0
    # (dodanie tovaru § 43 ods. 1 a 4) has a base row in the priznanie — r14
    # (per the DPHv25 poučenie, riadok 14 = "základ dane za dodané tovary
    # oslobodené § 43 ods. 1 a 4"). kód 1 (trojstranný obchod § 45 — explicitly
    # NOT in r13/r14 per the poučenie) and kód 2 (služby § 9, mimo predmetu dane
    # v SR) have no priznanie base row, so they are súhrnný-výkaz-only. The two
    # documents are filed for the same obdobie, so SV(kód 0) ≈ r14.

    @api.model
    def reconcile_sv_dph(self, sv, vat_return):
        """Return the SV↔priznanie row(s): ``{block, label, left, right,
        diff, status}`` (``left`` = súhrnný výkaz, ``right`` = priznanie)."""
        goods = sum(line.total_amount for line in sv.line_ids
                    if line.transaction_code == "0")
        r14 = next((l.value for l in vat_return.line_ids if l.code == "r14"), 0.0)
        diff = goods - r14
        tol = max(self._RECON_TOL, abs(r14) * 0.001)
        return [{
            "block": "sv_goods_r14", "left": goods, "right": r14, "diff": diff,
            "status": "ok" if abs(diff) <= tol else "mismatch",
            "label": _("Dodanie tovaru do EÚ § 43 (SV kód 0 ↔ priznanie r14)")}]

    @api.model
    def check_kontroly_sv_dph(self, sv, vat_return):
        out = []
        for row in self.reconcile_sv_dph(sv, vat_return):
            if row["status"] == "mismatch":
                out.append({
                    "code": "SVDP_RECON", "severity": "warning",
                    "desc": row["label"],
                    "detail": "súhrnný výkaz %.2f != priznanie r14 %.2f "
                              "(rozdiel %.2f) — skontrolujte označenie § 43 "
                              "dodaní a obdobie" % (row["left"], row["right"],
                                                    row["diff"])})
        return out

    # ------------------------------------------------------------------
    # DPH priznanie ↔ účtovníctvo (účet 343 + tržby)
    # ------------------------------------------------------------------
    # The priznanie is built from tax-tagged move lines; the same lines post the
    # daň to the VAT account (343). The control reconciliation (odsúhlasenie
    # účtu 343) ties the return to the ledger:
    #   * výstupná daň  — priznanie r17        ↔ daň na výstupe zaúčtovaná (343)
    #   * odpočítaná daň — priznanie odpočet   ↔ daň na vstupe zaúčtovaná (343)
    # These should match to the cent; a difference means VAT was booked but not
    # tagged (or vice versa), or a manual 343 entry — a warning. (The output/
    # input split uses the tax's type_tax_use, which is approximate under tuzemský
    # prenos daňovej povinnosti, where one line carries both directions.)
    #
    # The tržby tie (základ dane dodaní ↔ účtová trieda 60) is only INFORMATIONAL:
    # the VAT base and accounting revenue legitimately diverge (prijaté preddavky
    # create daňová povinnosť without výnos, accruals create výnos without daň,
    # nadobudnutie/služby na vstupe are not revenue, financial výnosy 66x are not
    # tržby), so it is reported, never flagged.

    @api.model
    def _ledger_vat(self, company, date_from, date_to):
        """(output_vat, input_vat) booked in the period, from the tax lines."""
        lines = self.env["account.move.line"].search([
            ("parent_state", "=", "posted"), ("company_id", "=", company.id),
            ("date", ">=", date_from), ("date", "<=", date_to),
            ("tax_line_id", "!=", False)])
        out = -sum(l.balance for l in lines if l.tax_line_id.type_tax_use == "sale")
        inp = sum(l.balance for l in lines if l.tax_line_id.type_tax_use == "purchase")
        return out, inp

    @api.model
    def _ledger_trzby(self, company, date_from, date_to):
        """Credit turnover of účtová trieda 60 (tržby) in the period."""
        lines = self.env["account.move.line"].search([
            ("parent_state", "=", "posted"), ("company_id", "=", company.id),
            ("date", ">=", date_from), ("date", "<=", date_to),
            ("account_id.code", "=like", "60%")])
        return -sum(lines.mapped("balance"))

    @api.model
    def reconcile_dph_books(self, vat_return):
        """Return the DP↔ledger rows ``{block, label, left, right, diff, status}``
        (``left`` = priznanie, ``right`` = účtovníctvo)."""
        vals = {l.code: l.value for l in vat_return.line_ids}
        company, df, dt = (vat_return.company_id, vat_return.date_from,
                           vat_return.date_to)
        out_led, in_led = self._ledger_vat(company, df, dt)
        rev = self._ledger_trzby(company, df, dt)
        r17 = vals.get("r17", 0.0)
        deduct = (vals.get("r18_total", 0.0) + vals.get("r18a_total", 0.0)
                  + vals.get("r19_total", 0.0))
        base = (vals.get("r01", 0.0) + vals.get("r01a", 0.0)
                + vals.get("r03", 0.0) + vals.get("r13", 0.0))

        def status(left, right):
            tol = max(self._RECON_TOL, abs(right) * 0.001)
            return "ok" if abs(left - right) <= tol else "mismatch"

        return [
            {"block": "out_vat", "left": r17, "right": out_led,
             "diff": r17 - out_led, "status": status(r17, out_led),
             "label": _("Daň na výstupe (priznanie r17 ↔ účet 343 výstup)")},
            {"block": "in_vat", "left": deduct, "right": in_led,
             "diff": deduct - in_led, "status": status(deduct, in_led),
             "label": _("Odpočítaná daň (priznanie ↔ účet 343 vstup)")},
            {"block": "trzby", "left": base, "right": rev, "diff": base - rev,
             "status": "info",
             "label": _("Základ dane dodaní ↔ tržby účt. tr. 60 (informačné)")},
        ]

    @api.model
    def check_kontroly_dph_books(self, vat_return):
        """Only the 343 control rows can fail; the tržby row is informational."""
        out = []
        for row in self.reconcile_dph_books(vat_return):
            if row["status"] == "mismatch":
                out.append({
                    "code": "DPBOOK_RECON", "severity": "warning",
                    "desc": row["label"],
                    "detail": "priznanie %.2f != účtovníctvo %.2f (rozdiel %.2f)"
                              % (row["left"], row["right"], row["diff"])})
        return out
