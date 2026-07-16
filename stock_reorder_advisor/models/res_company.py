# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    reorder_default_service_level = fields.Float(
        string='Default Service Level (%)',
        default=95.0,
        help='Default target probability of not stocking out during lead time. '
             'Used by the reorder advisor when no per-product override is set.',
    )
    reorder_analysis_days = fields.Integer(
        string='Default Analysis Period (days)',
        default=365,
        help='Number of days of historical done outgoing moves used to '
             'calculate demand statistics.',
    )
    reorder_slow_mover_threshold = fields.Float(
        string='Slow-Mover Annual Threshold (units)',
        default=20.0,
        help='Products with annual demand below this threshold are treated as '
             'slow movers and advised with longer review cycles.',
    )
