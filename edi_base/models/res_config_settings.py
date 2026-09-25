from odoo import models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _edi_persist_default_true_booleans(self, field_names):
        """Persist an explicit "True"/"False" for boolean config-parameter
        fields that default to True.

        Odoo's set_param() deletes the parameter row when handed a Python
        False; get_param() then falls back to the field's True default, so a
        checkbox that defaults to True can never be switched off through the
        settings form — it silently re-enables itself. Writing the string
        value keeps the chosen state.
        """
        ICP = self.env["ir.config_parameter"].sudo()
        for fname in field_names:
            ICP.set_param(self._fields[fname].config_parameter, str(self[fname]))
