from odoo import fields, models


class AccountMove(models.Model):
    """Which side of the business a document belongs to, where its type cannot say.

    The control statement needs to know whether a supply was made or received,
    and ``move_type`` answers that for an invoice. It cannot answer it for a
    journal entry: an entry carrying VAT has a direction, and ``entry`` is not
    one. Deriving it instead has been tried three times and failed three times
    — from the line's taxes, from its tags, and from the journal — each attempt
    correcting a minority by breaking a majority (see
    ``account.move.line._cssk_direction_sign``).

    The direction is therefore *declared* rather than inferred. Nothing sets it
    by default: an ordinary Czech or Slovak install has invoices, and invoices
    already know. It exists for the documents that do not — an entry that
    carries VAT, and above all an imported one, where whatever produced the
    entry knew perfectly well which side it was and had nowhere to record it.
    """

    _inherit = "account.move"

    cssk_vat_direction = fields.Selection(
        [("sale", "Supplied"), ("purchase", "Received")],
        string="VAT direction",
        copy=False,
        index=True,
        help="Set on a journal entry that carries VAT to say which side of the "
        "control statement it belongs to. Leave empty on an invoice: its own "
        "type is the better answer, and is used when this is not set.",
    )

    cssk_vat_correction = fields.Selection(
        [("yes", "Correction"), ("no", "Not a correction")],
        string="VAT correction",
        copy=False,
        index=True,
        help="Set on a journal entry to say whether it is a correction "
        "(opravný doklad / dobropis) for control-statement purposes. Leave "
        "empty on an invoice: its own type answers, and is used when this is "
        "not set.\n\n"
        "Exists for the same reason as the VAT direction above. The Slovak "
        "resolver sends corrections to oddiel C.1 and C.2, and it decides by "
        "`move_type in ('out_refund', 'in_refund')` — which an imported credit "
        "note posted as a journal ENTRY does not satisfy. Measured on the i6 "
        "spike: 16 926 of its documents are entries against 4 invoices, so no "
        "document could ever reach C.1 or C.2 at all; and on the Money import, "
        "22 credit notes are demoted to entries and lose the same test. The "
        "source knew it was a credit note and had nowhere to record it.",
    )

    cssk_control_original_ref = fields.Char(
        string="Original document number",
        copy=False,
        help="The number of the document this credit note or correction "
        "corrects, for when it is not linked to it — a credit note created by "
        "hand because it could not be raised from the invoice. The control "
        "statement reports it as the original document of a C.1 / C.2 row "
        "(Slovak kontrolný výkaz: poradové číslo pôvodnej faktúry). A linked "
        "original always wins over this.",
    )

    def _cssk_control_original(self):
        """The document this one corrects, when Odoo links it: a reversal's
        ``reversed_entry_id`` or a debit note's ``debit_origin_id``."""
        self.ensure_one()
        original = self.reversed_entry_id
        if not original and "debit_origin_id" in self._fields:
            original = self.debit_origin_id
        return original

    def _cssk_vat_document(self):
        """The document whose VAT each of these moves reports.

        Usually the move itself. A CASH-BASIS ENTRY is the exception: when a
        tax is "Based on Payment", Odoo leaves the invoice's VAT on a
        transition account until the invoice is paid and then posts a separate
        journal entry that makes it due. That entry carries the tax, but it is
        an ``entry`` with **no partner and no document number** of its own.
        Classified as itself, a paid customs bill therefore landed in B.3.1 as
        an anonymous receipt (a received document with no counterparty),
        while the bill it paid had already been reported unpaid.

        Everything the control statement asks of a document — which side it
        belongs to, whether it is a correction, who the counterparty is, what
        its number is — has its answer on the invoice, so it is read there.
        What stays with the entry is WHEN: the tax became due on payment, so
        the period and the date reported are the entry's own.
        """
        return self.browse([
            move.tax_cash_basis_origin_move_id.id or move.id for move in self])
