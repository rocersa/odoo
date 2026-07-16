# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools


class ReorderSuggestionReport(models.Model):
    _name = 'reorder.suggestion.report'
    _description = 'Reorder Suggestion Report'
    _auto = False

    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', readonly=True)
    demand_pattern = fields.Selection([
        ('none', 'No Demand'),
        ('smooth', 'Smooth'),
        ('erratic', 'Erratic'),
        ('intermittent', 'Intermittent'),
        ('lumpy', 'Lumpy'),
    ], readonly=True)
    annual_demand_units = fields.Float(readonly=True)
    avg_order_size = fields.Float(readonly=True)
    max_order_size = fields.Float(readonly=True)
    avg_order_interval_days = fields.Float(readonly=True)
    lead_days = fields.Float(readonly=True)
    coverage_days = fields.Float(readonly=True)
    product_min_qty = fields.Float(readonly=True)
    product_max_qty = fields.Float(readonly=True)
    suggested_min_qty = fields.Float(readonly=True)
    suggested_max_qty = fields.Float(readonly=True)
    suggested_order_qty = fields.Float(readonly=True)
    stockout_risk_score = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], readonly=True)
    last_sale_date = fields.Date(readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    op.id,
                    op.id AS orderpoint_id,
                    op.product_id,
                    op.warehouse_id,
                    op.demand_pattern,
                    op.annual_demand_units,
                    op.avg_order_size,
                    op.max_order_size,
                    op.avg_order_interval_days,
                    op.lead_days,
                    op.coverage_days,
                    op.product_min_qty,
                    op.product_max_qty,
                    op.suggested_min_qty,
                    op.suggested_max_qty,
                    op.suggested_order_qty,
                    op.stockout_risk_score,
                    op.last_sale_date
                FROM stock_warehouse_orderpoint op
                WHERE op.active = TRUE
            )
        """ % (self._table,))
