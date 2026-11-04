from odoo import fields, models

MAGNET_70 = "corten_magnet"
MAGNET_100 = "corten_magnet_100"
MAGNET_IMAGE = "corten_magnet_image"
MAGNET_REPORTS = {
    MAGNET_70: "corten_label_magnet.action_corten_label_location",
    MAGNET_100: "corten_label_magnet.action_corten_label_location_100",
    MAGNET_IMAGE: "corten_label_magnet.action_corten_label_location_image",
}


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(
        selection_add=[
            (MAGNET_70, "Magnet label (72 x 70 mm)"),
            (MAGNET_100, "Magnet label wide (72 x 100 mm)"),
            (MAGNET_IMAGE, "Magnet label with image (72 x 120 mm)"),
        ],
        ondelete={MAGNET_70: "set default", MAGNET_100: "set default",
                  MAGNET_IMAGE: "set default"},
    )

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        if self.print_format in MAGNET_REPORTS:
            xml_id = MAGNET_REPORTS[self.print_format]
        return xml_id, data
