# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from odoo import _, api, fields, models
from odoo.exceptions import UserError

#: line_filter keys of DPHDP3 ř. 33 / ř. 34 -> the side of the document
#: whose bad-debt corrections they collect.
BAD_DEBT_FILTERS = {
    "cz_bad_debt_creditor": "sale",      # ř. 33, věřitel, § 46 a násl.
    "cz_bad_debt_debtor": "purchase",    # ř. 34, dlužník, § 74b
}


#: The DPHDP3 sum and difference rows, as the EPO structure defines them
#: (``dphdp3_epo2.xsd``, the documentation of each attribute):
#:
#: * ř. 46 — "součet řádků 40 až 45" in each column;
#: * ř. 62 — "ř.62 = 1 + 2 + … + 13 - 61 + daň podle § 108 odst. 4 písm. g)
#:   a h)" (the § 108 odst. 4 g)/h) tax has no row of its own and is not
#:   modelled: enter it as an override of ř. 62 where it arises);
#: * ř. 63 — "ř.63 = 46 V plné výši + 52 Odpočet + 53 Změna odpočtu + 60".
#:
#: ``(code, ((sign, code), ...))``, evaluated in this order.
CZ_TOTALS = (
    ("odp_sum_nar", ((1, "odp_tuz23_nar"), (1, "odp_tuz5_nar"),
                     (1, "odp_cu_nar"), (1, "od_zdp23"), (1, "od_zdp5"),
                     (1, "odp_rez_nar"))),
    ("odp_sum_kr", ((1, "odp_tuz23"), (1, "odp_tuz5"), (1, "odp_cu"),
                    (1, "odkr_zdp23"), (1, "odkr_zdp5"), (1, "odp_rezim"))),
    ("dan_zocelk", ((1, "dan23"), (1, "dan5"), (1, "dan_pzb23"),
                    (1, "dan_pzb5"), (1, "dan_psl23_e"), (1, "dan_psl5_e"),
                    (1, "dan_dzb23"), (1, "dan_dzb5"), (1, "dan_pdop_nrg"),
                    (1, "dan_rpren23"), (1, "dan_rpren5"), (1, "dan_psl23_z"),
                    (1, "dan_psl5_z"), (-1, "dan_vrac"))),
    ("odp_zocelk", ((1, "odp_sum_nar"), (1, "odp_uprav_kf"),
                    (1, "vypor_odp"), (1, "uprav_odp"))),
)


#: DPHDP3 attributes that state a TAX — daň na výstupu, odpočet daně and the
#: rows computed from them. "Daň se zaokrouhluje na celé koruny nahoru"
#: (zákon č. 280/2009 Sb., daňový řád, § 146 odst. 1); the form only says
#: "Údaje v daňovém přiznání se uvedou zaokrouhlené na celé koruny" (25 5401
#: vzor 26) and its pokyny (25 5412 vzor 22) name no direction.
CZ_TAX_CODES = frozenset("""
    dan23 dan5 dan_dzb23 dan_dzb5 dan_pdop_nrg dan_psl23_e dan_psl23_z
    dan_psl5_e dan_psl5_z dan_pzb23 dan_pzb5 dan_rpren23 dan_rpren5
    opr_dane_dan opr_verit opr_dluz
    odp_tuz23_nar odp_tuz23 odp_tuz5_nar odp_tuz5 odp_cu_nar odp_cu
    od_zdp23 odkr_zdp23 od_zdp5 odkr_zdp5 odp_rez_nar odp_rezim
    odp_sum_nar odp_sum_kr od_maj odkr_maj odp_uprav_kf vypor_odp
    uprav_odp dan_vrac dan_zocelk odp_zocelk dano dano_da dano_no
""".split())

#: ř. 52 / ř. 53 coefficients: "Vypočtený koeficient se zaokrouhlí na celé
#: procento nahoru" (zákon č. 235/2004 Sb., § 76 odst. 3).
CZ_COEFFICIENT_CODES = frozenset({"koef_p20_nov", "koef_p20_vypor"})

