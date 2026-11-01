# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_disable_checkout = fields.Boolean(
        string="Quote Mode",
        related="website_id.is_disable_checkout",
        readonly=False,
        help="Hide the checkout button and replace it with a quote-request "
             "button on the cart page of this website.",
    )
