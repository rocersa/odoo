from odoo.tests.common import TransactionCase, tagged

from ..models.product_pricelist_item import panel_weight

# Real rows sampled from the 245 proxied AU panel SKUs (read-only query against
# the product DB on 2026-11-23). `wholesale` is `au_wholesale_cost` (true
# dimension weight x landcost); `retail_ex` is the storefront retail ex GST,
# `au_retail_cost / 1.10`. Asserting against these proves the proxy reproduces
# the storefront, not just its own formula.
PROXIED_SAMPLE = [
    # code, height, width, gauge, category, markup, pickfee, wholesale, retail_ex
    ("Gab3-1125-1050", 1125, 1050, 3.0, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 5.90468, 15.612619),
    ("Gab3-1125-1125", 1125, 1125, 3.0, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 6.31235, 17.616453),
    ("Gab3-1125-450", 1125, 450, 3.0, "Gabion Panel Margin 2 custom", 1.4214, 1.1, 2.6433, 7.914448),
    ("Gab3-1200-1125", 1200, 1125, 3.0, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 6.72003, 17.616453),
    ("Gab4.5-1125-1050", 1125, 1050, 4.5, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 13.2855, 33.753393),
    ("Gab4.5-1125-1125", 1125, 1125, 4.5, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 14.2028, 38.26202),
    ("Gab4.5-1125-450", 1125, 450, 4.5, "Gabion Panel Margin 2 custom", 1.4214, 1.1, 5.94742, 16.432509),
    ("Gab4.5-1200-1125", 1200, 1125, 4.5, "Gabion Panel Margin 1 Custom", 1.3087, 1.1, 15.1201, 38.26202),
]

# S00299 (`GabW1D2100-1275-450-4.5`) Bill of Materials, from the Supabase
# kitset recipe. (code, quantity, wholesale, category, markup, pickfee).
S00299_BOM = [
    ("Gab26H1275", 6, 0.2212, "Gabion Helicals", 11.0, 0.21),
    ("Gab26H2100", 4, 0.36656, "Gabion Helicals", 11.0, 0.21),
    ("Gab26H450", 6, 0.079, "Gabion Helicals", 11.0, 0.21),
    ("Gab4.5-1275-450", 3, 6.71674, "Gabion Panel Margin 2 custom", 1.4214, 1.1),
    ("Gab4.5-2100-1275", 2, 29.5004, "Gabion Panel Margin 1 Custom", 1.3087, 1.1),
    ("Gab4.5-2100-450", 2, 10.948, "Gabion Panel Margin 2 custom", 1.4214, 1.1),
]

KIT_MARKUP = 0.10
LANCOST_AU = 3.16


