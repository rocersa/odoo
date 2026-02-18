# -*- coding: utf-8 -*-
from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    category_id = fields.Many2many(
        'res.partner.category',
        relation='crm_lead_res_partner_category_rel',
        column1='lead_id',
        column2='category_id',
        string='Customer Type',
        related='partner_id.category_id',
        readonly=False,
        help="Tags from the related customer/partner"
    )
