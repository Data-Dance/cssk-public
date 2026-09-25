=========
Changelog
=========

All notable changes to **l10n_cssk_submission_base** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-09-06
-------------------------

Fixed
~~~~~

- **Marking a filing submitted raised ``AccessError`` for a user without the
  statutory-submission groups**, so the statement could not be saved at all.
  ``_ensure_submission`` read ``submission_ids`` as the acting user and did so
  *outside* its own ``try``, which made "never raises" cover only the
  ``create``. Filing is an accounting right and holding the submission groups
  is a separate one; opening the delivery is the system's bookkeeping, so it
  runs ``sudo`` now, with the whole body guarded. Found by a red
  ``l10n_sk_kv_dph`` test on ``19.0``, not by the review.

[19.0.1.0.0] — 2026-08-30
-------------------------

Added
~~~~~

- Initial release. ``cssk.submission`` — one record per delivery attempt-set of
  one statutory payload through one channel, with the lifecycle
  ``draft → queued → sending → delivered → accepted`` plus ``rejected`` /
  ``failed`` / ``cancelled``.
- Channel plug-in contract (``_channel_validate`` / ``_channel_send`` /
  ``_channel_poll``) dispatched on the ``channel`` value, so a transport module
  adds a channel without touching the statement models.
- ``receipt_attachment_ids`` holds potvrdenky and doručenky, so the proof of
  filing is retained on our side and survives losing the channel provider.
- Retry with capped backoff (1/5/15/60/180 min) on a five-minute cron; a
  submission that exhausts its attempts fails loudly and raises a
  ``mail.activity`` rather than retrying past the filing deadline.
- ``cssk.submittable.mixin`` — the seam the statutory statements inherit for
  ``submission_ids`` / ``active_submission_id`` / ``submission_state``.
- Channel ``pfs_manual``: the accountant files on the portal and attests it,
  which records who filed, when, and the potvrdenka they downloaded.

Notes
~~~~~

- This module is the **delivery** half only. Retention — the durable filed copy,
  filing date, reference and filed history — already lives in
  ``cssk.statutory.submission.mixin`` (``l10n_cssk_core``) and is not duplicated
  here; a submission points at the filed copy that mixin froze.
- ``delivered`` and ``accepted`` are kept apart deliberately: the first means the
  channel took the payload, the second that the authority accepted the filing. A
  channel that cannot observe acceptance stops at ``delivered`` and reports so
  through ``_channel_observes_acceptance``.
