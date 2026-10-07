import re

from odoo import api, fields, models

from odoo.addons.l10n_cssk_kv_kh_base.models.cssk_control_statement_mixins import (
    CSSKControlStatementSectionMixin,
)

from .product import RC_GOODS, RC_GOODS_KIND, RC_GOODS_WITH_CODE

# MJType of every vzor: the only units A.2 accepts, and the uom each maps to.
_KV_UNITS = (
    ("kg", "uom.product_uom_kgm"),
    ("t", "uom.product_uom_ton"),
    ("m", "uom.product_uom_meter"),
    ("ks", "uom.product_uom_unit"),
)


# ----------------------------------------------------------------------
# Detail sections (A.1, A.2, B.1, B.2, C.1, C.2) — one row per (invoice, rate)
# ----------------------------------------------------------------------
class L10nSKKvDphDetailMixin(models.AbstractModel):
    """Shared behaviour for SK KV DPH **detail** sections.

    Groups the section's eligible base lines by (move, VAT rate) and snapshots
    one row per group — a two-rate invoice produces two rows, as KV DPH
    requires. Concrete sections override ``_cssk_row_vals`` for extra columns.
    """

    _name = "l10n.sk.kv.dph.detail.mixin"
    _inherit = "cssk.control.statement.section.mixin"
    _description = "SK KV DPH detail section (mixin)"

    def _kv_identity(self):
        """A bare country code is "no VAT number", on either side.

        Where a supplier has no IČ DPH — a third-country one on B.1, mostly —
        the form leaves ``Dod`` optional and free-format, so ``US`` and an
        empty attribute file the same thing. Sources and Odoo both write
        either, depending on the partner record: on a migrated i6 agenda the
        same US supplier read ``US`` on one side and nothing on the other for
        some rows and the reverse for others, and every such row reported as
        two one-sided differences.
        """
        identity = super()._kv_identity()
        vat = (identity[0] or "").strip()
        if vat == "0" or re.fullmatch(r"[A-Za-z]{2}", vat):
            identity = ("",) + identity[1:]
        return identity

    def _kv_identity_ref(self):
        """The reference as the FORM carries it, whitespace removed.

        A filed KV DPH can only hold the stripped reference (``\\S{1,32}``,
        and the export writes ``entry_ref_xml``), so a comparison against a
        filed or migrated statement keyed on the stored ``FV 1/06/2024`` never
        met the ``FV1/06/2024`` the tax office received: 3 694 rows of a
        migrated i6 agenda read as pairs of one-sided differences with the
        money agreeing. Two references that differ only by whitespace are one
        row on this form anyway. The stored spelling is untouched.
        """
        self.ensure_one()
        return self._cssk_ref_for_xml(self.entry_ref)

    # Received-document sections (B.1, B.2, C.2) must report the SUPPLIER's
    # poradové číslo faktúry (move.ref), not our internal move name — for the
    # correction sections that applies to the original-document column too.
    _kv_inbound = False

    @api.model
    def _populate_for_statement(self, statement, section_code):
        groups = {}
        for line in self._eligible_move_lines(statement, section_code):
            base, tax = line._cssk_base_and_tax_amounts()
            rate = line._cssk_tax_rate()
            # Keyed on the move that carries the tax, so each payment of a
            # cash-basis invoice is its own row with its own date — but the
            # row DESCRIBES the invoice (see ``_cssk_vat_document``).
            #
            # Un-reconciling a payment makes Odoo REVERSE its cash-basis
            # entry, and the reversal inherits the origin, so it resolves to
            # the same invoice with the opposite sign. It joins the entry it
            # reverses: in the same period the two cancel and no row is filed,
            # where keying them apart filed +x and -x under one invoice
            # number. A reversal pushed into a later period by a lock date
            # stands alone there, negative, which is what happened.
            entry = line.move_id
            if entry.tax_cash_basis_origin_move_id and entry.reversed_entry_id:
                entry = entry.reversed_entry_id
            key = (entry.id, rate) + self._cssk_group_key_extra(line)
            group = groups.get(key)
            if group is None:
                group = groups[key] = {
                    "move": line.move_id._cssk_vat_document(),
                    "entry": entry,
                    "line": line,
                    "lines": self.env["account.move.line"],
                    "rate": rate,
                    "base": 0.0,
                    "tax": 0.0,
                }
            group["lines"] |= line
            group["base"] += base
            group["tax"] += tax
        currency = statement.company_id.currency_id
        return self.create([
            self._cssk_row_vals(statement, g) for g in groups.values()
            # Only a cash-basis group can cancel out (see above); any other
            # zero row is left for the kontroly to see, as before.
            if not (g["entry"] != g["move"]
                    and currency.is_zero(g["base"])
                    and currency.is_zero(g["tax"]))
        ])

    def _cssk_group_key_extra(self, line):
        """What else splits one document into rows, beyond its rate."""
        return ()

    def _cssk_row_vals(self, statement, group):
        move = group["move"]
        line = group["line"]
        # The corrected document: Odoo's link where there is one, else the
        # number typed on a credit note created by hand (which has no link to
        # follow). Without either a C.1 / C.2 row has no FO, and the export
        # refuses it rather than filing the credit note's own number as its
        # original, which is what the template used to fall back to.
        original = move._cssk_control_original()
        manual = move.cssk_control_original_ref or False
        if self._kv_inbound and not manual:
            # A received credit note's "Source Document" is where the
            # supplier's original invoice number is commonly typed, and on
            # some agendas it is mandatory before posting — one customer's requires
            # it on every SK vendor credit note. Read last: a link or the
            # dedicated field stays authoritative where filled. Not on the
            # sales side, where invoice_origin is the SALES ORDER number and
            # would be filed as the corrected invoice.
            manual = self._cssk_origin_as_invoice_number(move) or False
        if self._kv_inbound:
            entry_ref = move.ref or move.name
            entry_ref_original = (
                (original.ref or original.name) if original else manual
            )
        else:
            entry_ref = move.name
            entry_ref_original = original.name if original else manual
        vals = {
            "statement_id": statement.id,
            "move_line_id": line.id,
            "partner_id": move.partner_id.id,
            "partner_vat": line._cssk_partner_vat_for_statement(),
            "partner_vat_stripped": line._cssk_partner_vat_stripped(),
            "partner_country_code": (move.partner_id.country_id.code or "")[:2],
            "entry_ref": entry_ref,
            "entry_ref_original": entry_ref_original,
            # Dátum dodania: the move's taxable supply date when set
            # (advances: the payment date), else the invoice date. A tax that
            # became due on payment is dated by the payment — the cash-basis
            # entry's own date — and never by the invoice it settled.
            "supply_date": group["entry"].date
            if group["entry"] != move
            else (move.taxable_supply_date or move.invoice_date or move.date),
            "tax_base_amount": group["base"],
            "tax_amount": group["tax"],
            "tax_rate": group["rate"],
            "source_move_line_ids": [(6, 0, group["lines"].ids)],
        }
        if self._kv_inbound:
            vals["deducted_amount"] = self._cssk_deducted_amount(
                statement, group
            )
        return vals

    def _cssk_origin_as_invoice_number(self, move):
        """``invoice_origin`` when it can be the supplier's invoice number.

        A vendor credit note raised from a purchase order carries the ORDER
        name there ("P00012", or several, comma-separated). That is not the
        corrected invoice, and filing it as FO would pass the export's check
        that a number is present. So an origin naming a purchase order is not
        read, and the export asks for the real number instead."""
        origin = (move.invoice_origin or "").strip()
        if not origin or "purchase.order" not in self.env:
            return origin
        names = [n.strip() for n in origin.split(",") if n.strip()]
        if self.env["purchase.order"].sudo().search_count(
                [("name", "in", names), ("company_id", "=", move.company_id.id)],
                limit=1):
            return ""
        return origin

    def _cssk_deducted_amount(self, statement, group):
        """Odpočítaná daň — attribute ``O`` (``OR`` on C.2).

        Only the received sections (B.1 / B.2 / C.2) have one; A.1 / A.2 / C.1
        are output tax with nothing to deduct, and the field stays 0.00 there.

        The part of the tax that the TAX ITSELF deducts: the legs of its
        repartition that the VAT closing settles. A full deduction is the
        whole tax, as before. A partial one is what the return deducts —
        a vehicle at 50 % puts half on 343 and half on the expense, and only
        that half is on row 21 of the DP DPH, so only that half belongs in
        ``O``. A tax with no right to deduct (self-assessed with no deduction
        leg) deducts 0.00. A § 50 koeficient set on the tax the same way is
        honoured the same way.

        Confirmed by a customer's accountant (2026-10-03), who
        asked for exactly this: "tak ako do daňového priznania berieš ako
        uplatnenú daň na riadku 21 len 50 % z hodnoty DPH, tak aj do
        kontrolného výkazu do stĺpca Odpočítaná daň musí ísť len tých 50 % …
        brala by som to z nastavenia dane" — from the tax setting, not a
        hard-coded ratio. It used to file the full tax whatever the tax said.

        The year-end koeficient true-up stays a manual override:
        ``deducted_amount`` is in ``_KV_OVERRIDE_FIELDS``, so the override
        survives a recompute and reaches the XML.
        """
        return self._cssk_deducted_of(group["lines"], group["tax"])

    @api.model
    def _cssk_deducted_of(self, lines, tax):
        """``tax`` (as D files it) times the deductible share of ``lines``.

        Applied to D rather than recomputed per line, so a fully deductible
        tax files ``O`` equal to ``D`` to the cent — a per-line recomputation
        drifts on a foreign-currency or many-line document — and ``O`` can
        never exceed ``D``.
        """
        deductible = charged = 0.0
        for line in lines:
            d, c = line._cssk_deductible_share()
            deductible += d
            charged += c
        if not charged:
            return 0.0
        currency = self.env.company.currency_id
        return currency.round(tax * min(deductible / charged, 1.0))


