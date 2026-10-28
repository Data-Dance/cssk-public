# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

CZ_DOC_THRESHOLD = 10000.0  # CZK fallback; the version record is authoritative

# The second reduced rate (10 %) existed from 1. 1. 2015 to 31. 12. 2023. The
# KH reports it apart, in zakl_dane3/dan3: "Vyplní se v případě plnění s DPPD
# do 31. 12. 2023, a to základ daně pro druhou sníženou sazbu DPH platnou do
# 31. 12. 2023, a také v případě opravy základu daně a výše daně" (DPHKH1
# structure, VetaA2/A4/A5/B1/B2/B3). The rate identifies it on its own: no
# other Czech rate has been 10 %, and a 10 % line dated 2024 or later can only
# be a correction of such a supply, which the same sentence sends to
# zakl_dane3 as well. The 15 % first reduced rate of the same years, and its
# corrections, stay in zakl_dane2 next to today's 12 %.
CZ_SECOND_REDUCED_RATE = 10.0


class L10nCzKhRowMixin(models.AbstractModel):
    """Per-document KH row.

    Inherits the base ``cssk.control.statement.section.mixin`` (statement
    link, partner snapshot, drill-down audit trail — source lines +
    reconcile check + audit view) and adds only what is CZ-specific: the
    standard/reduced rate split the DPHKH1 Veta attributes expect
    (zakl_dane1/dan1 = standard, zakl_dane2/dan2 = reduced), the §92a kód
    předmětu plnění and the aggregate row count.

    NB: the inherited ``kod_opravy`` / ``_kv_snapshot`` machinery exists for
    the SK dodatočný-KV delta flow only. The CZ KH types are B/O/E and the
    následné hlášení (E) is a FULL restatement, never a kód-opravy delta —
    the machinery is kept inert for CZ by the explicit ``_is_dodatocny``
    guard in ``cz_kh_statement.py`` (not by data accident).
    """

    _name = "l10n.cz.kh.row.mixin"
    _inherit = "cssk.control.statement.section.mixin"
    _description = "CZ KH Row (mixin)"

    base_std = fields.Monetary(currency_field="company_currency_id")
    tax_std = fields.Monetary(currency_field="company_currency_id")
    base_red = fields.Monetary(currency_field="company_currency_id")
    tax_red = fields.Monetary(currency_field="company_currency_id")
    base_red3 = fields.Monetary(
        string="Base 2nd Reduced (to 2023)",
        currency_field="company_currency_id",
        help="zakl_dane3 — base at the second reduced rate (10 %) in force "
        "until 31. 12. 2023, and corrections of such supplies.")
    tax_red3 = fields.Monetary(
        string="Tax 2nd Reduced (to 2023)",
        currency_field="company_currency_id",
        help="dan3 — VAT at the second reduced rate (10 %) in force until "
        "31. 12. 2023, and corrections of such supplies.")
    supplies_code = fields.Char()
    row_count = fields.Integer(default=1)

    # --- manual override ---------------------------------------------------
    # The DPHDP3/DPHKH1 rows are filed from the rate split, not from the base
    # mixin's single tax_base_amount / tax_amount pair, so THOSE are what an
    # override must snapshot and re-apply. Overriding the inherited pair
    # changed two columns no export reads: a corrected row filed its computed
    # figures.
    _KV_OVERRIDE_FIELDS = (
        "base_std", "tax_std", "base_red", "tax_red", "base_red3", "tax_red3")

    def _kv_override_key(self):
        # A.1 / B.1 split one document into one row per § 92a code (see
        # ``_cz_move_buckets``), so the code is part of what makes an override
        # row-specific; elsewhere it is empty and changes nothing.
        self.ensure_one()
        return super()._kv_override_key() + (self.supplies_code or "",)

    def _drill_expected_amounts(self):
        """CZ rows carry the standard/reduced split instead of the base
        mixin's single tax_base_amount/tax_amount pair — the source lines
        must sum to the split's totals."""
        self.ensure_one()
        return (self.base_std + self.base_red + self.base_red3,
                self.tax_std + self.tax_red + self.tax_red3)

    # ------------------------------------------------------------------
    @api.model
    def _cz_move_buckets(self, statement, code):
        """{key: {move, base_std, tax_std, base_red, tax_red, base_red3,
        tax_red3, supplies_code, line, lines}} for code.

        The key is the move, except in A.1 / B.1, where it is (move, §92a
        code): "Pokud bude na jednom daňovém dokladu uvedeno více druhů plnění
        (spadajících pod různé kódy), je nutno rozepsat každý kód plnění na
        samostatný řádek (s uvedením stejného evidenčního čísla daňového
        dokladu)" (DPHKH1, kod_pred_pl). Taking the first code of the document
        filed the second kind of supply under the wrong code.
        """
        # Period selection goes through the shared helper, not a raw date
        # range: a control statement reconciles against the VAT return, so the
        # two must agree on what the period contains — output by tax point,
        # input by the period the deduction is claimed in.
        move_ids = statement._cssk_period_move_ids(
            statement.company_id, statement.date_from, statement.date_to
        )
        if not move_ids:
            return {}
        lines = self.env["account.move.line"].search([
            ("parent_state", "=", "posted"),
            ("company_id", "=", statement.company_id.id),
            ("move_id", "in", move_ids),
            ("cssk_control_section_code", "=", code),
        ])
        buckets = {}
        for line in lines:
            base, tax = line._cssk_base_and_tax_amounts()
            if not self._cz_line_bears_tax(code, tax):
                continue
            rate = line._cssk_tax_rate()
            supplies_code = ""
            key = line.move_id
            if code in ("A1", "B1"):
                supplies_code = line._cz_kh_commodity_code()
                key = (line.move_id, supplies_code)
            b = buckets.get(key)
            if b is None:
                b = buckets[key] = {
                    "move": line.move_id, "supplies_code": supplies_code,
                    "base_std": 0.0, "tax_std": 0.0, "base_red": 0.0,
                    "tax_red": 0.0, "base_red3": 0.0, "tax_red3": 0.0,
                    "line": line, "lines": self.env["account.move.line"],
                }
            b["lines"] |= line
            if code == "A1" or rate >= 20:
                # A.1 has one base "bez rozlišení sazby daně": the supplier
                # charges no VAT, so the stock 0 % RC sale tax must not send
                # the base to a reduced-rate column the row does not have.
                b["base_std"] += base
                b["tax_std"] += tax
            elif abs(rate - CZ_SECOND_REDUCED_RATE) < 0.005:
                b["base_red3"] += base
                b["tax_red3"] += tax
            else:
                b["base_red"] += base
                b["tax_red"] += tax
        return buckets

    @api.model
    def _cz_is_detailed(self, bucket, threshold):
        """Whether a document is reported in its own right or only in the total.

        Two conditions, not one. The obvious one is value: strictly **over**
        10 000 including tax, by magnitude, so a −50 000 credit note is a detail
        row and an exactly-10 000 document is not.

        The one that is easy to miss is the counterparty. A4 and B2 identify the
        other party by their DIČ; a supply to somebody who has none — a private
        individual, a non-payer — cannot be reported that way and belongs in the
        aggregate **whatever it is worth**.

        The evidence is one-directional, which is what gives it away. Across 59
        filed control statements every disagreement about the split went the same
        way: 12 documents the company filed in A5 and 11 in B3 were reported here
        as A4 and B2, and none the other way. Of those 23, 13 carry no
        counterparty VAT — against 0.7 % of the 4 212 documents whose section we
        agree on. Sorting by value alone cannot produce a one-way error.

        ⚠️ The counterparty condition is applied to the SUPPLY side only, and
        that asymmetry is measured rather than assumed. Requiring a DIČ on the
        purchase side too moved B2 from 26 periods agreeing to 17 and B3 from 32
        to 18, while A4 went 35 → 41 and A5 25 → 30. The reason is that the two
        absences mean different things: a customer may genuinely have no DIČ,
        because you can sell to anybody, whereas a purchase carrying a right to
        deduct implies a registered supplier — so a supplier with no VAT number
        in the imported data is a gap in OUR data, not a fact about the
        transaction, and treating it as one buries good detail rows in the
        aggregate.
        """
        line = bucket.get("line")
        # A bad-debt correction (§ 46 / § 74b, old § 44) is reported on its
        # own row with zdph_44 set, whatever it is worth: an aggregate row has
        # no zdph_44 to carry the flag. The DIČ condition still holds, A.4
        # cannot identify a customer who has none.
        if not (line and line.move_id.l10n_cz_bad_debt):
            if abs(self._cz_doc_total(bucket)) <= threshold:
                return False
        if self._cz_code != "A4":
            return True
        # A Czech DIČ, not merely some VAT number: a customer known only by
        # another member state's number cannot be identified in A.4 either.
        return bool(line and line._cz_kh_has_cz_dic())

    @api.model
    def _cz_line_bears_tax(self, code, tax):
        """Whether a line belongs in a section that reports taxable supplies.

        A4/A5 and B2/B3 report *zdanitelná plnění* — taxable supplies, and on
        the input side ones carrying a right to deduct. A line with no VAT on
        it is neither, and the company files none: of 52 documents made
        entirely of such lines, 50 appear in no section of any filing.

        It matters WITHIN a document as well as for whole ones. A sales invoice
        carrying a taxed line and an exempt one is filed for its taxable part
        alone: seven documents of one agenda reported a base of 67 476 against
        a filed 10 476, the 57 000 difference being an untaxed line — and the
        TAX agreed to the cent on both sides, which is what gives the shape
        away.

        Deliberately NOT applied to A1/B1. A §92a domestic reverse charge
        carries no VAT by design, because the recipient self-assesses, so every
        line there is untaxed and the section is correct as it stands.
        """
        if code not in ("A4", "B2"):
            return True
        return abs(tax) >= 0.005

    @api.model
    def _cz_doc_total(self, b):
        """The value the 10 000 threshold is measured against.

        The DOCUMENT's total including tax, not the taxable part of it. The
        limit is a property of the doklad — "celková částka za plnění včetně
        daně" — so an exempt or zero-rated line still counts towards it even
        though it is reported nowhere.

        The two only differ on a MIXED document, and summing the bucket instead
        got those wrong in one direction: a document whose taxable part is
        under the limit but whose total is over was filed as an aggregate
        instead of as a detail row. FV925039 is the clean example — 19 000
        exempt plus 3 492 at 21 % — where the taxable part is 4 225.32 and the
        document is 23 225.32. The accountant filed it in A4 as a detail row
        reporting the 3 492.00, which is the shape this produces: the threshold
        reads the whole document, the reported figures stay the taxable part.

        Note the reported amounts are deliberately NOT changed by this — the
        exempt line stays out of base_std/base_red, which is separately
        evidenced (see ``_cz_line_bears_tax``). Only the SPLIT moves.

        Measured on 19CE-IMPORT-SPIKE: 5 documents of 6 625 change side, all
        aggregate → detail, and two of them are the documents that account for
        the 2025-12 A5 and part of the 2025-04 B3 aggregate differences found
        by comparing against the filed statements.

        Never smaller than the part actually being reported, and that is
        enforced rather than assumed. Falling back only when ``amount_total``
        is zero left the case where it is merely SMALL: a move that nets
        opposite-signed lines can total a few crowns while the part reported in
        this section is large, and preferring it would demote a document that
        belongs in the detail section. Taking the larger magnitude keeps the
        threshold reading the whole document without ever contradicting the
        figures the row itself carries. (Raised by a Copilot review of the
        first version, which took the fallback literally — the docstring
        claimed this property before the code had it.)
        """
        bucket_total = (b["base_std"] + b["tax_std"] + b["base_red"]
                        + b["tax_red"] + b["base_red3"] + b["tax_red3"])
        line = b.get("line")
        doc_total = line.move_id.amount_total if line else 0.0
        return doc_total if abs(doc_total) >= abs(bucket_total) else bucket_total

    @api.model
    def _cz_kh_threshold(self, statement):
        """Per-document A4/A5 (B2/B3) split threshold in CZK — read from the
        statement's version record, falling back to the legal constant."""
        return statement.version_id.threshold_value or CZ_DOC_THRESHOLD

    # Received-document sections: DPHKH1 c_evid_dd must carry the SUPPLIER's
    # evidence number (move.ref), not our internal name. A2 is included: the
    # "document" of an EU acquisition is the supplier's invoice.
    _CZ_INBOUND_CODES = ("A2", "B1", "B2")

    @api.model
    def _cz_kh_vies_country(self, line, move):
        """k_stat of A.2: the code of the member state that issued the
        supplier's VAT number, as the structure's own table lists it — ŘECKO
        **EL**, SEVERNÍ IRSKO **XI** — not the ISO code of the partner's
        country (GR, GB). Read off the VAT prefix when there is one.

        Empty for a supplier from outside the EU (a third-country service in
        A.2): "V případě, že dodavatel nemá VAT ID … pole Identifikace
        dodavatele zůstává prázdné" (Metodická informace k vyplnění KH).
        """
        vat = "".join(line._cssk_partner_vat_for_statement().split()).upper()
        if len(vat) > 2 and vat[:2].isalpha():
            code = vat[:2]
        else:
            code = (move.partner_id.commercial_partner_id.country_id.code
                    or "")[:2]
        code = "EL" if code == "GR" else code
        eu = self.env.ref("base.europe", raise_if_not_found=False)
        vies = {"EL" if c == "GR" else c
                for c in (eu.country_ids.mapped("code") if eu else [])}
        vies.add("XI")
        return code if code in vies else ""

    @api.model
    def _cz_row_vals(self, statement, move, b):
        line = b["line"]
        if self._cz_code in self._CZ_INBOUND_CODES:
            entry_ref = move.ref or move.name
        else:
            entry_ref = move.name
        vals = {
            "statement_id": statement.id,
            "move_line_id": line.id,
            "partner_id": move.partner_id.id,
            "partner_vat": line._cssk_partner_vat_for_statement(),
            # DPHKH1 dic_odb/dic_dod want the DIČ without the country prefix
            "partner_vat_stripped": line._cssk_partner_vat_stripped(),
            "partner_country_code": self._cz_kh_vies_country(line, move),
            "entry_ref": entry_ref,
            # DUZP/DPPD: the move's taxable supply date when set (advances:
            # the payment date), else the invoice date.
            "supply_date": move.taxable_supply_date
            or move.invoice_date
            or move.date,
            "base_std": b["base_std"], "tax_std": b["tax_std"],
            "base_red": b["base_red"], "tax_red": b["tax_red"],
            "base_red3": b["base_red3"], "tax_red3": b["tax_red3"],
            "source_move_line_ids": [(6, 0, b["lines"].ids)],
        }
        # §92a kód předmětu plnění is mandatory in A.1 / B.1 only.
        if self._cz_code in ("A1", "B1"):
            vals["supplies_code"] = b["supplies_code"]
        return vals


