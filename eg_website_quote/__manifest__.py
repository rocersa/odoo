{
    "name": "Website Submit Quote",
    "version": "1.0",
    "category": "eCommerce, Website",
    "summary": "The Website Submit Quote app for Odoo enhances the customer experience by allowing flexible control over quotation requests. The app offers a simple toggle to enable or disable the \u201cGet Quote\u201d button on the cart page, streamlining the checkout process. Customers can request personalized quotes, with instant price updates based on their selections. Seamlessly integrated with Odoo, all quote submissions are automatically synced for easy follow-up. This app also includes a customizable quote request form to gather specific details for accurate pricing. Website Submit Quote, Odoo quote management, quote request button, Odoo website integration, cart quote request, Odoo quote generator, personalized quote, Odoo eCommerce, quote management system, custom quote form, quote request form, Odoo quote system, customer quote request, Odoo shopping cart, quotation tool, Odoo app for quotes, quote feature, instant quote, quote generation app, eCommerce quote solution, seamless quote integration, Odoo quote submission, quote feature toggle, quote PDF download, Odoo cart page feature, flexible quote management, Odoo checkout process, automatic quote syncing, customizable quote form, real-time pricing, Odoo quote request button, increase sales conversions, quote management for websites, easy quote submission, Odoo sales workflow, streamline checkout process, Odoo quote visibility, quote request for customers, website quote tool, improve customer experience, sales quote automation, Odoo quote feature control, boost online sales, website quote system, request for quotation in website.",
    "description": "Website Submit Quote allows flexible control over quotation requests on a website. A dedicated setting includes a boolean option that determines the visibility of the \u201cGet Quote\u201d button on the cart page. When the option is enabled, visitors can request quotations directly from the cart, enhancing the shopping experience. Disabling the option hides the feature, providing a clean and straightforward checkout process.",
    "author": "INKERP",
    "website": "www.inkerp.com",
    "depends": [
        "website_sale"
    ],
    "data": [
        "views/website_sale_check_out_template.xml",
        "views/res_config_settings.xml",
        "views/website_quote_template.xml",
        "views/sale_order.xml",
        "views/guest_quote_form.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "eg_website_quote/static/src/js/guest_quote_form.js",
            "eg_website_quote/static/src/css/guest_quote_form.css",
        ],
    },
    "images": [
        "static/description/banner.png"
    ],
    "license": "OPL-1",
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": "49.0",
    "currency": "EUR"
}