class L10nSKKvDphSectionA1(models.Model):
    """A.1 — issued domestic invoices with VAT (incl. HS-code column)."""

    _name = "l10n.sk.kv.dph.section.a1"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section A.1"

    product_code = fields.Char(string="HS code (4-digit)")

    def _cssk_row_vals(self, statement, group):
        vals = super()._cssk_row_vals(statement, group)
        # Display only — oddiel A.1 files no commodity code. It used to read a
        # field no module defines and so was always empty.
        vals["product_code"] = group["line"].product_id._l10n_sk_kv_cn_code() \
            if group["line"].product_id else ""
        return vals


class L10nSKKvDphSectionA2(models.Model):
    """A.2 — domestic reverse-charge supplied (§69 ods. 12).

    For goods under § 69 ods. 12 písm. f) to i) the row also carries what was
    supplied: the SCS code (TK, písm. f, g) or the kind (TD, písm. h, i), and
    the quantity (Mn) in one of the four units the form knows (MJ). The
    category is a property of the PRODUCT (``l10n_sk_kv_rc_goods``), so a
    document mixing two of them files one row per commodity — the form has
    one TK per row and nowhere else to put a second.

    Reported by an external accountant, who found the columns missing: the
    schema has always had them (every vzor from 2014), the template never
    wrote them.
    """

    _name = "l10n.sk.kv.dph.section.a2"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section A.2"

    rc_goods = fields.Selection(RC_GOODS, string="§ 69 ods. 12 goods")
    goods_code = fields.Char(string="Kód tovaru (TK)", size=4)
    goods_kind = fields.Selection(
        [("MT", "MT — mobilné telefóny"), ("IO", "IO — integrované obvody")],
        string="Druh tovaru (TD)")
    quantity = fields.Float(string="Množstvo (Mn)", digits=(16, 2))
    uom_code = fields.Selection(
        [("kg", "kg"), ("t", "t"), ("m", "m"), ("ks", "ks")],
        string="Merná jednotka (MJ)")

    _KV_SNAPSHOT_FIELDS = (
        CSSKControlStatementSectionMixin._KV_SNAPSHOT_FIELDS
        + ["rc_goods", "goods_code", "goods_kind", "quantity", "uom_code"])

    def _kv_identity(self):
        # Two commodities on one invoice are two rows; the dodatočný delta
        # must not pair the cereal row of the original with the metal row of
        # the correction.
        return super()._kv_identity() + (
            self.goods_code or "", self.goods_kind or "", self.uom_code or "")

    def _kv_values(self):
        return super()._kv_values() + (round(self.quantity or 0.0, 2),)

    @api.model
    def _cssk_goods_of(self, line):
        """(category, TK, TD, MJ, quantity-in-MJ) for one invoice line."""
        product = line.product_id
        goods = product.l10n_sk_kv_rc_goods
        if not goods:
            return False, "", False, False, 0.0
        code = product._l10n_sk_kv_cn_code() if goods in RC_GOODS_WITH_CODE else ""
        mj, qty = self._cssk_quantity_in_form_unit(line)
        return goods, code, RC_GOODS_KIND.get(goods, False), mj, qty

    @api.model
    def _cssk_quantity_in_form_unit(self, line):
        """The line's quantity in kg / t / m / ks, or (False, 0.0).

        The line's own unit when it IS one of the four; otherwise the first of
        them it converts to (grams to kg, a dozen to ks). A unit that converts
        to none of them cannot be filed, and the preflight names the document
        rather than inventing a number.
        """
        uom = line.product_uom_id
        targets = [(mj, self.env.ref(xid, raise_if_not_found=False))
                   for mj, xid in _KV_UNITS]
        for mj, target in targets:
            if target and uom == target:
                return mj, line.quantity
        for mj, target in targets:
            if target and uom and uom._has_common_reference(target):
                return mj, uom._compute_quantity(
                    line.quantity, target, round=False)
        return False, 0.0

    def _cssk_group_key_extra(self, line):
        goods, code, kind, mj, _qty = self._cssk_goods_of(line)
        return (goods or "", code, kind or "", mj or "")

    def _cssk_row_vals(self, statement, group):
        vals = super()._cssk_row_vals(statement, group)
        goods, code, kind, mj = False, "", False, False
        qty = 0.0
        for line in group["lines"]:
            goods, code, kind, mj, line_qty = self._cssk_goods_of(line)
            qty += line_qty
        if goods:
            vals.update({
                "rc_goods": goods, "goods_code": code, "goods_kind": kind,
                "uom_code": mj, "quantity": qty,
            })
        return vals


