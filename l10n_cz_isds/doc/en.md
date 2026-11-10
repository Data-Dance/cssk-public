---
title: CZ Data Box (ISDS)
summary: Signs in to the company's Czech data box through the operator's web services, so that filing channels can send data messages from it and read the answers that come back.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

A Czech company has a **data box** (*datová schránka*, ISDS), the state's
channel for official messages. Many authorities accept filings sent from it:
the message itself identifies the sender, so no electronic signature is
needed.

This module connects Odoo to the company's data box through the operator's
web services (WSDL/XSD version 3.11). It holds the login and offers **Test
Connection**; the filing channels built on it send the messages and read the
answers. By itself it sends nothing. The channel for the ČSSZ's JMHZ filings
is the first to use it.

## Legal background {#legal}

A filing a company makes through its data box has the same effect as a
written, signed one ([§ 18 odst. 2 of Act No. 300/2008 Sb.](law:cz/2008/300)).
That is why a data-box filing needs no qualified certificate.

## Setting it up {#setup}

Visible only to users in the group **Statutory submissions: file**.

1. Choose how Odoo signs in:
   - **Login and password** — create a data box **user** for Odoo with the
     right to send and read messages. A dedicated user is better than
     someone's personal login: it can be withdrawn on its own, and its
     password does not change when a person leaves.
   - **Login, password and certificate** — the same user, whose login also
     requires a commercial certificate assigned to it in the data box.
   - **System certificate** (recommended for a server) — the box's
     administrator registers a **commercial certificate** on the box for an
     external application, in the data box's settings. Odoo then signs in
     with the certificate alone: no password to expire or to change when
     someone leaves.

   A certificate must come from a certification authority the operator
   recognises (PostSignum, I.CA, eIdentity); the operator's servers refuse
   any other already in the secure connection.
2. *Settings → Users & Companies → Companies*, the company, page **Data box**
   (shown for Czech companies):

| Field | Purpose |
|---|---|
| Data box environment | *Test* (default): the operator's test environment (datovka-test.gov.cz), with test boxes and no legal effect. *Production*: the company's real box (datovka.gov.cz). |
| Data box sign-in | *Login and password*, *Login, password and certificate* or *System certificate (no password)*. |
| Data box login, password | The data box user Odoo signs in as (not used with a system certificate). |
| Data box certificate, password | The commercial certificate with its private key (`.p12` / `.pfx`), for the two certificate sign-ins. On saving, the module opens it and shows its subject and expiry; a file it cannot open is refused. |
| Data box ID, owner | Filled in by **Test Connection**. |

3. **Test Connection** signs in and shows whose box the login opens. It sends
   nothing.

The login and the certificate open the box for whoever holds them, so the
password and the certificate can be read or changed only by the filing group.
For each call, the certificate's key is loaded into the secure connection
from a temporary file encrypted with a one-time password and deleted before
anything is sent.

## Limitations {#limitations}

- A login secured by a one-time code (SMS, Mobilní klíč) cannot be used by
  software; use a system certificate instead. The operator's access for
  hosted records systems is not supported.
- Only what filing needs: sending a message, listing received messages and
  downloading one. Messages are not shown in Odoo as a mailbox, and nothing is
  marked as read.
- Built from the operator's published WSDL and XSD (every request is checked
  against them by the tests); not yet tried against a live data box.
