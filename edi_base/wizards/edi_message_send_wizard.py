from odoo import _, fields, models


class EdiMessageSendWizard(models.TransientModel):
    _name = "edi.message.send.wizard"
    _description = "Bulk-queue selected EDI messages for sending"

    sendable_ids = fields.Many2many(
        "edi.message",
        "edi_send_wiz_sendable_rel",
        "wizard_id",
        "message_id",
        string="Will be sent",
        readonly=True,
    )
    skipped_ids = fields.Many2many(
        "edi.message",
        "edi_send_wiz_skipped_rel",
        "wizard_id",
        "message_id",
        string="Will be skipped",
        readonly=True,
    )
    sendable_count = fields.Integer(compute="_compute_counts")
    skipped_count = fields.Integer(compute="_compute_counts")

    @staticmethod
    def _skip_reason(msg):
        """Short label explaining why a message is not sendable."""
        if msg.direction != "out":
            return _("inbound")
        if msg.state == "done":
            return _("already done")
        if msg.state == "sent":
            return _("already sent")
        return _("state '%s'") % (msg.state or "?")

    def _compute_counts(self):
        for wiz in self:
            wiz.sendable_count = len(wiz.sendable_ids)
            wiz.skipped_count = len(wiz.skipped_ids)

    def action_confirm(self):
        self.ensure_one()
        if self.sendable_ids:
            self.sendable_ids.action_send()
        return {"type": "ir.actions.act_window_close"}