class L10nSKKvDphSectionB1(models.Model):
    """B.1 — domestic reverse-charge received (recipient self-assesses)."""

    _name = "l10n.sk.kv.dph.section.b1"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section B.1"
    _kv_inbound = True


class L10nSKKvDphSectionB2(models.Model):
    """B.2 — standard received invoices with input-VAT deduction."""

    _name = "l10n.sk.kv.dph.section.b2"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section B.2"
    _kv_inbound = True


class L10nSKKvDphSectionC1(models.Model):
    """C.1 — corrections of issued invoices (ťarchopis / dobropis)."""

    _name = "l10n.sk.kv.dph.section.c1"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section C.1"


class L10nSKKvDphSectionC2(models.Model):
    """C.2 — corrections of received invoices (incl. § 53b bad-debt corrections)."""

    _name = "l10n.sk.kv.dph.section.c2"
    _inherit = "l10n.sk.kv.dph.detail.mixin"
    _description = "KV DPH Section C.2"
    _kv_inbound = True

    @api.model
    def _populate_for_statement(self, statement, section_code):
        # Normal C.2 rows (received credit/debit notes) + § 53b corrections.
        rows = super()._populate_for_statement(statement, section_code)
        return rows | self._cssk_populate_par53b(statement)

    @api.model
    def _cssk_populate_par53b(self, statement):
        """Surface § 53b bad-debt corrections (``l10n_sk_par53b``) in oddiel C.2.

        These are journal entries that carry the r29 tag **directly** on the VAT
        line (no invoice tax), so the line-by-line section resolver skips them —
        yet KVDPHv17 puts opravy odpočítanej dane podľa § 53/53a/**53b** in C.2.
        We derive the row from the correction's VAT line (tax = its balance, so
        a correction is negative, a re-claim positive) and the original unpaid
        bill (partner/Dod, FO, rate → base = tax / rate). No-op if l10n_sk_par53b
        isn't installed."""
        Move = self.env["account.move"]
        if "l10n_sk_par53b_origin_id" not in Move._fields:
            return self.browse()
        moves = Move.search([
            ("company_id", "=", statement.company_id.id),
            ("state", "=", "posted"),
            # Period through the shared helper, not a raw date range: KV DPH
            # reconciles against the VAT return, so both must agree on what the
            # period contains — output by tax point, input by the period the
            # deduction is claimed in.
            ("id", "in", statement._cssk_period_move_ids(
                statement.company_id, statement.date_from, statement.date_to)),
            ("l10n_sk_par53b_origin_id", "!=", False),
        ])
        vals = []
        for move in moves:
            origin = move.l10n_sk_par53b_origin_id
            vat_line = move.line_ids.filtered("tax_tag_ids")[:1]
            if not vat_line or not origin:
                continue
            rate = self._cssk_par53b_rate(origin)
            tax = vat_line.balance
            base = tax / (rate / 100.0) if rate else 0.0
            partner = origin.commercial_partner_id
            vat = partner.vat or ""
            stripped = vat[2:] if vat[:2].isalpha() else vat
            vals.append({
                "statement_id": statement.id,
                "move_line_id": vat_line.id,
                "partner_id": partner.id,
                "partner_vat": vat,
                "partner_vat_stripped": stripped,
                "partner_country_code": (partner.country_id.code or "")[:2],
                "entry_ref": move.name,
                "entry_ref_original": origin.ref or origin.name,
                "supply_date": move.date,
                "tax_base_amount": base,
                "tax_amount": tax,
                # OR — the § 53b correction IS a correction of odpočítaná daň,
                # so the deducted figure is the whole of it (see
                # ``_cssk_deducted_amount``).
                "deducted_amount": tax,
                "tax_rate": rate,
            })
        return self.create(vals)

    @api.model
    def _cssk_par53b_rate(self, origin):
        """VAT rate of the original unpaid bill (to recover base from the tax)."""
        taxes = origin.invoice_line_ids.tax_ids.filtered(lambda t: t.amount > 0)
        return taxes[:1].amount or 0.0


