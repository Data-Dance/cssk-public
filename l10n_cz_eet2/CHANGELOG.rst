=========
Changelog
=========

All notable changes to **l10n_cz_eet2** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Added
~~~~~

- **Automatic certificate renewal** through the CA EET 2.0 API
  (``caeetapi_jwt.yml``; ``lib/caeet_client.py``, no Odoo import). An hourly
  job renews the certificate a company has selected N days before it expires
  (setting *Renew Certificate (days before expiry)*, default 30, 0 = off):
  ``renew`` authorised by a JWT (RS256, ``x5t#S256``) signed with the
  certificate itself, ``status`` polled with the CA's ``pollAfterSeconds`` /
  ``Retry-After``, ``claim-download`` stored as a new certificate record
  linked both ways, a **verification-mode message** sent with the new
  certificate, and only on ``kod 0`` the company switched, ``ack-download``
  sent and the old certificate archived. A failed verification or a CA
  rejection keeps the old certificate in use, leaves the download
  unacknowledged (re-claimable for 30 days) and raises one activity; 429 and
  5xx defer and never fail the cycle. *Renew with CA EET* on the certificate
  starts or pushes the cycle. Hosts are system parameters
  ``l10n_cz_eet2.caeet_url_production`` / ``_playground``; the playground
  default (``ca.zkus``) is a reading of the spec that still has to be confirmed
  against the playground kit.

Fixed
~~~~~

- Nobody could open the EET 2.0 menus after a fresh install: the two EET groups
  were not implied by any accounting group, so even the administrator got an
  Access Error on every EET view (found in a browser check). *Accounting
  Manager* now implies *EET 2.0 Manager* and *Invoicing* implies *EET 2.0 User*.

Added
~~~~~

- **Storno on a reversed payment (§ 8 ZoET).** Resetting a posted payment to
  draft or cancelling it undoes a registered sale; a negative message with the
  same unit, till and sequence number, dated at the reversal, is queued
  (methodology ch. 4: a correction is evidenced when its reason is found). It
  is sent for an accepted sale and for one still queued, which will be sent
  (§ 20); not for a rejected one, which was never evidenced. The sale message
  stays as it is and the gateway keeps both. Re-posting the payment registers
  a new sale. Every message a payment produced is listed behind a stat button;
  the storno and its sale point at each other.
- A fresh ``uuid_zpravy`` and the real ``dat_odesl`` on **every attempt**, the
  Data block unchanged (methodology ch. 6: the repeated sending changes UUID,
  dat_odesl and prvni_zaslani). Earlier UUIDs are kept on the message for
  support.
- ``data/neutralize.sql``: Odoo's database neutralization (``odoo-bin
  neutralize``, Odoo.sh staging copies) switches EET 2.0 off on every company,
  so a copy of production never registers sales with the Financial
  Administration. Settings and queued messages are kept.

Fixed
~~~~~

- Only **customer** money is a tržba: a payment to a supplier from a journal
  flagged *Contact Payments* is no longer registered as a negative sale. A
  customer refund paid out still is (§ 8).
- *Send to EET* on a payment reuses its message instead of creating a second
  one: the old record would have stayed in the queue and both could be
  accepted, evidencing the sale twice (second-opinion review finding).
- A storno goes to the **environment the sale went to**, never to the
  company's current one, and keeps the sale's certificate when the company
  has since moved to the other environment.
- Two partial unique indexes back the Python guards: one storno per sale, one
  live sale per payment. A double click on *Reset to draft* or two posts of
  one payment by two workers now fail the second insert, which is logged,
  instead of evidencing twice.



Review against Act No. 180/2026 Sb. (published October 2026), the data-interface
description v1.2a (2026-10-02), the item-by-item methodology "Popis položek
datové zprávy" (2026-10-15) and the Financial Administration's EET 2.0 Q&A.

Fixed
~~~~~

- **A message is never abandoned.** The scheduled sender used to give up after
  *Max Send Attempts* (about seven hours of backoff) and park the message in
  ``error``, which no later run touched. § 20 ZoET requires sending as soon as
  the cause passes, at the latest within 48 hours of the sale, and the duty
  survives that deadline (FS answer 5570). Retries now keep the exponential
  backoff until 48 hours after ``dat_trzby`` and continue hourly afterwards;
  a message crossing the line is flagged *Past 48 h* and raises one warning
  activity for an EET 2.0 manager. *Max Send Attempts* is now *Warn After
  Attempts*: it logs, it does not stop. A message that could not even be built
  (no, expired or wrong-password certificate) stays in ``error`` for
  visibility but is retried hourly as well, and an unexpected crash inside the
  sender is rolled back to a savepoint and scheduled like any other failure
  instead of re-running every two minutes.
