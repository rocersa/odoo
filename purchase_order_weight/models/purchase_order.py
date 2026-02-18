# Copyright 2023 ooops404
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    line_weight = fields.Float(
        "Weight (kgs)", compute="_compute_line_physical_properties", digits="Stock Weight"
    )

    @api.depends("product_uom_qty", "product_id")
    def _compute_line_physical_properties(self):
        for line in self:
            line.line_weight = line.product_id.weight * line.product_uom_qty

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    total_weight = fields.Float(
        compute="_compute_total_physical_properties",
        digits="Stock Weight",
        store=True,
    )
    total_weight_uom_id = fields.Many2one(
        "uom.uom",
        compute="_compute_total_physical_properties",
        store=True,
    )

    @api.depends("order_line.product_uom_qty", "order_line.product_id")
    def _compute_total_physical_properties(self):
        default_weight_uom = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("product_default_weight_uom_id")
        )

        for po in self:
            po.total_weight = sum(po.mapped("order_line.line_weight"))
            if default_weight_uom:
                po.total_weight_uom_id = int(default_weight_uom)