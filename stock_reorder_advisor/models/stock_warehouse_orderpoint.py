# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math
from collections import defaultdict
from datetime import datetime, time
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero, float_round


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    analysis_days = fields.Integer(
        string='Analysis Period (days)',
        default=lambda self: self.env.company.reorder_analysis_days,
        help='Historical window used to compute demand statistics.',
    )
    service_level_pct = fields.Float(
        string='Target Service Level (%)',
        default=lambda self: self.env.company.reorder_default_service_level,
        help='Target probability of not stocking out during lead time.',
    )

    # ------------------------------------------------------------------
    # Demand pattern & statistics
    # ------------------------------------------------------------------
    demand_pattern = fields.Selection([
        ('none', 'No Demand'),
        ('smooth', 'Smooth'),
        ('erratic', 'Erratic'),
        ('intermittent', 'Intermittent'),
        ('lumpy', 'Lumpy'),
    ], string='Demand Pattern', compute='_compute_demand_stats', store=True)

    annual_demand_units = fields.Float(
        string='Annual Demand (units)', compute='_compute_demand_stats', store=True)
    avg_order_size = fields.Float(
        string='Avg Order Size', compute='_compute_demand_stats', store=True)
    max_order_size = fields.Float(
        string='Max Order Size', compute='_compute_demand_stats', store=True)
    avg_order_interval_days = fields.Float(
        string='Avg Order Interval (days)', compute='_compute_demand_stats', store=True)
    std_order_size = fields.Float(
        string='Order Size Std Dev', compute='_compute_demand_stats', store=True)
    std_order_interval_days = fields.Float(
        string='Order Interval Std Dev', compute='_compute_demand_stats', store=True)
    last_sale_date = fields.Date(
        string='Last Sale Date', compute='_compute_demand_stats', store=True)

    # ------------------------------------------------------------------
    # Lead-time risk
    # ------------------------------------------------------------------
    lead_time_demand = fields.Float(
        string='Lead-Time Demand', compute='_compute_demand_stats', store=True)
    lead_time_demand_std = fields.Float(
        string='Lead-Time Demand Std Dev', compute='_compute_demand_stats', store=True)

    # ------------------------------------------------------------------
    # Suggestions
    # ------------------------------------------------------------------
    suggested_safety_stock = fields.Float(
        string='Suggested Safety Stock', compute='_compute_suggestions', store=True)
    suggested_min_qty = fields.Float(
        string='Suggested Min Qty', compute='_compute_suggestions', store=True)
    suggested_max_qty = fields.Float(
        string='Suggested Max Qty', compute='_compute_suggestions', store=True)
    suggested_order_qty = fields.Float(
        string='Suggested Order Qty', compute='_compute_suggestions', store=True)
    coverage_days = fields.Float(
        string='Coverage (days)', compute='_compute_suggestions', store=True,
        help='Estimated days of stock on hand at current demand rate.')
    stockout_risk_score = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Stockout Risk', compute='_compute_suggestions', store=True)

    # ------------------------------------------------------------------
    # Advisor message
    # ------------------------------------------------------------------
    advisor_message = fields.Html(
        string='Advisor Notes', compute='_compute_advisor_message', store=True,
        sanitize=True)

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    @api.depends('product_id', 'location_id', 'analysis_days',
                 'product_id.stock_move_ids.state',
                 'product_id.stock_move_ids.date')
    def _compute_demand_stats(self):
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint._set_no_demand()
                continue

            wh_location_ids = orderpoint.env['stock.location'].search([
                ('id', 'child_of', orderpoint.warehouse_id.view_location_id.id)
            ]).ids
            stats = orderpoint.product_id._compute_demand_statistics(
                wh_location_ids, orderpoint.analysis_days)

            orderpoint.annual_demand_units = stats['annualised_demand']
            orderpoint.avg_order_size = stats['avg_order_size']
            orderpoint.max_order_size = stats['max_order_size']
            orderpoint.avg_order_interval_days = stats['avg_order_interval_days']
            orderpoint.std_order_size = stats['std_order_size']
            orderpoint.std_order_interval_days = stats['std_interval_days']
            orderpoint.last_sale_date = stats['last_sale_date']

            orderpoint.demand_pattern = orderpoint._classify_demand_pattern(
                stats['order_count'],
                stats['avg_order_interval_days'],
                stats['std_order_size'],
                stats['avg_order_size'],
            )

            # Lead-time demand
            lead_days = orderpoint.lead_days or 0.0
            daily_rate = (stats['annualised_demand'] / 365.0)
            orderpoint.lead_time_demand = daily_rate * lead_days

            # Combine size and interval uncertainty for lead-time std dev.
            # This is a heuristic: if intervals are long, demand is effectively
            # a compound Poisson-like process during lead time.
            if stats['order_count'] < 2 or stats['avg_order_interval_days'] <= 0:
                orderpoint.lead_time_demand_std = stats['std_order_size']
            else:
                expected_orders_in_lead_time = lead_days / stats['avg_order_interval_days']
                variance_size = (stats['std_order_size'] ** 2) * expected_orders_in_lead_time
                variance_interval = (stats['avg_order_size'] ** 2) * expected_orders_in_lead_time
                orderpoint.lead_time_demand_std = math.sqrt(variance_size + variance_interval)

    @api.depends('lead_time_demand', 'lead_time_demand_std', 'service_level_pct',
                 'avg_order_size', 'annual_demand_units', 'demand_pattern',
                 'qty_on_hand')
    def _compute_suggestions(self):
        for orderpoint in self:
            rounding = orderpoint.product_uom.rounding
            service_level = max(0.0, min(100.0, orderpoint.service_level_pct or 95.0))
            z = self._service_level_to_z(service_level)

            safety = z * orderpoint.lead_time_demand_std
            suggested_min = orderpoint.lead_time_demand + safety

            # Slow movers: max should cover lead time + a review period.
            review_days = 30.0 if orderpoint.annual_demand_units < orderpoint.env.company.reorder_slow_mover_threshold else 14.0
            daily_rate = orderpoint.annual_demand_units / 365.0
            suggested_max = suggested_min + max(orderpoint.avg_order_size, daily_rate * review_days)

            orderpoint.suggested_safety_stock = float_round(safety, precision_rounding=rounding)
            orderpoint.suggested_min_qty = float_round(suggested_min, precision_rounding=rounding)
            orderpoint.suggested_max_qty = float_round(suggested_max, precision_rounding=rounding)
            orderpoint.suggested_order_qty = float_round(
                max(0.0, suggested_max - orderpoint.qty_forecast),
                precision_rounding=rounding,
            )

            # Coverage days based on annual demand
            if daily_rate > 0:
                orderpoint.coverage_days = orderpoint.qty_on_hand / daily_rate
            else:
                orderpoint.coverage_days = 9999.0

            orderpoint.stockout_risk_score = orderpoint._evaluate_stockout_risk()

    @api.depends('demand_pattern', 'stockout_risk_score', 'suggested_min_qty',
                 'suggested_max_qty', 'product_min_qty', 'product_max_qty',
                 'coverage_days', 'avg_order_size')
    def _compute_advisor_message(self):
        for orderpoint in self:
            messages = []
            pattern = orderpoint.demand_pattern

            if pattern == 'none':
                messages.append(_(
                    'No historical demand found in the analysis period. '
                    'Consider setting a manual Min/Max or reviewing whether '
                    'this product should remain stocked.'
                ))
            elif pattern == 'intermittent':
                messages.append(_(
                    'Intermittent demand: average gap between orders is '
                    '%(interval).0f days. A periodic review (e.g. monthly) '
                    'often works better than reacting to every sale.',
                    interval=orderpoint.avg_order_interval_days,
                ))
            elif pattern == 'lumpy':
                messages.append(_(
                    'Lumpy demand: order sizes vary widely. Ensure Min Qty can '
                    'absorb at least one large order (max historical size: '
                    '%(max_size).0f).',
                    max_size=orderpoint.max_order_size,
                ))
            elif pattern == 'erratic':
                messages.append(_(
                    'Erratic demand: both timing and quantity are variable. '
                    'Safety stock should be set conservatively.'
                ))

            if orderpoint.stockout_risk_score in ('high', 'critical'):
                messages.append(_(
                    'High stockout risk: current Min Qty (%(current_min).0f) is '
                    'below the suggested Min Qty (%(suggested_min).0f).',
                    current_min=orderpoint.product_min_qty,
                    suggested_min=orderpoint.suggested_min_qty,
                ))

            if orderpoint.coverage_days > 365:
                messages.append(_(
                    'More than one year of supply on hand. Consider reducing '
                    'Max Qty to free up capital and shelf space.'
                ))
            elif orderpoint.coverage_days < orderpoint.lead_days and orderpoint.demand_pattern != 'none':
                messages.append(_(
                    'Coverage (%(coverage).0f days) is less than supplier lead '
                    'time (%(lead).0f days). A replenishment should already be '
                    'in flight.',
                    coverage=orderpoint.coverage_days,
                    lead=orderpoint.lead_days,
                ))

            orderpoint.advisor_message = '<br/>'.join(messages) if messages else False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _set_no_demand(self):
        self.update({
            'demand_pattern': 'none',
            'annual_demand_units': 0.0,
            'avg_order_size': 0.0,
            'max_order_size': 0.0,
            'avg_order_interval_days': 0.0,
            'std_order_size': 0.0,
            'std_order_interval_days': 0.0,
            'last_sale_date': False,
            'lead_time_demand': 0.0,
            'lead_time_demand_std': 0.0,
        })

    def _classify_demand_pattern(self, order_count, avg_interval, std_size, avg_size):
        if order_count == 0:
            return 'none'
        if avg_size == 0:
            return 'none'
        cv_size = std_size / avg_size if avg_size else 0.0
        # Thresholds are rules of thumb from spare-parts inventory literature.
        is_intermittent = avg_interval > 30.0
        is_erratic = cv_size > 1.0
        if is_intermittent and is_erratic:
            return 'lumpy'
        if is_intermittent:
            return 'intermittent'
        if is_erratic:
            return 'erratic'
        return 'smooth'

    def _evaluate_stockout_risk(self):
        rounding = self.product_uom.rounding
        if self.demand_pattern == 'none':
            return 'low'
        if float_compare(self.product_min_qty, self.suggested_min_qty, precision_rounding=rounding) < 0:
            if self.coverage_days < self.lead_days:
                return 'critical'
            return 'high'
        if float_compare(self.product_max_qty, self.suggested_max_qty, precision_rounding=rounding) < 0:
            return 'medium'
        return 'low'

    @api.model
    def _service_level_to_z(self, service_level_pct):
        """Return the Z-score for a one-sided service level.

        Uses a coarse lookup table. Replace with a proper inverse normal CDF
        if higher precision is required.
        """
        table = {
            50.0: 0.00,
            60.0: 0.25,
            70.0: 0.52,
            75.0: 0.67,
            80.0: 0.84,
            85.0: 1.04,
            90.0: 1.28,
            95.0: 1.65,
            97.0: 1.88,
            98.0: 2.05,
            99.0: 2.33,
            99.5: 2.58,
            99.9: 3.09,
        }
        if service_level_pct in table:
            return table[service_level_pct]
        # Linear interpolation between nearest table entries.
        levels = sorted(table.keys())
        for i in range(1, len(levels)):
            if levels[i - 1] <= service_level_pct <= levels[i]:
                low_z, high_z = table[levels[i - 1]], table[levels[i]]
                ratio = (service_level_pct - levels[i - 1]) / (levels[i] - levels[i - 1])
                return low_z + (high_z - low_z) * ratio
        return table[95.0]

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_apply_suggested_min_max(self):
        for orderpoint in self:
            orderpoint.product_min_qty = orderpoint.suggested_min_qty
            orderpoint.product_max_qty = orderpoint.suggested_max_qty
        return True

    def action_recompute_advisor(self):
        self._compute_demand_stats()
        self._compute_suggestions()
        self._compute_advisor_message()
        return True

    @api.model
    def cron_recompute_advisor(self):
        """Nightly refresh of demand statistics and suggestions."""
        orderpoints = self.search([('product_id.is_storable', '=', True)])
        orderpoints.action_recompute_advisor()
