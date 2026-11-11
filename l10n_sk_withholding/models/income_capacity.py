# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Read native author-source capacity; never create or alter accounting entries."""

from decimal import Decimal

from odoo.exceptions import UserError


def income_pool_key(move_id, account_id):
    """One bill/account pool, also reconstructible from legacy source snapshots."""
    return f"income:{move_id}:{account_id}"


def income_pool_facts(event, line):
    """Original author sources minus linked posted credits effective by payment.

    A bill may have several payable instalments: allocating separate lines must
    not consume the same reduced bill twice. Do not invent a proportional credit
    allocation to those lines. Other source types retain their reversal policy.
    """
    move = line.move_id
    if (
        event.income_kind != "author"
        or move.move_type not in {"in_invoice", "entry"}
        or move.reversed_entry_id
    ):
        return None
    move.check_access("read")
    original = move.line_ids.filtered(lambda row: row.account_id == line.account_id)
    original.check_access("read")
    if move.move_type == "entry" and any(
        row.balance > 0 or row.partner_id != line.partner_id for row in original
    ):
        # A compound/multiple-recipient journal has no unambiguous common
        # income pool. Preserve its existing per-line/reversal workflow.
        return None
    if any(row.balance > 0 or row.partner_id != line.partner_id for row in original):
        raise UserError(
            event.env._(
                "Review the original author bill's payable lines and recipient before allocating its income."
            )
        )
    capacity = -sum((Decimal(str(row.balance)) for row in original), Decimal(0))
    seen, frontier = move, move
    credit_rows = []
    while frontier:
        children = frontier.reversal_move_ids.filtered(
            lambda row: row.state == "posted"
            and (row.invoice_date or row.date) <= event.paid_on
        )
        if children & seen:
            raise UserError(
                event.env._("Review the cyclic native author-bill reversal links.")
            )
        children.check_access("read")
        if any(child.company_id != move.company_id for child in children):
            raise UserError(
                event.env._(
                    "Every linked author credit must belong to the original bill's company."
                )
            )
        for child in children.sorted("id"):
            expected = {
                "in_invoice": "in_refund",
                "in_refund": "in_invoice",
                "entry": "entry",
            }.get(child.reversed_entry_id.move_type)
            if child.move_type != expected:
                raise UserError(
                    event.env._(
                        "Use matching native invoice or journal reversal links for the remaining author income."
                    )
                )
            rows = child.line_ids.filtered(
                lambda row: row.account_id == line.account_id
            )
            rows.check_access("read")
            sign = 1 if child.move_type == "in_refund" else -1
            if child.move_type == "entry":
                parent_rows = child.reversed_entry_id.line_ids.filtered(
                    lambda row: row.account_id == line.account_id
                )
                parent_rows.check_access("read")
                parent_balance = sum(
                    (Decimal(str(row.balance)) for row in parent_rows), Decimal(0)
                )
                sign = 1 if parent_balance < 0 else -1
            if not rows or any(
                row.partner_id != line.partner_id or row.balance * sign < 0
                for row in rows
            ):
                raise UserError(
                    event.env._(
                        "Review the linked author credit's payable account and recipient before allocating the remaining income."
                    )
                )
            capacity -= sum((Decimal(str(row.balance)) for row in rows), Decimal(0))
            credit_rows.extend(
                {
                    "id": row.id,
                    "move_id": child.id,
                    "parent_id": child.reversed_entry_id.id,
                    "move_type": child.move_type,
                    "balance": row.balance,
                    "date": str(child.date),
                    "invoice_date": str(child.invoice_date)
                    if child.invoice_date
                    else None,
                }
                for row in rows.sorted("id")
            )
        seen |= children
        frontier = children
    return {
        "key": income_pool_key(move.id, line.account_id.id),
        "original_move_id": move.id,
        "account_id": line.account_id.id,
        "capacity": float(capacity),
        "cutoff": str(event.paid_on),
        "original_lines": [
            {"id": row.id, "balance": row.balance} for row in original.sorted("id")
        ],
        "credit_lines": credit_rows,
    }
