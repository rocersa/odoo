# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Payment states that mean the invoice is fully covered. ``in_payment`` is a
# registered payment that has not cleared the bank yet; it is still full
# payment, not a partial one.
SETTLED_PAYMENT_STATES = ("paid", "in_payment")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pick_released = fields.Boolean(
        string="Delivery Released",
        copy=False,
        readonly=True,
        help="Set when staff released the delivery by hand before payment.",
    )
    pick_release_user_id = fields.Many2one(
        "res.users",
        string="Released By",
        copy=False,
        readonly=True,
    )
    pick_release_date = fields.Datetime(
        string="Released On",
        copy=False,
        readonly=True,
    )
    sale_pick_missing = fields.Boolean(
        string="Delivery Can Be Created",
        compute="_compute_sale_pick_missing",
        help="The order is confirmed, has stockable lines, and has no active delivery.",
    )

    @api.depends("state", "picking_ids", "order_line.product_id")
    def _compute_sale_pick_missing(self):
        for order in self:
            has_active_delivery = any(
                picking.state != "cancel" for picking in order.picking_ids
            )
            has_stockable_line = any(
                not line.display_type and line.product_id.type == "consu"
                for line in order.order_line
            )
            order.sale_pick_missing = (
                order.state == "sale"
                and not has_active_delivery
                and has_stockable_line
            )

    def _sale_pick_active_deliveries(self):
        self.ensure_one()
        return self.picking_ids.filtered(lambda picking: picking.state != "cancel")

    def _sale_pick_has_settled_invoice(self):
        """True when the whole order is invoiced and every invoice is settled.

        Requiring the order to be fully invoiced stops a paid deposit invoice
        (a down payment) from releasing the delivery before the balance is
        invoiced and paid.
        """
        self.ensure_one()
        if self.invoice_status != "invoiced":
            return False
        invoices = self.invoice_ids.filtered(
            lambda move: move.move_type == "out_invoice"
        )
        return bool(invoices) and all(
            invoice.state == "posted"
            and invoice.payment_state in SETTLED_PAYMENT_STATES
            for invoice in invoices
        )

    def _sale_pick_is_released(self):
        """A delivery may be created once the order is paid or released by hand."""
        self.ensure_one()
        return bool(self.pick_released or self._sale_pick_has_settled_invoice())

    def _sale_pick_create_delivery(self, manual=False):
        """Create the delivery at most once for a released order.

        Automatic callers (``manual=False``) never recreate a cancelled pick.
        A manual release is explicit, so it may create a fresh pick after a
        cancellation, but it still reuses an active one.
        """
        self.ensure_one()
        active = self._sale_pick_active_deliveries()
        if active:
            return active
        if self.picking_ids and not manual:
            return self.env["stock.picking"]
        if not manual and not self._sale_pick_is_released():
            return self.env["stock.picking"]

        if manual:
            if not self.pick_released or not self.pick_release_user_id:
                self.write({
                    "pick_released": True,
                    "pick_release_user_id": self.env.user.id,
                    "pick_release_date": fields.Datetime.now(),
                })
                self.message_post(body=_(
                    "Delivery released by hand by %(user)s.",
                    user=self.env.user.name,
                ))

        before = self.picking_ids
        self.order_line._action_launch_stock_rule()
        return self.picking_ids - before

    def _sale_pick_create_if_paid(self):
        """Create the delivery for paid orders that do not have one yet."""
        for order in self:
            if order.state != "sale":
                continue
            if not order._sale_pick_is_released():
                continue
            order._sale_pick_create_delivery(manual=False)

    def action_sale_pick_create_delivery(self):
        """Release the delivery by hand for an urgent order or trusted customer."""
        self.ensure_one()
        created = self._sale_pick_create_delivery(manual=True)
        if not created:
            raise UserError(_(
                "There is no stockable product on this order to deliver, or the "
                "delivery could not be created."
            ))
        return self.action_view_delivery()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, *, previous_product_uom_qty=False):
        released = self.filtered(
            lambda line: line.order_id._sale_pick_is_released()
        )
        return super(SaleOrderLine, released)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
