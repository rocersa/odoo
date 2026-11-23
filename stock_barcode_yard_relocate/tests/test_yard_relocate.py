# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestYardRelocate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        Location = cls.env["stock.location"]
        cls.source = Location.create({
            "name": "Yard A",
            "usage": "internal",
            "barcode": "YARD-A",
            "location_id": cls.warehouse.lot_stock_id.id,
        })
        cls.destination = Location.create({
            "name": "Yard B",
            "usage": "internal",
            "barcode": "YARD-B",
            "location_id": cls.warehouse.lot_stock_id.id,
        })
        cls.child = Location.create({
            "name": "Yard A Shelf 1",
            "usage": "internal",
            "barcode": "YARD-A-1",
            "location_id": cls.source.id,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Corten Ring 450",
            "default_code": "CorRin450",
            "barcode": "P0002308",
            "type": "consu",
            "is_storable": True,
        })
        cls.other_product = cls.env["product.product"].create({
            "name": "Corten Corner",
            "default_code": "CorCnr",
            "barcode": "P0002309",
            "type": "consu",
            "is_storable": True,
        })
        cls.relocate = cls.env["stock.yard.relocate"]
        cls.quant = cls.env["stock.quant"]

    def _qty_at(self, product, location):
        quants = self.env["stock.quant"].search([
            ("product_id", "=", product.id),
            ("location_id", "=", location.id),
        ])
        return sum(quants.mapped("quantity"))

    def _stock(self, product, location, quantity, **kwargs):
        return self.quant._update_available_quantity(
            product, location, quantity, **kwargs
        )

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def test_resolve_location_by_barcode(self):
        result = self.relocate.resolve_location("YARD-A")
        self.assertTrue(result["ok"])
        self.assertEqual(result["id"], self.source.id)

    def test_resolve_location_by_full_path(self):
        result = self.relocate.resolve_location(self.destination.complete_name)
        self.assertTrue(result["ok"])
        self.assertEqual(result["id"], self.destination.id)

    def test_resolve_location_unknown(self):
        result = self.relocate.resolve_location("no-such-label")
        self.assertFalse(result["ok"])
        self.assertIn("No internal location", result["warning"])

    def test_resolve_location_ambiguous_leaf_name(self):
        self.env["stock.location"].create({
            "name": "Yard A",
            "usage": "internal",
            "location_id": self.warehouse.view_location_id.id,
        })
        result = self.relocate.resolve_location("Yard A")
        self.assertFalse(result["ok"])
        self.assertIn("Several locations", result["warning"])

    def test_scan_product_by_barcode_and_by_reference(self):
        self._stock(self.product, self.source, 5)
        by_barcode = self.relocate.scan_product(self.source.id, "P0002308")
        self.assertTrue(by_barcode["ok"])
        self.assertEqual(by_barcode["product_id"], self.product.id)
        self.assertEqual(by_barcode["qty"], 5.0)
        by_reference = self.relocate.scan_product(self.source.id, "CorRin450")
        self.assertTrue(by_reference["ok"])
        self.assertEqual(by_reference["product_id"], self.product.id)

    def test_scan_product_queues_full_quantity_at_exact_location_only(self):
        self._stock(self.product, self.source, 5)
        self._stock(self.product, self.child, 3)
        result = self.relocate.scan_product(self.source.id, "P0002308")
        self.assertTrue(result["ok"])
        self.assertEqual(result["qty"], 5.0)
        # Nothing moves on scan.
        self.assertEqual(self._qty_at(self.product, self.source), 5.0)
        self.assertEqual(self._qty_at(self.product, self.child), 3.0)

    def test_scan_product_without_stock_warns(self):
        result = self.relocate.scan_product(self.source.id, "P0002309")
        self.assertFalse(result["ok"])
        self.assertIn("has no stock", result["warning"])

    def test_scan_unknown_product_warns(self):
        result = self.relocate.scan_product(self.source.id, "nope")
        self.assertFalse(result["ok"])
        self.assertIn("No product matches", result["warning"])

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------
    def test_commit_moves_entire_quantity_and_leaves_children(self):
        self._stock(self.product, self.source, 5)
        self._stock(self.product, self.child, 3)

        result = self.relocate.commit(
            self.source.id, self.destination.id, [self.product.id]
        )

        self.assertEqual(len(result["moved"]), 1)
        self.assertEqual(self._qty_at(self.product, self.source), 0.0)
        self.assertEqual(self._qty_at(self.product, self.destination), 5.0)
        self.assertEqual(self._qty_at(self.product, self.child), 3.0)

        move = self.env["stock.move"].search(
            [("product_id", "=", self.product.id),
             ("location_dest_id", "=", self.destination.id)],
            limit=1,
        )
        self.assertTrue(move)
        self.assertIn("Yard relocate:", move.inventory_name)
        self.assertIn(self.source.complete_name, move.inventory_name)
        self.assertIn(self.destination.complete_name, move.inventory_name)
        self.assertIn(self.env.user.name, move.inventory_name)

    def test_commit_moves_every_queued_product(self):
        self._stock(self.product, self.source, 5)
        self._stock(self.other_product, self.source, 2)

        result = self.relocate.commit(
            self.source.id,
            self.destination.id,
            [self.product.id, self.other_product.id],
        )

        self.assertEqual(len(result["moved"]), 2)
        self.assertEqual(self._qty_at(self.product, self.destination), 5.0)
        self.assertEqual(self._qty_at(self.other_product, self.destination), 2.0)

    def test_commit_blocks_identical_locations(self):
        self._stock(self.product, self.source, 5)
        with self.assertRaises(UserError):
            self.relocate.commit(
                self.source.id, self.source.id, [self.product.id]
            )
        self.assertEqual(self._qty_at(self.product, self.source), 5.0)

    def test_commit_empty_list_is_a_noop(self):
        moves_before = self.env["stock.move"].search_count([])
        result = self.relocate.commit(self.source.id, self.destination.id, [])
        self.assertEqual(result["moved"], [])
        self.assertEqual(result["skipped"], [])
        self.assertEqual(self.env["stock.move"].search_count([]), moves_before)

    def test_commit_skips_a_product_without_stock(self):
        self._stock(self.product, self.source, 5)
        result = self.relocate.commit(
            self.source.id,
            self.destination.id,
            [self.product.id, self.other_product.id],
        )
        self.assertEqual(len(result["moved"]), 1)
        self.assertEqual(len(result["skipped"]), 1)

    def test_commit_keeps_the_package_intact(self):
        package = self.env["stock.package"].create({"name": "Yard pack 1"})
        self._stock(self.product, self.source, 4, package_id=package)

        self.relocate.commit(self.source.id, self.destination.id, [self.product.id])

        quant = self.env["stock.quant"].search([
            ("product_id", "=", self.product.id),
            ("location_id", "=", self.destination.id),
        ])
        self.assertEqual(sum(quant.mapped("quantity")), 4.0)
        self.assertEqual(quant.package_id, package)

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------
    def test_non_inventory_user_is_refused(self):
        user = self.env["res.users"].create({
            "name": "Yard Guest",
            "login": "yard_guest_relocate_test",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            self.env["stock.yard.relocate"].with_user(user).resolve_location("YARD-A")
