from odoo import fields, models

class Website(models.Model):
    _inherit = 'website'

    is_disable_checkout = fields.Boolean(string="Disable Proceed to Checkout",)