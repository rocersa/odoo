from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_images(self):
        images = super()._get_images()
        seen = set()
        all_cats = []
        for category in self.product_tmpl_id.public_categ_ids.sorted('sequence'):
            for cat in category.parents_and_self:
                if cat.id not in seen:
                    seen.add(cat.id)
                    all_cats.append(cat)
        all_cats.sort(key=lambda c: -len(c.parent_path or ''))
        for cat in all_cats:
            images += list(cat.category_image_ids)
        return images
