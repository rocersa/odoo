# -*- coding: utf-8 -*-
"""Point striped companies at the module's local striped layout."""
try:
    from odoo.upgrade import util
    _env = util.env
except ImportError:  # local development: the upgrade utils live on the platform
    from odoo import SUPERUSER_ID, api

    def _env(cr):
        return api.Environment(cr, SUPERUSER_ID, {})


def migrate(cr, version):
    env = _env(cr)
    raw = env['ir.config_parameter'].sudo().get_param(
        'brand_report_layout.striped_company_ids')
    if not raw:
        return
    new_view = env.ref('brand_report_layout.external_layout_striped',
                       raise_if_not_found=False)
    if not new_view:
        return
    ids = [int(value) for value in raw.split(',') if value.strip()]
    env['res.company'].browse(ids).write({
        'external_report_layout_id': new_view.id,
    })
    env['ir.config_parameter'].sudo().set_param(
        'brand_report_layout.striped_company_ids', False)
