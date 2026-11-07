# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountingTerms(TransactionCase):
    """The shipped accounting terms reach the selections they are meant for,
    and only those.

    Odoo uses one msgid, "Sales" or "Purchases", for the tax type, the journal
    type and menus. Our catalogue retranslates the tax type alone (*Výstup* /
    *Vstup*, as the VAT acts say) with an entry that carries a msgctxt. Odoo's
    PO reader ignores msgctxt and loads such an entry by its occurrence lines,
    so this test is what notices if a future reader stops doing that.
    """

    EXPECTED = {
        "cs_CZ": {
            ("account.tax", "type_tax_use", "sale"): "Výstup",
            ("account.tax", "type_tax_use", "purchase"): "Vstup",
            ("account.account", "account_type", "income"): "Výnosy",
            ("account.account", "account_type", "income_other"): "Ostatní výnosy",
            ("account.account", "account_type", "expense"): "Náklady",
            ("account.account", "internal_group", "income"): "Výnosy",
            ("account.account", "internal_group", "expense"): "Náklady",
        },
        "sk_SK": {
            ("account.tax", "type_tax_use", "sale"): "Výstup",
            ("account.tax", "type_tax_use", "purchase"): "Vstup",
            ("account.account", "account_type", "income"): "Výnosy",
            ("account.account", "account_type", "income_other"): "Ostatné výnosy",
            ("account.account", "account_type", "expense"): "Náklady",
            ("account.account", "account_type", "expense_other"): "Ostatné náklady",
            ("account.account", "internal_group", "income"): "Výnosy",
            ("account.account", "internal_group", "expense"): "Náklady",
        },
    }
    #: The same msgids elsewhere keep Odoo's wording: a sales journal is not
    #: an output-tax journal.
    UNTOUCHED = {
        "cs_CZ": {("account.journal", "type", "sale"): "Prodej"},
        "sk_SK": {("account.journal", "type", "sale"): "Predaj"},
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "account.tax" not in cls.env:
            cls.skipTest(cls, "account is not installed")
        for lang in cls.EXPECTED:
            cls.env["res.lang"]._activate_lang(lang)
        cls.env["ir.module.module"]._cssk_apply_translation_overrides(list(cls.EXPECTED))

    def _labels(self, lang, model, field):
        description = self.env[model].with_context(lang=lang).fields_get([field])[field]
        return dict(description["selection"])

    def test_tax_type_and_account_types(self):
        for lang, expected in self.EXPECTED.items():
            for (model, field, value), label in expected.items():
                with self.subTest(lang=lang, field=f"{model}.{field}", value=value):
                    self.assertEqual(self._labels(lang, model, field)[value], label)

    def test_shared_msgid_left_alone_elsewhere(self):
        for lang, expected in self.UNTOUCHED.items():
            for (model, field, value), label in expected.items():
                with self.subTest(lang=lang, field=f"{model}.{field}"):
                    self.assertEqual(self._labels(lang, model, field)[value], label)
