# -*- coding: utf-8 -*-
# Copyright 2025 Sveltware Solutions

{
    'name': 'Multi-Company Product',
    'category': 'Product',
    'summary': "Filter each company's product catalog by a per-product list of companies.",
    'version': '1.2.2',
    'license': 'LGPL-3',
    'author': 'Sveltware Solutions',
    'website': 'https://www.linkedin.com/in/sveltware',
    'depends': [
        'product',
    ],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
