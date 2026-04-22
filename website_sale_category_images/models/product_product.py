from odoo import models
from odoo.http import request


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_images(self):
        images = super()._get_images()
        try:
            current_website = request.env['website'].get_current_website()
        except Exception:
            current_website = None
        seen = set()
        all_cats = []
        for category in self.product_tmpl_id.public_categ_ids.sorted('sequence'):
            for cat in category.parents_and_self:
                if cat.id not in seen:
                    seen.add(cat.id)
                    all_cats.append(cat)
        all_cats.sort(key=lambda c: -len(c.parent_path or ''))
        for cat in all_cats:
            cat_images = cat.category_image_ids
            if current_website:
                cat_images = cat_images.filtered(
                    lambda img: not img.website_ids or current_website in img.website_ids
                )
            images += list(cat_images)
        if images and images[0] == self and not self.image_1920 and len(images) > 1:
            images = images[1:]
        return images
