from odoo import fields, models
from odoo.tools import float_is_zero


class AccountTax(models.Model):
    _inherit = "account.tax"

    cssk_control_section_default = fields.Char(
        string="Control-statement section",
        help="Default control-statement section code for lines using this tax. "
        "Used by the section resolver as a starting hint.",
    )
    cssk_control_is_reverse_charge = fields.Boolean(
        string="Reverse charge",
        help="Marks this tax as triggering reverse-charge classification "
        "(prenos/přenesení daňové povinnosti). Checked first by the resolver.",
    )

    def _cssk_self_assesses(self):
        """Whether this tax posts its output leg AND its deduction on the same
        line, so ``compute_all`` nets them to ~0.

        Read off the tax's own repartition rather than a flag, because this is
        a different question from the one ``cssk_control_is_reverse_charge``
        answers and the two only look alike. That flag is a CLASSIFICATION
        hint — it means "domestic § 92a / § 69 ods. 12", and the country
        modules deliberately keep intra-EU acquisitions out of it so the
        section resolver reaches A.2/B.1 by the intra-EU branch instead. But an
        EU acquisition self-assesses just as much as a domestic reverse charge
        does, and the AMOUNT logic needs that broader question answered.

        Conflating them cost the whole tax column of Czech oddíl A2: those
        lines carry ``21% EU G`` / ``12% EU G`` / ``15% EU G``, which are
        unflagged by design, so the flat recovery never fired and the netted
        pair was reported as the tax. Measured on the import spike: 595
        A2-classified lines, every one of them an EU tax, every one reporting
        its base with ``dan1`` absent — and the XSD makes ``dan1`` optional, so
        it exported clean and wrong.

        The structural test discriminates exactly, on the same database:

            21% EU G / 12% EU G / 21% EU S   tax legs +100, -100  -> sum 0
            21% RC (domestic § 92a)          tax legs +100, -100  -> sum 0
            21% G  (ordinary output tax)     tax leg  +100        -> sum 100

        Note it is the **tax** legs that must net out, not the base leg, and
        two of them at minimum. A partial-VAT-deduction tax also carries two
        tax legs — one tagged, one not — but they are both positive (+50/+50),
        so it sums to 100 and is correctly not self-assessed.
        """
        self.ensure_one()
        if self.amount_type != "percent" or not self.amount:
            return False
        # Refund-aware: Odoo lets the refund repartition differ from the
        # invoice one, so a credit note can self-assess where the invoice does
        # not, or the reverse. Reading only the invoice legs would classify a
        # correction by its original's structure. ``_tax_self_cancels`` in the
        # importer already makes the same distinction; the two answering it
        # differently is exactly the sort of split that hides a defect.
        refund = (self.env.context.get("cssk_refund") or "").endswith("_refund")
        legs = (
            self.refund_repartition_line_ids if refund
            else self.invoice_repartition_line_ids
        ).filtered(lambda r: r.repartition_type == "tax")
        if len(legs) < 2:
            return False
        return float_is_zero(sum(legs.mapped("factor_percent")), precision_digits=2)
