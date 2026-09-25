==================================================
CZ/SK Partner Balance Confirmation (Saldokonto)
==================================================

Slovak/Czech **saldokonto** — *odsúhlasenie / potvrdenie zostatkov pohľadávok a
záväzkov*. A stored document that snapshots a partner's open AR/AP as of a date,
tracks a state machine (draft → sent → agreed / disputed) and prints a PDF for
countersigning.

Depends on Odoo core only (``account`` + ``mail``). Complements OCA
``partner_statement`` (aging view) with the signable confirmation document.

Features
========

Saldokonto (balance confirmation)
---------------------------------

* ``cssk.partner.confirmation`` + lines — snapshot of open AR/AP, totals,
  state machine, sequence-numbered (``SALDO/YYYY/NNNN``), chatter, PDF.
* Bulk wizard — issue for every partner with an open balance.
* Disputed lines ``blocked`` (excluded from totals, shown on the PDF).

Mutual offsetting (zápočet)
---------------------------

* ``cssk.partner.netting.agreement`` + picker wizard — auto-allocates a
  partner's open AR against AP up to ``min(receivables, payables)``.
* Posting builds a **clearing journal entry** and reconciles the offset
  invoices (partial offsetting supported); ``ZAP/YYYY/NNNN`` sequence;
  *cancel with reversal* undoes a posted agreement.
* **Bilateral** mode (``dohoda``) requires countersignature before posting;
  **unilateral** mode (``jednostranné započítanie``) posts on delivery without
  countersignature, for claims that meet the legal set-off conditions.

Status
======

**Functional.** Saldokonto (snapshot, totals, blocked lines, state machine,
bulk wizard, bilingual SK/EN PDF) and the zápočet agreement (auto-allocation,
clearing entry + reconciliation, both legal modes, cancel-with-reversal) are
tested, including a bilingual SK/EN PDF whose wording switches between the
bilateral *agreement* (two signatures) and the unilateral *set-off notice*
(§ 358 Obchodného zákonníka, single signature, effective on delivery).

Why not OCA ``account_netting``? That module is a single wizard that posts one
compensating journal item — no agreement document, state machine, sequence,
reconciliation tracking or the bilateral/unilateral legal workflow a zápočet
needs. It automates only the journal-entry step, which is the small part.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
