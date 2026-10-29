from odoo import fields, models


class StockLocation(models.Model):
    _inherit = "stock.location"

    corten_label_png = fields.Binary(
        "Magnet Label", compute="_compute_corten_label_png", store=False)

    def _compute_corten_label_png(self):
        helper = self.env["corten.label.image"]
        for rec in self:
            code = rec.barcode or rec.complete_name or ""
            rec.corten_label_png = helper.get_label_image(
                "location", rec.complete_name, code)
