import re

from odoo import _, fields, models
from odoo.exceptions import UserError

# Master-data preflight scope — derived from the OFFICIAL kv_dph_2025.xsd +
# the QWeb template (report/l10n_sk_kv_dph_templates.xml):
#   * counterparty IČ DPH (Odb/Dod): REQUIRED by the form on A.2, B.2 and
#     B.3.2 only — verified attribute by attribute across all four vzory
#     (2014/2016/2023/2025), where it is `use="required"` on those three and
#     `use="optional"` on A.1, B.1, C.1 and C.2. The aggregates B.3.1/D.1/D.2
#     have no such attribute at all.
#
#     ⚠️ This used to be checked on EVERY detail section, on the reasoning that
#     a row without the counterparty's IČ DPH is a master-data gap. That
#     reasoning was wrong and the guard was stricter than the form it guards.
#     `IcDphType` is a union of IcDphSkType, IcDphClenskychStatovType and
#     IcDphTretichStranType — a third-country member exists precisely because a
#     counterparty may hold no EU VAT number, so a B.1 row without one is
#     ordinary rather than defective.
#
#     What the over-strictness nearly cost is the point: it blocked all 150
#     periods of one agenda, and the obvious way past it was to backfill the
#     98 partners it named. Of those 98 only 47 hold a real VAT number — 24
#     carry the literal "0", 26 a bare country code (US, MX, CN, ZA, CA, IL,
#     LT, UA), one the word "IRELAND". Backfilling would have written 51
#     INVENTED VAT numbers into a customer's partner master to satisfy a rule
#     the form does not impose, and every export would then have passed. A
#     guard stricter than its form does not fail safe: it pushes the person
#     past it into falsifying the data it was protecting.
#
#     It also HID the real cases. A.2/B.2/B.3.2 genuinely require the number,
#     and those rows could never be reached while B.1 refused first.
#   * Den (dátum dodania / prijatia platby): XSD-REQUIRED attribute of
#     A1/A2/B1/B2 — the template renders '' for a missing date, which fails
#     XSD validation with a cryptic type error; fail early and name the rows.
#: Sections whose counterparty IČ DPH the FORM requires. Narrower than the set
#: of sections that CARRY one — see the note above.
#:
#: These same three are also the DOMESTIC-ONLY sections, and it is one fact
#: rather than two: their attribute is typed `IcDphSkType` (`SK\d{10}`), while
#: A.1/B.1/C.1/C.2 take `IcDphType`, a union that admits member-state and
#: third-country numbers. A supply reported in A.2, B.2 or B.3.2 is by
#: construction one where the counterparty is registered in Slovakia — which
#: is why the number can be required there and not elsewhere.
_KV_VAT_REQUIRED_SECTIONS = ("A.2", "B.2", "B.3.2")
#: What `IcDphSkType` accepts, verbatim from the XSD.
_KV_SK_VAT_RE = re.compile(r"^SK\d{10}$")
#: Every detail section, i.e. those carrying a document reference. The 32-char
#: limit applies wherever a reference is emitted, whatever the VAT rule is.
_KV_DETAIL_SECTIONS = ("A.1", "A.2", "B.1", "B.2", "B.3.2", "C.1", "C.2")
_KV_DEN_SECTIONS = ("A.1", "A.2", "B.1", "B.2")


