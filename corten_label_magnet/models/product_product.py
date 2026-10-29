from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    corten_label_png = fields.Binary(
        "Magnet Label", compute="_compute_corten_label_png", store=False)

    def _compute_corten_label_png(self):
        helper = self.env["corten.label.image"]
        for rec in self:
            code = rec.barcode or rec.default_code or ""
            rec.corten_label_png = helper.get_label_image(
                "product", rec.display_name, code, rec.default_code)
