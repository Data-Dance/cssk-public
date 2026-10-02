"""The e-invoice as a method of Odoo's Send & Print.

``edi_peppol`` is offered and checked by default when the invoice routes to
Peppol (``account.move._peppol_route``: the contact's choice, else the
company's scope); sending through it generates the UBL and hands it to the
installed EDI provider, exactly as the "Send via Peppol" button does.

If Odoo's own ``account_peppol`` is installed too, its ``peppol`` method is
taken out of the defaults wherever ours applies: one invoice, one access point.
"""

from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_sending_methods(self, move) -> set:
        methods = super()._get_default_sending_methods(move)
        if self._is_applicable_to_move("edi_peppol", move):
            customer = move.commercial_partner_id.with_company(move.company_id)
            if not customer.invoice_sending_method:
                # Nothing chosen on the contact: the e-invoice replaces the
                # email default rather than going out beside it.
                methods.discard("email")
            methods.add("edi_peppol")
            methods.discard("peppol")
        return methods

    @api.model
    def _is_applicable_to_company(self, method, company):
        if method == "edi_peppol":
            return bool(company.sudo().peppol_send_enabled)
        return super()._is_applicable_to_company(method, company)

    @api.model
    def _is_applicable_to_move(self, method, move, **move_data):
        if method == "edi_peppol":
            return bool(
                move.move_type in ("out_invoice", "out_refund")
                and move._peppol_provider()
                and move._peppol_route()[0] == "peppol"
            )
        return super()._is_applicable_to_move(method, move, **move_data)

    def _call_web_service_after_invoice_pdf_render(self, invoices_data):
        super()._call_web_service_after_invoice_pdf_render(invoices_data)
        for invoice, invoice_data in invoices_data.items():
            if ("edi_peppol" not in invoice_data.get("sending_methods", ())
                    or not self._is_applicable_to_move("edi_peppol", invoice)):
                continue
            sent = invoice.peppol_message_ids.filtered(
                lambda m: m.direction == "out" and m.state in ("queued", "sent"))
            if sent:
                continue  # already on its way, e.g. auto-sent when posted
            try:
                with self.env.cr.savepoint():
                    invoice._peppol_emit(queue_send=True)
            except Exception as error:  # noqa: BLE001 - shown in the wizard
                previous = invoice_data.get("error")
                errors = ([previous["error_title"]] + previous.get("errors", [])
                          if isinstance(previous, dict) else [previous] if previous else [])
                invoice_data["error"] = {
                    "error_title": invoice.env._("The e-invoice could not be sent"),
                    "errors": errors + [str(error)],
                }