# --- detail sections (no threshold) -----------------------------------------
class _CzKhDetailAll(models.AbstractModel):
    _name = "l10n.cz.kh.detail.all"
    _inherit = "l10n.cz.kh.row.mixin"
    _description = "CZ KH detail (all rows of a code)"
    _cz_code = None

    @api.model
    def _populate_for_statement(self, statement, section_code):
        buckets = self._cz_move_buckets(statement, self._cz_code)
        return self.create([
            self._cz_row_vals(statement, b["move"], b)
            for b in buckets.values()
        ])


class L10nCzKhA1(models.Model):
    _name = "l10n.cz.kh.a1"
    _inherit = "l10n.cz.kh.detail.all"
    _description = "KH A1 — domestic reverse-charge supplied"
    _cz_code = "A1"


class L10nCzKhA2(models.Model):
    _name = "l10n.cz.kh.a2"
    _inherit = "l10n.cz.kh.detail.all"
    _description = "KH A2 — acquisition from EU"
    _cz_code = "A2"


class L10nCzKhB1(models.Model):
    _name = "l10n.cz.kh.b1"
    _inherit = "l10n.cz.kh.detail.all"
    _description = "KH B1 — domestic reverse-charge received"
    _cz_code = "B1"


# --- threshold-split sections (A4/A5 output, B2/B3 input) --------------------