- **Response timestamps were stored in the server's local zone.** ``dat_prij`` /
  ``dat_odmit`` were converted with a bare ``astimezone()`` before the offset
  was dropped, so a host running in Europe/Prague stored them one to two hours
  off. They are converted to UTC now.
- **Foreign-currency sales were sent unconverted.** A till or payment in EUR
  reported the EUR figure as if it were CZK. ``create_from_values`` converts
  ``celk_trzba``, ``urceno_cerp_zuct`` and ``cerp_zuct`` to CZK at the company
  rate of the sale date (FS answer 5012: the total is always in CZK) and keeps
  the original amount and currency on the message for audit.
- Messages that could not be built or were rejected for a bad signature are put
  back in the queue automatically when a certificate is re-uploaded or a new
  one is selected for the company, and a *Requeue* button does the same by hand.
- The *POK* wording of the 19.0.1.0.0 entry below was corrected: EET 2.0 has no
  FIK / BKP / PKP, the gateway returns a POK and nothing else.
- The EET 2.0 *certificate* picker in Settings listed every company's
  certificates: Odoo drops a string domain when it copies a field into a
  related one.

Added
~~~~~

- **Validation before the gateway does it.** The taxpayer EIC must be ``CZ`` +
  8–10 digits (error 6 on every message otherwise) and every evidence-unit
  number (company, journal, point of sale) must have the DIS+ shape, two to
  nine digits ending in 1–4 (warning 6 otherwise). The EIC is pre-filled from
  the company VAT number when that already has the right shape (§ 18 ZoET:
  EIČ = DIČ).
- **Response time limit (mezní doba odezvy, § 19 ZoET)** as a company setting,
  default 5 s, at least 2 s. The synchronous point-of-sale send waits that long
  for the POK; the scheduled sender keeps a longer transport timeout.
- **Test certificate** button: sends a verification-mode message
  (``overeni=true``) signed with the certificate to its environment. The
  gateway validates schema, signature and EIC and answers with code 0 without
  recording a sale, which proves the certificate, its password and the network
  path. The production endpoint accepts such messages from 2026-11-01.
- **Per-payment contact flag** on ``account.payment``: the journal only gives
  the default. The same bank account receives a QR scanned at the counter (a
  contact payment, § 6 ZoET) and the same QR paid from home (not one); the
  cashier decides per payment (FS answers 574, 586, 2532).
- **Certificate expiry warnings**: a daily job raises one activity 30, 14 and
  7 days before a certificate expires (a pokladní certifikát lives 366 days).
  Automated renewal through the CA EET API is noted as a TODO in
  ``models/eet2_certificate.py`` with the endpoint facts.
- Chatter on messages and certificates, so the warnings have somewhere to live.


Port from 19.0 (18.0 adaptations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- The automatic certificate renewal (19.0.1.3.0) is ported as well. 18.0
  adaptations: the renewal cron commits per certificate instead of
  ``ir.cron._commit_progress``, and the EET manager lookup reads
  ``res.groups.users`` (19.0: ``user_ids``).
- Carried over from ``l10n_cz_eet2`` 19.0.1.1.0 and 19.0.1.2.0 on 2026-10-31.
  18.0 differences: the two partial unique indexes are created in ``init()``
  (no ``models.UniqueIndex`` on 18.0); the scheduled sender commits per
  message and reports ``done`` / ``remaining`` through
  ``ir.cron._notify_progress`` (no ``_commit_progress``); the "created" chatter
  note is suppressed with the ``mail_create_nolog`` context; the EET group's
  members are read from ``res.groups.users``.

[18.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Sends registered-sale data messages to the Czech EET 2.0 system
  (Elektronická evidence tržeb) over the v4.1 SOAP data interface with WS-Security
  (``lib/eet2_client.py``), returning the POK acknowledgement code
  (corrected 2026-10-31: EET 2.0 has no FIK / BKP / PKP).
- ``eet2.certificate`` model storing and using the taxpayer's signing certificate
  (WS-Security signature; requires ``cryptography``, ``lxml``, ``requests``).
- ``eet2.transaction`` ledger of sent registrations with retry handling and a
  scheduled cron for pending/failed messages (``data/ir_cron.xml``).
- Company / journal / payment configuration for EET registration
  (``res.company``, ``account.journal``, ``account.payment``, config settings) plus
  dedicated menus and security groups/access rules.
