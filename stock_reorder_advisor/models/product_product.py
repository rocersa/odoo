# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # ------------------------------------------------------------------
    # Demand history helpers
    # ------------------------------------------------------------------
    def _get_done_outgoing_moves(self, location_ids, date_from, date_to=None, states=None):
        """Return done outgoing moves for this product from internal locations.

        :param location_ids: source locations to consider (usually a warehouse
            stock tree).
        :param date_from: datetime start of analysis window.
        :param date_to: datetime end of analysis window (defaults to now).
        :param states: move states to include (defaults to ['done']).
        :return: stock.move recordset.
        """
        self.ensure_one()
        date_to = date_to or fields.Datetime.now()
        states = states or ['done']
        domain = Domain.AND([
            [('product_id', '=', self.id)],
            [('state', 'in', states)],
            [('date', '>=', date_from), ('date', '<=', date_to)],
            [('location_id.usage', '=', 'internal')],
            ['|',
                ('location_dest_id.usage', 'in', ['customer', 'production']),
                '&',
                    ('location_dest_id.usage', '=', 'internal'),
                    ('location_dest_id', 'not in', location_ids)],
        ])
        return self.env['stock.move'].search(domain, order='date')

    def _get_demand_history(self, location_ids, analysis_days=365):
        """Group historical outgoing moves into demand events.

        Returns a list of dicts with keys: date, qty, origin (pickings/so).
        Consecutive same-day moves from the same origin are collapsed into one
        event so that a single multi-line shipment does not look like many
        small orders.
        """
        self.ensure_one()
        date_to = fields.Datetime.now()
        date_from = date_to - relativedelta(days=analysis_days)
        moves = self._get_done_outgoing_moves(location_ids, date_from, date_to)

        events = []
        current = None
        for move in moves:
            if move.quantity <= 0:
                continue
            origin = move.picking_id.origin or move.origin or ''
            key = (move.date.date(), origin)
            if current and current['_key'] == key:
                current['qty'] += move.product_uom._compute_quantity(
                    move.quantity, self.uom_id, round=False)
                current['move_ids'] |= move
            else:
                if current:
                    events.append(current)
                current = {
                    '_key': key,
                    'date': move.date,
                    'qty': move.product_uom._compute_quantity(
                        move.quantity, self.uom_id, round=False),
                    'origin': origin,
                    'move_ids': move,
                }
        if current:
            events.append(current)
        return events

    def _compute_demand_statistics(self, location_ids, analysis_days=365):
        """Compute basic demand statistics for the advisor.

        :return: dict with total_qty, order_count, avg_order_size,
            avg_order_interval_days, std_order_size, std_interval_days,
            max_order_size, annualised_demand, last_sale_date.
        """
        self.ensure_one()
        events = self._get_demand_history(location_ids, analysis_days)
        if not events:
            return {
                'total_qty': 0.0,
                'order_count': 0,
                'avg_order_size': 0.0,
                'avg_order_interval_days': 0.0,
                'std_order_size': 0.0,
                'std_interval_days': 0.0,
                'max_order_size': 0.0,
                'annualised_demand': 0.0,
                'last_sale_date': False,
            }

        quantities = [e['qty'] for e in events]
        dates = [e['date'] for e in events]
        intervals = []
        for i in range(1, len(dates)):
            delta = (dates[i] - dates[i - 1]).days
            if delta > 0:
                intervals.append(float(delta))

        total_qty = sum(quantities)
        order_count = len(quantities)
        avg_size = total_qty / order_count
        std_size = self._std_dev(quantities)
        max_size = max(quantities)
        last_sale_date = fields.Date.to_date(max(dates))

        avg_interval = sum(intervals) / len(intervals) if intervals else 0.0
        std_interval = self._std_dev(intervals)

        # Annualise based on observed span, not analysis window, to avoid
        # distortions when the product has only recently been sold.
        observed_days = max((dates[-1] - dates[0]).days, 1)
        annualised = total_qty * 365.0 / observed_days

        return {
            'total_qty': total_qty,
            'order_count': order_count,
            'avg_order_size': avg_size,
            'avg_order_interval_days': avg_interval,
            'std_order_size': std_size,
            'std_interval_days': std_interval,
            'max_order_size': max_size,
            'annualised_demand': annualised,
            'last_sale_date': last_sale_date,
        }

    @api.model
    def _std_dev(self, values):
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