# ----------------------------------------------------------------------
# B.3 — simplified invoices (receipts). Below the 3 000 EUR period threshold
# they aggregate into B.3.1; at/above it they are listed per supplier in B.3.2.
#
# ASSUMPTION (validate with accountant): B.3.1 and B.3.2 are treated as mutually
# exclusive on the period grand total of deductible VAT.
# ----------------------------------------------------------------------
class L10nSKKvDphB3Mixin(models.AbstractModel):
    _name = "l10n.sk.kv.dph.b3.mixin"
    _inherit = "cssk.control.statement.summary.mixin"
    _description = "SK KV DPH B.3 (mixin)"

    @api.model
    def _cssk_b3_lines(self, statement):
        return self.env["account.move.line"].search(
            [
                ("parent_state", "=", "posted"),
                ("company_id", "=", statement.company_id.id),
                ("move_id", "in", statement._cssk_period_move_ids(
                    statement.company_id, statement.date_from, statement.date_to)),
                ("cssk_control_section_code", "=", "B.3"),
            ]
        )

    @api.model
    def _cssk_b3_totals(self, statement):
        """Return ``(grand_base, grand_tax, by_supplier)`` over the B.3 set.

        Each supplier also carries ``share`` — the deductible and charged legs
        of its taxes, as on the detail rows (fuel on a pokladničný doklad is
        exactly the 50 % case); :meth:`_cssk_b3_deducted` applies it."""
        grand_base = grand_tax = 0.0
        by_supplier = {}
        for line in self._cssk_b3_lines(statement):
            base, tax = line._cssk_base_and_tax_amounts()
            grand_base += base
            grand_tax += tax
            partner = line.move_id._cssk_vat_document().partner_id
            sup = by_supplier.get(partner.id)
            if sup is None:
                sup = by_supplier[partner.id] = {
                    "partner": partner,
                    "base": 0.0,
                    "tax": 0.0,
                    "moves": set(),
                    "lines": self.env["account.move.line"],
                }
            sup["base"] += base
            sup["tax"] += tax
            sup.setdefault("share", [0.0, 0.0])
            d, c = line._cssk_deductible_share()
            sup["share"][0] += d
            sup["share"][1] += c
            sup["moves"].add(line.move_id.id)
            sup["lines"] |= line
        return grand_base, grand_tax, by_supplier

    @api.model
    def _cssk_b3_deducted(self, by_supplier):
        return sum(self._cssk_sup_deducted(sup) for sup in by_supplier.values())

    @api.model
    def _cssk_sup_deducted(self, sup):
        """A supplier's tax times its deductible share (see ``_cssk_deducted_of``)."""
        deductible, charged = sup.get("share", (0.0, 0.0))
        if not charged:
            return 0.0
        return self.env.company.currency_id.round(
            sup["tax"] * min(deductible / charged, 1.0))


