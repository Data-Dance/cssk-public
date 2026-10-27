---
title: CZ/SK Statutory Submissions
summary: A record of how each statutory filing reached the authority — channel, attempts, delivery, acceptance — and a place to keep the receipts that prove it.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Exporting a VAT return or a control statement and marking it submitted (see
[the filing life cycle](module:l10n_cssk_core#filings)) freezes the XML that
was filed. It does not record **how** it got to the tax administration,
whether it arrived, or what came back. This module adds that: a
**submission** record per delivery of a filing, with its state, its attempts
and the **receipts** — the *potvrdenka* / *potvrzení o podání* and the
*doručenka* — kept in Odoo rather than in someone's mailbox.

It is a framework. On its own it offers one channel, a filing made **by hand
on the portal** and attested in Odoo. Electronic channels come from other
modules — for example [module:l10n_cz_epo](module:l10n_cz_epo) files Czech
returns directly to the EPO of the Czech Financial Administration. The
statutory forms of the localization install it themselves.

## Delivered is not accepted {#states}

| State | Meaning |
|---|---|
| Draft | prepared, not sent |
| Queued | waiting to be sent, or waiting for the next retry |
| Sending | an attempt is in progress |
| **Delivered** | the **channel** confirmed it took the filing — the transport worked |
| **Accepted** | the **authority** accepted the filing — it counts |
| Rejected | the authority refused it |
| Failed | it could not be sent; retrying will not help, or the attempts ran out |
| Cancelled | withdrawn before it reached the authority |

A channel that cannot see the authority's answer stops at *Delivered*, and the
form says so: *"The channel confirmed it took this filing. Acceptance by the
authority is a separate step and has not been recorded yet."*

## Who may do what {#access}

Two groups under *Accounting* in the user settings:

- **Statutory submissions: prepare** — sees submissions and their receipts.
- **Statutory submissions: file** — also queues, sends, attests and cancels
  them. Includes the accounting administrator rights.

## Filing a return {#usage}

1. On the filing, *Mark Submitted*. A submission in **Draft** is opened
   automatically, pointing at the filed XML, so the filing has somewhere for
   its receipts to go.
2. Alternatively, *File it* on an exported or submitted filing opens a new
   submission; if more than one channel can file it, you choose the channel.
   Only channels that can file for the filing's company are offered — EPO,
   for example, only for a Czech company.
3. **Filed by hand** (channel *Authority portal — filed by hand*): file the
   XML on the authority's portal yourself — the Slovak PFS, the Czech EPO or
   the data box — then click **Attest filing**. Odoo records who attested and
   when, and the submission becomes *Delivered*.
4. **Electronic channel**: click **Queue**. The submission is sent within a few
   minutes, or immediately with **Send now**.
5. Attach the receipts on the **Receipts** tab and enter the authority's
   reference (*podacie číslo*, *číslo podání*) in **Authority reference**.
6. **Filed by hand, accepted**: once you hold the authority's confirmation,
   attach it on the **Receipts** tab and click **Attest acceptance**. The
   submission becomes *Accepted*. The button refuses while no receipt is
   attached: the confirmation is the evidence.

**The submission and the filing stay in step:**

- A submission that has not been sent yet always carries the filing's
  **current** export. If you reset the filing, recompute it and export again,
  the submission picks up the new XML (and says so in its chatter) the next
  time it is validated, queued or attested. One already queued is **not**
  sent if the filing was reset or exported again in the meantime: it fails
  with a message to queue it anew.
- When a submission reaches the authority — a channel delivers it, or you
  attest a manual filing — a filing still at *Exported* is **marked
  submitted** (its filed copy is frozen) and the authority's reference is
  copied to its *Submission reference*.

All submissions are listed under *Accounting → Reporting → Statutory Reports
→ Submissions*, filtered to those not yet accepted; *Needs attention* shows the
failed and rejected ones. The filing form shows the state of its current
submission as a badge.

## Retries and failures {#retries}

Two scheduled actions run in the background:

- *Statutory submissions: send queued* — every 5 minutes, sends what is due;
- *Statutory submissions: poll for acceptance* — every hour, asks channels
  that can tell whether delivered filings were accepted.

A temporary error the channel recognises (the gateway is down, the connection
could not be made) puts the submission back in the queue and retries after 1,
5, 15, 60 and 180 minutes. After that, or at once for an error retrying cannot
fix (wrong data, missing certificate), the submission becomes **Failed**, the
error is shown on the form, and a to-do activity is created for the person who
opened it — on the filing itself where possible. Fix the cause and *Queue*
again.

An **unexpected** error is not retried: it may have happened after the filing
reached the authority, and sending it again would file the return twice. The
submission fails with *"the outcome is unknown … check its portal before
sending it again"*. Check the portal first; queue it again only if the filing
is not there.

A submission that is *Delivered* or *Accepted* cannot be cancelled: file a
correction instead.

## Limitations {#limitations}

- The submission does not check the filing deadline.
- *Attest acceptance* records what a person says, backed by the attached
  confirmation; nothing checks the attachment's content.
