# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Weight",

    'summary': """
        Adds a weight field to purchase orders"
    """,

    'description': """
        Adds a weight field to purchase orders"
    """,

    'author': "Harry",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Purchase Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase', 'stock'],
    'application': True,
    'installable': True,
    'data': [
        'views/purchase_order_view.xml',
    ],
    'license': 'AGPL-3'
}
