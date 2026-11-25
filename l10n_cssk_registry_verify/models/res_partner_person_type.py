# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The partner's *Entity Type*, from what the register said.

The register knows whether an IČO belongs to a person in business or to a
company; the partner form has a field for exactly that, and until now somebody
had to fill it by hand, which on a signed-up customer nobody did.
"""
from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _cssk_store_verification(self, result):
        res = super()._cssk_store_verification(result)
        self._cssk_set_person_type_from(result)
        return res

    def _cssk_set_person_type_from(self, result):
        """Write the person type the register's answer implies, if it does.

        Three answers are possible and only two of them are knowledge:

        * ``natural_person`` set: a person in business.
        * not set, with a ``legal_form``: a company.
        * neither: the register was not asked for it. That is every answer
          cached before the legal form was read, and reading it as "a company"
          would label each sole trader among them a legal entity. Nothing is
          written.

        A type somebody chose is kept as long as it says the same thing; the
        catalogue may hold finer types than the two seeded ones. It is
        replaced when it contradicts the register or belongs to the other
        country.
        """
        self.ensure_one()
        if result.get("outcome") != "verified":
            return
        natural_person = bool(result.get("natural_person"))
        if not natural_person and not result.get("legal_form"):
            return
        country_code = (self.country_id.code or "").upper()
        current = self.l10n_cssk_person_type_id
        if (
            current
            and current.country_code == country_code
            and current.is_legal_entity != natural_person
        ):
            return
        person_type = self.env["cssk.person.type"].sudo()._cssk_for_subject(
            country_code, natural_person
        )
        if person_type and person_type != current:
            self.sudo().l10n_cssk_person_type_id = person_type
