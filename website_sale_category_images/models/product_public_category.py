from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    category_image_ids = fields.One2many(
        string="Extra Images",
        comodel_name='product.public.category.image',
        inverse_name='category_id',
    )