class L10nSKKvDphSectionB3(models.Model):
    """B.3 — the single aggregate of the vintage that ran to 31. 3. 2016.

    B.3.1 without the threshold test, and that is the whole difference. The
    split into B.3.1 (below the limit, aggregated) and B.3.2 (at or above it,
    per supplier) arrived with the vzor effective 1. 4. 2016; before that the
    form carried ONE aggregate of every simplified invoice in the period,
    whatever it was worth.

    Read off the schemas rather than assumed, because the Odoo model is richer
    than the form here and reading the model instead gets it wrong: in
    ``kv_dph_2014.xsd`` the ref is ``B3 maxOccurs="2"`` with attributes
    Z/D/O/KOpr and NO supplier attribute at all, identical to ``B31`` in every
    later vintage. ``l10n.sk.kv.dph.section.b32`` carries ``partner_id`` and
    ``partner_vat`` because B.3.2 needs them — B.3 never did.
    """

    _name = "l10n.sk.kv.dph.section.b3"
    _inherit = "l10n.sk.kv.dph.b3.mixin"
    _description = "KV DPH Section B.3 (vintage to 31. 3. 2016)"

    @api.model
    def _populate_for_statement(self, statement, section_code):
        grand_base, grand_tax, by_supplier = self._cssk_b3_totals(statement)
        if not by_supplier:
            return self.browse()
        moves = set().union(*(s["moves"] for s in by_supplier.values()))
        lines = self.env["account.move.line"].union(
            *(s["lines"] for s in by_supplier.values()))
        return self.create(
            [
                {
                    "statement_id": statement.id,
                    "total_tax_base": grand_base,
                    "total_tax_amount": grand_tax,
                    "total_deducted_amount": self._cssk_b3_deducted(by_supplier),
                    "row_count": len(moves),
                    # An aggregate names no document, so the documents behind
                    # it are only reachable from here — the one way to check
                    # which receipts a B.3.1 total is made of.
                    "source_move_line_ids": [(6, 0, lines.ids)],
                }
            ]
        )


