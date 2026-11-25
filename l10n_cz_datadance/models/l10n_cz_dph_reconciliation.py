# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Czech cross-checks before filing: KH ↔ DPH, SH ↔ DPH, DPH ↔ ledger.

None of the three is a rule of ours. The first two are the links the forms
state themselves:

* the kontrolní hlášení closes with *kontrolní řádky* (věta C), and the EPO
  structure says what each must agree with, to the row: "Celková hodnota
  základu daně A.4. a A.5. za období (nebo součet tří kontrolních hlášení u
  čtvrtletního plátce) odpovídá řádku 1 přiznání k DPH. (Výpočet s maximální
  tolerancí +/- 1000 Kč.)" and so on for ř. 2, 40, 41, 25, 10, 11 and the
  acquisitions of A.2 (ř. 3, 4, 5, 6, 9, 12, 13) — ``dphkh1_epo2.xsd``;
* the instructions of the přiznání send three of its rows to the souhrnné
  hlášení: "Hodnota plnění z řádku 20 se uvede v souhrnném hlášení s kódy 0
  a 1", "z řádku 21 … s kódem 3", "z řádku 31 … s kódem 2" —
  ``dphdp3_epo2.xsd``.

The third ties the return to account 343: what the return states as tax must
be what the tax lines booked there.