class CSSKControlStatement(models.Model):
    """Extend the shared statement with the SK section O2M fields and the
    SK section collector used by the XML template."""

    _inherit = "cssk.control.statement"

    sk_section_a1_ids = fields.One2many(
        "l10n.sk.kv.dph.section.a1", "statement_id"
    )
    sk_section_a2_ids = fields.One2many(
        "l10n.sk.kv.dph.section.a2", "statement_id"
    )
    sk_section_b1_ids = fields.One2many(
        "l10n.sk.kv.dph.section.b1", "statement_id"
    )
    sk_section_b2_ids = fields.One2many(
        "l10n.sk.kv.dph.section.b2", "statement_id"
    )
    sk_section_b31_ids = fields.One2many(
        "l10n.sk.kv.dph.section.b31", "statement_id"
    )
    sk_section_b32_ids = fields.One2many(
        "l10n.sk.kv.dph.section.b32", "statement_id"
    )
    sk_section_c1_ids = fields.One2many(
        "l10n.sk.kv.dph.section.c1", "statement_id"
    )
    sk_section_c2_ids = fields.One2many(
        "l10n.sk.kv.dph.section.c2", "statement_id"
    )
    sk_section_d1_ids = fields.One2many(
        "l10n.sk.kv.dph.section.d1", "statement_id"
    )
    sk_section_d2_ids = fields.One2many(
        "l10n.sk.kv.dph.section.d2", "statement_id"
    )

    def _collect_sections_by_code(self):
        self.ensure_one()
        if self.country_id.code == "SK":
            return {
                "A.1": self.sk_section_a1_ids,
                "A.2": self.sk_section_a2_ids,
                "B.1": self.sk_section_b1_ids,
                "B.2": self.sk_section_b2_ids,
                "B.3.1": self.sk_section_b31_ids,
                "B.3.2": self.sk_section_b32_ids,
                "C.1": self.sk_section_c1_ids,
                "C.2": self.sk_section_c2_ids,
                "D.1": self.sk_section_d1_ids,
                "D.2": self.sk_section_d2_ids,
            }
        return super()._collect_sections_by_code()

    # ------------------------------------------------------------------
    # Master-data preflight (fail early with the offending invoice numbers,
    # instead of a cryptic XSD error / a portal rejection)
    # ------------------------------------------------------------------
    @staticmethod
    def _kv_row_label(row):
        ref = getattr(row, "entry_ref", False)
        return ref or row.partner_id.display_name or ("#%d" % row.id)

    @staticmethod
    def _kv_offenders_detail(rows):
        labels = [CSSKControlStatement._kv_row_label(r) for r in rows]
        detail = ", ".join(labels[:5])
        if len(labels) > 5:
            detail += ", … (+%d)" % (len(labels) - 5)
        return detail

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            if rec.country_id.code != "SK":
                continue
            problems = []
            sections = rec._collect_sections_by_code()
            for code in _KV_VAT_REQUIRED_SECTIONS:
                rows = sections.get(code, [])
                bad = [r for r in rows if not r.partner_vat]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) without the counterparty's "
                        "IČ DPH — set the VAT number on the partner "
                        "(Contacts → partner → Tax ID): %(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kv_offenders_detail(bad)))
                # A FOREIGN number here is not a missing-data problem, it is a
                # classification one, and the form says so by TYPE rather than
                # by rule: these sections take IcDphSkType, so a supply from a
                # counterparty registered elsewhere cannot be reported in them
                # at all. Named here because the alternative is an XSD pattern
                # error — "value 'CZ27082440' is not accepted by the pattern
                # 'SK\d{10}'" against a line number — which says nothing about
                # which document or why.
                foreign = [
                    r for r in rows
                    if r.partner_vat
                    and not _KV_SK_VAT_RE.match(
                        re.sub(r"\s+", "", r.partner_vat.upper()))
                ]
                if foreign:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) whose counterparty IČ DPH is "
                        "not Slovak — this section reports domestic supplies "
                        "only (the form types it SK+10 digits), so the "
                        "document belongs in another section or the partner's "
                        "country/VAT disagree: %(refs)s",
                        sec=code, n=len(foreign),
                        refs=self._kv_offenders_detail(foreign)))
            # The document reference is typed \S{1,32} in both vzory. The
            # whitespace half is normalised at export — the form cannot carry a
            # space and a real accepted filing shows the tax office takes the
            # stripped form — but the LENGTH half cannot be fixed silently:
            # shortening a reference the FS cross-matches against the
            # supplier's own filing would break the match it exists for. So it
            # is named here, the way a missing IČ DPH is, rather than surfacing
            # as an XSD pattern error against a line number.
            for code in _KV_DETAIL_SECTIONS:
                bad = [
                    r for r in sections.get(code, [])
                    if r.entry_ref_xml and len(r.entry_ref_xml) > 32
                ]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) whose document reference is "
                        "longer than the 32 characters the form allows — "
                        "shorten it on the document; it is cross-matched "
                        "against the supplier's own filing, so it cannot be "
                        "truncated here: %(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kv_offenders_detail(bad)))
            for code in _KV_DEN_SECTIONS:
                bad = [r for r in sections.get(code, []) if not r.supply_date]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) without the supply date (Den) "
                        "— set the invoice/delivery date on the document: "
                        "%(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kv_offenders_detail(bad)))
            # C.1 / C.2 name the corrected invoice (FO), and the form requires
            # it. A credit note created by hand has no link to it, so without
            # the number typed on the document there is nothing true to file.
            # Kód opravy 1 re-files a row exactly as it was filed before (a
            # snapshot), and older filings put the credit note's own number in
            # FO when there was no link — so that row repeats it and is not
            # held to this. Kód 2 is a new or changed row and needs the real
            # original like any other. Checked on the value the XML carries,
            # whitespace stripped: a number of spaces is no number.
            for code in ("C.1", "C.2"):
                bad = [r for r in sections.get(code, [])
                       if not r.entry_ref_original_xml and r.kod_opravy != "1"]
                if bad:
                    problems.append(_(
                        "%(sec)s: %(n)d row(s) without the number of the "
                        "invoice being corrected — the credit note is not "
                        "linked to it; enter it on the credit note (Other Info "
                        "→ Original document number) and recompute: %(refs)s",
                        sec=code, n=len(bad),
                        refs=self._kv_offenders_detail(bad)))
            # A.2 goods under § 69 ods. 12 písm. f) to i): the form wants the
            # commodity code (f, g) and the quantity in kg / t / m / ks. Both
            # attributes are optional in the SCHEMA — which is how their
            # absence went unnoticed — and required by the poučenie for these
            # goods, so the schema cannot be the check.
            a2 = sections.get("A.2", [])
            bad = [r for r in a2 if r.rc_goods in ("f", "g") and not r.goods_code]
            if bad:
                problems.append(_(
                    "A.2: %(n)d row(s) of § 69 ods. 12 písm. f)/g) goods "
                    "without the 4-digit commodity code — set it on the "
                    "product (KV DPH commodity code, or its intrastat/HS "
                    "code): %(refs)s",
                    n=len(bad), refs=self._kv_offenders_detail(bad)))
            bad = [r for r in a2 if r.rc_goods and not r.uom_code]
            if bad:
                problems.append(_(
                    "A.2: %(n)d row(s) of § 69 ods. 12 goods whose unit "
                    "converts to none of kg, t, m, ks — the only units the "
                    "form accepts; invoice them in one of those: %(refs)s",
                    n=len(bad), refs=self._kv_offenders_detail(bad)))
            if problems:
                raise UserError(_(
                    "The kontrolný výkaz cannot be exported — the official "
                    "KVDPH form requires data that is missing:\n%s")
                    % "\n".join("  • %s" % p for p in problems))
        return res

    # ------------------------------------------------------------------
    # kontrolné pravidlá — SK-specific
    # ------------------------------------------------------------------
    def check_kontroly(self):
        """Add the D.2 data-quality check to the shared kontroly."""
        out = super().check_kontroly()
        out += self._kv_check_d2_looks_like_a_business()
        return out

    def _kv_check_d2_looks_like_a_business(self):
        """Warn where a D.2 supply's customer looks like a taxable person.

        D.2 is reached by having neither IČ DPH nor IČO, which is the best
        proxy we have for "not a zdaniteľná osoba" — and a proxy fails in one
        direction that nobody can see from the statement. Until
        ``l10n_cssk_core`` 7babaf6 core hid ``company_registry`` behind
        ``invisible="parent_id or not is_company"``, so on a CZ/SK partner
        stored as a natural person the IČO could not be entered at all. On any
        database predating that, an unregistered BUSINESS can carry an empty
        IČO, be read as a private individual, and have its supplies quietly
        aggregated into D.2 instead of itemised in A.1.

        That is invisible to the person filing: D.2 is a total, so the customer
        never appears. Hence a warning rather than an error — a genuine retail
        D.2 is perfectly normal and must not block an export — naming the
        partners whose own record contradicts the classification: flagged as a
        company, or previously reported in A.1, which a private individual
        never is.
        """
        self.ensure_one()
        code = self.version_id.section_code_ids.filtered(
            lambda c: c.code == "D.2")
        if not code:
            return []
        lines = self.env["l10n.sk.kv.dph.section.d2"]._eligible_move_lines(
            self, code[:1])
        partners = lines.move_id._cssk_vat_document(
        ).partner_id.commercial_partner_id
        if not partners:
            return []
        seen_in_a1 = self.env["account.move.line"].search([
            ("cssk_control_section_code", "=", "A.1"),
            ("move_id.partner_id.commercial_partner_id", "in", partners.ids),
        ]).move_id.partner_id.commercial_partner_id
        suspect = partners.filtered(
            lambda p: p.is_company or p in seen_in_a1)
        if not suspect:
            return []
        return [{
            "code": "KV_D2_BUSINESS",
            "severity": "warning",
            "desc": _("D.2: odberateľ vyzerá ako zdaniteľná osoba"),
            "detail": _(
                "%(n)d odberateľ(ov) v oddiele D.2 nemá IČ DPH ani IČO, ale "
                "podľa vlastného záznamu ide o podnikateľa: %(names)s. Ak IČO "
                "chýba len v evidencii, doplňte ho — dodanie potom patrí do "
                "A.1 (IČ DPH sa v A.1 neuvádza povinne). D.2 je súhrn, takže "
                "v samotnom výkaze odberateľa nevidno.",
                n=len(suspect),
                names=", ".join(sorted(suspect.mapped("display_name"))[:10]),
            ),
        }]