#: Rows a dodatečné přiznání files AS THEY ARE rather than as a difference:
#: the coefficient is stated ("do levého sloupce Koeficient (%) se uvede
#: příslušný koeficient"), ř. 66 is itself the difference, ř. 64 / 65 are
#: not filled at all.
CZ_NOT_DIFFERENCED = CZ_COEFFICIENT_CODES | {"dano", "dano_da", "dano_no"}


def _cz_whole(value, code=None):
    """A DPHDP3 amount in whole crowns, as the export files it.

    A tax (``CZ_TAX_CODES``) and a coefficient round UP — towards plus
    infinity, the reading of "nahoru" that never states less tax; a base or
    a value rounds to the nearest crown, half away from zero. The amount is
    first taken at its two decimals so that float noise in a sum
    (``1000.0000000001``) is not mistaken for a part of a crown.

    This used to be ``'%.0f'``, which is round-half-EVEN: 210.50 of tax went
    on the return as 210 and 211.50 as 212.
    """
    amount = Decimal("%.2f" % (value or 0.0))
    if code in CZ_TAX_CODES or code in CZ_COEFFICIENT_CODES:
        rounding = ROUND_CEILING
    else:
        rounding = ROUND_HALF_UP
    return float(amount.to_integral_value(rounding=rounding))


class CsskVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    cz_filing_code = fields.Char(related="statement_type_id.fa_xml_value")
    cz_country_code = fields.Char(related="country_id.code")
    # ONE date, not two: the shared ``discovery_date`` is what an amendment
    # gets on creation and what the base form asked for, while the XML read a
    # second, Czech field — so a return could carry two different dates and
    # file the one nobody looked at. (Values of the old column are copied
    # over by the 19.0.1.11.0 migration.)
    cz_discovery_date = fields.Date(
        related="discovery_date", readonly=False,
        string="Důvody zjištěny dne",
        help="d_zjist — the day the reasons for a dodatečné přiznání were "
        "found. Required for a dodatečné (D) or dodatečné/opravné (E) return.")

    # ------------------------------------------------------------------
    # Bad-debt corrections (l10n_cz_statutory ``l10n_cz_bad_debt``)
    # ------------------------------------------------------------------
    # A correction of tax on an unrecoverable receivable is reported on ř. 33
    # (creditor) or ř. 34 (debtor) and on no ordinary row. Its taxes are the
    # ordinary ones, so its lines carry the ordinary tags; the return
    # therefore leaves flagged documents out of the period it reads every
    # ordinary row from — for the figure AND its drill-down, which must agree
    # — and ř. 33 / ř. 34 add their tax back.
    def _cssk_period_move_ids(self, company, date_from, date_to):
        move_ids = super()._cssk_period_move_ids(company, date_from, date_to)
        if (self.env.context.get("cz_with_bad_debt")
                or company.account_fiscal_country_id.code != "CZ"
                or not move_ids):
            return move_ids
        flagged = set(self._cz_bad_debt_moves(move_ids).ids)
        return [mid for mid in move_ids if mid not in flagged]

    def _cz_bad_debt_moves(self, move_ids):
        return self.env["account.move"].search([
            ("id", "in", list(move_ids)), ("l10n_cz_bad_debt", "!=", False)])

    def _cz_bad_debt_tax_lines(self, side):
        """Tax lines of this period's flagged documents on ``side``."""
        self.ensure_one()
        all_ids = self.with_context(cz_with_bad_debt=True)._cssk_period_move_ids(
            self.company_id, self.date_from, self.date_to)
        moves = self._cz_bad_debt_moves(all_ids)
        moves = moves.filtered(
            lambda m: m.is_sale_document(include_receipts=True)
            if side == "sale" else m.is_purchase_document(include_receipts=True))
        return moves.line_ids.filtered(
            lambda l: l.tax_line_id and l.tax_tag_ids)

    def _eval_tags(self, formula, move_lines, line_filter=None):
        side = BAD_DEBT_FILTERS.get(line_filter)
        if side is None or self.country_id.code != "CZ":
            return super()._eval_tags(formula, move_lines, line_filter)
        # Hand-tagged entries (VAT 33 / VAT 34) keep counting.
        total = super()._eval_tags(formula, move_lines, None)
        balance = sum(self._cz_bad_debt_tax_lines(side).mapped("balance"))
        # Both rows are positive for the correction the section describes:
        # the creditor's credit note DEBITS output tax, the debtor's CREDITS
        # input tax.
        return total + (balance if side == "sale" else -balance)

    def _cssk_tag_source_line_filter(self, key, domain):
        # ř. 33 / ř. 34 are not a share of their tags: their drill-down is
        # built whole by ``_tag_source_domain`` below.
        if key in BAD_DEBT_FILTERS and self.country_id.code == "CZ":
            return domain
        return super()._cssk_tag_source_line_filter(key, domain)

    def _tag_source_domain(self, formula, move_ids=None):
        """ř. 33 / ř. 34 drill into the flagged documents' tax lines as well."""
        domain = super()._tag_source_domain(formula, move_ids)
        if self.country_id.code != "CZ":
            return domain
        ldef = self.version_id.line_def_ids.filtered(
            lambda d: d.tag_formula == formula and d.line_filter in BAD_DEBT_FILTERS)[:1]
        if not ldef:
            return domain
        lines = self._cz_bad_debt_tax_lines(BAD_DEBT_FILTERS[ldef.line_filter])
        if not lines:
            return domain
        Tag = self.env["account.account.tag"]
        tags = Tag.browse()
        for _sign, name in self._iter_tag_terms(formula):
            tags |= Tag._get_tax_tags(name, self.country_id.id)
        own_moves = set(move_ids or [])
        if tags and own_moves:
            own_moves = set(self.env["account.move.line"].search([
                ("move_id", "in", list(own_moves)),
                ("tax_tag_ids", "in", tags.ids)]).move_id.ids)
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("move_id", "in", sorted(own_moves | set(lines.move_id.ids))),
                ("tax_tag_ids", "in", (tags | lines.tax_tag_ids).ids)]

    # ------------------------------------------------------------------
    # ř. 46 and ř. 62 – 66: computed, not typed
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        res = super().action_compute_lines()
        for ret in self.filtered(lambda r: r.country_id.code == "CZ"):
            ret._cz_fill_totals()
        return res

    def _cz_fill_totals(self):
        """The sum and difference rows were manual lines, so a return
        exported 0 on ř. 46 and ř. 62 – 66 unless an accountant overrode
        every one of them. Computed here from the rows as filed; an override
        on any of them is kept and feeds the rows after it."""
        self.ensure_one()
        lines = {line.code: line for line in self.line_ids}
        vals = {code: line.value for code, line in lines.items()}

        def put(code, value, note):
            line = lines.get(code)
            if line and not line.is_overridden:
                line.write({"value": value, "formula_note": note})
                vals[code] = value
            elif line:
                vals[code] = line.value

        for code, terms in CZ_TOTALS:
            put(code,
                sum(sign * _cz_whole(vals.get(term, 0.0), term)
                    for sign, term in terms),
                " ".join("%s %s" % ("+" if sign > 0 else "-", term)
                         for sign, term in terms).lstrip("+ "))
        net = (_cz_whole(vals.get("dan_zocelk"), "dan_zocelk")
               - _cz_whole(vals.get("odp_zocelk"), "odp_zocelk"))
        if self.cz_filing_code in ("D", "E"):
            # "Vyplňuje se pouze při podání dodatečného přiznání … ř.62 - ř.63";
            # ř. 64 / 65 "Při podání dodatečného přiznání se nevyplňuje".
            # The rows of a dodatečné are DIFFERENCES ("V dodatečném přiznání
            # se uvádí pouze rozdíly od údajů, ze kterých byla stanovena
            # poslední známá daň", pokyny 25 5412), so ř. 66 is this net
            # minus the net of the return it amends — "Na ř. 66 se vyznačí
            # rozdíl oproti poslední známé dani". It used to be the full net,
            # which claimed the whole period's tax a second time.
            base = self._cz_baseline_values() or {}
            base_net = (_cz_whole(base.get("dan_zocelk"), "dan_zocelk")
                        - _cz_whole(base.get("odp_zocelk"), "odp_zocelk"))
            put("dano_da", 0.0, "dan_zocelk - odp_zocelk (řádné/opravné)")
            put("dano_no", 0.0, "odp_zocelk - dan_zocelk (řádné/opravné)")
            put("dano", net - base_net,
                "(dan_zocelk - odp_zocelk) - poslední známá daň")
        else:
            put("dano_da", max(net, 0.0), "dan_zocelk - odp_zocelk, if > 0")
            put("dano_no", max(-net, 0.0), "odp_zocelk - dan_zocelk, if > 0")
            put("dano", 0.0, "dan_zocelk - odp_zocelk (dodatečné)")

    @api.depends("cz_filing_code")
    def _compute_to_pay(self):
        """On a dodatečné (D / E) the settlement is ř. 66.

        ř. 64 / 65 are not filled on a dodatečné, so the base computation
        read them as zero and showed nothing to pay. ř. 66 is the difference
        against the poslední známá daň: positive is tax to pay, negative a
        reduction, and no excess is carried on it.
        """
        super()._compute_to_pay()
        for ret in self.filtered(lambda r: r.cz_filing_code in ("D", "E")):
            dano = sum(ret.line_ids.filtered(lambda l: l.code == "dano").mapped("value"))
            ret.to_pay = ret.currency_id.round(dano) if ret.currency_id else dano

    # ------------------------------------------------------------------
    # Dodatečné přiznání: differences against the poslední známá daň
    # ------------------------------------------------------------------
    def _cz_baseline_return(self):
        """The return whose figures a dodatečné states its differences from.

        The one it amends (``original_return_id``). A dodatečné/opravné (E)
        REPLACES an earlier dodatečné filed within its deadline ("Takto lze
        nahradit i dodatečná daňová přiznání", pokyny 25 5412), so where it
        was raised from that dodatečné its baseline is what the dodatečné
        itself amended. Rows of every return stay at their full values, so a
        dodatečné is a valid baseline for the next one.
        """
        self.ensure_one()
        base = self.original_return_id
        if self.cz_filing_code == "E":
            seen = set()
            while (base and base.cz_filing_code in ("D", "E")
                   and base.id not in seen):
                seen.add(base.id)
                base = base.original_return_id
        return base

    def _cz_baseline_values(self):
        """``{code: full value}`` of the baseline, or None when this is not
        a dodatečné or it has nothing to difference against."""
        self.ensure_one()
        if self.cz_filing_code not in ("D", "E"):
            return None
        base = self._cz_baseline_return()
        if not base or not base.line_ids:
            return None
        return {line.code: line.value for line in base.line_ids}

    def _cz_epo_values(self):
        """``{code: 'whole crowns'}`` as the DPHDP3 attributes file them:
        rounded per ``_cz_whole``, and on a dodatečné the difference against
        the baseline for every row but ``CZ_NOT_DIFFERENCED``."""
        self.ensure_one()
        base = self._cz_baseline_values()
        out = {}
        for line in self.line_ids:
            filed = _cz_whole(line.value, line.code)
            if base is not None and line.code not in CZ_NOT_DIFFERENCED:
                filed -= _cz_whole(base.get(line.code, 0.0), line.code)
            out[line.code] = "%d" % filed
        return out

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        if self.country_id.code == "CZ":
            ctx["cz_epo"] = self._cz_epo_values()
        return ctx

    def _kontroly_rules(self):
        rules = super()._kontroly_rules()
        if self.country_id.code != "CZ":
            return rules
        # vlastní daň and nadměrný odpočet are both positive figures and
        # never both present (dphdp3_epo2.xsd, ř. 64 / ř. 65).
        rules += [
            {"type": "nonneg", "code": "dano_da"},
            {"type": "nonneg", "code": "dano_no"},
            {"type": "exclusive", "a": "dano_da", "b": "dano_no"},
        ]
        return rules

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.cz_country_code != "CZ":
                continue
            if rec.cz_filing_code in ("D", "E") and not rec.cz_discovery_date:
                raise UserError(_(
                    "A dodatečné přiznání needs the date its reasons were "
                    "found (Důvody zjištěny dne, d_zjist)."))
            if (rec.cz_filing_code in ("D", "E")
                    and rec._cz_baseline_values() is None):
                raise UserError(_(
                    "A dodatečné přiznání states only the differences from "
                    "the return it amends, so it needs that return with its "
                    "rows computed. Create it with \"Amended / corrective\" on "
                    "the filed return."))
        return res
