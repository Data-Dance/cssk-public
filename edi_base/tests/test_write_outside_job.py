"""Argument handling of ``edi.message._write_outside_job``.

**What is deliberately NOT tested here, and why.** The point of the helper is
that it commits on a second cursor so the write survives the rollback
queue_job performs before recording a job failure. That cannot be exercised
from a ``TransactionCase``: Odoo asserts hard on any ``commit()`` /
``rollback()`` of a cursor taken inside a test —

    Cannot commit or rollback a cursor from inside a test, this will lead to
    a broken cursor when trying to rollback the test.

so both the rollback and the second cursor's commit are refused by the
framework, not by our code. The helper swallows that (it must never mask the
transport error that prompted it) and returns False, which is also why calling
it from within any test is a safe no-op rather than a durable write.

The durable path was instead verified out-of-band against a real database, in
a non-test process: value written via ``_write_outside_job`` survived a
subsequent ``cr.rollback()`` and was visible to a *separate* process, while an
inline ``write()`` on the same record did not survive. See the module
CHANGELOG.

What remains genuinely unit-testable is the guard logic that runs before any
cursor is opened.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWriteOutsideJob(TransactionCase):
    """post_install: at-install tests for this module run before the provider
    modules reach the registry, so ``_selection_provider()`` is still empty and
    the required ``provider`` field cannot be filled."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        providers = cls.env["edi.message"]._selection_provider()
        if not providers:
            raise cls.skipTest(cls, "no EDI provider module installed")
        cls.provider = providers[0][0]

    def _message(self):
        return self.env["edi.message"].create({
            "name": "outside-job.xml",
            "direction": "out",
            "provider": self.provider,
            "state": "queued",
        })

    def test_empty_recordset_is_refused_before_any_cursor(self):
        """Guard runs first, so no rollback is attempted on an empty set."""
        self.assertFalse(
            self.env["edi.message"]._write_outside_job({"state": "error"}))

    def test_empty_vals_are_refused_before_any_cursor(self):
        self.assertFalse(self._message()._write_outside_job({}))

    def test_never_raises(self):
        """The contract that matters most at the call site: this is
        bookkeeping for a failure that is already being raised, so it must
        report a problem by returning False, never by raising over it."""
        msg = self._message()
        try:
            result = msg._write_outside_job({"state": "error"})
        except Exception as exc:  # pragma: no cover - the assertion is the point
            self.fail("_write_outside_job raised %r instead of returning" % exc)
        self.assertIn(result, (True, False))
