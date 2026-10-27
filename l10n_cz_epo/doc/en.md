---
title: CZ EPO — Check and File with Finanční správa
summary: Signs Czech statutory filings with the company's qualified certificate and sends them to EPO — in test mode to check them, or for real to file them — and follows each filing to acceptance or rejection.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

**EPO** (*Elektronická podání pro Finanční správu*) is the Czech tax
administration's electronic filing gateway, behind the MOJE daně portal. Besides
its web forms and the data box, it has an interface for accounting software,
the *Podatelna EPO*. That interface has no user accounts or API keys: a filing
is the XML wrapped in a signature made with the filer's **qualified
certificate**, and the signature is the identity.

This module adds EPO as a **channel** to the submission records of
[module:l10n_cssk_submission_base](module:l10n_cssk_submission_base). Any
statement that can be filed through that framework can then be:

- **checked** — signed and sent in EPO's test mode, which runs EPO's checks
  (signature, structure, content) and files nothing;
- **filed** — signed and sent for real, if the company allows it;
- **followed** — the *potvrzení* (receipt) and *podací číslo* (filing number)
  are kept, and EPO is asked periodically whether the tax office accepted or
  rejected the filing.

The Czech statements that produce an EPO file, and so can go through this
channel, are among others:

| Filing | Module |
|---|---|
| VAT return (DPHDP3) | [module:l10n_cz_vat_return](module:l10n_cz_vat_return) |
| VAT control statement (DPHKH1) | [module:l10n_cz_kh](module:l10n_cz_kh) |
| EC sales list (DPHSHV) | [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) |
| OSS return (OSSEI1) | [module:l10n_cz_oss](module:l10n_cz_oss) |
| corporate income tax return | [module:l10n_cz_dppo](module:l10n_cz_dppo) |
| annual employer's statement of wage tax | [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) |

The channel signs and sends whatever file the statement exported; it does not
check that the file is an EPO form.

## Legal background {#legal}

Under the Tax Procedure Code, [§ 71 odst. 1 of Act No. 280/2009 Sb.](law:cz/2009/280),
a filing can be made electronically only as a data message signed in a way
that has the effect of a handwritten signature, sent from the filer's data box
or with another verified identity. A taxpayer with a data box set up by law,
or with a duty to have its financial statements audited, must make form
filings — tax returns among them — electronically
([§ 72 odst. 6](law:cz/2009/280)). A filing sent to the tax administration's
technical equipment is made on the day it arrives, and the equipment confirms
receipt with the time it was received ([§ 73 odst. 1 and 3](law:cz/2009/280)).
This module uses the first route: the signed data message.

## Setting it up {#setup}

Everything below is visible only to users in the group **Statutory
submissions: file**.

1. **The certificate.** *Accounting → Configuration → Accounting → EPO
   certificates*, then *New*. Upload the qualified certificate **with its
   private key** as a `.p12` / `.pfx` file, as issued by the certification
   authority (I.CA, PostSignum, eIdentity), and its password. Include the
   issuer's intermediate certificates in the file. On saving, the module opens
   the file and shows the subject, issuer and validity; a file that cannot be
   opened is refused.
2. **The company.** *Settings → Users & Companies → Companies*, the company,
   page **EPO podání**, group **Sending to EPO**:

| Field | Purpose |
|---|---|
| EPO signing certificate | The certificate the company's filings are signed with. |
| Allow filing through EPO | Off (default): EPO is used only to **check** filings. On: a queued EPO submission is **filed for real**. |

The rest of the EPO podání page (the signatory, the preparer, a representative)
belongs to the Czech statutory forms and is described with them.

Whoever holds the certificate can file in the company's name, so the
certificate file and password can be read or changed only by the filing group.
Other accounting users see that a certificate exists, not its contents.

## Checking and filing {#usage}

The statement itself — a VAT return, say — is prepared and exported as usual.
Then:

1. On the statement, **File it** (*Podat* where the statement is translated).
   With more than one channel installed, Odoo shows the statement's
   submissions instead of creating one; create one with the channel **EPO — Finanční správa (signed,
   direct)**. The channel is offered only when the company's fiscal country is
   Czechia. Marking the statement submitted also opens a submission, on the
   channel *Authority portal — filed by hand*; while it is a draft you can
   switch its channel to EPO instead.
2. **Check with EPO.** The file is signed and sent in test mode. The result is
   stored on the submission, page **EPO check**: *No errors*, *Warnings only*
   or *Errors*, with EPO's list of messages and its answer as an XML
   attachment. A check never files and never changes the submission's state;
   you can repeat it as often as you like.
3. **Queue**, then **Send now** (or wait for the scheduled job, which sends
   queued submissions every five minutes). This files for real and is refused
   unless *Allow filing through EPO* is on. The signed file is kept on the
   submission. EPO answers with:
   - a **potvrzení** — kept under **Receipts**, and its *podací číslo* becomes
     the submission's *Authority reference*; the submission is *Delivered*;
   - for a large filing processed off-line, an *ID předání* — the submission is
     *Delivered* and the potvrzení is fetched later;
   - a list of **errors** — the submission *Fails* with EPO's messages, and a
     to-do activity is scheduled for the user who created the submission.
4. **Acceptance.** An hourly job asks EPO for the state of every delivered
   EPO filing until the tax office has **accepted** or **rejected** it, and sets
   the submission to *Accepted* or *Rejected*.
5. Once EPO has taken the filing, a statement still at *Exported* is marked
   **submitted** automatically — its filed copy is frozen — and the podací
   číslo is copied to its *Submission reference*.

*Delivered* means EPO received the filing; only *Accepted* means the tax office
took it. The submission form says so while a filing is delivered.

## What happens when something goes wrong {#errors}

- **EPO could not be reached** (the connection was never established): the
  submission goes back to the queue and is retried after 1, 5, 15, 60 and
  180 minutes, then fails.
- **The outcome is unknown** — the request may have reached EPO but no proper
  answer came back: the submission **fails and is not retried**, because sending
  it again could file the return twice. Check the filing on the MOJE daně portal
  before you send anything again. The same applies to any unexpected error,
  including one while recording EPO's potvrzení after it has filed: the
  submission fails with the podací číslo in the message and a warning not to
  send it again.
- **The certificate has expired** or is not yet valid: the module refuses to
  sign.

## Limitations {#limitations}

- EPO's checks are a subset of the tax office's. A clean check is not a
  guarantee that the filing will be accepted; the module repeats that warning.
- The handling of the live service's answers is implemented from EPO's
  published interface description and has not been confirmed against the live
  service from this code base.
- The module checks the certificate's validity dates, not that it is a
  qualified certificate; EPO checks that.
- EPO returns no PDF of the filing.
