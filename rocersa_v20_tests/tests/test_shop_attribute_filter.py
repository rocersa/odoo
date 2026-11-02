# -*- coding: utf-8 -*-
from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestShopAttributeFilter(HttpCase):
    """The retired OCA module's behaviour is now native in Odoo 20.

    Loads /shop with four attribute values: three used by the two published
    products and one unused. The unused value must not appear in the filter
    panel; a search that excludes a product must also drop its values.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env.ref('website_sale.products_attributes').active = True

        attribute = cls.env['product.attribute'].create({
            'name': 'Test Colour',
            'display_type': 'color',
            'create_variant': 'no_variant',
        })
        values = {}
        for name, html_color in (
            ('Test red', '#ff0000'),
            ('Test green', '#00ff00'),
            ('Test blue', '#0000ff'),
            ('Test yellow', '#ffff00'),
        ):
            values[name] = cls.env['product.attribute.value'].create({
                'name': name,
                'attribute_id': attribute.id,
                'html_color': html_color,
            })

        def make_product(name, price, value_names):
            return cls.env['product.template'].create({
                'name': name,
                'list_price': price,
                'is_published': True,
                'sale_ok': True,
                'attribute_line_ids': [(0, 0, {
                    'attribute_id': attribute.id,
                    'value_ids': [(6, 0, [values[v].id for v in value_names])],
                })],
            })

        make_product('Filter Test One', 10.0, ['Test red', 'Test green'])
        make_product('Filter Test Two', 20.0, ['Test red', 'Test blue'])

    def test_unused_value_hidden(self):
        html = self.url_open('/shop').text
        self.assertIn('Test red', html)
        self.assertIn('Test green', html)
        self.assertIn('Test blue', html)
        self.assertNotIn('Test yellow', html)

    def test_search_limits_values(self):
        html = self.url_open('/shop?search=Filter+Test+One').text
        self.assertIn('Test red', html)
        self.assertIn('Test green', html)
        self.assertNotIn('Test blue', html)
        self.assertNotIn('Test yellow', html)
