"""Label renderer and report wiring. Runs on the odoo.sh staging build."""
import base64
import io

from PIL import Image

from odoo.tests import TransactionCase, tagged

from ..tools.label_render import derive_location, encode_code128b, render_png


@tagged("post_install", "-at_install")
class TestLabelRender(TransactionCase):
    def test_code128_structure(self):
        modules = encode_code128b("AUC/UCC/R01/B03-L2")
        self.assertEqual((len(modules) - 13) % 11, 0)
        self.assertTrue(modules.endswith("1100011101011"))

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
        self.assertTrue(location.corten_label_png)
        self.assertTrue(base64.b64decode(location.corten_label_png))

        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        self.assertTrue(product.corten_label_png)

    def test_report_is_bound(self):
        for model in ("product.template", "product.product", "stock.location"):
            actions = self.env["ir.actions.report"].search([
                ("binding_model_id.model", "=", model),
                ("report_name", "=", "corten_label_magnet.report_label"),
            ])
            self.assertTrue(actions, model)
