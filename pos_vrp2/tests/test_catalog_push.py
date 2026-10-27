import json
from contextlib import contextmanager
from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon

VATLIST = [{"id": 501, "vatRate": 0.19}, {"id": 2000, "vatRate": 0}]


@tagged("post_install", "-at_install")
class TestCatalogPush(TestPoSCommon):
    """A push touches only what this till created on its register.

    It used to delete every remote category, and deactivate every remote
    product, that Odoo did not list — whatever the cashier typed into the
    VRP2 app, whatever another till or another database had put there.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.till_a = cls.basic_config
        cls.till_b = cls.other_currency_config
        cls.till_a.vrp2_login = "1111111111"
        cls.till_b.vrp2_login = "2222222222"
        cls.vat19 = cls.env["account.tax"].create({
            "name": "VAT 19 %", "amount": 19, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": cls.company.id,
        })
        cls.company.write({
            "vrp2_vatlist_json": json.dumps(VATLIST),
            "vrp2_tax_19": cls.vat19.id,
        })
        cls.drinks = cls.env["pos.category"].create({"name": "Drinks"})
        cls.tea = cls.env["product.template"].create({
            "name": "Tea", "list_price": 2.0, "available_in_pos": True,
            "taxes_id": [(6, 0, cls.vat19.ids)],
            "pos_categ_ids": [(6, 0, cls.drinks.ids)],
        })

    def setUp(self):
        super().setUp()
        # One register per till: {login: {"categories": {id: name},
        # "services": {code: dict}}}
        self.registers = {
            "1111111111": {"categories": {}, "services": {}},
            "2222222222": {"categories": {}, "services": {}},
        }
        self.sent = []
        self.next_id = 7000

    @contextmanager
    def _vrp2(self):
        Client = type(self.env["vrp2.client"])
        test = self

        def reg(holder):
            return test.registers[holder.vrp2_login]

        def get_categories(self_, holder):
            return {"categories": [
                {"id": cid, "name": name, "order": 1}
                for cid, name in reg(holder)["categories"].items()]}

        def set_category(self_, holder, data):
            test.sent.append((holder.vrp2_login, "setcategory", data))
            cats = reg(holder)["categories"]
            for entry in data["deleteCategories"]:
                cats.pop(entry["categoryId"], None)
            for entry in data["setCategories"]:
                if entry.get("categoryId"):
                    cats[entry["categoryId"]] = entry["name"]
                else:
                    test.next_id += 1
                    cats[test.next_id] = entry["name"]
            return get_categories(self_, holder)

        def get_services(self_, holder):
            services = list(reg(holder)["services"].values())
            return {"results": services, "resultCount": len(services),
                    "resultTotalCount": len(services)}

        def add_service(self_, holder, body):
            test.next_id += 1
            code = "80000000000000000%04d" % test.next_id
            reg(holder)["services"][code] = {
                "code": code, "name": body["dto"]["name"],
                "vat": {"id": body["dto"]["vatId"]},
                "priceWithVat": body["dto"]["priceWithVat"], "invalid": False,
            }
            test.sent.append((holder.vrp2_login, "add", body["dto"]))
            return {"code": code}

        def set_service(self_, holder, body):
            dto = body["dto"]
            test.sent.append((holder.vrp2_login, "set", dto))
            service = reg(holder)["services"].get(dto["code"])
            if service is None:
                raise AssertionError("updated a code the register lacks")
            service["invalid"] = dto.get("invalid", False)
            return {}

        with patch.object(Client, "_ensure_session", return_value="TOK"), \
                patch.object(Client, "_get_category_list", get_categories), \
                patch.object(Client, "_set_category", set_category), \
                patch.object(Client, "_get_service_list", get_services), \
                patch.object(Client, "_add_service", add_service), \
                patch.object(Client, "_set_service_data", set_service):
            yield

    def _push(self, till):
        with self._vrp2():
            return till.action_vrp2_sync_to()

    def test_the_zero_rate_reason_is_pushed(self):
        """The special regulation was read from VRP2 but never sent back."""
        vat0 = self.env["account.tax"].create({
            "name": "VAT 0 %", "amount": 0, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": self.company.id,
        })
        self.company.vrp2_tax_0 = vat0
        book = self.env["product.template"].create({
            "name": "Exempt", "list_price": 5.0, "available_in_pos": True,
            "taxes_id": [(6, 0, vat0.ids)],
            "vrp2_special_regulation": "TAX_EXEMPTION",
        })
        # a 19 % product carrying a stale value must not send it
        self.tea.vrp2_special_regulation = "TAX_EXEMPTION"
        self._push(self.till_a)
        added = {dto["name"]: dto for _login, kind, dto in self.sent if kind == "add"}
        self.assertEqual(added["Exempt"]["specialRegulation"], "TAX_EXEMPTION")
        self.assertNotIn("specialRegulation", added["Tea"])
        self.sent.clear()
        self._push(self.till_a)
        updated = [dto for _login, kind, dto in self.sent if kind == "set"
                   and dto["code"] == book._vrp2_code_for(self.till_a)]
        self.assertEqual(updated[0]["specialRegulation"], "TAX_EXEMPTION")

    # ---- categories --------------------------------------------------------

    def test_a_category_made_in_the_app_survives_a_push(self):
        self.registers["1111111111"]["categories"][900] = "Typed at the till"
        self._push(self.till_a)
        self.assertIn(900, self.registers["1111111111"]["categories"])
        for login, kind, data in self.sent:
            if kind == "setcategory":
                self.assertEqual(data["deleteCategories"], [])

    def test_another_tills_categories_survive_a_push(self):
        self._push(self.till_a)
        a_ids = set(self.registers["1111111111"]["categories"])
        # Till B's register happens to hold the same ids (a shared catalogue).
        self.registers["2222222222"]["categories"] = dict(
            self.registers["1111111111"]["categories"])
        self.registers["2222222222"]["categories"][901] = "B's own"
        self.drinks.unlink()
        self._push(self.till_b)
        self.assertLessEqual(a_ids | {901},
                             set(self.registers["2222222222"]["categories"]))

    def test_a_category_this_till_created_is_deleted_when_gone(self):
        self._push(self.till_a)
        cats = self.registers["1111111111"]["categories"]
        self.assertIn("Drinks", cats.values())
        self.tea.pos_categ_ids = False
        self.drinks.unlink()
        self._push(self.till_a)
        self.assertNotIn("Drinks", cats.values())

    def test_one_tills_category_id_is_not_sent_to_another(self):
        self._push(self.till_a)
        a_id = self.drinks.vrp2_id
        self.assertTrue(a_id)
        self.sent.clear()
        self._push(self.till_b)
        entries = [e for login, kind, data in self.sent if kind == "setcategory"
                   for e in data["setCategories"] if e["name"] == "Drinks"]
        self.assertEqual(len(entries), 1)
        self.assertNotIn("categoryId", entries[0])

    # ---- products ---------------------------------------------------------

    def test_a_product_made_in_the_app_is_never_deactivated(self):
        self.registers["1111111111"]["services"]["APP-1"] = {
            "code": "APP-1", "name": "Typed", "vat": {"id": 501},
            "priceWithVat": 1.0, "invalid": False,
        }
        self._push(self.till_a)
        self.assertFalse(self.registers["1111111111"]["services"]["APP-1"]["invalid"])

    def test_a_product_this_till_created_is_deactivated_only_there(self):
        self._push(self.till_a)
        code = self.tea.vrp2_code
        self.assertTrue(code)
        # The same code also lives on till B's register (shared catalogue).
        self.registers["2222222222"]["services"][code] = dict(
            self.registers["1111111111"]["services"][code])
        self.tea.available_in_pos = False
        self._push(self.till_b)
        self.assertFalse(self.registers["2222222222"]["services"][code]["invalid"])
        self._push(self.till_a)
        self.assertTrue(self.registers["1111111111"]["services"][code]["invalid"])

    def test_an_existing_code_is_adopted_not_duplicated(self):
        """Codes stored before per-till links are taken over, not re-created
        — and, adopted, never deactivated."""
        self.registers["1111111111"]["services"]["LEGACY-1"] = {
            "code": "LEGACY-1", "name": "Tea", "vat": {"id": 501},
            "priceWithVat": 2.38, "invalid": False,
        }
        self.tea.vrp2_code = "LEGACY-1"
        self._push(self.till_a)
        self.assertFalse([1 for login, kind, dto in self.sent
                          if kind == "add" and dto["name"] == "Tea"])
        self.tea.available_in_pos = False
        self._push(self.till_a)
        self.assertFalse(self.registers["1111111111"]["services"]["LEGACY-1"]["invalid"])

    def test_each_till_sells_under_its_own_code(self):
        self._push(self.till_a)
        self._push(self.till_b)
        code_a = self.tea._vrp2_code_for(self.till_a)
        code_b = self.tea._vrp2_code_for(self.till_b)
        self.assertIn(code_a, self.registers["1111111111"]["services"])
        self.assertIn(code_b, self.registers["2222222222"]["services"])
        self.assertNotEqual(code_a, code_b)
