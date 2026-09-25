# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError

# Master-data preflight scope — derived from the OFFICIAL dphkh1_epo2.xsd +
# the QWeb template (report/l10n_cz_kh_templates.xml):
#   * DIČ protistrany: dic_odb/dic_dod is an XSD-REQUIRED attribute of
#     VetaA1/VetaA4/VetaB1/VetaB2. VetaA2's vatid_dod is XSD-optional (an EU
#     supplier without a VAT ID is legitimate), and the A5/B3 aggregates carry
#     no counterparty at all — both exempt.
#   * DUZP/DPPD (supply date): XSD-REQUIRED on all per-document rows
#     (A1 duzp, A2/A4 dppd, B1 duzp, B2 dppd); the template renders '' for a
#     missing date, which fails XSD validation with a cryptic type error.
_KH_VAT_SECTIONS = ("A1", "A4", "B1", "B2")
_KH_DATE_SECTIONS = ("A1", "A2", "A4", "B1", "B2")


class CSSKControlStatement(models.Model):
    _inherit = "cssk.control.statement"

    cz_a1_ids = fields.One2many("l10n.cz.kh.a1", "statement_id")
    cz_a2_ids = fields.One2many("l10n.cz.kh.a2", "statement_id")
    cz_a4_ids = fields.One2many("l10n.cz.kh.a4", "statement_id")
    cz_a5_ids = fields.One2many("l10n.cz.kh.a5", "statement_id")
    cz_b1_ids = fields.One2many("l10n.cz.kh.b1", "statement_id")
    cz_b2_ids = fields.One2many("l10n.cz.kh.b2", "statement_id")
    cz_b3_ids = fields.One2many("l10n.cz.kh.b3", "statement_id")

    def _collect_sections_by_code(self):
        self.ensure_one()
        if self.country_id.code == "CZ":
            return {
                "A1": self.cz_a1_ids, "A2": self.cz_a2_ids,
                "A4": self.cz_a4_ids, "A5": self.cz_a5_ids,
                "B1": self.cz_b1_ids, "B2": self.cz_b2_ids,
                "B3": self.cz_b3_ids,
            }
        return super()._collect_sections_by_code()

    def _is_dodatocny(self):
        """Explicit guard: the SK dodatočný-KV delta machinery (kod_opravy,
        _kv_snapshot, _apply_dodatocny_delta) must NEVER run for CZ.

        The CZ KH rows inherit those fields from the base section mixin, but
        the CZ amendment types are B (řádné) / O (opravné) / E (následné) and
        the následné hlášení is a FULL restatement of the period — Czech law
        has no kód-opravy delta filing. Today no CZ type carries the SK
        fa_xml_value 'D', but that is a data accident; guard by country so a
        future/custom CZ type can never trigger the SK flow.
        """
        self.ensure_one()
        if self.country_id.code == "CZ":
            return False
        return super()._is_dodatocny()

    # ------------------------------------------------------------------
    # Master-data preflight (fail early with the offending document numbers,
    # instead of a cryptic XSD error)
    # ------------------------------------------------------------------
    @staticmethod
    def _kh_offenders_detail(rows):
        labels = [
            r.entry_ref or r.move_id.name or ("#%d" % r.id) for r in rows]
        detail = ", ".join(labels[:5])
        if len(labels) > 5:
            detail += ", … (+%d)" % (len(labels) - 5)
        return detail

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.country_id.code != "CZ":
                continue
            problems = []
            sections = rec._collect_sections_by_code()
            for code in _KH_VAT_SECTIONS:
                # partner_vat_stripped is what the template renders as
                # dic_odb/dic_dod — guard exactly what the XSD will see.
                bad = [r for r in sections.get(code, [])
                       if not r.partner_vat_stripped]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) without the counterparty's DIČ "
                        "— set the VAT number on the partner (Contacts → "
                        "partner → Tax ID): %(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kh_offenders_detail(bad)))
            for code in _KH_DATE_SECTIONS:
                bad = [r for r in sections.get(code, []) if not r.supply_date]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) without the taxable-supply "
                        "date (DUZP/DPPD) — set the invoice date on the "
                        "document: %(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kh_offenders_detail(bad)))
            if problems:
                raise UserError(_(
                    "The kontrolní hlášení cannot be exported — the official "
                    "DPHKH1 form requires data that is missing:\n%s")
                    % "\n".join("  • %s" % p for p in problems))
        return res