class L10nSKKvDphSectionB31(models.Model):
    """B.3.1 — single aggregate of simplified invoices below the threshold."""

    _name = "l10n.sk.kv.dph.section.b31"
    _inherit = "l10n.sk.kv.dph.b3.mixin"
    _description = "KV DPH Section B.3.1"

    @api.model
    def _populate_for_statement(self, statement, section_code):
        grand_base, grand_tax, by_supplier = self._cssk_b3_totals(statement)
        if not by_supplier or grand_tax >= statement.version_id.threshold_value:
            return self.browse()  # at/above threshold → B.3.2
        moves = set().union(*(s["moves"] for s in by_supplier.values()))
        lines = self.env["account.move.line"].union(
            *(s["lines"] for s in by_supplier.values()))
        return self.create(
            [
                {
                    "statement_id": statement.id,
                    "total_tax_base": grand_base,
                    "total_tax_amount": grand_tax,
                    "total_deducted_amount": self._cssk_b3_deducted(by_supplier),
                    "row_count": len(moves),
                    # An aggregate names no document, so the documents behind
                    # it are only reachable from here — the one way to check
                    # which receipts a B.3.1 total is made of.
                    "source_move_line_ids": [(6, 0, lines.ids)],
                }
            ]
        )


class L10nSKKvDphSectionB32(models.Model):
    """B.3.2 — per-supplier breakdown of simplified invoices at/above the
    threshold."""

    _name = "l10n.sk.kv.dph.section.b32"
    _inherit = "l10n.sk.kv.dph.b3.mixin"
    _description = "KV DPH Section B.3.2"

    @api.model
    def _populate_for_statement(self, statement, section_code):
        grand_base, grand_tax, by_supplier = self._cssk_b3_totals(statement)
        if grand_tax < statement.version_id.threshold_value:
            return self.browse()  # below threshold → B.3.1
        return self.create(
            [
                {
                    "statement_id": statement.id,
                    "partner_id": sup["partner"].id,
                    "partner_vat": sup["partner"].vat or "",
                    "total_tax_base": sup["base"],
                    "total_tax_amount": sup["tax"],
                    "total_deducted_amount": self._cssk_sup_deducted(sup),
                    "row_count": len(sup["moves"]),
                    "source_move_line_ids": [(6, 0, sup["lines"].ids)],
                }
                for sup in by_supplier.values()
            ]
        )


