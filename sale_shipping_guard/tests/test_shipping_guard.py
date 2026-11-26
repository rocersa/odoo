# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

SHIPPING_ERROR = "Please select a shipping method before confirming this order."


@tagged("post_install", "-at_install")
class TestShippingGuard(TransactionCase):
    """The guard lives on the confirmation hook; these tests exercise it through
    action_confirm, which is the path a user takes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Shipping Guard Customer",
        })
        cls.physical = cls.env["product.product"].create({
            "name": "Corten Ring 450",
            "type": "consu",
        })
        cls.service = cls.env["product.product"].create({
            "name": "Cutting service",
            "type": "service",
        })
        delivery_product = cls.env["product.product"].create({
            "name": "Collect",
            "type": "service",
        })
        cls.collect = cls.env["delivery.carrier"].create({
            "name": "Collect",
            "delivery_type": "fixed",
            "fixed_price": 0,
            "product_id": delivery_product.id,
        })

    def _order(self, *products):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                (0, 0, {"product_id": product.id, "product_uom_qty": 1})
                for product in products
            ],
        })

    def test_physical_without_carrier_is_blocked(self):
        order = self._order(self.physical)
        self.assertEqual(order._confirmation_error_message(), SHIPPING_ERROR)
        with self.assertRaises(UserError) as caught:
            order.action_confirm()
        self.assertEqual(caught.exception.args[0], SHIPPING_ERROR)
        self.assertEqual(order.state, "draft")

    def test_physical_with_collect_confirms(self):
        order = self._order(self.physical)
        order.carrier_id = self.collect
        self.assertFalse(order._confirmation_error_message())
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_service_only_without_carrier_confirms(self):
        order = self._order(self.service)
        self.assertFalse(order._confirmation_error_message())
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_missing_product_returns_core_error_first(self):
        order = self._order(self.physical)
        self.env["sale.order.line"].create({
            "order_id": order.id,
            "name": "Line without a product",
            "product_uom_qty": 1,
        })
        error = order._confirmation_error_message()
        self.assertTrue(error)
        self.assertNotEqual(error, SHIPPING_ERROR)
