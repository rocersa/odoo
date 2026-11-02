# -*- coding: utf-8 -*-
from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    # Kept under the vendor module's field name so the existing AU setting and
    # column survive the module replacement.
    is_disable_checkout = fields.Boolean(string="Quote Mode")
