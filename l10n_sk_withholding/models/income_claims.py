# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dated reservations of original author income, independent of record order."""

from decimal import Decimal, ROUND_HALF_UP


def exceeded_income_capacity(current, other_groups, checkpoints=()):
    """Return the first exceeded pool/date, or None.

    Each other group is one replacement chain containing alternative complete
    snapshots. Reserve its greatest cumulative claim at each payment date,
    rather than summing a filed ancestor and its still-working replacement.
    Different chains add up. Each claim supplies its own dated capacity proof.
    """
    pools = sorted({row["key"] for row in current})
    for pool in pools:
        own = [row for row in current if row["key"] == pool]
        groups = [
            [[row for row in variant if row["key"] == pool] for variant in group]
            for group in other_groups
        ]
        rows = own + [row for group in groups for variant in group for row in variant]
        bounds = [row for row in checkpoints if row["key"] == pool]
        for day in sorted({row["paid_on"] for row in rows + bounds}):
            amount = sum(
                (Decimal(str(row["amount"])) for row in own if row["paid_on"] <= day),
                Decimal(0),
            )
            for group in groups:
                amount += max(
                    (
                        sum(
                            (Decimal(str(row["amount"])) for row in variant if row["paid_on"] <= day),
                            Decimal(0),
                        )
                        for variant in group
                    ),
                    default=Decimal(0),
                )
            capacities = [
                Decimal(str(row["capacity"])) for row in rows + bounds
                if row["paid_on"] == day and row.get("capacity") is not None
            ]
            if not capacities:
                # Pre-feature retained facts establish claims, not a missing
                # historical shared capacity. Preserve their original guards.
                continue
            capacity = min(capacities)
            # Currency inputs are already statutory cent amounts. Avoid binary
            # float accumulation changing whether an exact last cent fits.
            if amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) > capacity.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ):
                return {"key": pool, "paid_on": day, "amount": float(amount), "capacity": float(capacity)}
    return None