A quarterly payer files one přiznání for three monthly hlášení, so a
statement is compared together with its siblings of the same quarter; where
one of them is missing the rows are reported as not compared rather than as
differing.
"""

from odoo import _, api, models

#: Věta C of DPHKH1: (row code, sections, columns, DPHDP3 line codes, label).
#: The reduced-rate columns include the second reduced rate, which the
#: přiznání carried on the same row until 2023.
KH_CONTROL_ROWS = (
    ("obrat23", ("A4", "A5"), ("base_std",), ("obrat23",),
     "A.4 + A.5, základní sazba ↔ ř. 1"),
    ("obrat5", ("A4", "A5"), ("base_red", "base_red3"), ("obrat5",),
     "A.4 + A.5, snížená sazba ↔ ř. 2"),
    ("pln23", ("B2", "B3"), ("base_std",), ("pln23",),
     "B.2 + B.3, základní sazba ↔ ř. 40"),
    ("pln5", ("B2", "B3"), ("base_red", "base_red3"), ("pln5",),
     "B.2 + B.3, snížená sazba ↔ ř. 41"),
    ("pln_rez_pren", ("A1",), ("base_std",), ("pln_rez_pren",),
     "A.1 ↔ ř. 25"),
    ("rez_pren23", ("B1",), ("base_std",), ("rez_pren23",),
     "B.1, základní sazba ↔ ř. 10"),
    ("rez_pren5", ("B1",), ("base_red", "base_red3"), ("rez_pren5",),
     "B.1, snížená sazba ↔ ř. 11"),
    ("celk_zd_a2", ("A2",), ("base_std", "base_red", "base_red3"),
     ("p_zb23", "p_zb5", "p_sl23_e", "p_sl5_e", "p_dop_nrg", "p_sl23_z",
      "p_sl5_z"),
     "A.2 ↔ ř. 3 + 4 + 5 + 6 + 9 + 12 + 13"),
)

#: Souhrnné hlášení: (row code, k_pln_eu codes, DPHDP3 line code, label).
SH_ROWS = (
    ("sh_goods", ("0", "1"), "dod_zb",
     "Dodání a přemístění zboží (kódy 0 a 1) ↔ ř. 20"),
    ("sh_services", ("3",), "pln_sluzby",
     "Služby podle § 9 odst. 1 (kód 3) ↔ ř. 21"),
    ("sh_triangular", ("2",), "tri_dozb",
     "Třístranný obchod, prostřední osoba (kód 2) ↔ ř. 31"),
)

#: DPHDP3 rows stating a value of supplies made, for the turnover row.
_SUPPLY_ROWS = ("obrat23", "obrat5", "dod_zb", "pln_sluzby", "pln_vyvoz",
                "dod_dop_nrg", "pln_zaslani", "pln_rez_pren", "pln_ost")


class L10nCzDphReconciliation(models.AbstractModel):
    _name = "l10n.cz.dph.reconciliation"
    _description = "CZ cross-form checks (KH↔DPH, SH↔DPH, DPH↔účetnictví)"

    #: "Výpočet s maximální tolerancí +/- 1000 Kč" (věta C).
    KH_TOLERANCE = 1000.0
    #: Every row of the přiznání is rounded to a whole crown on its own, the
    #: tax rows upwards; a sum of fifteen of them may be that far from the
    #: ledger.
    LEDGER_TOLERANCE = 20.0

    # ------------------------------------------------------------------
    # Which filings belong together
    # ------------------------------------------------------------------
    @api.model
    def find_vat_return(self, statement):
        """The computed přiznání covering ``statement``'s period."""
        returns = self.env["cssk.vat.return"].search([
            ("company_id", "=", statement.company_id.id),
            ("state", "in", ("preview", "exported", "submitted")),
            ("date_from", "<=", statement.date_from),
            ("date_to", ">=", statement.date_to),
        ], order="date_from desc, id desc")
        exact = returns.filtered(
            lambda r: r.date_from == statement.date_from
            and r.date_to == statement.date_to)
        return (exact or returns)[:1]

    @api.model
    def siblings(self, statement, vat_return):
        """``(statements, missing)`` of the return's period.

        The statements of the same model covering the return's period, the
        latest of each sub-period (a následné hlášení replaces the řádné),
        and whether some part of the period has none.
        """
        if (statement.date_from == vat_return.date_from
                and statement.date_to == vat_return.date_to):
            return statement, False
        others = statement.search([
            ("company_id", "=", statement.company_id.id),
            ("state", "in", ("preview", "exported", "submitted")),
            ("date_from", ">=", vat_return.date_from),
            ("date_to", "<=", vat_return.date_to),
        ], order="id desc")
        latest = {}
        for other in others | statement:
            key = (other.date_from, other.date_to)
            if key not in latest or other == statement:
                latest[key] = other
        chosen = statement.browse([st.id for st in latest.values()])
        days = sum((st.date_to - st.date_from).days + 1 for st in chosen)
        whole = (vat_return.date_to - vat_return.date_from).days + 1
        return chosen, days != whole

    @api.model
    def _status(self, diff, tolerance, missing):
        if missing:
            return "info"
        return "ok" if abs(diff) <= tolerance else "amount"

    # ------------------------------------------------------------------
    # Kontrolní hlášení ↔ přiznání
    # ------------------------------------------------------------------
    @api.model
    def reconcile_kh(self, statement, vat_return):
        """``[{code, label, filed, computed, diff, kind, detail}]``."""
        statements, missing = self.siblings(statement, vat_return)
        values = {line.code: line.value for line in vat_return.line_ids}
        sections = {}
        for st in statements:
            for code, rows in st._collect_sections_by_code().items():
                sections.setdefault(code, []).append(rows)
        out = []
        for code, section_codes, columns, row_codes, label in KH_CONTROL_ROWS:
            kh = sum(sum(rows.mapped(column))
                     for section in section_codes
                     for rows in sections.get(section, [])
                     for column in columns)
            dp = sum(values.get(row, 0.0) for row in row_codes)
            diff = kh - dp
            kind = self._status(diff, self.KH_TOLERANCE, missing)
            detail = False
            if missing:
                detail = _(
                    "The přiznání covers %(from)s – %(to)s and not every "
                    "kontrolní hlášení of that period is computed; the row "
                    "is not compared.",
                    **{"from": vat_return.date_from, "to": vat_return.date_to})
            elif kind == "amount":
                detail = _(
                    "Kontrolní hlášení %(kh).2f ≠ přiznání %(dp).2f (rozdíl "
                    "%(diff).2f, tolerance 1 000 Kč). Zkontrolujte daně a "
                    "štítky dokladů období a zda byly oba výkazy přepočteny "
                    "po posledním zaúčtování.", kh=kh, dp=dp, diff=diff)
            out.append({"code": code, "label": label, "filed": kh,
                        "computed": dp, "diff": diff, "kind": kind,
                        "detail": detail})
        return out

    # ------------------------------------------------------------------
    # Souhrnné hlášení ↔ přiznání
    # ------------------------------------------------------------------
    @api.model
    def reconcile_sh(self, statement, vat_return):
        statements, missing = self.siblings(statement, vat_return)
        values = {line.code: line.value for line in vat_return.line_ids}
        lines = statements.line_ids
        out = []
        for code, sh_codes, row_code, label in SH_ROWS:
            rows = lines.filtered(lambda l: l.transaction_code in sh_codes)
            sh = sum(rows.mapped("total_amount"))
            dp = values.get(row_code, 0.0)
            diff = sh - dp
            # each partner's value is filed in whole crowns
            kind = self._status(diff, max(1.0, len(rows)), missing)
            detail = False
            if missing:
                detail = _(
                    "The přiznání covers %(from)s – %(to)s and not every "
                    "souhrnné hlášení of that period is computed; the row "
                    "is not compared.",
                    **{"from": vat_return.date_from, "to": vat_return.date_to})
            elif kind == "amount":
                detail = _(
                    "Souhrnné hlášení %(sh).2f ≠ přiznání %(dp).2f (rozdíl "
                    "%(diff).2f). Zkontrolujte DIČ odběratelů, daně dokladů "
                    "do EU a období.", sh=sh, dp=dp, diff=diff)
            out.append({"code": code, "label": label, "filed": sh,
                        "computed": dp, "diff": diff, "kind": kind,
                        "detail": detail})
        return out

    # ------------------------------------------------------------------
    # Přiznání ↔ účetnictví
    # ------------------------------------------------------------------
    @api.model
    def ledger_vat(self, company, date_from, date_to):
        """``(output, deduction, other)`` booked on account 343 in the period.

        A tax line is output tax when its tax is a sales tax, or when it is
        the negative leg of a purchase tax (reverse charge and acquisitions
        book both sides under one tax); the positive leg is the deduction.
        ``other`` is what moved on 343 without a tax behind it: payments to
        and from the tax office, and anything booked by hand.
        """
        lines = self.env["account.move.line"].search([
            ("parent_state", "=", "posted"), ("company_id", "=", company.id),
            ("date", ">=", date_from), ("date", "<=", date_to),
            ("account_id.code", "=like", "343%")])
        output = deduction = other = 0.0
        for line in lines:
            tax = line.tax_line_id
            if not tax:
                other += line.balance
            elif tax.type_tax_use == "sale" or (
                    line.tax_repartition_line_id.factor_percent < 0):
                output -= line.balance
            else:
                deduction += line.balance
        return output, deduction, other

    @api.model
    def ledger_revenue(self, company, date_from, date_to):
        """Credit turnover of účtová třída 6, skupina 60 (tržby)."""
        lines = self.env["account.move.line"].search([
            ("parent_state", "=", "posted"), ("company_id", "=", company.id),
            ("date", ">=", date_from), ("date", "<=", date_to),
            ("account_id.code", "=like", "60%")])
        return -sum(lines.mapped("balance"))

    @api.model
    def reconcile_books(self, vat_return):
        values = {line.code: line.value for line in vat_return.line_ids}
        output, deduction, other = self.ledger_vat(
            vat_return.company_id, vat_return.date_from, vat_return.date_to)
        revenue = self.ledger_revenue(
            vat_return.company_id, vat_return.date_from, vat_return.date_to)
        r62 = values.get("dan_zocelk", 0.0)
        # ř. 46 in both columns: the deduction as booked, before the
        # coefficient rows (52, 53, 60), which no tax line posts.
        r46 = values.get("odp_sum_nar", 0.0) + values.get("odp_sum_kr", 0.0)
        supplies = sum(values.get(code, 0.0) for code in _SUPPLY_ROWS)

        def row(code, label, left, right, kind=None, detail=False):
            diff = left - right
            if kind is None:
                kind = self._status(diff, self.LEDGER_TOLERANCE, False)
                if kind == "amount":
                    detail = _(
                        "Přiznání %(left).2f ≠ účet 343 %(right).2f (rozdíl "
                        "%(diff).2f). Hledejte daň zaúčtovanou na 343 bez "
                        "daně na řádku, daňový řádek bez štítku, nebo ručně "
                        "upravený řádek přiznání.",
                        left=left, right=right, diff=diff)
            return {"code": code, "label": label, "filed": left,
                    "computed": right, "diff": diff, "kind": kind,
                    "detail": detail}

        return [
            row("out_vat", _("Daň na výstupu (ř. 62 ↔ účet 343)"), r62, output),
            row("in_vat", _("Odpočet daně (ř. 46 ↔ účet 343)"), r46,
                deduction),
            row("other_343", _("Pohyby na účtu 343 mimo daňové řádky"),
                0.0, other, kind="info", detail=_(
                    "Payments to and from the tax office belong here. "
                    "Anything else was booked on 343 by hand and is in no "
                    "row of the return.") if other else False),
            row("revenue", _("Uskutečněná plnění ↔ tržby skupiny 60"),
                supplies, revenue, kind="info", detail=_(
                    "For orientation only: advances are taxed before they "
                    "are revenue, accruals are revenue before they are "
                    "taxed, and other revenue is outside group 60.")),
        ]
