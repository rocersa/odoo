{
    'name': 'Restrict Dynamic Variants',
    'version': '1.0.0',
    'category': 'Website/Website',
    'summary': 'Prevent on-the-fly creation of dynamic variants for selected products',
    'description': """
        Adds a flag on product templates that prevents customers from selecting
        attribute combinations for which no variant already exists.

        When enabled on a template:
        - The e-commerce product page disables the add-to-cart button for
          missing combinations.
        - Odoo refuses to create new variants on demand via the website,
          sale configurator, or POS.
        - Only combinations that already have an active variant are shown
          as available.

        This is useful for sparse variant matrices (e.g. Corten Rings with
        Radius × Height) where not every combination is a real product.
    """,
    'depends': ['udoo_ec_multi_site'],
    'data': [
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_restrict_dynamic_variants/static/src/interactions/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
