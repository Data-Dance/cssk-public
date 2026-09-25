# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Statutory Submissions — Shared Framework",
    "version": "19.0.1.0.1",
    "summary": "Channel-agnostic delivery framework for statutory filings: one "
               "record per delivery attempt-set, a pluggable channel contract, "
               "retry with backoff, and durable authority receipts.",
    "description": """
CZ/SK Statutory Submissions — Shared Framework
==============================================

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
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account", "mail", "l10n_cssk_core"],
    "data": [
        "security/submission_groups.xml",
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/cssk_submission_views.xml",
        "views/cssk_submission_menus.xml",
    ],
    "installable": True,
}
