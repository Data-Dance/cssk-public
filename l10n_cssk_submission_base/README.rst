================================================
CZ/SK Statutory Submissions — Shared Framework
================================================

.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :alt: License: AGPL-3

**Channel-agnostic delivery framework for statutory filings: one record per delivery attempt-set, a pluggable channel contract, retry with backoff, and durable authority receipts.**

The statutory statements already keep a **durable filed copy**:
``cssk.statutory.submission.mixin`` (in ``l10n_cssk_core``) freezes the exported
XML at ``action_submit``, stamps the date and reference, and accumulates every
filed copy in ``filed_history_ids``. That is the *retention* half and this module
does not duplicate it.

What is missing is the *delivery* half — how a filing actually reaches the
authority, and what comes back. This module adds it:

* ``cssk.submission`` — one row per delivery attempt-set of one payload through
  one channel, with its own lifecycle
  (``draft → queued → sending → delivered → accepted``, plus ``rejected`` /
  ``failed`` / ``cancelled``).
* A **channel plug-in contract** (``_channel_validate`` / ``_channel_send`` /
  ``_channel_poll``) dispatched on the ``channel`` value, so a transport module
  adds a channel without touching the statements.
* **Authority receipts** — potvrdenky and doručenky land in
  ``receipt_attachment_ids``, so the proof of filing is ours and survives losing
  the channel provider.
* **Retry with backoff**, on ``queue_job`` where it is installed and on a cron
  otherwise; failures raise a ``mail.activity`` on whoever is responsible.
* ``cssk.submittable.mixin`` — the seam the statements inherit, adding
  ``submission_ids`` / ``active_submission_id`` / ``submission_state`` on top of
  the retention mixin they already have.

Ships one channel, ``pfs_manual``: the accountant files by hand on the portal
and attests it, which records the evidence and the person who filed. Automated
channels (``govbox_fs``, ``upvs_general``, …) are separate modules.

**Distinction worth keeping:** ``delivered`` means the channel confirmed receipt;
``accepted`` means the authority accepted the filing. A channel that cannot
observe acceptance stops at ``delivered`` and says so.

.. rubric:: Module facts

- **Technical name:** ``l10n_cssk_submission_base``
- **Version:** 18.0.1.0.1
- **Licence:** AGPL-3
- **Requires:** ``account``, ``mail``, ``l10n_cssk_core``

Authors: Data Dance s.r.o.
