from odoo.tests.common import TransactionCase


class TestEdiEnvelopePartner(TransactionCase):
    """Cover the four shapes _edi_envelope_partner() must handle:

      1. Top-level partner, single GLN, no comm endpoint set → self.
      2. Sub-contact whose commercial root has no comm endpoint → cascades
         up to commercial root.
      3. Top-level partner with edi_communication_partner_id set (METRO
         style) → returns the comm endpoint partner.
      4. Sub-contact under a top-level multi-GLN partner → cascades up
         via commercial_partner_id and resolves to the comm endpoint.

    Cases 3 + 4 are the multi-GLN scenarios this refactor targets.
    """

    @classmethod
    def _partner_defaults(cls):
        """Defaults to satisfy res.partner NOT NULL columns added by
        other modules. Only sets fields actually present on the live
        model so the test stays portable across module sets."""
        Partner = cls.env["res.partner"]
        candidates = {"group_rfq": "default"}
        return {k: v for k, v in candidates.items() if k in Partner._fields}

    @classmethod
    def _patch_stale_db_constraints(cls):
        """Some module uninstalls (e.g. purchase_stock) leave a NOT NULL
        column on res_partner without re-installing the field. Drop NOT
        NULL on those columns inside the transaction so test inserts
        don't blow up on DB-only artefacts. Rolled back with the test."""
        cls.env.cr.execute("""
            SELECT a.attname
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            WHERE c.relname = 'res_partner'
              AND a.attnotnull = true
              AND a.attnum > 0
              AND NOT a.attisdropped
        """)
        Partner = cls.env["res.partner"]
        for (col,) in cls.env.cr.fetchall():
            if col not in Partner._fields and col not in (
                "id", "create_date", "write_date", "active",
            ):
                cls.env.cr.execute(
                    f'ALTER TABLE res_partner ALTER COLUMN "{col}" DROP NOT NULL'
                )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._patch_stale_db_constraints()
        Partner = cls.env["res.partner"]
        d = cls._partner_defaults()
        # Case 1+2: single-GLN customer
        cls.solo = Partner.create({
            **d,
            "name": "Solo Trading GmbH",
            "is_company": True,
            "global_location_number": "0000000000001",
        })
        cls.solo_invoice_addr = Partner.create({
            **d,
            "name": "Solo Invoice Address",
            "parent_id": cls.solo.id,
            "type": "invoice",
            "is_company": False,
            "global_location_number": "0000000000002",
        })
        # Case 3+4: METRO-style multi-GLN customer.
        # metro_hq = the standalone partner owning the eXite mailbox.
        cls.metro_hq = Partner.create({
            **d,
            "name": "METRO HQ EDI",
            "is_company": True,
            "global_location_number": "9999000000009",
        })
        # metro_legal = the actual legal entity (the buyer).
        cls.metro_legal = Partner.create({
            **d,
            "name": "METRO Cash & Carry",
            "is_company": True,
            "global_location_number": "9999000000001",
            "edi_communication_partner_id": cls.metro_hq.id,
        })
        # Sub-contact under metro_legal — invoice address with its own GLN.
        cls.metro_invoice_addr = Partner.create({
            **d,
            "name": "METRO Billing",
            "parent_id": cls.metro_legal.id,
            "type": "invoice",
            "is_company": False,
            "global_location_number": "9999000000094",
        })

    def test_single_gln_top_level_returns_self(self):
        result = self.solo._edi_envelope_partner()
        self.assertEqual(result, self.solo)
        self.assertEqual(result.global_location_number, "0000000000001")

    def test_single_gln_subcontact_cascades_to_commercial(self):
        result = self.solo_invoice_addr._edi_envelope_partner()
        self.assertEqual(result, self.solo)
        # Should NOT return the sub-contact's own GLN.
        self.assertEqual(result.global_location_number, "0000000000001")

    def test_multi_gln_top_level_returns_comm_endpoint(self):
        result = self.metro_legal._edi_envelope_partner()
        self.assertEqual(result, self.metro_hq)
        self.assertEqual(result.global_location_number, "9999000000009")

    def test_multi_gln_subcontact_cascades_to_comm_endpoint(self):
        """The key multi-GLN behaviour: a sub-contact (invoice address
        with its own GLN) used as invoice.partner_id should resolve to
        the parent legal entity's EDI communication endpoint — NOT to
        the sub-contact itself, NOT to the commercial root, but to the
        comm endpoint set on the commercial root."""
        result = self.metro_invoice_addr._edi_envelope_partner()
        self.assertEqual(result, self.metro_hq)
        # Critical: the wire GLN must NOT be the sub-contact's own GLN.
        self.assertNotEqual(result.global_location_number, "9999000000094")
        # Critical: the wire GLN must NOT be the legal entity's GLN.
        self.assertNotEqual(result.global_location_number, "9999000000001")
        # Must be the eXite mailbox GLN.
        self.assertEqual(result.global_location_number, "9999000000009")

    def test_empty_comm_endpoint_falls_back(self):
        """Setting edi_communication_partner_id to False explicitly
        behaves like leaving it unset — cascade still resolves to the
        commercial root."""
        self.metro_legal.edi_communication_partner_id = False
        result = self.metro_invoice_addr._edi_envelope_partner()
        self.assertEqual(result, self.metro_legal)
