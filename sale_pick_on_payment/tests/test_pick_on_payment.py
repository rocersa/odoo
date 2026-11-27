# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPickOnPayment(TransactionCase):
    """The delivery is created on full payment or by a deliberate release, never
    at confirmation. These tests follow the path a user takes: confirm the
    order, invoice it, register payment, or press *Create Delivery*."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Pick On Payment Customer",
        })
        cls.product = cls.env["product.product"].create({
            "name": "Corten Ring 450",
            "type": "consu",
            "is_storable": True,
            "invoice_policy": "order",
            "list_price": 100.0,
            "taxes_id": [(5, 0, 0)],
        })
        cls.service = cls.env["product.product"].create({
            "name": "Cutting service",
            "type": "service",
            "invoice_policy": "order",
            "list_price": 50.0,
            "taxes_id": [(5, 0, 0)],
        })
        cls.bank_journal = cls.env["account.journal"].search([
            ("type", "=", "bank"),
            ("company_id", "=", cls.env.company.id),
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env["account.journal"].create({
                "name": "Bank",
                "type": "bank",
                "code": "BNK",
            })

    def _order(self, *products):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [
                (0, 0, {
                    "product_id": product.id,
                    "product_uom_qty": 1,
                })
                for product in products
            ],
        })

    def _confirmed_invoiced(self, *products):
        order = self._order(*products)
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        return order, invoice

    def _register_payment(self, invoice, amount=None):
        vals = {"journal_id": self.bank_journal.id}
        if amount is not None:
            vals["amount"] = amount
        wizard = self.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create(vals)
        wizard.action_create_payments()
        invoice.invalidate_recordset()

    def test_confirmation_creates_invoice_but_no_pick(self):
        order, invoice = self._confirmed_invoiced(self.product)

        self.assertEqual(order.state, "sale")
        self.assertEqual(order.invoice_ids, invoice)
        self.assertFalse(order.picking_ids)
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_full_payment_creates_exactly_one_pick(self):
        order, invoice = self._confirmed_invoiced(self.product)
        self.assertFalse(order.picking_ids)

        self._register_payment(invoice)

        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertEqual(len(order.picking_ids), 1)
        self.assertNotEqual(order.picking_ids.state, "cancel")

    def test_partial_payment_does_not_create_pick(self):
        order, invoice = self._confirmed_invoiced(self.product)

        self._register_payment(invoice, amount=40.0)

        self.assertEqual(invoice.payment_state, "partial")
        self.assertFalse(order.picking_ids)

    def test_second_payment_or_resave_does_not_duplicate_pick(self):
        order, invoice = self._confirmed_invoiced(self.product)
        self._register_payment(invoice)
        self.assertEqual(len(order.picking_ids), 1)

        # A re-save or a repeated hook must reuse the delivery, not add one.
        invoice._invoice_paid_hook()
        order._sale_pick_create_if_paid()
        order.action_sale_pick_create_delivery()

        self.assertEqual(len(order.picking_ids), 1)

    def test_manual_release_creates_pick_and_records_who_and_when(self):
        order = self._order(self.product)
        order.action_confirm()
        self.assertFalse(order.picking_ids)

        order.action_sale_pick_create_delivery()

        self.assertEqual(len(order.picking_ids), 1)
        self.assertTrue(order.pick_released)
        self.assertEqual(order.pick_release_user_id, self.env.user)
        self.assertTrue(order.pick_release_date)

    def test_cancelled_pick_is_not_recreated_automatically(self):
        order, invoice = self._confirmed_invoiced(self.product)
        order.action_sale_pick_create_delivery()
        self.assertEqual(len(order.picking_ids), 1)
        order.picking_ids.action_cancel()
        self.assertEqual(order.picking_ids.state, "cancel")

        self._register_payment(invoice)
        order._sale_pick_create_if_paid()

        self.assertEqual(len(order.picking_ids), 1)
        self.assertEqual(order.picking_ids.state, "cancel")

    def test_manual_release_recreates_after_cancellation(self):
        order = self._order(self.product)
        order.action_confirm()
        order.action_sale_pick_create_delivery()
        order.picking_ids.action_cancel()

        created = order.action_sale_pick_create_delivery()

        active = order.picking_ids.filtered(lambda picking: picking.state != "cancel")
        self.assertEqual(len(active), 1)
        self.assertEqual(len(order.picking_ids), 2)
        self.assertEqual(created["res_model"], "stock.picking")

    def test_service_only_order_has_no_pick(self):
        order = self._order(self.service)
        order.action_confirm()

        self.assertFalse(order.picking_ids)
        self.assertFalse(order.sale_pick_missing)
