# -*- coding: utf-8 -*-
"""Remember which companies were on the stock striped layout.

Odoo 20 deletes web.external_layout_striped. Capture the companies using it
before the core upgrade removes the view, then point them at our local copy in
the post script.
"""
try:
    from odoo.upgrade import util
    _env = util.env
except ImportError:  # local development: the upgrade utils live on the platform
    from odoo import SUPERUSER_ID, api

    def _env(cr):
        return api.Environment(cr, SUPERUSER_ID, {})


def migrate(cr, version):
    env = _env(cr)
    old_view = env.ref('web.external_layout_striped', raise_if_not_found=False)
    if not old_view:
        return
    companies = env['res.company'].search([
        ('external_report_layout_id', '=', old_view.id),
    ])
    if companies:
        env['ir.config_parameter'].sudo().set_param(
            'brand_report_layout.striped_company_ids',
            ','.join(str(company.id) for company in companies),
        )
