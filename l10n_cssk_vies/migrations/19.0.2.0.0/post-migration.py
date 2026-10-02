# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Move the VIES proof stored on the partner into the per-company check log.

Up to 19.0.1.x the consultation number and the rest lived in plain partner
columns, overwritten by whichever company checked last. The fields are now
computed from ``cssk.vies.check``, so each stored proof becomes one log row.

Which company made a stored check was never recorded. With a single company
it can only have been that one; otherwise the row is left without a company
and serves every company as a legacy check until each checks for itself.

The old columns are left in place, not dropped: they are the source of this
migration and cost nothing to keep.
"""
import logging

_logger = logging.getLogger(__name__)

_COLUMNS = (
    "vies_consultation_number", "vies_check_date", "vies_fault_date",
    "vies_request_date", "vies_trader_name", "vies_address", "vies_name_match",
)


def _existing_columns(cr):
    cr.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'res_partner' AND column_name = ANY(%s)",
        [list(_COLUMNS)],
    )
    return {row[0] for row in cr.fetchall()}


def migrate(cr, version):
    if not version:
        return
    present = _existing_columns(cr)
    if "vies_check_date" not in present:
        return
    cr.execute("SELECT id FROM res_company")
    companies = [row[0] for row in cr.fetchall()]
    company_id = companies[0] if len(companies) == 1 else None

    def col(name):
        return name if name in present else "NULL"

    # One row per answered check. vies_valid (core base_vat) says whether the
    # answer was yes; the proof columns were cleared on a "no".
    cr.execute(f"""
        INSERT INTO cssk_vies_check (
            partner_id, company_id, vat, check_date, result,
            consultation_number, request_date, trader_name, address,
            name_match, create_uid, write_uid, create_date, write_date
        )
        SELECT p.id, %s, p.vat, p.vies_check_date,
               CASE WHEN COALESCE({col('vies_consultation_number')}, '') <> ''
                         OR p.vies_valid THEN 'valid' ELSE 'invalid' END,
               NULLIF({col('vies_consultation_number')}, ''),
               {col('vies_request_date')},
               NULLIF({col('vies_trader_name')}, ''),
               NULLIF({col('vies_address')}, ''),
               NULLIF({col('vies_name_match')}, ''),
               1, 1, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC'
          FROM res_partner p
         WHERE p.vies_check_date IS NOT NULL
    """, [company_id])
    answered = cr.rowcount
    faults = 0
    if "vies_fault_date" in present:
        cr.execute("""
            INSERT INTO cssk_vies_check (
                partner_id, company_id, vat, check_date, result, fault_reason,
                create_uid, write_uid, create_date, write_date
            )
            SELECT p.id, %s, p.vat, p.vies_fault_date, 'fault',
                   'migrated from the partner',
                   1, 1, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC'
              FROM res_partner p
             WHERE p.vies_fault_date IS NOT NULL
        """, [company_id])
        faults = cr.rowcount
    _logger.info(
        "l10n_cssk_vies: %s VIES check(s) and %s fault(s) moved to the check "
        "log (company %s)", answered, faults,
        company_id or "not recorded — shared legacy rows",
    )
