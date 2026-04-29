# -*- coding: utf-8 -*-
# Copyright 2025 Sveltware Solutions

{
    'name': 'Multi-Company Product',
    'category': 'Product',
    'summary': 'Assign products to multiple companies instead of a single company or all companies',
    'version': '1.1.5',
    'license': 'LGPL-3',
    'author': 'Sveltware Solutions',
    'website': 'https://www.linkedin.com/in/sveltware',
    'depends': [
        'product',
        'sale',
        'purchase',
    ],
    'data': [
        'security/product_security.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
