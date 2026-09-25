# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #: Odoo's own wording for the two directions, so the footprint agrees with
    #: what the declaration form calls itself.
    _INTRASTAT_DIRECTION = {
        "arrivals": _("arrivals"),
        "dispatches": _("dispatches"),
    }

    def _cssk_statutory_footprint(self):
        """Name the Intrastat declaration that reports this line.

        READ, do not re-derive. What puts a line on a declaration is a goods
        movement across an EU border, decided by the declaration's own
        generation with the company's thresholds, exclusions and transaction
        codes in hand. Re-deciding eligibility here would be a second reader of
        that question and would drift from it — which is exactly how three
        other contributors to this footprint went wrong. The declaration
        already records which lines it took, so that link is what is read.

        The consequence worth stating: a period whose declaration has not been
        generated yet reports NOTHING, and that is honest. A document is not
        "on an Intrastat declaration" until one exists; saying it would be
        predicting rather than reporting.
        """
        res = super()._cssk_statutory_footprint()
        computations = self.env["intrastat.product.computation.line"].search(
            [("invoice_line_id", "=", self.id)])
        seen = set()
        for computation in computations:
            declaration = computation.parent_id
            if not declaration or declaration.id in seen:
                continue
            seen.add(declaration.id)
            direction = self._INTRASTAT_DIRECTION.get(
                declaration.declaration_type, declaration.declaration_type)
            res.append({
                "form": _("Intrastat"),
                "code": declaration.year_month or "",
                "name": _("Intrastat %(direction)s — %(state)s",
                          direction=direction,
                          state=self._intrastat_state_label(declaration)),
                # This contributor is the one case that needs no resolution:
                # it reached the row THROUGH the declaration, so it already
                # holds the record the others have to go looking for.
                "res_model": declaration._name,
                "res_id": declaration.id,
            })
        return res

    @staticmethod
    def _intrastat_state_label(declaration):
        """Whether the declaration has been filed, in its own vocabulary.

        A footprint that named a declaration without saying so would read the
        same for a draft nobody has sent and for one lodged with Colná správa,
        and the difference is the whole question an accountant is asking.
        """
        field = declaration._fields.get("state")
        if not field:
            return ""
        selection = dict(field._description_selection(declaration.env))
        return selection.get(declaration.state, declaration.state or "")
