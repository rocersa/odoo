from odoo import fields, models

MAGNET_FORMAT = "corten_magnet"
MAGNET_REPORT = "corten_label_magnet.action_corten_label_location"


class ProductLabelLayout(models.TransientModel):
    _inherit = "product.label.layout"

    print_format = fields.Selection(
        selection_add=[(MAGNET_FORMAT, "Magnet label (72 x 70 mm)")],
        ondelete={MAGNET_FORMAT: "set default"},
    )

    def _prepare_report_data(self):
        xml_id, data = super()._prepare_report_data()
        if self.print_format == MAGNET_FORMAT:
            xml_id = MAGNET_REPORT
        return xml_id, data