class _CzKhDetailAbove(models.AbstractModel):
    _name = "l10n.cz.kh.detail.above"
    _inherit = "l10n.cz.kh.row.mixin"
    _description = "CZ KH detail rows above the per-doc threshold"
    _cz_code = None

    @api.model
    def _populate_for_statement(self, statement, section_code):
        buckets = self._cz_move_buckets(statement, self._cz_code)
        threshold = self._cz_kh_threshold(statement)
        # abs(): the split is by document MAGNITUDE — a −50 000 credit note is
        # a detail row (A4/B2), not part of the ≤10k aggregate.
        return self.create([
            self._cz_row_vals(statement, b["move"], b)
            for b in buckets.values()
            if self._cz_is_detailed(b, threshold)
        ])


class _CzKhSummaryBelow(models.AbstractModel):
    _name = "l10n.cz.kh.summary.below"
    _inherit = "l10n.cz.kh.row.mixin"
    _description = "CZ KH single aggregate of docs at/below the threshold"
    _cz_code = None

    @api.model
    def _populate_for_statement(self, statement, section_code):
        buckets = self._cz_move_buckets(statement, self._cz_code)
        threshold = self._cz_kh_threshold(statement)
        below = [b for b in buckets.values()
                 if not self._cz_is_detailed(b, threshold)]
        if not below:
            return self.browse()
        # The aggregate keeps the ≤10k documents' move lines as its source,
        # so the drill-down + reconcile check are meaningful on A5/B3 too
        # (they used to stay empty, permanently failing the check).
        source_lines = self.env["account.move.line"]
        for b in below:
            source_lines |= b["lines"]
        return self.create([{
            "statement_id": statement.id,
            "base_std": sum(b["base_std"] for b in below),
            "tax_std": sum(b["tax_std"] for b in below),
            "base_red": sum(b["base_red"] for b in below),
            "tax_red": sum(b["tax_red"] for b in below),
            "base_red3": sum(b["base_red3"] for b in below),
            "tax_red3": sum(b["tax_red3"] for b in below),
            "row_count": len(below),
            "source_move_line_ids": [(6, 0, source_lines.ids)],
        }])


class L10nCzKhA4(models.Model):
    _name = "l10n.cz.kh.a4"
    _inherit = "l10n.cz.kh.detail.above"
    _description = "KH A4 — taxable supplies over 10 000 CZK"
    _cz_code = "A4"


class L10nCzKhA5(models.Model):
    _name = "l10n.cz.kh.a5"
    _inherit = "l10n.cz.kh.summary.below"
    _description = "KH A5 — taxable supplies up to 10 000 CZK (aggregate)"
    _cz_code = "A4"


class L10nCzKhB2(models.Model):
    _name = "l10n.cz.kh.b2"
    _inherit = "l10n.cz.kh.detail.above"
    _description = "KH B2 — received supplies over 10 000 CZK"
    _cz_code = "B2"


class L10nCzKhB3(models.Model):
    _name = "l10n.cz.kh.b3"
    _inherit = "l10n.cz.kh.summary.below"
    _description = "KH B3 — received supplies up to 10 000 CZK (aggregate)"
    _cz_code = "B2"
