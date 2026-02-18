from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_disable_checkout = fields.Boolean(string="Disable Proceed to Checkout", related='website_id.is_disable_checkout',
                                         readonly=False)
