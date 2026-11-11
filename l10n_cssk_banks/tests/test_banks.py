# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib
import os
import re
from collections import Counter

from lxml import etree

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path

from odoo.addons.l10n_cssk_banks.hooks import (
    MODULE,
    adopt_existing_banks,
    shipped_banks,
    sync_registry,
)

BIC_RE = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")


@tagged("post_install", "-at_install")
class TestCsskBanks(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Bank = cls.env["res.bank"].with_context(active_test=False)
        # The banks the registries list now. An upgraded database also holds
        # archived ones that left the registry; those are not the data set.
        cls.banks = cls.Bank.browse([
            cls.env.ref(f"{MODULE}.{name}").id for name in shipped_banks()])
        cls.partner = cls.env["res.partner"].create({"name": "Bank test partner"})

    def test_bic_format(self):
        bad = [(b.code, b.bic) for b in self.banks
               if b.bic and (len(b.bic) not in (8, 11) or not BIC_RE.match(b.bic))]
        self.assertFalse(bad, "BICs that are not 8/11 characters of ISO 9362")
        for vals in shipped_banks().values():
            if vals["bic"]:
                self.assertRegex(vals["bic"], BIC_RE)

    def test_bic_country_matches(self):
        # A BIC names its country in characters 5-6; a Slovak record with a
        # Czech BIC is the foreign-SIPS-participant row the generator drops.
        for bank in self.banks.filtered("bic"):
            self.assertEqual(bank.bic[4:6], bank.country.code, bank.display_name)

    def test_codes_unique_per_country(self):
        counts = Counter((b.country.code, b.code) for b in self.banks)
        self.assertFalse([k for k, n in counts.items() if n > 1])
        self.assertEqual(set(self.banks.mapped("country.code")), {"CZ", "SK"})
        # Nor may an active bank under any of our xmlids — a leftover of the
        # rename included — share a code with another one.
        ours = self.env["res.bank"].browse(self.env["ir.model.data"].search(
            [("module", "=", MODULE), ("model", "=", "res.bank")]).mapped("res_id"))
        counts = Counter((b.country.code, b.code) for b in ours if b.active)
        self.assertFalse([k for k, n in counts.items() if n > 1])

    def test_xmlids_unique_and_prefixed(self):
        names = []
        for rel in ("data/res_bank_cz.xml", "data/res_bank_sk.xml"):
            country = rel[-6:-4]
            for rec in etree.parse(file_path(f"{MODULE}/{rel}")).iter("record"):
                self.assertTrue(rec.get("id").startswith(f"bank_{country}_"),
                                rec.get("id"))
                names.append(rec.get("id"))
        self.assertEqual(len(names), len(set(names)), "an xmlid is in both files")
        self.assertEqual(len(self.banks), len(names), "an xmlid does not resolve")
        self.assertTrue(all(self.banks.mapped("active")), "a shipped bank is archived")

    def test_key_banks(self):
        expected = {
            "l10n_cssk_banks.bank_sk_1100": ("SK", "1100", "TATRSKBX"),
            "l10n_cssk_banks.bank_sk_0200": ("SK", "0200", "SUBASKBX"),
            "l10n_cssk_banks.bank_sk_0900": ("SK", "0900", "GIBASKBX"),
            "l10n_cssk_banks.bank_sk_8330": ("SK", "8330", "FIOZSKBA"),
            "l10n_cssk_banks.bank_cz_0100": ("CZ", "0100", "KOMBCZPP"),
            "l10n_cssk_banks.bank_cz_0300": ("CZ", "0300", "CEKOCZPP"),
            "l10n_cssk_banks.bank_cz_0800": ("CZ", "0800", "GIBACZPX"),
            "l10n_cssk_banks.bank_cz_2010": ("CZ", "2010", "FIOBCZPP"),
        }
        for xmlid, (country, code, bic) in expected.items():
            bank = self.env.ref(xmlid)
            self.assertEqual((bank.country.code, bank.code, bank.bic),
                             (country, code, bic), xmlid)

    def test_iban_lookup_sk(self):
        account = self.env["res.partner.bank"].create({
            "acc_number": "SK0511000000000000000123", "partner_id": self.partner.id})
        self.assertEqual(account.bank_id,
                         self.env.ref("l10n_cssk_banks.bank_sk_1100"))

    def test_iban_lookup_cz(self):
        account = self.env["res.partner.bank"].create({
            "acc_number": "CZ6508000000192000145399", "partner_id": self.partner.id})
        self.assertEqual(account.bank_id,
                         self.env.ref("l10n_cssk_banks.bank_cz_0800"))

    def test_sources_pinned(self):
        pin = file_path(f"{MODULE}/data/SOURCE_VERSION")
        pinned = {}
        with open(pin, encoding="utf8") as fh:
            for line in fh:
                if line.strip() and not line.startswith("#"):
                    name, _when, size, digest, _url = line.split()
                    pinned[name] = (int(size), digest)
        src = os.path.join(os.path.dirname(pin), "source")
        present = sorted(os.listdir(src))
        self.assertEqual(present, sorted(pinned), "a source file is not pinned")
        for name in present:
            with open(os.path.join(src, name), "rb") as fh:
                body = fh.read()
            self.assertEqual((len(body), hashlib.sha256(body).hexdigest()),
                             pinned[name], name)

    def test_sync_restores_registry_values_and_archives(self):
        fio = self.env.ref("l10n_cssk_banks.bank_sk_8330")
        fio.write({"bic": "FIOZSKBAX", "name": "Fio, sporiteľné družstvo",
                   "street": "user street"})
        gone = self.Bank.create({"name": "Gone bank", "code": "0001",
                                 "country": self.env.ref("base.cz").id})
        self.env["ir.model.data"].create({
            "module": MODULE, "name": "bank_cz_0001", "model": "res.bank",
            "res_id": gone.id, "noupdate": True})
        account = self.env["res.partner.bank"].create({
            "acc_number": "123456", "partner_id": self.partner.id,
            "bank_id": gone.id})
        changed, archived = sync_registry(self.env)
        self.assertIn("bank_sk_8330", changed)
        self.assertEqual(fio.bic, "FIOZSKBA")
        self.assertEqual(fio.name, "Fio banka, a.s., pobočka zahraničnej banky")
        self.assertEqual(fio.street, "user street", "not a registry field")
        self.assertIn("bank_cz_0001", archived)
        self.assertFalse(gone.active)
        self.assertTrue(gone.exists())
        self.assertEqual(account.bank_id, gone)

    def test_adopt_existing_bank(self):
        # A bank typed in by hand before the module, under the same code: it
        # must take the xmlid rather than sit beside a second copy.
        tatra = self.env.ref("l10n_cssk_banks.bank_sk_1100")
        self.env["ir.model.data"].search(
            [("module", "=", MODULE), ("name", "=", "bank_sk_1100")]).unlink()
        manual = self.Bank.create({"name": "Tatra", "code": "1100",
                                   "country": self.env.ref("base.sk").id})
        # One account more than the shipped record has, whatever the database.
        uses = self.env["res.partner.bank"].with_context(active_test=False).search_count(
            [("bank_id", "=", tatra.id)])
        for n in range(uses + 1):
            self.env["res.partner.bank"].create({
                "acc_number": f"999{n}", "partner_id": self.partner.id,
                "bank_id": manual.id})
        adopted = adopt_existing_banks(self.env)
        self.assertEqual(adopted, [f"bank_sk_1100=res.bank({manual.id})"],
                         "the referenced record wins over the unreferenced one")
        self.assertEqual(self.env.ref("l10n_cssk_banks.bank_sk_1100"), manual)
        self.assertNotEqual(manual, tatra)
