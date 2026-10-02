# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the interní / interný doklad prints, worked out once for the template.

Czech § 11 odst. 1 zákona č. 563/1991 Sb. and Slovak § 10 ods. 1 zákona
č. 431/2002 Z. z. ask the same of an accounting document: its designation, the
content of the accounting case and its participants, the amount, the date it
was prepared, the date of the case where the two differ, and the signature
records of the person responsible for the case and of the person responsible
for booking it. The labels are the statutes' own terms, in the language of the
company's fiscal country, and are not translated.
"""

from odoo import models
from odoo.tools import html2plaintext

#: The statutory wording, per country. Czech is the default.
LABELS = {
    "CZ": {
        "title": "Interní doklad",
        "number": "Označení dokladu",
        "entity": "Účetní jednotka",
        "company_id": "IČO",
        "journal": "Deník",
        "content": "Obsah účetního případu",
        "participants": "Účastníci účetního případu",
        "amount": "Peněžní částka",
        "prepared": "Datum vyhotovení",
        "occurred": "Datum uskutečnění účetního případu",
        "account": "Účet",
        "label": "Popis",
        "partner": "Partner",
        "analytic": "Analytika",
        "debit": "Má dáti",
        "credit": "Dal",
        "total": "Celkem",
        "responsible": "Podpisový záznam osoby odpovědné za účetní případ",
        "booked": "Podpisový záznam osoby odpovědné za jeho zaúčtování",
        "draft": "NEZAÚČTOVÁNO",
    },
    "SK": {
        "title": "Interný doklad",
        "number": "Označenie dokladu",
        "entity": "Účtovná jednotka",
        "company_id": "IČO",
        "journal": "Denník",
        "content": "Obsah účtovného prípadu",
        "participants": "Účastníci účtovného prípadu",
        "amount": "Peňažná suma",
        "prepared": "Dátum vyhotovenia",
        "occurred": "Dátum uskutočnenia účtovného prípadu",
        "account": "Účet",
        "label": "Popis",
        "partner": "Partner",
        "analytic": "Analytika",
        "debit": "Má dať",
        "credit": "Dal",
        "total": "Spolu",
        "responsible": "Podpisový záznam osoby zodpovednej za účtovný prípad",
        "booked": "Podpisový záznam osoby zodpovednej za jeho zaúčtovanie",
        "draft": "NEZAÚČTOVANÉ",
    },
}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _cssk_internal_document_labels(self):
        self.ensure_one()
        country = self.company_id.account_fiscal_country_id.code
        return LABELS.get(country, LABELS["CZ"])

    def _cssk_internal_document_poster(self):
        """Who posted the entry, as a partner, or an empty recordset.

        ``state`` is tracked, and while the entry is posted its last state
        change is the posting, whoever or whatever (the auto-post cron) did
        it. The tracking message's author is that user; the tracking value
        itself is written under sudo and names nobody.
        """
        self.ensure_one()
        if self.state != "posted":
            return self.env["res.partner"]
        tracking = self.env["mail.tracking.value"].sudo().search([
            ("mail_message_id.model", "=", self._name),
            ("mail_message_id.res_id", "=", self.id),
            ("field_id.name", "=", "state"),
            ("field_id.model", "=", self._name),
        ], order="id desc", limit=1)
        return tracking.mail_message_id.author_id

    def _cssk_internal_document_content(self):
        """The content of the accounting case: the reference, else the
        narration, else the lines' own labels."""
        self.ensure_one()
        if self.ref:
            return self.ref
        narration = html2plaintext(self.narration or "").strip()
        if narration:
            return narration
        labels = [name for name in self.line_ids.mapped("name") if name]
        return "; ".join(dict.fromkeys(labels))

    def _cssk_internal_document_participants(self):
        """The company, then every partner the lines name."""
        self.ensure_one()
        partners = self.company_id.partner_id | self.partner_id | self.line_ids.partner_id
        return partners.mapped("display_name")

    def _cssk_internal_document_amount(self):
        self.ensure_one()
        return sum(self.line_ids.mapped("debit"))


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _cssk_analytic_label(self):
        """``analytic_distribution`` as names and shares, e.g. "Sklad (60 %)"."""
        self.ensure_one()
        parts = []
        for key, share in (self.analytic_distribution or {}).items():
            ids = [int(i) for i in str(key).split(",") if i.strip().isdigit()]
            names = self.env["account.analytic.account"].browse(ids).exists().mapped("name")
            if names:
                share_text = ("%g" % share).replace(".", ",")
                parts.append("%s (%s %%)" % (" / ".join(names), share_text))
        return ", ".join(parts)
