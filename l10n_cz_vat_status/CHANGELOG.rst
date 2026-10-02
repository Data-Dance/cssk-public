=========
Changelog
=========

All notable changes to **l10n_cz_vat_status** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.1.0] — 2026-09-29
-------------------------

Fixed
~~~~~

- **A later "VAT period declared" deferred an identifikovaná osoba's
  liability.** ``l10n_cssk_core``'s ``cssk_vat_deduction_date`` moves a
  document onto a later DPHDP3 / KH / SH and, with a deferral account, its VAT
  off 343 until then. On an identifikovaná osoba's self-assessed acquisition
  or foreign service that moved the **liability** (§ 108 odst. 2 with § 25,
  § 108 odst. 3 písm. a) with § 24) out of the period it arose in, which the
  Act does not allow: the date stands for the § 73 deferral of a *deduction*,
  and § 72 odst. 1 gives the deduction to a plátce only. On any document whose
  DUZP (a credit note: the corrected document's) falls in an
  identifikovaná-osoba or neplátce period the date is now ignored — no
  deferral entries, and every filing reports the document where it would with
  the date empty. The form says so in a notice. Plátce documents, and
  companies with no status history, behave exactly as before.

  Ignoring was chosen over refusing the date: the status history can change
  after the document is posted, so a check at entry time could not be the
  rule; imports that carry the date keep posting; and the date stays on
  record in case the status is later corrected.
- **Editing the status history brings the deferral entries along.** A
  document the change moves out of a plátce period has its entries withdrawn
  (cancelled, as ``l10n_cssk_core`` does on reset); one moved into a plátce
  period gets them. Only documents whose answer changed are touched. An entry
  in a locked period cannot be changed: the history is still recorded, the
  document says in its chatter what should have happened, and correcting it
  is left to the accountant. Filings already submitted are not changed —
  that is a dodatečné přiznání, as for any other correction.

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- The company's VAT status history — plátce (§ 6–6f), identifikovaná osoba
  (§ 6g–6l), neplátce — as change points, with a legal basis and event date
  that propose the first day the Act names (§ 6 odst. 1/2, § 6f, § 6g–6l,
  § 106 odst. 8, § 107, § 107b).
- ``res.company._l10n_cz_typ_platce`` answers P / I / N from that history for
  DPHDP3 ``VetaD/typ_platce``; with no history it is still P.
- Documents take the status on their DUZP: a neplátce's and an identifikovaná
  osoba's invoices carry no VAT, input VAT goes to the cost, and an
  identifikovaná osoba self-assesses EU acquisitions and foreign services
  without a deduction (§ 108 odst. 2, § 108 odst. 3 písm. a), § 72 odst. 1).
  Posting a document whose taxes contradict the status is refused.
- No kontrolní hlášení for days the company was not a plátce (§ 101c).
- The invoice PDF of a non-payer is not presented as a daňový doklad and
  carries "Nejsem plátce DPH." (configurable).
- DPHDP3 and KH note in their chatter when the status changes inside the
  period.
