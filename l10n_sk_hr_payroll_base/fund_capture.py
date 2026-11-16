# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Engine-neutral parts of recording the fund bases a payslip used.

Both payroll engines record during their own calculation; what they share is
here: the in-process capability that marks a calculation as recording, and
the finalisation that turns rule emissions into stored rows. Nothing here
recomputes a premium. Each engine bridge owns its capture hooks, its rule
emissions and the stored JSON field.
"""

from decimal import Decimal

from .fund_assessment import fund_assessment, index_assessments
from .fund_codes import SOCIAL_FUNDS

#: Rule codes that charge a fund; a computed one without a record is missing.
FUND_RULE_CODES = frozenset(SOCIAL_FUNDS) | {"HEALTH", "HEALTHEMPLOYER"}

#: Context key carrying the capability; JSON/RPC cannot construct its value.
CAPTURE_KEY = "_l10n_sk_fund_capture"

#: Context key allowing the bridge itself to store generated evidence.
WRITER_KEY = "_l10n_sk_fund_evidence_writer"
_WRITER = object()


class _FundCapture:
    """An in-process context capability; JSON/RPC cannot construct this object.

    ``supported`` holds the payslip IDs that may record, ``rows`` the
    finalised rows (or False) per payslip. An engine evaluating rules on a
    dictionary that lives for the whole payslip registers that dictionary in
    ``localdicts`` and collects emissions in ``emissions``.
    """

    def __init__(self, supported):
        self.supported = set(supported)
        self.rows = {}
        self.localdicts = {}
        self.emissions = {}


def writer_context():
    """The context under which the bridge may write generated evidence."""
    return {WRITER_KEY: _WRITER}


def may_write_evidence(context):
    return context.get(WRITER_KEY) is _WRITER


def normalize_record(record):
    """One emitted record in its stored shape; ValueError when unusable."""
    return next(iter(index_assessments([record]).values()))


def finalize_fund_rows(entries, *, compare_amounts, topup=None, fund_codes=None):
    """Turn rule emissions into stored rows, or False when any is unusable.

    ``entries`` is an iterable of ``(code, record, native_total)`` in the
    order the rules were evaluated: ``record`` is the rule's emission (None
    when it emitted nothing) and ``native_total`` the signed total of the
    payslip line it produced (None when there is no line). The rule's
    emission retains the sign by side: an employee charge is stored positive
    against a negative line.

    A fund rule without a record, a record without a line, a record whose
    charge differs from the native line, an invalid record, and a second
    record for the same fund and side all make the payslip unrecorded.
    ``topup`` is the native total of the engine's separate health minimum
    rule (OCA ``HEALTHDOPLATOK``, Enterprise ``HEALTH_DOPLATOK``) when it was
    computed; it adds a charge to the employee health row, not a base.
    """
    codes = FUND_RULE_CODES if fund_codes is None else fund_codes
    records, missing = {}, False
    for code, record, native_total in entries:
        if record is None:
            if code in codes:
                missing = True
            continue
        try:
            normalized = normalize_record(record)
        except ValueError:
            missing = True
            continue
        if native_total is None:
            missing = True
            continue
        native_charge = native_total
        if normalized["side"] == "employee":
            native_charge = -native_charge
        if compare_amounts(float(normalized["amount"]), native_charge):
            # A customised rate/quantity can invalidate the optional metadata
            # while the native calculation remains valid.
            missing = True
            continue
        key = normalized["fund"], normalized["side"]
        if key in records:
            missing = True
        records[key] = normalized
    if not records or missing:
        return False
    employee = records.get(("health", "employee"))
    if employee and topup is not None:
        topup = -topup
        records[("health", "employee")] = fund_assessment(
            fund="health",
            side="employee",
            base=employee["base"],
            rate=employee["rate"],
            amount=Decimal(employee["amount"]) + Decimal(str(topup)),
            facts=dict(employee["facts"], topup=topup),
        )
    return list(records.values())
