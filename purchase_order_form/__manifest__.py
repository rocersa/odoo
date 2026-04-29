# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Form",

    'summary': """
        Enhances the purchase order form with weight totals and sortable lines.
    """,

    'description': """
        Enhances the purchase order form with:
        - A computed weight field on each order line
        - A total weight summary on the purchase order
        - Order lines sorted by product name by default
    """,

    'author': "Harry",

    'category': 'Purchase Management',
    'version': '0.3',

    'depends': ['purchase', 'stock'],
    'application': True,
    'installable': True,
    'data': [
        'views/purchase_order_view.xml',
    ],
    'license': 'AGPL-3'
}
