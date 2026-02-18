# -*- coding: utf-8 -*-
{
    'name': "CRM Customer Tag",

    'summary': """
        Adds the customer tag field to the opportunity form view."
    """,

    'description': """
        Adds the customer tag field to the opportunity form view."
    """,

    'author': "Harry",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm'],
    'application': True,
    'installable': True,
    'data': [
        'views/crm_lead_view.xml',
    ],
    'license': 'AGPL-3'
}