@tagged("post_install", "-at_install")
class TestGabionPanelProxyPricing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "AU Gabions Proxy Test", "currency_id": cls.env.company.currency_id.id}
        )

    def setUp(self):
        super().setUp()
        self._rules = {}

    def _category(self, name):
        return self.env["product.category"].create({"name": name})

    def _rule(self, category, markup, pickfee):
        key = (category.id, markup, pickfee)
        if key not in self._rules:
            self._rules[key] = self.env["product.pricelist.item"].create(
                {
                    "pricelist_id": self.pricelist.id,
                    "applied_on": "2_product_category",
                    "categ_id": category.id,
                    "compute_price": "formula",
                    "base": "standard_price",
                    "price_markup": markup * 100.0,
                    "price_surcharge": pickfee,
                }
            )
        return self._rules[key]

    def _product(self, code, wholesale, category, gauge=None, height=None, width=None):
        vals = {
            "name": code,
            "default_code": code,
            "type": "consu",
            "categ_id": category.id,
            "standard_price": wholesale,
        }
        if gauge and height and width:
            vals["weight"] = panel_weight(height, width, gauge)
        return self.env["product.product"].create(vals)

    def test_override_table_is_seeded(self):
        overrides = {
            row.current_length: row.proxy_length
            for row in self.env["gabion.panel.override"].search([])
        }
        self.assertEqual(
            overrides,
            {
                75: 300,
                150: 300,
                225: 300,
                1125: 1200,
                1275: 1350,
                1425: 1500,
                1800: 2100,
                1875: 2100,
                1950: 2100,
                2025: 2100,
            },
        )

    def test_standard_length_quotes_true_cost(self):
        category = self._category("Gabion Panel Margin 2 custom")
        self._rule(category, 1.4214, 1.1)
        product = self._product("Gab4.5-1200-450", 8.4, category, 4.5, 1200, 450)
        price = self.pricelist._get_product_price(product, 1.0)
        self.assertAlmostEqual(price, 8.4 * 2.4214 + 1.1, places=4)

    def test_proxied_length_quotes_storefront_retail(self):
        category = self._category("Gabion Panel Margin 2 custom")
        self._rule(category, 1.4214, 1.1)
        # Gab4.5-1275-450: width 1275 is priced as 1350.
        wholesale = panel_weight(1275, 450, 4.5) * LANCOST_AU
        product = self._product("Gab4.5-1275-450", wholesale, category, 4.5, 1275, 450)
        price = self.pricelist._get_product_price(product, 1.0)
        expected = panel_weight(1350, 450, 4.5) * LANCOST_AU * 2.4214 + 1.1
        self.assertAlmostEqual(price, expected, places=4)
        self.assertAlmostEqual(price, 18.2954, delta=0.01)

    def test_sample_of_the_245_matches_retail_within_a_cent(self):
        for code, height, width, gauge, category_name, markup, pickfee, wholesale, retail_ex in PROXIED_SAMPLE:
            with self.subTest(code=code):
                category = self.env["product.category"].search(
                    [("name", "=", category_name)], limit=1
                ) or self._category(category_name)
                self._rule(category, markup, pickfee)
                product = self._product(code, wholesale, category, gauge, height, width)
                price = self.pricelist._get_product_price(product, 1.0)
                self.assertAlmostEqual(price, retail_ex, delta=0.01)

    def test_corrected_anomaly_quotes_its_recomputed_retail(self):
        # `Gab4.5-1650-1275` after its stored weight is corrected to the true
        # dimension weight (7.37 kg): the quote is the proxied retail, 63.73 inc
        # GST. The weight correction itself is a live Supabase write (Harry).
        category = self._category("Gabion Panel Margin 1 Custom")
        self._rule(category, 1.3087, 1.1)
        wholesale = panel_weight(1650, 1275, 4.5) * LANCOST_AU
        product = self._product("Gab4.5-1650-1275", wholesale, category, 4.5, 1650, 1275)
        price = self.pricelist._get_product_price(product, 1.0)
        expected_ex = panel_weight(1650, 1350, 4.5) * LANCOST_AU * 2.3087 + 1.1
        self.assertAlmostEqual(price, expected_ex, places=4)
        self.assertAlmostEqual(price * 1.10, 63.7296, delta=0.01)

    def test_non_gabion_product_is_unchanged(self):
        category = self._category("Fasteners")
        self._rule(category, 0.5, 2.0)
        product = self._product("BOLT-M10", 4.0, category)
        price = self.pricelist._get_product_price(product, 1.0)
        self.assertAlmostEqual(price, 4.0 * 1.5 + 2.0, places=4)

    def test_panel_outside_the_two_categories_is_unchanged(self):
        category = self._category("Gabion Panel Margin 3 Custom")
        self._rule(category, 1.3087, 1.1)
        product = self._product("Gab4.5-1275-450", 8.0, category, 4.5, 1275, 450)
        price = self.pricelist._get_product_price(product, 1.0)
        self.assertAlmostEqual(price, 8.0 * 2.3087 + 1.1, places=4)

    def test_s00299_quotes_328_7647_ex(self):
        products = []
        categories = {}
        for code, qty, wholesale, category_name, markup, pickfee in S00299_BOM:
            category = categories.get(category_name)
            if category is None:
                category = categories[category_name] = (
                    self.env["product.category"].search(
                        [("name", "=", category_name)], limit=1
                    )
                    or self._category(category_name)
                )
            self._rule(category, markup, pickfee)
            gauge = height = width = None
            if code.startswith(("Gab4.5-", "Gab3-", "gab")):
                _, h, w = code.split("-")
                gauge, height, width = float(code.split("-")[0][3:]), int(h), int(w)
            product = self._product(code, wholesale, category, gauge, height, width)
            products.append((product, qty))

        component_sum = sum(
            self.pricelist._get_product_price(product, qty) * qty
            for product, qty in products
        )
        line = component_sum * (1 + KIT_MARKUP)
        self.assertAlmostEqual(line, 328.7647, delta=0.01)
        self.assertAlmostEqual(line * 1.10, 361.641, delta=0.01)
