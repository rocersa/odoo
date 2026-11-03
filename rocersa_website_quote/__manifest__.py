# -*- coding: utf-8 -*-
{
    "name": "Website Quote Request",
    "summary": "Replace checkout with a quote request (cart -> RFQ) per website",
    "version": "20.0.1.0.5",
    "category": "Website",
    "author": "Rocersa",
    "license": "AGPL-3",
    "depends": ["website_sale", "website_posthog_experiments"],
    "data": [
        "views/website_quote_templates.xml",
        "views/sale_order_views.xml",
        "views/res_config_settings.xml",
        "data/mail_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "rocersa_website_quote/static/src/js/quote_form.js",
            "rocersa_website_quote/static/src/css/quote_form.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
