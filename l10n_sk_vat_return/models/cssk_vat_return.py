# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""SK DPH return kontrolné pravidlá (content checks beyond the XSD).

Source of truth: the official DPHv25 eForm itself (FS SR,
``pfseform.financnasprava.sk/Formulare/eFormVzor/DP/form.616.html``), whose
embedded ``vypocet_rNN`` functions compute each daň row as
``round(základ × sadzba, 2)`` — pinning the EXACT rate per riadok-pair:
19 % (§ 27 ods. 2), 5 % (§ 27 ods. 3) and 23 % (základná, § 27 ods. 1). The
poučenie gives the same pairing in prose; the eForm resolves the ods. 2 vs
ods. 3 split numerically (e.g. ``vypocet_r02 = round(r01 × 0.19)``,
``vypocet_r02a = round(r01a × 0.05)``, ``vypocet_r04 = round(r03 × 0.23)``).

The XSD validates data types only, not this content relation, so a base/tax
tagged into the wrong rate band is XSD-valid but wrong; this kontrola catches
it. (The DPH eForm itself recomputes daň from základ, so it would silently
overwrite a wrong figure; we instead flag the inconsistency in our tag-derived
values.)

The base/tax rate PAIRING is version DATA (``rate_pairs`` on the version
record, seeded in ``data/cssk_vat_return_version_data.xml``), not code: the
pairing follows the form vintage (DPHv25 uses 19/5/23; the 2024 form 10/20).
Likewise the settlement / amendment line codes (r32 / r33 / r36) come from
the version's ``own_tax_line_code`` / ``excess_line_code`` /
``diff_line_code``.
"""
from odoo import models


class CSSKVatReturn(models.Model):
    _inherit = "cssk.vat.return"

    def _kontroly_rules(self):
        rules = super()._kontroly_rules()
        if self.country_id.code != "SK":
            return rules
        version = self.version_id
        # daň = základ × sadzba pairing, from version DATA (rate_pairs)
        for pair in (version.rate_pairs or []):
            base, tax, rate = pair
            rates = rate if isinstance(rate, (list, tuple)) else [rate]
            rules.append({"type": "rate", "base": base, "tax": tax,
                          "rates": [float(r) for r in rates]})
        own_code = version.own_tax_line_code
        excess_code = version.excess_line_code
        # vlastná daňová povinnosť a nadmerný odpočet sú nezáporné a navzájom
        # sa vylučujú (§ 78 / § 79 zákona o DPH).
        if own_code:
            rules.append({"type": "nonneg", "code": own_code})
            # r35 = r32 − r34 musí byť ≥ 0, t. j. odpočítaný nadmerný odpočet
            # (r34) nesmie byť vyšší ako vlastná daňová povinnosť — DPHv25
            # poučenie bod 49.
            rules.append({"type": "le", "a": "r34", "b": own_code})
        if excess_code:
            rules.append({"type": "nonneg", "code": excess_code})
        if own_code and excess_code:
            rules.append({"type": "exclusive", "a": own_code, "b": excess_code})
        return rules

    def action_compute_lines(self):
        res = super().action_compute_lines()
        if self.original_return_id and self.country_id.code == "SK":
            self._fill_dodatocne_diff()
        return res

    def _fill_dodatocne_diff(self):
        """Dodatočné priznanie: the difference row (DPHv25 r36, from the
        version's ``diff_line_code``) = "Rozdiel oproti poslednej známej
        dani" = (táto čistá daň) − (čistá daň pôvodného priznania), kde čistá
        daň = own_tax − excess (r32 − r33 on DPHv25). Pulled from
        ``original_return_id`` so the accountant doesn't re-key it; skipped
        if the row was manually overridden or the version declares no
        settlement/difference codes."""
        self.ensure_one()
        version = self.version_id
        own_code = version.own_tax_line_code
        excess_code = version.excess_line_code
        diff_code = version.diff_line_code
        if not (own_code and excess_code and diff_code):
            return
        orig = {l.code: l.value for l in self.original_return_id.line_ids}
        cur = {l.code: l.value for l in self.line_ids}
        diff = ((cur.get(own_code, 0.0) - cur.get(excess_code, 0.0))
                - (orig.get(own_code, 0.0) - orig.get(excess_code, 0.0)))
        row = self.line_ids.filtered(lambda l: l.code == diff_code)
        if row and not row.is_overridden:
            row.value = diff

    # ------------------------------------------------------------------
    # § 69 ods. 3 — the split the pre-2021 vzory need and no tag can make
    # ------------------------------------------------------------------
    def _cssk_tag_line_filter(self, key, lines):
        """Separate § 69 ods. 3 from § 69 ods. 2 a 9 až 12.

        The vzory in force 2012-2020 put "služba, pri ktorej príjemca platí
        daň podľa § 69 ods. 3" on r11/r12, apart from § 69 ods. 2 a 9 až 12 on
        r09/r10. The 2021 vzor merged them, so ``l10n_sk`` has ONE
        reverse-charge family carrying tags 09/10 and the tag cannot say which
        paragraph a line is.

        What the paragraph actually turns on is WHO SUPPLIED: § 69 ods. 3 is a
        service from a person not established in Slovakia. So that is what is
        read, per line, from the supplier — no configuration, and right for the
        shared taxes. ``l10n_sk_dph_69_par`` overrides it on a tax a company
        uses for one paragraph only, which the country test would misread: a
        dedicated domestic-construction prenos tax (§ 69 ods. 12) whoever the
        supplier is, or a § 69 ods. 2 goods-with-installation tax, whose
        supplier IS foreign but whose row is r09/r10.

        Deliberately NOT defaulted to "all of it is § 69 ods. 3": that would
        move every domestic construction reverse charge onto r11/r12, which is
        the error the split exists to prevent.
        """
        if key not in ("69_3", "not_69_3"):
            return super()._cssk_tag_line_filter(key, lines)

        sk = self.env.ref("base.sk")

        def is_69_3(line):
            marker = "auto"
            taxes = line.tax_line_id or line.tax_ids
            markers = {t.l10n_sk_dph_69_par or "auto" for t in taxes}
            # One line, one answer: a mix is not decidable and falls back to
            # the supplier, which is the rule the taxes themselves default to.
            if len(markers) == 1:
                marker = markers.pop()
            if marker == "69_3":
                return True
            if marker == "69_other":
                return False
            partner = line.move_id.partner_id
            country = partner.commercial_partner_id.country_id or partner.country_id
            # No country recorded is not evidence of a foreign supplier. Treat
            # it as domestic so an unmaintained partner cannot move an amount
            # onto r11/r12 unnoticed; the unfiled-row kontrola is what asks
            # about it.
            return bool(country) and country != sk

        want = key == "69_3"
        return lines.filtered(lambda line: is_69_3(line) == want)
