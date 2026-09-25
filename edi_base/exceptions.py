"""Dispatch outcomes, whether or not a job runner is installed.

A connector says "retry me" or "give up" by raising, and OCA's ``queue_job``
defines the two types its runner understands. Since ``edi_base`` no longer
requires that module, a connector importing them directly would fail at the
first send on a database dispatched by cron.

So they are imported here when they exist and stand in for themselves when they
do not. **Re-exported, never shadowed**, when queue_job is present: the runner
recognises its own classes by identity, and a look-alike defined here would be
caught by nothing and retried never.
"""

try:  # pragma: no cover - depends on what is installed
    from odoo.addons.queue_job.exception import (  # noqa: F401
        FailedJobError,
        RetryableJobError,
    )
except ImportError:  # pragma: no cover - the queue-free deployment

    class FailedJobError(Exception):
        """Permanent: this will fail the same way next time."""

    class RetryableJobError(Exception):
        """Transient: the same call may succeed later."""
