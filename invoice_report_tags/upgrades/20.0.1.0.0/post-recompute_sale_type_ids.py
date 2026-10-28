# -*- coding: utf-8 -*-
"""Recompute stored sale-type tags after the tag classification changed.

``sale_type_ids`` switched from a status-tag blacklist to a sale-type
allowlist, so previously stored values (e.g. the pickup-cage tag) are stale.
Odoo only auto-recomputes a stored computed field when its column is newly
added, so existing invoices must be marked for recomputation explicitly.
"""
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    moves = env['account.move'].search([
        ('move_type', 'in', ('out_invoice', 'out_refund')),
    ])
    if moves:
        env.add_to_compute(env['account.move']._fields['sale_type_ids'], moves)
