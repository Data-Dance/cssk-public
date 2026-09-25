from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    ai_extract_extraction_id = fields.Many2one(
        'account.invoice.ai.extraction', string="AI Extraction", readonly=True, copy=False)

    def action_view_ai_extraction(self):
        """Smart button: open the AI extraction that produced this bill."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice.ai.extraction',
            'res_id': self.ai_extract_extraction_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ------------------------------------------------------------------
    # Email-alias ingestion
    # ------------------------------------------------------------------
    def _message_post_after_hook(self, message, msg_vals):
        """When a PDF lands on an empty draft vendor bill (typically via the
        vendor-bills email alias), queue an AI extraction to fill it. Runs
        asynchronously through the cron so e-mail intake is never blocked."""
        res = super()._message_post_after_hook(message, msg_vals)
        for move in self:
            company = move.company_id
            if not company.ai_extract_auto_extract:
                continue
            if move.move_type not in ('in_invoice', 'in_refund'):
                continue
            if move.state != 'draft' or move.ai_extract_extraction_id or move.invoice_line_ids:
                continue
            pdf = message.attachment_ids.filtered(
                lambda a: a.mimetype == 'application/pdf')[:1]
            if pdf:
                move._ai_extract_create_extraction(pdf, run_now=False)
        return res

    # ------------------------------------------------------------------
    # Manual trigger
    # ------------------------------------------------------------------
    def action_ai_extract(self):
        """Manual: extract from the latest PDF attached to this bill and fill it."""
        self.ensure_one()
        pdf = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id),
            ('mimetype', '=', 'application/pdf'),
        ], order='id desc', limit=1)
        if not pdf:
            raise UserError(_("Attach a PDF to this bill first."))
        extraction = self._ai_extract_create_extraction(pdf, run_now=True)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.invoice.ai.extraction',
            'res_id': extraction.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _ai_extract_create_extraction(self, attachment, run_now=False):
        self.ensure_one()
        extraction = self.env['account.invoice.ai.extraction'].create({
            'attachment_id': attachment.id,
            'company_id': self.company_id.id,
            'move_id': self.id,
        })
        self.ai_extract_extraction_id = extraction.id
        if run_now:
            extraction._process_one()
        return extraction
