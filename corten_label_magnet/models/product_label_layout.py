from odoo import _, fields, models
from odoo.exceptions import UserError

MAGNET_70 = "corten_magnet"
MAGNET_100 = "corten_magnet_100"
MAGNET_REPORTS = {
    MAGNET_70: "corten_label_magnet.action_corten_label_location",
    MAGNET_100: "corten_label_magnet.action_corten_label_location_100",
}


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(
        selection_add=[
            (MAGNET_70, "Magnet label (72 x 70 mm)"),
            (MAGNET_100, "Magnet label wide (72 x 100 mm)"),
        ],
        ondelete={MAGNET_70: "set default", MAGNET_100: "set default"},
    )

    def _prepare_report_data(self):
        if self.print_format not in MAGNET_REPORTS:
            return super()._prepare_report_data()
        self.ensure_one()
        if self.custom_quantity <= 0:
            raise UserError(_("You need to set a positive quantity."))

        # Odoo 20 builds a generic ``labels`` list for its own label templates.
        # The magnet report renders its PNGs in Python, so it keeps the v19
        # ``quantity_by_product`` contract instead.
        requests = self._get_label_requests()
        quantities = {}
        active_model = "product.product"
        for request in requests:
            product = request["product"]
            active_model = product._name
            quantities[product.id] = quantities.get(product.id, 0) + request["copies"]

        return MAGNET_REPORTS[self.print_format], {
            "active_model": active_model,
            "quantity_by_product": quantities,
        }