# ----------------------------------------------------------------------
# D.1 — e-kasa / cash-register supplies (single aggregate)
# ----------------------------------------------------------------------
class L10nSKKvDphSectionD1(models.Model):
    """D.1 — supplies recorded via e-kasa.

    This data originates from the registered-sales (e-kasa) system, not from
    ``account.move.line``; it is normally imported. Implemented as an aggregate
    over any moves explicitly tagged ``D.1`` (inert by default — the resolver
    never assigns D.1).
    """

    _name = "l10n.sk.kv.dph.section.d1"
    _inherit = "cssk.control.statement.summary.mixin"
    _description = "KV DPH Section D.1"

    @api.model
    def _populate_for_statement(self, statement, section_code):
        grand_base = grand_tax = 0.0
        moves = set()
        lines = self._eligible_move_lines(statement, section_code)
        for line in lines:
            base, tax = line._cssk_base_and_tax_amounts()
            grand_base += base
            grand_tax += tax
            moves.add(line.move_id.id)
        if not moves:
            return self.browse()
        return self.create(
            [
                {
                    "statement_id": statement.id,
                    "total_tax_base": grand_base,
                    "total_tax_amount": grand_tax,
                    "row_count": len(moves),
                    "source_move_line_ids": [(6, 0, lines.ids)],
                }
            ]
        )


# ----------------------------------------------------------------------
# D.2 — other taxable supplies, split by basic vs reduced rate
# ----------------------------------------------------------------------
class L10nSKKvDphSectionD2(models.Model):
    """D.2 — other taxable supplies, base and tax split by rate band.

    Fed by the resolver: a domestic taxable supply to a customer with neither
    an IČ DPH nor an IČO (see ``_cssk_customer_is_taxable_person``), or a line
    tagged 'D.2' by journal override. Rate banding: >= 20 % counts as the
    basic rate, below as reduced — covers both the legacy 20 % and the 2025
    23 % basic rates.
    """

    _name = "l10n.sk.kv.dph.section.d2"
    _inherit = "cssk.control.statement.summary.mixin"
    _description = "KV DPH Section D.2"

    tax_base_basic = fields.Monetary(currency_field="company_currency_id")
    tax_amount_basic = fields.Monetary(currency_field="company_currency_id")
    tax_base_lower = fields.Monetary(currency_field="company_currency_id")
    tax_amount_lower = fields.Monetary(currency_field="company_currency_id")
    # snapshot the rate-banded columns too, so a dodatočný-KV storno reproduces them
    _KV_SNAPSHOT_FIELDS = [
        "partner_id", "partner_vat", "total_tax_base", "total_tax_amount",
        "total_deducted_amount", "row_count",
        "tax_base_basic", "tax_amount_basic", "tax_base_lower", "tax_amount_lower"]

    @api.model
    def _populate_for_statement(self, statement, section_code):
        basic_base = basic_tax = lower_base = lower_tax = 0.0
        found = False
        lines = self._eligible_move_lines(statement, section_code)
        for line in lines:
            base, tax = line._cssk_base_and_tax_amounts()
            found = True
            if line._cssk_tax_rate() >= 20.0:
                basic_base += base
                basic_tax += tax
            else:
                lower_base += base
                lower_tax += tax
        if not found:
            return self.browse()
        return self.create(
            [
                {
                    "statement_id": statement.id,
                    "tax_base_basic": basic_base,
                    "tax_amount_basic": basic_tax,
                    "tax_base_lower": lower_base,
                    "tax_amount_lower": lower_tax,
                    "total_tax_base": basic_base + lower_base,
                    "total_tax_amount": basic_tax + lower_tax,
                    "row_count": len(lines.move_id),
                    "source_move_line_ids": [(6, 0, lines.ids)],
                }
            ]
        )
