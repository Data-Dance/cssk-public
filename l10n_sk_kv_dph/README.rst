==========================================
Slovakia — Kontrolný výkaz DPH (KV DPH)
==========================================

The Slovak **VAT control statement** (kontrolný výkaz DPH) built on the shared
``l10n_cssk_kv_kh_base`` framework. It classifies every taxable line into the
statutory sections **A.1, A.2, B.1, B.2, B.3.1/B.3.2, C.1, C.2, D.1 and D.2** and
exports the official Finančná správa ``KVDPH`` XML.

It reads VAT data straight from ``account.move.line`` tax tags — it does **not**
depend on ``account_reports`` — so it runs on both Community and Enterprise, on
Odoo 18.0 and 19.0.

Features
========

* Line-level section resolver: reverse charge first, then domestic supplies,
  simplified invoices (B.3) and corrections (C.1/C.2).
* Section **B.1** follows the official *KVDPHv17 poučenie*: received supplies on
  which the recipient is liable under § 69 ods. 2, 3, 6, 7, 9–12 — including
  self-assessed foreign services (§ 69 ods. 2 / § 15 ods. 1) and intra-EU goods
  acquisitions (§ 11) — carrying the **gross** self-assessed tax (base × rate).
* B.3 simplified-invoice threshold split (B.3.1 below / B.3.2 above the period
  limit) and the D.2 basic/reduced rate-band split.
* ``KVDPH`` XML export covering all sections, for direct upload to the FS portal.
* Dodatočný (supplementary) control statement support via the shared retention /
  amendment mixin.

Validation
==========

Reconstructed against **24 months of really filed KV DPH** (2024–2025) from a
production MRP dataset: **24/24 periods match** the filed control statement to the
cent, after the § 69 B.1 scope was confirmed with a Slovak accountant against the
official poučenie.

Usage
=====

*Accounting ▸ Reporting ▸ Slovakia ▸ Kontrolný výkaz DPH.* Create a statement for
a period, **Compute** to populate the sections from the period's postings, review
the per-section detail, then **Export XML** for the FS portal. Reverse-charge
purchase taxes must carry the ``cssk_control_is_reverse_charge`` flag, or their
lines will not appear in B.1.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
