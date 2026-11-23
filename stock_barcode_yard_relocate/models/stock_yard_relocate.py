# -*- coding: utf-8 -*-
"""Server side of the barcode app's yard relocate flow.

The client keeps the queued products; these methods resolve the scanned
barcodes and do the single atomic move on confirm.
"""

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError


class StockYardRelocate(models.TransientModel):
    _name = "stock.yard.relocate"
    _description = "Yard Relocate"

    # ------------------------------------------------------------------
    # Guards and lookups
    # ------------------------------------------------------------------
    @api.model
    def _check_user(self):
        if not self.env.user.has_group("stock.group_stock_user"):
            raise AccessError(_("Only inventory users can move stock from the barcode app."))

    @api.model
    def _location_domain(self):
        return [
            ("usage", "=", "internal"),
            ("company_id", "in", self.env.companies.ids + [False]),
        ]

    @api.model
    def _find_locations(self, barcode):
        """Return the internal locations a scanned label could mean.

        Labels carry the location's barcode, falling back to its full path
        (``corten_label_magnet``), so try the barcode first, then the path,
        then a leaf name. A barcode and a full path are unique; a leaf name
        may match several locations and the caller decides.
        """
        barcode = (barcode or "").strip()
        if not barcode:
            return self.env["stock.location"]
        Location = self.env["stock.location"]
        domain = self._location_domain()
        location = Location.search(domain + [("barcode", "=", barcode)], limit=1)
        if location:
            return location
        location = Location.search(domain + [("complete_name", "=", barcode)], limit=1)
        if location:
            return location
        candidates = Location.search(domain + [("complete_name", "=ilike", barcode)])
        if not candidates:
            candidates = Location.search(domain + [("name", "=ilike", barcode)])
        return candidates

    @api.model
    def _find_product(self, barcode):
        """Resolve a product label to one product.

        Product labels carry the product's barcode, falling back to its
        internal reference, so try both.
        """
        barcode = (barcode or "").strip()
        if not barcode:
            return self.env["product.product"]
        Product = self.env["product.product"]
        product = Product.search([("barcode", "=", barcode)], limit=1)
        if product:
            return product
        product = Product.search([("default_code", "=", barcode)], limit=1)
        if product:
            return product
        candidates = Product.search([("default_code", "=ilike", barcode)])
        return candidates if len(candidates) == 1 else Product

    @api.model
    def _get_location(self, location_id):
        try:
            location = self.env["stock.location"].browse(int(location_id)).exists()
        except (TypeError, ValueError):
            location = self.env["stock.location"]
        if (
            not location
            or location.usage != "internal"
            or (location.company_id and location.company_id not in self.env.companies)
        ):
            raise UserError(_("Choose an internal location first."))
        return location

    @api.model
    def _source_quants(self, location, product):
        """The product's positive quants at the exact scanned location."""
        return self.env["stock.quant"].search([
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("quantity", ">", 0),
        ])

    # ------------------------------------------------------------------
    # Client API
    # ------------------------------------------------------------------
    @api.model
    def resolve_location(self, barcode):
        """Return the location a scanned label points at."""
        self._check_user()
        barcode = (barcode or "").strip()
        if not barcode:
            return {"ok": False, "warning": _("Scan a location label.")}
        locations = self._find_locations(barcode)
        if not locations:
            return {
                "ok": False,
                "warning": _(
                    "No internal location matches %(barcode)s. Scan a location label.",
                    barcode=barcode,
                ),
            }
        if len(locations) > 1:
            return {
                "ok": False,
                "warning": _(
                    "Several locations match %(barcode)s. Scan the location's barcode.",
                    barcode=barcode,
                ),
            }
        location = locations
        return {
            "ok": True,
            "id": location.id,
            "name": location.complete_name,
        }

    @api.model
    def scan_product(self, source_location_id, barcode):
        """Return the product and its full quantity at the source, if any."""
        self._check_user()
        source = self._get_location(source_location_id)
        barcode = (barcode or "").strip()
        if not barcode:
            return {"ok": False, "warning": _("Scan a product label.")}
        product = self._find_product(barcode)
        if not product:
            return {
                "ok": False,
                "warning": _("No product matches %(barcode)s.", barcode=barcode),
            }
        quants = self._source_quants(source, product)
        quantity = sum(quants.mapped("quantity"))
        if quantity <= 0:
            return {
                "ok": False,
                "warning": _(
                    "%(product)s has no stock at %(location)s. Nothing queued.",
                    product=product.display_name,
                    location=source.display_name,
                ),
            }
        return {
            "ok": True,
            "product_id": product.id,
            "name": product.display_name,
            "qty": quantity,
            "uom": product.uom_id.name,
        }

    @api.model
    def commit(self, source_location_id, dest_location_id, product_ids):
        """Move every queued product's full quantity from source to destination."""
        self._check_user()
        source = self._get_location(source_location_id)
        destination = self._get_location(dest_location_id)
        if source == destination:
            raise UserError(_("The source and destination locations must differ."))
        try:
            ids = [int(product_id) for product_id in (product_ids or [])]
        except (TypeError, ValueError):
            raise UserError(_("The queued product list is invalid.")) from None
        products = self.env["product.product"].browse(ids).exists()
        if not products:
            return {"moved": [], "skipped": []}

        message = _(
            "Yard relocate: %(source)s -> %(destination)s (%(user)s)",
            source=source.complete_name,
            destination=destination.complete_name,
            user=self.env.user.name,
        )
        moved, skipped = [], []
        for product in products:
            quants = self._source_quants(source, product)
            if not quants:
                skipped.append(product.display_name)
                continue
            moved.append({
                "product_id": product.id,
                "name": product.display_name,
                "qty": sum(quants.mapped("quantity")),
                "uom": product.uom_id.name,
            })
            # Follow the core relocate wizard: drop any pending inventory
            # count before the quant moves with it.
            quants.action_clear_inventory_quantity()
            quants.move_quants(location_dest_id=destination, message=message)

        return {
            "moved": moved,
            "skipped": skipped,
            "message": message,
        }
