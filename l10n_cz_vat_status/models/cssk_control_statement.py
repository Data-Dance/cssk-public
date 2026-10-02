# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Kontrolní hlášení only for days the company was a plátce.

§ 101c: "**Plátce** je povinen podat kontrolní hlášení, pokud …". Neither an
identifikovaná osoba nor a neplátce is named, and DPHDP3's own rules say the
same by omission: § 101 odst. 1 makes an identifikovaná osoba file a return,
§ 101c never makes it file a KH. The DPHKH1 XSD agrees — it has no filer-type
attribute at all, only "plátce" throughout its documentation, and the only
answer it offers a non-filer is the výzva response "B – Nemám povinnost podat
KH".

So:

* a period with **no** plátce day cannot be computed — there is nothing to file;
* a period with **some** plátce days is computed normally, and the lines of
  documents dated outside them never reach it (``account.move.line.
  _cssk_resolve_section_code``); the statement's chatter says which days
  counted.
"""

from odoo import _, models
from odoo.exceptions import UserError


class CsskControlStatement(models.Model):
    _inherit = "cssk.control.statement"

    def action_compute_lines(self):
        for st in self:
            company = st.company_id
            if (st.country_id.code != "CZ"
                    or not company._l10n_cz_vat_status_has_history()):
                continue
            segments = company._l10n_cz_vat_status_segments(
                st.date_from, st.date_to)
            if all(s != "payer" for _a, _b, s in segments):
                raise UserError(_(
                    "The company was not a VAT payer on any day of %(from)s – "
                    "%(to)s (%(detail)s). Only a plátce files a kontrolní "
                    "hlášení (§ 101c zákona o DPH). If the tax office asks for "
                    "one, answer the výzva with “B – Nemám povinnost podat KH”.",
                    **{"from": st.date_from, "to": st.date_to,
                       "detail": company._l10n_cz_vat_status_describe(segments)}))
        res = super().action_compute_lines()
        for st in self:
            company = st.company_id
            if (st.country_id.code != "CZ"
                    or not company._l10n_cz_vat_status_has_history()):
                continue
            segments = company._l10n_cz_vat_status_segments(
                st.date_from, st.date_to)
            if len({s for _a, _b, s in segments}) > 1:
                st.message_post(body=_(
                    "The company's VAT status changes within this period: "
                    "%(detail)s. Only documents dated on plátce days were "
                    "included (§ 101c).",
                    detail=company._l10n_cz_vat_status_describe(segments)))
        return res
