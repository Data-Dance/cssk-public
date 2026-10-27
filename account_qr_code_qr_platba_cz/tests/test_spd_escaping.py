# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

METHOD = "czqrplatba_qr"


@tagged("post_install", "-at_install")
class TestSpdEscaping(AccountTestInvoicingCommon):
    """An asterisk ends an SPD field; inside a value it must be %2A."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.bank = cls.env["res.partner.bank"].sudo().create({
            "acc_number": "CZ6508000000192000145399",
            "partner_id": cls.company_data["company"].partner_id.id,
            "acc_holder_name": "Firma *Hvězda* 100%",
        })

    def _code(self, communication):
        return self.bank._get_qr_code_generation_params(
            METHOD, 10.0, self.czk, self.partner_a, communication, communication,
        )["value"]

    def _fields(self, code):
        return dict(part.split(":", 1) for part in code.split("*")[2:] if part)

    def test_an_asterisk_in_the_reference_is_escaped(self):
        code = self._code("FA*2026*0042")
        fields = self._fields(code)
        self.assertEqual(fields["MSG"], "FA%2A2026%2A0042")
        # Nothing was shifted: every field still has its own key.
        self.assertEqual(set(fields), {"ACC", "AM", "CC", "MSG", "RF", "RN"})

    def test_the_payee_name_is_escaped_too(self):
        fields = self._fields(self._code("INV/1"))
        self.assertEqual(fields["RN"], "Firma %2AHvězda%2A 100%25")

    def test_an_escape_is_never_cut_at_the_limit(self):
        fields = self._fields(self._code("A" * 58 + "*B"))
        self.assertEqual(fields["MSG"], "A" * 58)

    def test_a_plain_reference_is_untouched(self):
        self.assertEqual(self._fields(self._code("INV/2026/0042"))["MSG"],
                         "INV/2026/0042")
