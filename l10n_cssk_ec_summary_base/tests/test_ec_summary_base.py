from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestEcSummaryBase(TransactionCase):
    """Smoke tests for the shared EC sales list framework."""

    def test_models_load(self):
        for model in (
            "cssk.ec.summary.statement.version",
            "cssk.ec.summary.statement",
            "cssk.ec.summary.statement.line",
        ):
            self.assertIn(model, self.env)

    def test_account_tax_field_present(self):
        self.assertIn(
            "cssk_ec_summary_code", self.env["account.tax"]._fields
        )

    def test_vies_preflight_blocks_invalid(self):
        template = self.env["ir.ui.view"].create({
            "name": "cssk ec summary test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_ec_summary_test_template'><SDV/></t>",
        })
        version = self.env["cssk.ec.summary.statement.version"].create({
            "name": "T", "country_id": self.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "SDV",
        })
        st_type = self.env["cssk.ec.summary.statement.type"].create({
            "version_id": version.id, "code": "R", "name": "Riadny",
            "fa_xml_value": "R",
        })
        st = self.env["cssk.ec.summary.statement"].create({
            "company_id": self.env.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month", "statement_type_id": st_type.id,
        })
        self.env["cssk.ec.summary.statement.line"].create({
            "statement_id": st.id, "partner_country_code": "",
            "partner_vat": "", "transaction_code": "0",
        })
        st.state = "preview"
        from odoo.exceptions import UserError
        # master-data preflight fires first: no company VAT → named error
        self.env.company.vat = False
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        self.assertIn("VAT", str(cm.exception))
        # with the company VAT set, the VIES line gate still hard-blocks the
        # line with the missing/non-EU customer VAT
        self.env.company.vat = "SK2023456787"
        with self.assertRaises(UserError):
            st.action_export_xml()

    def _make_statement(self):
        template = self.env["ir.ui.view"].create({
            "name": "cssk ec summary override test template",
            "type": "qweb",
            "arch": "<t t-name='cssk_ec_summary_ovr_template'><SDV/></t>",
        })
        version = self.env["cssk.ec.summary.statement.version"].create({
            "name": "TOVR", "country_id": self.env.ref("base.sk").id,
            "valid_from": "2025-01-01",
            "xml_template_ref_id": template.id,
            "xml_root_element": "SDV",
        })
        st_type = self.env["cssk.ec.summary.statement.type"].create({
            "version_id": version.id, "code": "R", "name": "Riadny",
            "fa_xml_value": "R",
        })
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.env.company.id, "version_id": version.id,
            "date_from": "2026-06-01", "date_to": "2026-06-30",
            "period_type": "month", "statement_type_id": st_type.id,
        })

    def _line_vals(self, st, vat="DE811907980", country="DE", code="0",
                   amount=1000.0):
        return [{
            "statement_id": st.id,
            "partner_country_code": country,
            "partner_vat": vat,
            "transaction_code": code,
            "total_amount": amount,
            "supplies_count": 1,
        }]

    def _compute_patch(self, st, **line_kwargs):
        # NB: patch with ``new=`` (a plain function), NEVER a MagicMock — the
        # registry's lazy ``_ondelete_methods`` scan collects every class
        # attribute that *has* an ``_ondelete`` attribute, and a MagicMock
        # auto-creates one on ``getattr``, so it would be cached as an unlink
        # hook and poison unrelated tests.
        def fake_compute(model):
            return self._line_vals(st, **line_kwargs)
        return patch.object(
            type(self.env["cssk.ec.summary.statement"]),
            "_compute_line_values", new=fake_compute)

    def test_manual_override_survives_recompute(self):
        """Task-2 regression: an EC line's manual override must survive
        ``action_compute_lines`` (the recompute is destructive) — re-applied
        to the row with the same (country, VAT, transaction code)."""
        st = self._make_statement()
        with self._compute_patch(st):
            st.action_compute_lines()
        self.assertAlmostEqual(st.line_ids.total_amount, 1000.0, places=2)

        st.line_ids.write({"is_overridden": True, "manual_value": 750.0})
        with self._compute_patch(st):
            st.action_compute_lines()
        line = st.line_ids
        self.assertEqual(len(line), 1)
        self.assertTrue(line.is_overridden)
        self.assertAlmostEqual(line.manual_value, 750.0, places=2)
        self.assertAlmostEqual(line.total_amount, 750.0, places=2,
                               msg="the override must be the reported value")

    def test_unmatched_override_warns_in_chatter(self):
        """Task-2 regression: an override whose row disappears on recompute
        is reported in the chatter (listing the row), not silently lost."""
        st = self._make_statement()
        with self._compute_patch(st):
            st.action_compute_lines()
        st.line_ids.write({"is_overridden": True, "manual_value": 750.0})

        # the DE row disappears; only an FR row remains after the recompute
        with self._compute_patch(st, vat="FR40303265045", country="FR"):
            st.action_compute_lines()
        line = st.line_ids
        self.assertEqual(line.partner_vat, "FR40303265045")
        self.assertFalse(line.is_overridden,
                         "the override must not leak onto a different row")
        warn = st.message_ids.filtered(
            lambda m: "DE811907980" in (m.body or ""))
        self.assertTrue(warn, "the dropped override must be named in chatter")
