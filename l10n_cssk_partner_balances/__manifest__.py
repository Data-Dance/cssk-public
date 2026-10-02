{
    "name": "CZ/SK Partner Balance Confirmation (Saldokonto)",
    "version": "19.0.1.2.0",
    "summary": "Saldokonto / odsúhlasenie (potvrdenie) zostatkov pohľadávok a "
               "záväzkov — a stored, state-tracked confirmation of a partner's "
               "open AR/AP as of a date, with a PDF for countersigning.",
    "description": """
CZ/SK Partner Balance Confirmation (Saldokonto)
===============================================

Slovak/Czech **saldokonto** — *odsúhlasenie / potvrdenie zostatkov pohľadávok a
záväzkov*. A stored document that **snapshots** a partner's open receivables and
payables as of a chosen date (reproducible — re-opening an old confirmation
shows what was sent), tracks a state machine (draft → sent → agreed / disputed),
and prints a PDF for the partner to countersign.

Depends on **Odoo core only** (``account`` + ``mail``). Complements OCA
``partner_statement`` (aging/activity view) — this adds the signable
confirmation document the aging report doesn't.

Provides:

* ``cssk.partner.confirmation`` (mail.thread) + ``cssk.partner.confirmation.line``
  — snapshot of open AR/AP move lines, totals, state machine, PDF.
* A bulk wizard to issue confirmations for all partners with open balances.
* Disputed lines can be ``blocked`` (excluded from totals, still shown on the PDF).

Mutual offsetting (zápočet)
---------------------------

The same module also provides the **mutual-offset agreement**
``cssk.partner.netting.agreement`` (*zápočet*) with its picker wizard:

* Loads a partner's open receivables and payables and **auto-allocates** the
  offset up to the netting amount = ``min(receivables, payables)``.
* On posting, builds a **clearing journal entry** (credit AR / debit AP) and
  **reconciles** the offset invoices (partial offsetting supported); undo via
  *cancel with reversal*. ``ZAP/YYYY/NNNN`` sequence.
* **Two legal modes:**

  * *Bilateral* (``dohoda o vzájomnom započítaní``) — draft → confirmed → sent →
    **countersigned** → posted (both parties sign before it takes effect).
  * *Unilateral* (``jednostranné započítanie``) — draft → confirmed → **sent**
    (delivered) → posted, **no countersignature**: a one-sided declaration of
    set-off that takes legal effect on delivery, permitted for mutual, like-kind,
    due and eligible claims not excluded from set-off.

Both the saldokonto confirmation and the netting agreement print a bilingual
SK/EN PDF; the zápočet PDF switches wording between the bilateral agreement (two
signatures) and the unilateral set-off notice (single signature, effective on
delivery).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence_data.xml",
        "report/cssk_partner_confirmation_report.xml",
        "report/cssk_partner_netting_report.xml",
        "views/cssk_partner_confirmation_views.xml",
        "views/cssk_partner_netting_views.xml",
        "wizard/cssk_partner_confirmation_wizard_views.xml",
        "wizard/cssk_netting_wizard_views.xml",
        "views/cssk_partner_balances_menus.xml",
    ],
    "installable": True,
}
