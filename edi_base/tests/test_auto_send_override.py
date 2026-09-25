from odoo.tests.common import TransactionCase


_FAKE_CONFIG_PARAM = "edi_base.test.auto_send_fake"


class TestEdiResolveAutoSend(TransactionCase):
    """Cover _edi_resolve_auto_send when no per-partner override Selection
    field is declared (the override-field-name is unknown to res.partner):
    in that case the resolver must always fall through to the global
    ir.config_parameter, regardless of the toggle.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Auto-Send Partner",
            "is_company": True,
        })
        cls.ICP = cls.env["ir.config_parameter"].sudo()

    def _resolve(self):
        return self.partner._edi_resolve_auto_send(
            "edi_no_such_override_field", _FAKE_CONFIG_PARAM,
        )

    def test_override_off_follows_global_true(self):
        self.partner.edi_auto_send_override = False
        self.ICP.set_param(_FAKE_CONFIG_PARAM, "True")
        self.assertTrue(self._resolve())

    def test_override_off_follows_global_false(self):
        self.partner.edi_auto_send_override = False
        self.ICP.set_param(_FAKE_CONFIG_PARAM, "False")
        self.assertFalse(self._resolve())

    def test_override_on_but_unknown_field_follows_global(self):
        """When the override toggle is on but the named Selection field
        doesn't exist on res.partner (the provider module isn't
        installed), the resolver must still fall back to the global."""
        self.partner.edi_auto_send_override = True
        self.ICP.set_param(_FAKE_CONFIG_PARAM, "False")
        self.assertFalse(self._resolve())
        self.ICP.set_param(_FAKE_CONFIG_PARAM, "True")
        self.assertTrue(self._resolve())

    def test_global_default_when_param_unset(self):
        """When the config parameter is unset, the resolver defaults to True."""
        self.partner.edi_auto_send_override = False
        self.ICP.set_param(_FAKE_CONFIG_PARAM, False)
        self.assertTrue(self._resolve())
