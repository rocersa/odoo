from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_images(self):
        images = super()._get_images()
        seen_categories = set()
        for category in self.product_tmpl_id.public_categ_ids.sorted('sequence'):
            for cat in category.parents_and_self.sorted(
                lambda c: -len(c.parent_path or '')
            ):
                if cat.id not in seen_categories:
                    seen_categories.add(cat.id)
                    images += list(cat.category_image_ids)
        return images
