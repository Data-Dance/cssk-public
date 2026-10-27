# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
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


def _cz_whole(value):
    """A DPHDP3 amount as the export writes it (``'%.0f'``), so a total
    foots with the rows it is filed beside."""
    return float("%.0f" % (value or 0.0))


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
                sum(sign * _cz_whole(vals.get(term, 0.0)) for sign, term in terms),
                " ".join("%s %s" % ("+" if sign > 0 else "-", term)
                         for sign, term in terms).lstrip("+ "))
        net = _cz_whole(vals.get("dan_zocelk")) - _cz_whole(vals.get("odp_zocelk"))
        if self.cz_filing_code in ("D", "E"):
            # "Vyplňuje se pouze při podání dodatečného přiznání … ř.62 - ř.63";
            # ř. 64 / 65 "Při podání dodatečného přiznání se nevyplňuje".
            put("dano_da", 0.0, "dan_zocelk - odp_zocelk (řádné/opravné)")
            put("dano_no", 0.0, "odp_zocelk - dan_zocelk (řádné/opravné)")
            put("dano", net, "dan_zocelk - odp_zocelk")
        else:
            put("dano_da", max(net, 0.0), "dan_zocelk - odp_zocelk, if > 0")
            put("dano_no", max(-net, 0.0), "odp_zocelk - dan_zocelk, if > 0")
            put("dano", 0.0, "dan_zocelk - odp_zocelk (dodatečné)")

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
        return res
