import base64
import json
import logging
import time
from datetime import datetime, timezone

import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools import format_datetime

from odoo.addons.l10n_sk_vrp2_base.models.vrp2_client import (
    vrp2_round2,
    vrp2_round4,
    vrp2_round5,
)

_logger = logging.getLogger(__name__)

# Odoo order states in which the sale has actually been settled.
_SETTLED_STATES = ("paid", "done")


def _js_numbers(value):
    """Integral floats as ints, recursively, so the body serializes the way
    the web app's ``JSON.stringify`` does (``1`` and ``0``, never ``1.0``).
    """
    if isinstance(value, dict):
        return {k: _js_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_js_numbers(v) for v in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


class PosOrder(models.Model):
    _inherit = "pos.order"

    vrp2_state = fields.Selection(
        [
            ("not_fiscalized", "Not Fiscalized"),
            ("fiscalized", "Fiscalized"),
            ("error", "Error"),
        ],
        string="VRP2 Status",
        default="not_fiscalized",
        readonly=True,
        copy=False,
        index=True,
    )
    vrp2_receipt_number = fields.Char(
        string="VRP2 Receipt Number", readonly=True, copy=False
    )
    vrp2_server_id = fields.Char(
        string="VRP2 Receipt ID", readonly=True, copy=False
    )
    vrp2_receipt_uuid = fields.Char(
        string="VRP2 Receipt UUID",
        readonly=True,
        copy=False,
        help="VRP2 receiptId (V-…). This is exactly what the QR code on the "
        "official receipt encodes.",
    )
    vrp2_created = fields.Datetime(
        string="VRP2 Fiscalized On", readonly=True, copy=False
    )
    vrp2_okp = fields.Char(string="OKP", readonly=True, copy=False)
    vrp2_qr_content = fields.Char(
        string="VRP2 Receipt Data",
        readonly=True,
        copy=False,
        help="VRP2 dataBase64: the whole receipt as base64 JSON (items as "
        "VRP2 named them, VAT summary, payments, rounding). NOT the QR code, "
        "which encodes only the receiptId.",
    )
    vrp2_pdf = fields.Binary(
        string="VRP2 Receipt PDF", readonly=True, copy=False, attachment=True
    )
    vrp2_pdf_filename = fields.Char(readonly=True, copy=False)
    vrp2_request_json = fields.Text(
        string="VRP2 Request", readonly=True, copy=False
    )
    vrp2_response_json = fields.Text(
        string="VRP2 Response", readonly=True, copy=False
    )
    vrp2_error_message = fields.Text(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_vrp2_fiscalize(self):
        """Fiscalize the selected orders in VRP2.

        One order: fail loudly. Several (list action): each receipt is an
        external side effect a rollback cannot undo, so one failure must not
        roll back the others — failures are recorded on their orders.
        """
        if len(self) == 1:
            self._vrp2_fiscalize()
            return True
        todo = self.filtered(
            lambda o: o.vrp2_state != "fiscalized"
            and o.state in _SETTLED_STATES
            and o.config_id.vrp2_enabled
        )
        for order in todo:
            order._vrp2_fiscalize_or_record_error()
        failed = todo.filtered(lambda o: o.vrp2_state == "error")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("VRP2"),
                "message": _(
                    "%(done)s order(s) fiscalized, %(failed)s failed, "
                    "%(skipped)s skipped.",
                    done=len(todo) - len(failed),
                    failed=len(failed),
                    skipped=len(self) - len(todo),
                ),
                "type": "warning" if failed else "success",
                "sticky": bool(failed),
            },
        }

    def action_vrp2_print_receipt(self):
        """Download the official VRP2 PDF receipt for this order."""
        self.ensure_one()
        if not self.vrp2_pdf:
            raise UserError(_("No VRP2 PDF is stored for this order."))
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/pos.order/%s/vrp2_pdf/%s?download=true"
            % (self.id, self.vrp2_pdf_filename or "receipt.pdf"),
            "target": "self",
        }

    # ------------------------------------------------------------------
    # Automatic fiscalization when the POS syncs a paid order
    # ------------------------------------------------------------------

    def _process_saved_order(self, draft):
        order_id = super()._process_saved_order(draft)
        if (
            not draft
            and self.state in _SETTLED_STATES
            and self.config_id.vrp2_enabled
            and self.config_id.vrp2_auto_fiscalize
            and self.vrp2_state != "fiscalized"
        ):
            self._vrp2_fiscalize_after_commit()
        return order_id

    def _vrp2_fiscalize_after_commit(self):
        """Fiscalize once the order's own transaction has COMMITTED.

        ``sync_from_ui`` saves a whole batch of orders in one transaction. A
        receipt issued from inside it would survive a later rollback (say, the
        next order of the batch failing) while the order did not, and the
        till's re-sync would then fiscalize the same sale a second time. After
        the commit, the order exists for certain; the worst left is a crash
        before the call, which leaves the order visibly "Not Fiscalized"
        rather than fiscalized twice.
        """
        self.ensure_one()
        dbname = self.env.cr.dbname
        uid = self.env.uid
        context = dict(self.env.context)
        order_id = self.id

        @self.env.cr.postcommit.add
        def _fiscalize():
            with Registry(dbname).cursor() as cr:
                env = api.Environment(cr, uid, context)
                env["pos.order"].browse(order_id)._vrp2_fiscalize_or_record_error()

    def _vrp2_fiscalize_or_record_error(self, retry_on_concurrency=False):
        """Fiscalize, but never let a VRP2 failure lose the sale itself.

        The order sync from the till must succeed even when the Financial
        Administration is unreachable, so a failure is recorded on the order
        (``vrp2_state = error``) instead of raised. The savepoint discards the
        half-written request fields of the failed attempt.

        Another transaction fiscalizing the same order is NOT a failure: its
        lock (``LockNotAvailable``) or its commit (``SerializationFailure``
        under REPEATABLE READ) means the receipt is, or is being, issued
        there, and recording an error would overwrite it. Background callers
        skip; ``retry_on_concurrency`` re-raises instead, so that Odoo replays
        the request on a fresh snapshot and the caller reads the real result.
        """
        self.ensure_one()
        if self.vrp2_state == "fiscalized":
            return
        try:
            with self.env.cr.savepoint():
                self._vrp2_fiscalize()
        except (
            psycopg2.errors.LockNotAvailable,
            psycopg2.errors.SerializationFailure,
        ):
            if retry_on_concurrency:
                raise
            _logger.info(
                "VRP2: order %s is being fiscalized elsewhere; skipped.",
                self.name,
            )
        except Exception as exc:  # noqa: BLE001 — recorded, never swallowed silently
            _logger.exception(
                "VRP2 fiscalization of POS order %s failed", self.name
            )
            self.write({
                "vrp2_state": "error",
                "vrp2_error_message": _(
                    "%(error)s\n\nIf the failure was a timeout, VRP2 may "
                    "already hold this receipt: check the register's receipt "
                    "list in the VRP2 portal before fiscalizing again.",
                    error=exc,
                ),
            })

    # ------------------------------------------------------------------
    # POS frontend
    # ------------------------------------------------------------------

    # Audit payloads and the PDF stay on the server: the POS loads every
    # pos.order field it is sent, for each order in its history.
    _VRP2_NOT_FOR_POS = (
        "vrp2_pdf", "vrp2_qr_content", "vrp2_request_json", "vrp2_response_json",
    )

    @api.model
    def _load_pos_data_read(self, records, config):
        # bin_size: read the PDF's size, not the PDF, before dropping it.
        rows = super()._load_pos_data_read(
            records.with_context(bin_size=True), config
        )
        for row in rows:
            for key in self._VRP2_NOT_FOR_POS:
                row.pop(key, None)
        return rows

    def vrp2_receipt_for_ui(self):
        """The order's VRP2 receipt as the till prints it.

        Called by the POS right after it validated the order. The receipt is
        normally already issued — the post-commit fiscalization runs before
        the sync request returns — so this only reads it. It fiscalizes when
        that step never ran (``not_fiscalized``), but never retries an
        ``error`` on its own: after a timeout VRP2 may already hold the
        receipt, and only a person can check the portal.
        """
        self.ensure_one()
        config = self.config_id
        if not config.vrp2_enabled:
            return {"enabled": False}
        if (
            self.vrp2_state == "not_fiscalized"
            and config.vrp2_auto_fiscalize
            and self.state in _SETTLED_STATES
        ):
            self._vrp2_fiscalize_or_record_error(retry_on_concurrency=True)
        return self._vrp2_receipt_values()

    def _vrp2_receipt_values(self):
        self.ensure_one()
        return {
            "enabled": True,
            "state": self.vrp2_state,
            "receipt_number": self.vrp2_receipt_number or False,
            "receipt_uuid": self.vrp2_receipt_uuid or False,
            "okp": self.vrp2_okp or False,
            "dkp": self.config_id.vrp2_dkp or False,
            "created": format_datetime(self.env, self.vrp2_created)
            if self.vrp2_created else False,
            "error": self.vrp2_error_message or False,
            "has_pdf": bool(self.vrp2_pdf),
        }

    # ------------------------------------------------------------------
    # Fiscalization
    # ------------------------------------------------------------------

    def _vrp2_fiscalize(self):
        """Issue this order's VRP2 receipt on its till's own cash register.

        - an invoiced order → "Úhrada faktúry" (``/v5/receipt/create/invoice``,
          no item breakdown: the invoice already carries the VAT);
        - otherwise → an itemized sale receipt (``/v5/receipt/create/valid``),
          where refund lines become ``REFUND`` items that reference the
          original order's receipt — that is VRP2's storno of a sale.

        A VRP2 error raises so the transaction rolls back and the order is not
        left half-fiscalized; the automatic path catches it (see
        ``_vrp2_fiscalize_or_record_error``).
        """
        self.ensure_one()
        # Serialize concurrent attempts (automatic + a manager's click, two
        # workers): lock the order and re-read its state, so only one of them
        # can reach VRP2. NOWAIT: the loser fails at once instead of queueing
        # behind a network call and then sending a second receipt.
        self.env.cr.execute(
            "SELECT id FROM pos_order WHERE id = %s FOR UPDATE NOWAIT",
            (self.id,),
        )
        self.invalidate_recordset(["vrp2_state"])
        till = self.config_id
        if not till.vrp2_enabled:
            raise UserError(
                _("VRP2 is not enabled for Point of Sale '%s'.")
                % till.display_name
            )
        if not till.vrp2_login:
            raise UserError(
                _("VRP2 credentials are not configured on till '%s'.")
                % till.display_name
            )
        if self.vrp2_state == "fiscalized":
            raise UserError(
                _("Order %s is already fiscalized in VRP2.") % self.name
            )
        if self.state not in _SETTLED_STATES:
            raise UserError(
                _("Order %s must be paid before it can be fiscalized.")
                % self.name
            )

        client = self.env["vrp2.client"]
        client._ensure_session(till)

        if self.account_move:
            request_body = self._vrp2_build_invoice_dto()
            self.vrp2_request_json = json.dumps(
                request_body, ensure_ascii=False, indent=2
            )
            response = client._create_invoice(till, request_body)
        else:
            request_body = self._vrp2_build_receipt_dto()
            self.vrp2_request_json = json.dumps(
                request_body, ensure_ascii=False, indent=2
            )
            response = client._create_receipt_valid(till, request_body)
        self._vrp2_apply_response(response)
        _logger.info(
            "VRP2 POS receipt %s created for order %s",
            self.vrp2_receipt_number,
            self.name,
        )
        return True

    # ------------------------------------------------------------------
    # Item lines
    # ------------------------------------------------------------------

    def _vrp2_fiscal_lines(self):
        """The order lines that become receipt items, in receipt order."""
        self.ensure_one()
        return self.lines.filtered(lambda line: line.qty).sorted("id")

    def _vrp2_line_figures(self, line):
        """Unit price, per-unit discount and VAT rate as VRP2 expects them.

        From the web app's ``parseToAPI`` (app.js): ``priceWithVat`` is the
        UNIT price including VAT, ``discount`` is an ABSOLUTE per-unit amount
        (a percentage discount is converted with ``zaokruhli4``) and VRP2
        computes the line total itself as ``zaokruhli2((unit − discount) ×
        quantity)``. Both stay positive here; the item type carries the sign.
        """
        taxes = line.tax_ids_after_fiscal_position
        vat_taxes = taxes.filtered(lambda t: t.amount_type == "percent")
        if len(vat_taxes) > 1 or (taxes - vat_taxes):
            raise UserError(_(
                "Order line '%(line)s' carries taxes VRP2 cannot express: a "
                "receipt item has exactly one percentage VAT rate.",
                line=line.full_product_name or line.product_id.display_name,
            ))
        rate = vrp2_round4((vat_taxes.amount or 0.0) / 100.0)
        allowed = {
            vrp2_round4(entry.get("vatRate") or 0.0)
            for entry in line.order_id.company_id._vrp2_vatlist()
        }
        if allowed and rate not in allowed:
            raise UserError(_(
                "Order line '%(line)s' has VAT %(rate)s %%, which is not a "
                "VRP2 VAT rate (%(allowed)s).",
                line=line.full_product_name or line.product_id.display_name,
                rate=rate * 100,
                allowed=", ".join(
                    "%g %%" % (r * 100) for r in sorted(allowed)
                ),
            ))
        if vat_taxes:
            unit = vat_taxes.compute_all(
                line.price_unit,
                currency=line.order_id.currency_id,
                quantity=1.0,
                product=line.product_id,
            )["total_included"]
        else:
            unit = line.price_unit
        unit = vrp2_round4(unit)
        discount = vrp2_round4((line.discount or 0.0) / 100.0 * unit)
        quantity = abs(line.qty)
        total = vrp2_round2((unit - discount) * quantity)
        return {
            "unit": unit,
            "discount": discount,
            "quantity": quantity,
            "rate": rate,
            "total": total,
        }

    def _vrp2_item(self, line):
        """One receipt item plus its signed line total."""
        figures = self._vrp2_line_figures(line)
        if line.qty > 0:
            code = line.product_id.product_tmpl_id.vrp2_code
            if not code:
                raise UserError(_(
                    "Product '%(product)s' is not in this till's VRP2 "
                    "catalogue (it has no VRP2 service code). Push the "
                    "catalogue to VRP2 first.",
                    product=line.product_id.display_name,
                ))
            # Sale capture 2026-10-06: a POSITIVE item names its service by
            # code only; VRP2 prints the catalogue name.
            item = {
                "priceWithVat": figures["unit"],
                "discount": figures["discount"],
                "quantity": figures["quantity"],
                "type": "POSITIVE",
                "serviceCode": code,
                "vatRate": figures["rate"],
            }
            return item, figures["total"]

        original = line.refunded_orderline_id
        template = line.product_id.product_tmpl_id
        if not original and template.vrp2_returnable_packaging:
            # "vrátené obaly": the web app's parseToAPI keeps the serviceCode
            # for every type but REFUND/CORRECTION and negates the unit price
            # for every type but POSITIVE.
            if not template.vrp2_code:
                raise UserError(_(
                    "Packaging '%(product)s' is not in this till's VRP2 "
                    "catalogue (it has no VRP2 service code). Push the "
                    "catalogue to VRP2 first.",
                    product=line.product_id.display_name,
                ))
            item = {
                "priceWithVat": -figures["unit"],
                "discount": figures["discount"],
                "quantity": figures["quantity"],
                "type": "NEGATIVE",
                "serviceCode": template.vrp2_code,
                "vatRate": figures["rate"],
            }
            return item, -figures["total"]
        if not original:
            raise UserError(_(
                "Line '%(line)s' returns goods without referencing the order "
                "they were sold on. VRP2 accepts a return only against the "
                "original receipt: refund it from that order in the POS. "
                "(Returned deposit packaging is different: mark the product "
                "'VRP2 Returnable Packaging'.)",
                line=line.full_product_name or line.product_id.display_name,
            ))
        original_order = original.order_id
        if (
            original_order.vrp2_state != "fiscalized"
            or not original_order.vrp2_receipt_uuid
        ):
            raise UserError(_(
                "Order %(order)s, which this refund returns goods from, has "
                "no VRP2 receipt to reference. Fiscalize it first.",
                order=original_order.name,
            ))
        if original_order.account_move:
            raise UserError(_(
                "Order %(order)s was invoiced, so VRP2 holds an invoice "
                "payment for it, not a sale. Cancel that payment receipt "
                "rather than returning items against it.",
                order=original_order.name,
            ))
        # Storno capture 2026-10-06: a REFUND item carries no serviceCode but
        # the name VRP2 printed on the original receipt, verbatim (trailing
        # space included), and the original receiptId.
        item = {
            "priceWithVat": -figures["unit"],
            "discount": figures["discount"],
            "quantity": figures["quantity"],
            "type": "REFUND",
            "vatRate": figures["rate"],
            "referenceReceiptId": original_order.vrp2_receipt_uuid,
            "receiptItemName": original.vrp2_item_name
            or original.product_id.product_tmpl_id.name,
        }
        return item, -figures["total"]

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------

    def _vrp2_payment_split(self):
        """(non-cash payments by VRP2 type, has_cash) of this order.

        Change handed back (``is_change``) belongs to the cash payment and
        is netted into it, so it is not a payment of its own here.
        """
        self.ensure_one()
        non_cash = {}
        has_cash = False
        for payment in self.payment_ids:
            vrp2_type = payment.payment_method_id.vrp2_payment_type
            if not vrp2_type:
                raise UserError(_(
                    "Payment method '%(method)s' has no VRP2 payment type. A "
                    "sale settled on a customer account is not a cash-"
                    "register sale; set the type on the payment method if it "
                    "is one.",
                    method=payment.payment_method_id.display_name,
                ))
            if vrp2_type == "CASH":
                has_cash = True
                continue
            non_cash[vrp2_type] = non_cash.get(vrp2_type, 0.0) + payment.amount
        return non_cash, has_cash

    @staticmethod
    def _vrp2_payment(vrp2_type, amount, currency):
        amount = vrp2_round2(amount)
        return {
            "type": vrp2_type,
            "sum": amount,
            "currency": currency,
            "exchangeRate": None,
            "amount": amount,
        }

    def _vrp2_build_receipt_dto(self):
        """Build the body for POST /v5/receipt/create/valid.

        Verified against the 2026-10-06 sale + storno capture and the web
        app's receipt builder:

        - ``vatPayer`` / ``version`` come from the register's dashboard;
        - items: see ``_vrp2_item``;
        - only the CASH share is rounded to 0.05 €: ``rounding =
          zaokruhli5(total − non-cash) − (total − non-cash)``, the top-level
          ``priceWithVat`` is ``total + rounding`` and VRP2 derives the printed
          ZAOKRÚHLENIE from it (the request carries no ``roundingAmount``);
        - a negative total is settled by one ``EXPENSE`` payment, and a
          receipt containing refund items is never rounded
          (``VYPNUTIE_ZAOKRUHLOVANIA_ZAPOR``) — hence the storno's −18.48
          against the sale's 18.50.

        The receipt total is computed the way VRP2 computes it, not taken
        from Odoo: they can differ by a cent of tax rounding, and a non-cash
        payment is then aligned to the receipt so that it balances.
        """
        self.ensure_one()
        till = self.config_id
        currency = self.currency_id.name or "EUR"
        header = till._vrp2_valid_receipt_header()

        items = []
        total = 0.0
        # The web app never rounds a negative receipt that holds a NEGATIVE,
        # REFUND or CORRECTION item (nezaokruhliZaporne).
        has_negative_item = False
        lines = self._vrp2_fiscal_lines()
        if not lines:
            raise UserError(_("Order %s has no lines to fiscalize.") % self.name)
        for line in lines:
            item, line_total = self._vrp2_item(line)
            items.append(item)
            total += line_total
            has_negative_item = has_negative_item or item["type"] in (
                "NEGATIVE", "REFUND", "CORRECTION",
            )
        total = vrp2_round2(total)

        use_rounding = bool(till.vrp2_round_5c)
        if total < 0 and has_negative_item:
            use_rounding = False

        if total < 0:
            price_with_vat = total
            payments = [self._vrp2_payment("EXPENSE", total, currency)]
        else:
            non_cash, has_cash = self._vrp2_payment_split()
            non_cash_total = vrp2_round2(sum(non_cash.values()))
            if has_cash:
                cash_due = vrp2_round2(total - non_cash_total)
                if cash_due < 0:
                    raise UserError(_(
                        "Order %(order)s was paid more by non-cash means "
                        "(%(non_cash)s) than it costs (%(total)s) and also in "
                        "cash; that cannot be put on a receipt.",
                        order=self.name, non_cash=non_cash_total, total=total,
                    ))
                cash = vrp2_round5(cash_due) if use_rounding else cash_due
                price_with_vat = vrp2_round2(total + cash - cash_due)
            else:
                cash = 0.0
                price_with_vat = total
            payments = []
            gap = vrp2_round2(price_with_vat - cash - non_cash_total)
            if gap and non_cash:
                if abs(gap) > 0.05:
                    raise UserError(_(
                        "Order %(order)s was paid %(paid)s but its VRP2 "
                        "receipt totals %(total)s; the difference is too "
                        "large to be tax rounding.",
                        order=self.name,
                        paid=non_cash_total + cash,
                        total=price_with_vat,
                    ))
                largest = max(non_cash, key=lambda k: abs(non_cash[k]))
                non_cash[largest] += gap
            for vrp2_type, amount in non_cash.items():
                if vrp2_round2(amount):
                    payments.append(
                        self._vrp2_payment(vrp2_type, amount, currency)
                    )
            if cash:
                payments.append(self._vrp2_payment("CASH", cash, currency))

        return _js_numbers({
            "vatPayer": header["vatPayer"],
            "items": items,
            "payments": payments,
            "priceWithVat": price_with_vat,
            "version": header["version"],
            "useRounding": use_rounding,
        })

    def _vrp2_build_invoice_dto(self):
        """Build the body for POST /v5/receipt/create/invoice.

        An invoiced POS order is an invoice paid at the till, so it is
        fiscalized as "Úhrada faktúry", exactly like
        ``l10n_sk_vrp2_account`` does for a back-office invoice (verified
        2026-06-18): exact ``priceWithVat``, CASH rounded to 0.05 €, the
        difference in ``roundingAmount``, ``version`` = the clock.
        """
        self.ensure_one()
        if self.amount_total < 0:
            raise UserError(_(
                "Order %s is an invoiced refund. A credit note is not "
                "fiscalized as an invoice payment; cancel the original "
                "payment receipt instead.",
            ) % self.name)
        till = self.config_id
        currency = self.currency_id.name or "EUR"
        total = vrp2_round2(self.amount_total)
        use_rounding = bool(till.vrp2_round_5c)
        non_cash, has_cash = self._vrp2_payment_split()
        non_cash_total = vrp2_round2(sum(non_cash.values()))
        payments = [
            self._vrp2_payment(vrp2_type, amount, currency)
            for vrp2_type, amount in non_cash.items()
            if vrp2_round2(amount)
        ]
        paid = non_cash_total
        if has_cash:
            cash_due = vrp2_round2(total - non_cash_total)
            if cash_due < 0:
                raise UserError(_(
                    "Order %(order)s was paid more by non-cash means than it "
                    "costs and also in cash; that cannot be put on a receipt.",
                    order=self.name,
                ))
            cash = vrp2_round5(cash_due) if use_rounding else cash_due
            if cash:
                payments.append(self._vrp2_payment("CASH", cash, currency))
            paid += cash
        return _js_numbers({
            "version": int(time.time() * 1000),
            "priceWithVat": total,
            "payments": payments,
            "invoiceNumber": self.account_move.name or "",
            "roundingAmount": vrp2_round2(paid - total),
            "useRounding": use_rounding,
        })

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    @staticmethod
    def _vrp2_decode_receipt_data(data_b64):
        """Decode dataBase64 into the receipt dto, or {} when unreadable."""
        if not data_b64:
            return {}
        try:
            decoded = json.loads(base64.b64decode(data_b64))
        except (ValueError, TypeError):
            return {}
        return (decoded or {}).get("dto") or {}

    def _vrp2_apply_response(self, response):
        """Store the VRP2 create response on the order.

        Response mapping follows the verified captures: ``receiptNumber`` /
        ``receiptId`` / ``id`` / ``okp``, the official ``pdfBase64`` and the
        ``dataBase64`` receipt dump. The item names VRP2 printed are copied
        from that dump onto the order lines, because a later refund must
        repeat them verbatim.
        """
        self.ensure_one()
        data = response or {}

        number = data.get("receiptNumber")
        receipt_uuid = data.get("receiptId")
        server_id = data.get("id")

        created = fields.Datetime.now()
        created_ms = data.get("createDate") or data.get("issueDate")
        if created_ms:
            created = fields.Datetime.to_string(
                datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc)
            )

        vals = {
            "vrp2_state": "fiscalized",
            "vrp2_receipt_number": str(number) if number not in (None, "") else (
                receipt_uuid or False
            ),
            "vrp2_server_id": str(server_id) if server_id else False,
            "vrp2_receipt_uuid": receipt_uuid or False,
            "vrp2_okp": data.get("okp"),
            "vrp2_qr_content": data.get("dataBase64"),
            "vrp2_created": created,
            "vrp2_error_message": False,
        }

        pdf_b64 = data.get("pdfBase64")
        if pdf_b64:
            vals["vrp2_pdf"] = pdf_b64
            vals["vrp2_pdf_filename"] = "VRP2-%s.pdf" % (
                number or receipt_uuid or self.id
            )

        slim = {k: v for k, v in data.items() if k not in ("pdfBase64",)}
        vals["vrp2_response_json"] = json.dumps(slim, ensure_ascii=False, indent=2)

        self.write(vals)
        if not self.account_move:
            self._vrp2_store_item_names(data.get("dataBase64"))

    def _vrp2_store_item_names(self, data_b64):
        """Copy each item's printed name onto the order line it came from.

        VRP2 returns the items in request order, so they pair with
        ``_vrp2_fiscal_lines`` by position. A catalogue item is named by
        ``service.name``, a refund item by ``itemName``.
        """
        items = self._vrp2_decode_receipt_data(data_b64).get("items") or []
        lines = self._vrp2_fiscal_lines()
        if len(items) != len(lines):
            if items:
                _logger.warning(
                    "VRP2 receipt %s has %d items for %d lines of order %s; "
                    "item names not stored.",
                    self.vrp2_receipt_number, len(items), len(lines), self.name,
                )
            return
        for line, item in zip(lines, items):
            name = (item.get("service") or {}).get("name") or item.get(
                "itemName"
            )
            if name:
                line.vrp2_item_name = name


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    vrp2_item_name = fields.Char(
        string="VRP2 Item Name",
        readonly=True,
        copy=False,
        help="The name VRP2 printed for this line on the fiscal receipt. A "
        "refund of the line must repeat it verbatim.",
    )
