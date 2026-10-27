from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command


class AccountMoveLinkAdvanceInvoiceWizard(models.TransientModel):
    _name = "account.move.link.advance.invoice.wizard"
    _description = "Link Standalone Advance Invoices"

    move_id = fields.Many2one(
        "account.move",
        string="Final Invoice",
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="move_id.partner_id",
        readonly=True,
    )
    available_advance_invoice_ids = fields.Many2many(
        "sale.order",
        compute="_compute_available_advance_invoice_ids",
    )
    advance_invoice_ids = fields.Many2many(
        "sale.order",
        string="Advance Invoices",
        domain="[('id', 'in', available_advance_invoice_ids)]",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("active_model") == "account.move" and self.env.context.get("active_id"):
            values.setdefault("move_id", self.env.context["active_id"])
        return values

    def _is_already_linked_elsewhere(self, advance, move):
        """Whether another live invoice already deducts this advance.

        A deduction is a negative-quantity line linked to the advance's order
        lines. Its tax documents are linked to the same lines with a positive
        quantity, and must not count: they are what makes an advance worth
        deducting with its VAT in the first place.
        """
        linked_invoice_lines = advance.order_line.invoice_lines.filtered(
            lambda line: line.move_id.move_type == "out_invoice"
            and line.move_id.state != "cancel"
            and line.move_id.id != move.id
            and line.quantity < 0
        )
        return bool(linked_invoice_lines)

    @api.depends("move_id", "move_id.partner_id")
    def _compute_available_advance_invoice_ids(self):
        SaleOrder = self.env["sale.order"]
        for wizard in self:
            move = wizard.move_id
            if not move or move.move_type != "out_invoice" or not move.partner_id:
                wizard.available_advance_invoice_ids = False
                continue

            commercial_partner = move.partner_id.commercial_partner_id
            candidate_advances = SaleOrder.search([
                ("is_advance_invoice", "=", True),
                ("state", "=", "sale"),
                ("partner_id", "child_of", commercial_partner.id),
                ("advance_invoice_parent_order_id", "=", False),
            ])

            available = candidate_advances.filtered(
                lambda advance: not wizard._is_already_linked_elsewhere(advance, move)
                and advance._advance_deduction_components()
            )
            wizard.available_advance_invoice_ids = available

    def action_link_advance_invoices(self):
        self.ensure_one()
        move = self.move_id

        if move.move_type != "out_invoice":
            raise UserError(_("This action is only available for customer invoices."))
        if move.state != "draft":
            raise UserError(_("You can only link advance invoices on a draft invoice."))
        if not self.advance_invoice_ids:
            raise UserError(_("Please select at least one advance invoice."))

        lines_to_add = []
        max_seq = max(move.invoice_line_ids.mapped("sequence") or [0])
        has_advance_section = any(
            l.display_type == "line_section" and l.name == _("Advance Invoices")
            for l in move.invoice_line_ids
        )
        if not has_advance_section:
            lines_to_add.append(Command.create({
                "display_type": "line_section",
                "name": _("Advance Invoices"),
                "sequence": max_seq + 1,
            }))

        for seq_offset, advance in enumerate(self.advance_invoice_ids, start=2):
            if advance.partner_id.commercial_partner_id != move.partner_id.commercial_partner_id:
                continue
            if self._is_already_linked_elsewhere(advance, move):
                continue

            source_line = advance.order_line.filtered(lambda l: not l.display_type)[:1]
            if not source_line:
                continue

            already_linked_on_move = bool(
                move.invoice_line_ids.filtered(
                    lambda line: source_line in line.sale_line_ids
                )
            )
            if already_linked_on_move:
                continue

            # The same parts as on an order's final invoice: the net each
            # posted tax document declared, at its own taxes, and gross
            # without VAT whatever was received beyond them. A draft tax
            # document has declared nothing yet.
            components = advance._advance_deduction_components()
            for offset, component in enumerate(components):
                name = _("Advance Invoice %(name)s", name=advance.name)
                if component["taxes"] and len(components) > 1:
                    name = "%s (%s)" % (name, ", ".join(component["taxes"].mapped("name")))
                line_vals = {
                    "product_id": source_line.product_id.id,
                    "name": name,
                    "quantity": -1.0,
                    "price_unit": component["amount"],
                    "tax_ids": [Command.set(component["taxes"].ids)],
                    "sale_line_ids": [Command.link(source_line.id)],
                    "sequence": max_seq + seq_offset * 100 + offset,
                }
                if component["account"]:
                    line_vals["account_id"] = component["account"].id
                lines_to_add.append(Command.create(line_vals))

        if len(lines_to_add) == (1 if not has_advance_section else 0):
            raise UserError(_("No eligible advance invoices were found to link."))

        move.write({"invoice_line_ids": lines_to_add})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Advance Invoices Linked"),
                "message": _("Selected advance invoices were linked to the final invoice."),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }