"""Label renderer, report model and wizard wiring. Runs on the odoo.sh build."""
import base64
import io

from PIL import Image

from odoo.tests import TransactionCase, tagged

from ..tools.label_render import (
    barcode_fits,
    derive_location,
    encode_code128b,
    render_png,
)


@tagged("post_install", "-at_install")
class TestLabelRender(TransactionCase):
    def test_code128_structure(self):
        modules = encode_code128b("AUC/UCC/R01/B03-L2")
        self.assertEqual((len(modules) - 13) % 11, 0)
        self.assertTrue(modules.endswith("1100011101011"))

    def test_barcode_fit_guard(self):
        self.assertTrue(barcode_fits("AUC/UCC/R01/B03-L2"))
        self.assertTrue(barcode_fits("P0001234"))
        self.assertFalse(barcode_fits("CorRetKitL-Int-S-10015-2215-900-ntc-tra"))

    def test_location_lines(self):
        self.assertEqual(derive_location("AUC/UCC/R01/B03-L2"), ("UCC / R01", "B03-L2"))
        self.assertEqual(derive_location("C-R01-B03-L2"), ("", "C-R01-B03-L2"))

    def test_png_is_print_oriented(self):
        png = render_png("location", "AUC/UCC/R01/B03-L2", dpi=203.2)
        with Image.open(io.BytesIO(png)) as img:
            # 72 mm across the roll x 70 mm along the feed at 8 dots/mm.
            self.assertEqual(img.size, (576, 560))

    def test_computed_fields(self):
        location = self.env["stock.location"].create({
            "name": "B03-L2",
            "usage": "internal",
            "barcode": "AUC/UCC/R01/B03-L2",
        })
        self.assertTrue(base64.b64decode(location.corten_label_png))

        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        self.assertTrue(product.corten_label_png)
        self.assertTrue(product.product_tmpl_id.corten_label_png)

    def test_location_report_is_bound(self):
        actions = self.env["ir.actions.report"].search([
            ("binding_model_id.model", "=", "stock.location"),
            ("report_name", "=", "corten_label_magnet.report_label"),
        ])
        self.assertEqual(len(actions), 1)

    def test_wizard_offers_the_magnet_format(self):
        field = self.env["product.label.layout"]._fields["print_format"]
        self.assertIn("corten_magnet", field.selection)

        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        wizard = self.env["product.label.layout"].create({
            "print_format": "corten_magnet",
            "custom_quantity": 2,
            "product_ids": [(6, 0, product.ids)],
        })
        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(xml_id, "corten_label_magnet.action_corten_label_location")
        self.assertEqual(data["quantity_by_product"][product.id], 2)

    def test_report_model_resolves_products_and_locations(self):
        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        report = self.env["report.corten_label_magnet.report_label"]
        values = report._get_report_values([], {
            "active_model": "product.product",
            "quantity_by_product": {product.id: 3},
        })
        self.assertEqual(values["docs"], product)
        self.assertEqual(values["copies"][product.id], 3)

        location = self.env["stock.location"].create({
            "name": "B03-L2", "usage": "internal"})
        values = report._get_report_values([location.id], {})
        self.assertEqual(values["docs"], location)
