import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

VRP2_SPECIAL_REGULATIONS = [
    ("TAX_EXEMPTION", "Oslobodené od dane"),
    ("TAX_OBLIGATION_TRANSFER", "Prenesenie daňovej povinnosti"),
    ("TRAVEL_AGENCIES", "Cestovné kancelárie"),
    ("ART_WORKS", "Umelecké diela"),
    ("USED_GOODS", "Použitý tovar"),
    ("COLLECTIVE_SUBJECTS_AND_ANTIQUES", "Zberateľské predmety a starožitnosti"),
]


class ProductTemplate(models.Model):
    _inherit = "product.template"

    vrp2_code = fields.Char(
        string="VRP2 Service Code",
        readonly=True,
        copy=False,
        help="Internal code assigned by VRP2 when the product is created.",
    )
    vrp2_special_regulation = fields.Selection(
        VRP2_SPECIAL_REGULATIONS,
        string="VRP2 Special Regulation",
        help="Verbal information required on receipt for 0%% VAT items.",
    )
    vrp2_returnable_packaging = fields.Boolean(
        string="VRP2 Returnable Packaging",
        help="A deposit-bearing package (zálohovaný obal). Taking it back is "
        "a negative quantity WITHOUT a sale to refer to, which VRP2 records "
        "as 'vrátené obaly' (item type NEGATIVE) rather than as a return of "
        "goods. Push it to the VRP2 catalogue like any other product.",
    )
    vrp2_favourite = fields.Boolean(
        string="VRP2 Favourite",
        help="Show in VRP2 favourites quick-access.",
    )
    vrp2_note = fields.Text(
        string="VRP2 Note",
        help="Internal note for VRP2 (max 1000 chars, not printed).",
    )
    vrp2_synced = fields.Boolean(
        string="Synced to VRP2",
        readonly=True,
        copy=False,
        help="Whether this product exists on the VRP2 server.",
    )

    # ------------------------------------------------------------------
    # Pull: VRP2 → Odoo
    # ------------------------------------------------------------------

    @api.model
    def _vrp2_pull(self, register):
        """Pull all products from VRP2 and upsert onto product.template.

        Returns the count of products synced.
        """
        client = self.env["vrp2.client"]
        company = register.company_id
        resp = client._get_service_list(register)
        services = resp.get("results", [])
        self._vrp2_warn_if_truncated(resp, "service")

        cat_map = {}
        for cat in self.env["pos.category"].search([("vrp2_id", "!=", False)]):
            cat_map[cat.vrp2_id] = cat.id

        vat_id_map = company._vrp2_vat_id_to_tax()

        synced = 0
        for svc in services:
            code = svc.get("code")
            if not code:
                continue

            existing = self.search([("vrp2_code", "=", code)], limit=1)

            vat_data = svc.get("vat", {})
            vat_id = vat_data.get("id")
            tax_id = vat_id_map.get(vat_id)

            pos_categ_id = False
            cat_data = svc.get("category")
            if cat_data and cat_data.get("id"):
                pos_categ_id = cat_map.get(cat_data["id"])

            # VRP2 stores gross (priceWithVat); Odoo's list_price is net.
            gross = svc.get("priceWithVat") or 0.0
            tax = self.env["account.tax"].browse(tax_id) if tax_id else None
            net = gross
            if tax and gross and tax.amount_type == "percent":
                net = gross / (1.0 + (tax.amount or 0.0) / 100.0)

            vals = {
                "name": svc.get("name", ""),
                "vrp2_code": code,
                "list_price": round(net, 2),
                "default_code": svc.get("codeCustom") or False,
                "vrp2_special_regulation": svc.get("specialRegulation") or False,
                "vrp2_favourite": bool(svc.get("favourite")),
                "vrp2_synced": True,
                "available_in_pos": True,
                "sale_ok": True,
                "type": "service",
            }

            if tax_id:
                vals["taxes_id"] = [(6, 0, [tax_id])]
            if pos_categ_id:
                vals["pos_categ_ids"] = [(4, pos_categ_id)]

            ean = svc.get("ean") or False

            if existing:
                existing.write(vals)
                # Barcode lives on product.product
                if ean and existing.product_variant_ids:
                    existing.product_variant_ids[0].barcode = ean
            else:
                tmpl = self.create(vals)
                if ean and tmpl.product_variant_ids:
                    tmpl.product_variant_ids[0].barcode = ean
            synced += 1

        _logger.info(
            "VRP2 product pull for %s: %d products",
            company.display_name,
            synced,
        )
        return synced

    # ------------------------------------------------------------------
    # Push: Odoo → VRP2  (per-product API calls)
    # ------------------------------------------------------------------

    @api.model
    def _vrp2_push(self, register):
        """Push all POS-available products to VRP2.

        Intended products = available_in_pos + has a tax mapped in VRP2.
        Products in VRP2 but no longer intended get deactivated.

        Returns (created, updated, deactivated) counts.
        """
        client = self.env["vrp2.client"]
        company = register.company_id
        tax_reverse = company._vrp2_tax_to_vat_id()

        # 1. Intended products: available_in_pos + has a mapped tax
        all_pos = self.search([
            ("available_in_pos", "=", True),
            ("sale_ok", "=", True),
        ])
        intended = all_pos.filtered(
            lambda p: any(
                tax_reverse.get(t.id) is not None for t in p.taxes_id
            )
        )

        # 2. Current VRP2 codes
        resp = client._get_service_list(register)
        remote_products = resp.get("results", [])
        self._vrp2_warn_if_truncated(resp, "service")
        remote_codes = {p["code"] for p in remote_products if p.get("code")}

        # 3. Push intended products
        intended_codes = set()
        created = 0
        updated = 0

        for product in intended:
            vat_id = None
            matched_tax = None
            for tax in product.taxes_id:
                vid = tax_reverse.get(tax.id)
                if vid is not None:
                    vat_id = vid
                    matched_tax = tax
                    break
            if vat_id is None:
                continue

            if product.vrp2_code:
                # Update
                dto = product._to_vrp2_update_dto(vat_id, matched_tax)
                client._set_service_data(register, {"dto": dto})
                product.vrp2_synced = True
                intended_codes.add(product.vrp2_code)
                updated += 1
            else:
                # Create
                dto = product._to_vrp2_create_dto(vat_id, matched_tax)
                resp = client._add_service(register, {"dto": dto})
                if resp and resp.get("code"):
                    product.vrp2_code = resp["code"]
                    product.vrp2_synced = True
                    intended_codes.add(resp["code"])
                    created += 1

        # 4. Deactivate VRP2 products no longer in intended set
        deactivated = 0
        codes_to_deactivate = remote_codes - intended_codes

        if codes_to_deactivate:
            # We need vatId and priceWithVat for deactivation — get from remote data
            remote_by_code = {p["code"]: p for p in remote_products}
            for code in codes_to_deactivate:
                rp = remote_by_code.get(code, {})
                vat_id = rp.get("vat", {}).get("id")
                price = rp.get("priceWithVat", 0)
                if not vat_id:
                    continue
                dto = {
                    "code": code,
                    "vatId": vat_id,
                    "priceWithVat": price,
                    "invalid": True,
                }
                try:
                    client._set_service_data(register, {"dto": dto})
                    deactivated += 1
                    # Clear vrp2_synced on local record if it exists
                    local = self.search([("vrp2_code", "=", code)], limit=1)
                    if local:
                        local.vrp2_synced = False
                except Exception:
                    _logger.warning(
                        "VRP2 failed to deactivate product code=%s", code,
                        exc_info=True,
                    )

        _logger.info(
            "VRP2 product push for %s: %d created, %d updated, %d deactivated",
            company.display_name,
            created,
            updated,
            deactivated,
        )
        return created, updated, deactivated

    # ------------------------------------------------------------------
    # DTO builders
    # ------------------------------------------------------------------

    def _to_vrp2_create_dto(self, vat_id, tax):
        """Build dto for POST /v1/service/addservice."""
        self.ensure_one()
        price_with_vat = self._compute_price_with_vat(tax)
        dto = {
            "name": self.name,
            "priceWithVat": price_with_vat,
            "vatId": vat_id,
            "favourite": self.vrp2_favourite,
        }
        barcode = self._vrp2_barcode()
        if barcode:
            dto["ean"] = barcode
        if self.default_code:
            dto["codeCustom"] = self.default_code
        cat_id = self._resolve_vrp2_category_id()
        if cat_id:
            dto["categoryId"] = cat_id
        if self.vrp2_note:
            dto["note"] = self.vrp2_note[:1000]
        return dto

    def _to_vrp2_update_dto(self, vat_id, tax):
        """Build dto for POST /v1/service/setservicedata."""
        self.ensure_one()
        price_with_vat = self._compute_price_with_vat(tax)
        dto = {
            "code": self.vrp2_code,
            "priceWithVat": price_with_vat,
            "vatId": vat_id,
            "favourite": self.vrp2_favourite,
            "invalid": False,
        }
        barcode = self._vrp2_barcode()
        if barcode:
            dto["ean"] = barcode
        if self.default_code:
            dto["codeCustom"] = self.default_code
        cat_id = self._resolve_vrp2_category_id()
        if cat_id:
            dto["categoryId"] = cat_id
        if self.vrp2_note:
            dto["note"] = self.vrp2_note[:1000]
        return dto

    def _compute_price_with_vat(self, tax):
        """Compute gross price (with VAT) from Odoo's net list_price.

        Odoo stores list_price WITHOUT tax; VRP2 expects priceWithVat. We use
        the tax engine (``compute_all``) so price-included taxes, fixed
        amounts and Odoo rounding all behave consistently — not a naive
        percentage multiplication.
        """
        self.ensure_one()
        net = self.list_price or 0.0
        if not net:
            return None
        result = tax.compute_all(
            net, currency=self.currency_id, quantity=1.0, product=self
        )
        return round(result["total_included"], 2)

    @api.model
    def _vrp2_warn_if_truncated(self, resp, what):
        """Log a warning if VRP2 returned fewer rows than the total count.

        Pagination of the service list is not implemented; surface it loudly
        rather than silently syncing a partial catalog.
        """
        total = resp.get("resultTotalCount")
        count = resp.get("resultCount")
        results = resp.get("results") or []
        n = count if count is not None else len(results)
        if total is not None and n < total:
            _logger.warning(
                "VRP2 %s list truncated: received %s of %s rows; "
                "pagination is not implemented.",
                what, n, total,
            )

    def _vrp2_barcode(self):
        """Get barcode from first product variant (barcode is on product.product)."""
        self.ensure_one()
        for variant in self.product_variant_ids:
            if variant.barcode:
                return variant.barcode
        return None

    def _resolve_vrp2_category_id(self):
        """Walk up to the top-level pos.category and return its vrp2_id."""
        for categ in self.pos_categ_ids:
            root = categ
            while root.parent_id:
                root = root.parent_id
            if root.vrp2_id:
                return root.vrp2_id
        return None
