# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""CZ preflight: the competent finanční úřad (``c_ufo``).

Every Czech EPO submission carries the destination tax office in its header —
``c_ufo`` on DPHDP3 / KH / souhrnné hlášení, ``c_ufo_cil`` on DPPO — and all
four templates read it from ``company.l10n_cssk_tax_authority_id``. The check
lives HERE rather than in each of those four modules because they all depend on
``l10n_cz_statutory`` and the requirement is identical for each; the same
reasoning that put the ``ondelete`` fix on the shared control-statement mixin.

Without it the failure is silent-then-cryptic: the templates emit
``... or ''``, so an unset office renders ``c_ufo=""`` and the user gets an XSD
type error about a decimal, naming neither the field nor where to set it.

The digit check is not defensive padding — it is the one the XSD actually
makes, and it is the likely mistake rather than an unlikely one. ``c_ufo`` is
``xs:decimal totalDigits="3"``; the *workplace* goes in the separate optional
``c_pracufo`` (``totalDigits="4"``), which the templates already take from
Odoo's own ``l10n_cz_tax_office_id.workplace_code``. But
``cssk.tax.authority`` seeds both kinds — on a current database 15 regional
offices (2-3 digits, no parent) and **214 územní pracoviště** (4 digits, each
parented to its region). So 214 of the 229 selectable values are the wrong
answer for this field, and picking one is the overwhelmingly likely user
error. Where the chosen record is a workplace we can name its parent as the
fix instead of merely rejecting it.
"""

from odoo import _, models
from odoo.exceptions import UserError


class CsskStatutorySubmissionMixin(models.AbstractModel):
    _inherit = "cssk.statutory.submission.mixin"

    def _cssk_preflight_export(self):
        res = super()._cssk_preflight_export()
        for rec in self:
            company = getattr(rec, "company_id", None)
            if company is None:
                continue
            # Gate on the COMPANY's fiscal country, not on the record: this
            # module can be installed on a database that also files Slovak
            # statements, and those carry no c_ufo at all.
            if company.account_fiscal_country_id.code != "CZ":
                continue
            if not rec._cz_requires_tax_authority():
                continue
            rec._cz_check_tax_authority(company)
        return res

    def _cz_requires_tax_authority(self):
        """Whether this form carries the competent office (``c_ufo``).

        Every form this module was written for does. The OSS return does not:
        the special schemes are administered by one office for everyone, and
        OSSEI1 has no ``c_ufo`` at all — so it overrides this.
        """
        return True

    def _cz_check_tax_authority(self, company):
        """Raise a named error unless ``company`` can render a valid c_ufo."""
        self.ensure_one()
        authority = company.l10n_cssk_tax_authority_id
        if not authority:
            raise UserError(_(
                "Company '%(company)s' has no competent tax office (finanční "
                "úřad) set, but every Czech EPO submission must carry its "
                "code in the XML header (c_ufo). Set 'Tax authority' on the "
                "company (Settings → Users & Companies → Companies → "
                "%(company)s) and export again.",
                company=company.display_name))
        if authority.country_code != "CZ":
            raise UserError(_(
                "Company '%(company)s' is a Czech filer, but its tax office "
                "'%(authority)s' is not a Czech one. A Czech EPO submission "
                "must name a finanční úřad. Pick a Czech office and export "
                "again.",
                company=company.display_name,
                authority=authority.display_name))
        code = authority.submission_code or ""
        if not code:
            raise UserError(_(
                "Tax office '%(authority)s' has no submission code, but it is "
                "what the Czech EPO submission emits as c_ufo. Set "
                "'Submission code' on the office and export again.",
                authority=authority.display_name))
        if not (code.isdigit() and len(code) <= 3):
            parent = authority.parent_authority_id
            if parent and (parent.submission_code or "").isdigit():
                raise UserError(_(
                    "Tax office '%(authority)s' is a territorial workplace "
                    "(územní pracoviště), and its code %(code)s cannot be "
                    "used as c_ufo — that field takes the regional finanční "
                    "úřad (at most 3 digits). Set the company's tax authority "
                    "to '%(parent)s' instead; the workplace belongs in the "
                    "separate 'Tax office' field, which the XML emits as "
                    "c_pracufo.",
                    authority=authority.display_name, code=code,
                    parent=parent.display_name))
            raise UserError(_(
                "Tax office '%(authority)s' has submission code %(code)s, "
                "which the Czech EPO submission cannot emit as c_ufo — that "
                "field takes at most 3 digits (xs:decimal, totalDigits=3). "
                "Correct the office's 'Submission code' and export again.",
                authority=authority.display_name, code=code))
