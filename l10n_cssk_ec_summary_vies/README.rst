================================
CZ/SK EC Sales List — VIES proof
================================

Glue module that wires the CZ/SK **EC Sales List** (recapitulative statement —
*Súhrnný výkaz* / *Souhrnné hlášení*) to **direct EU VIES** validation. When
both ``l10n_cssk_ec_summary_base`` and ``l10n_cssk_vies`` are installed, this
module makes the EC sales list export perform a **real VIES check** (not merely
a format gate) for companies that use direct EU VIES, and **snapshots** the
official consultation number, the check timestamp and the validity onto each
reported line — so re-opening a filed statement shows exactly what was confirmed.

It ``auto_install``s when its two dependencies are present and adds three
read-only columns to the EC sales list line table.

Features
========

* On export, every reported line's foreign VAT number is verified against the
  EU VIES service via ``res.partner._vies_query_direct`` (only when the company
  has *Use direct EU VIES* enabled).
* A line whose VAT VIES reports as **invalid** is a hard block on export — a
  filing carrying an invalid VAT number is penalised.
* The official **consultation number** (``requestIdentifier``), the **check
  date** and the **validity** are stored on each line, preserving proof of the
  consultation as of the filing date.
* A transient VIES outage does **not** block the statutory filing; the affected
  lines are exported without a fresh confirmation and the gap is logged in the
  statement chatter so the check can be repeated.
* The base presence/format hard-block from ``l10n_cssk_ec_summary_base`` runs
  first and is unchanged.

Usage
=====

*Accounting ▸ Reporting ▸ EC Sales List.* Build and compute a statement as
usual, then export it. If the company uses direct EU VIES, each line is checked
against VIES at export: invalid numbers stop the export, the consultation
number / check date / validity are written to the line, and an unreachable VIES
is logged in the chatter without blocking the filing. Enable *Use direct EU
VIES* under the VIES settings (``l10n_cssk_vies``) for the check to run.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
