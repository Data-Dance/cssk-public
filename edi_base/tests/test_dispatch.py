"""How a queued message leaves `queued`, when nothing is there to take it.

``edi_base`` no longer requires ``queue_job``. These tests hold that line: the
dispatch hooks do nothing on their own, the cron picks up only the providers
that asked for it, and — the one that matters — a provider dispatched by job is
never touched by the cron, because on a database carrying both a message picked
up twice is a document sent twice.
"""

from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.edi_base.exceptions import RetryableJobError


class DispatchCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Message = cls.env["edi.message"]
        # Two made-up providers, registered the way a connector module does it
        # in _register_hook. Real providers are not used: this is about the
        # registry, and borrowing one would tie the test to whatever else is
        # installed.
        cls.Message.PROVIDER_CONNECTOR_MAP["t_cron"] = "edi.connector.mixin"
        cls.Message.PROVIDER_CONNECTOR_MAP["t_queue"] = "edi.connector.mixin"
        cls.Message.PROVIDER_DISPATCH_MAP["t_cron"] = "cron"
        cls.Message.PROVIDER_DISPATCH_MAP["t_queue"] = "queue"
        cls.addClassCleanup(cls._forget_providers)

    @classmethod
    def _forget_providers(cls):
        for provider in ("t_cron", "t_queue"):
            cls.Message.PROVIDER_CONNECTOR_MAP.pop(provider, None)
            cls.Message.PROVIDER_DISPATCH_MAP.pop(provider, None)

    def _message(self, provider):
        return self.env["edi.message"].create({
            "provider": provider,
            "direction": "out",
            "state": "queued",
        })


class TestDispatchRegistry(DispatchCase):

    def test_an_unregistered_provider_still_means_a_queue(self):
        """Every provider was job-dispatched before the registry existed, so
        that is what silence has to keep meaning."""
        message = self._message("t_queue")
        self.Message.PROVIDER_DISPATCH_MAP.pop("t_queue")
        self.assertEqual(message._dispatch_mode(), "queue")
        self.Message.PROVIDER_DISPATCH_MAP["t_queue"] = "queue"

    def test_the_core_hook_does_nothing_by_itself(self):
        """With no job runner installed, handing over is somebody else's job —
        here, the cron. The message stays queued and no exception is raised."""
        message = self._message("t_cron")
        connector = self.env["edi.connector.mixin"]
        self.assertFalse(message._dispatch_send(connector))
        self.assertEqual(message.state, "queued")


class TestCronScope(DispatchCase):
    """The double-send guard."""

    def test_the_cron_sends_only_cron_registered_providers(self):
        cron_message = self._message("t_cron")
        queue_message = self._message("t_queue")
        sent = []

        def fake_send(self_, message):
            sent.append(message.id)
            return True

        with patch("odoo.addons.edi_base.models.edi_connector_mixin"
                   ".EdiConnectorMixin._send_message", fake_send, create=True):
            self.Message._cron_send_queued()

        self.assertIn(cron_message.id, sent)
        self.assertNotIn(
            queue_message.id, sent,
            "a job-dispatched message picked up by the cron is a document "
            "sent twice",
        )

    def test_a_retryable_failure_stays_queued(self):
        """The signal a job runner acts on, honoured the same way.

        Losing this would turn every rate limit and every timeout into a
        document a human has to re-send by hand.
        """
        message = self._message("t_cron")

        def fake_send(self_, record):
            raise RetryableJobError("the provider is busy")

        with patch("odoo.addons.edi_base.models.edi_connector_mixin"
                   ".EdiConnectorMixin._send_message", fake_send, create=True):
            self.Message._cron_send_queued()

        message.invalidate_recordset()
        self.assertEqual(message.state, "queued", "it must be tried again")
        self.assertEqual(message.blocking_level, "warning")

    def test_a_permanent_failure_becomes_an_error(self):
        message = self._message("t_cron")

        def fake_send(self_, record):
            raise ValueError("this document will never be accepted")

        with patch("odoo.addons.edi_base.models.edi_connector_mixin"
                   ".EdiConnectorMixin._send_message", fake_send, create=True):
            self.Message._cron_send_queued()

        message.invalidate_recordset()
        self.assertEqual(message.state, "error")
        self.assertIn("never be accepted", message.error_message)


class TestExceptionShim(TransactionCase):

    def test_the_real_queue_job_classes_are_used_when_present(self):
        """Re-exported, never shadowed.

        A runner recognises its own exception classes by identity. A look-alike
        defined here would be caught by nothing and retried never — so if
        queue_job is installed, these must BE its classes.
        """
        try:
            from odoo.addons.queue_job.exception import (
                RetryableJobError as TheirRetryable,
            )
        except ImportError:
            self.skipTest("queue_job is not installed in this run")
        self.assertIs(RetryableJobError, TheirRetryable)
