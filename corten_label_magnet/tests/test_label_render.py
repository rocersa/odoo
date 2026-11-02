"""Label renderer, report models and wizard wiring. Runs on the odoo.sh build."""
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

LONGEST = "CorCnrJoiIntRol100-90-300"  # 25 chars, company-18 stock 2026-10-29


@tagged("post_install", "-at_install")
class TestLabelRender(TransactionCase):
    def test_code128_structure(self):
        modules = encode_code128b("AUC/UCC/R01/B03-L2")
        self.assertEqual((len(modules) - 13) % 11, 0)
        self.assertTrue(modules.endswith("1100011101011"))

    def test_barcode_fit_guard(self):
        self.assertEqual(len(LONGEST), 25)
        self.assertTrue(barcode_fits("AUC/UCC/R01/B03-L2"))
        self.assertTrue(barcode_fits(LONGEST))            # 70 mm label
        self.assertTrue(barcode_fits(LONGEST, 94))        # 100 mm label
        self.assertFalse(barcode_fits("CorRetKitL-Int-S-10015-2215-900-ntc-tra"))

    def test_location_lines(self):
        self.assertEqual(derive_location("AUC/UCC/R01/B03-L2"), ("UCC / R01", "B03-L2"))
        self.assertEqual(derive_location("AUC/Stock/Unit 1"), ("Stock", "Unit 1"))
        self.assertEqual(derive_location("AUC/S/U3/R01/B03"), ("S / U3 / R01", "B03"))
        self.assertEqual(derive_location("AUC/S/U3/R01/B03/L0"), ("S / U3 / R01 / B03", "L0"))
        self.assertEqual(derive_location("C-R01-B03-L2"), ("", "C-R01-B03-L2"))

    def test_png_is_print_oriented(self):
        with Image.open(io.BytesIO(render_png("location", "AUC/UCC/R01/B03-L2", dpi=203.2))) as img:
            # 72 mm across the roll x 70 mm along the feed at 8 dots/mm.
            self.assertEqual(img.size, (576, 560))
        with Image.open(io.BytesIO(render_png("product", LONGEST, name="Corner", dpi=203.2,
                                              length_mm=100))) as img:
            self.assertEqual(img.size, (576, 800))

    def test_wizard_offers_both_lengths(self):
        field = self.env["product.label.layout"]._fields["print_format"]
        self.assertIn("corten_magnet", field.selection)
        self.assertIn("corten_magnet_100", field.selection)

        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        for fmt, xml_id in (
            ("corten_magnet", "corten_label_magnet.action_corten_label_location"),
            ("corten_magnet_100", "corten_label_magnet.action_corten_label_location_100"),
        ):
            wizard = self.env["product.label.layout"].create({
                "print_format": fmt,
                "custom_quantity": 2,
                "product_ids": [(6, 0, product.ids)],
            })
            got_xml_id, data = wizard._prepare_report_data()
            self.assertEqual(got_xml_id, xml_id)
            self.assertEqual(data["quantity_by_product"][product.id], 2)

    def test_report_models_resolve_and_render(self):
        product = self.env["product.product"].create({
            "name": "Flamed Corten Edging 1000",
            "default_code": "CT-EDG-1000",
            "type": "product",
        })
        for model, page_h in (
            ("report.corten_label_magnet.report_label", 70),
            ("report.corten_label_magnet.report_label_100", 100),
        ):
            values = self.env[model]._get_report_values([], {
                "active_model": "product.product",
                "quantity_by_product": {product.id: 3},
            })
            self.assertEqual(values["docs"], product)
            self.assertEqual(values["copies"][product.id], 3)
            self.assertEqual(values["page_h"], page_h)
            self.assertEqual(
                base64.b64decode(values["labels"][product.id])[:4], b"\x89PNG")

    def test_location_reports_are_bound(self):
        actions = self.env["ir.actions.report"].search([
            ("binding_model_id.model", "=", "stock.location"),
            ("report_name", "like", "corten_label_magnet.report_label"),
        ])
        self.assertEqual(len(actions), 2)
