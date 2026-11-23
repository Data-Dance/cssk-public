# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
import os

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSchemaPin(TransactionCase):
    """data/SCHEMA_VERSION pins the bundled XSDs (digest, size). Nothing
    local can tell a stale schema from a current one: the pin makes a
    refresh a deliberate change instead of a silent one."""

    def test_every_bundled_schema_matches_its_pin(self):
        data = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data")
        with open(os.path.join(data, "SCHEMA_VERSION"),
                  encoding="utf-8") as fh:
            lines = [raw.split() for raw in fh]
        pins = {p[0]: (p[1], int(p[2])) for p in lines
                if len(p) == 3 and p[0].endswith(".xsd")}
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(pins), "unpinned or missing schema")
        for name, (digest, size) in pins.items():
            with open(os.path.join(data, name), "rb") as fh:
                blob = fh.read()
            self.assertEqual((hashlib.md5(blob).hexdigest(), len(blob)),
                             (digest, size), "%s moved without its pin" % name)

    def test_the_version_records_name_the_pinned_files(self):
        versions = self.env["cssk.payroll.declaration.version"].search(
            [("xml_schema_module", "=", "l10n_cz_hr_payroll_health")])
        self.assertEqual(
            set(versions.mapped("xml_schema_filename")),
            {"data/PPPZ_2025_v8.xsd", "data/HOZ_2025_v8.xsd"})
