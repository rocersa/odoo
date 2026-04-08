from odoo import api, fields, models
from odoo.tools.image import is_image_size_above


class ProductPublicCategoryImage(models.Model):
    _name = 'product.public.category.image'
    _description = "Product Public Category Image"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    image_1920 = fields.Image()

    category_id = fields.Many2one(
        string="Category",
        comodel_name='product.public.category',
        ondelete='cascade',
        index=True,
        required=True,
    )
    website_ids = fields.Many2many(
        string="Websites",
        comodel_name='website',
        relation='product_public_category_image_website_rel',
        column1='category_image_id',
        column2='website_id',
    )

    can_image_1024_be_zoomed = fields.Boolean(
        string="Can Image 1024 be zoomed",
        compute='_compute_can_image_1024_be_zoomed',
        store=True,
    )

    @api.depends('image_1920', 'image_1024')
    def _compute_can_image_1024_be_zoomed(self):
        for image in self.with_context(bin_size=False):
            image.can_image_1024_be_zoomed = (
                image.image_1920 and is_image_size_above(image.image_1920, image.image_1024)
            )
