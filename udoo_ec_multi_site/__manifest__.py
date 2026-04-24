# -*- coding: utf-8 -*-
# Copyright 2024 Sveltware Solutions

{
    'name': 'Multi-Company Product Visibility',
    'category': 'Website/Website',
    'summary': 'Manage multichannel listing eCommerce product with bulk website assign, multi website product, multi website category, mass update publishing state, product multi website, managing products across multiple websites, multi shop, multi product, multi categories, multiple websites sale per product, odoo multi websites, multi website selection for products | multiple websites per category | bulk website assign | product multiple website',
    'version': '1.0.6',
    'license': 'LGPL-3',
    'author': 'Sveltware Solutions',
    'website': 'https://www.linkedin.com/in/sveltware',
    'live_test_url': 'https://omux.sveltware.com/web/login',
    'images': ['static/description/banner.png'],
    'depends': [
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/multi_website_product.xml',
        'wizard/multi_website_setter.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'udoo_ec_multi_site/static/src/**/*',
        ],
    },
}
