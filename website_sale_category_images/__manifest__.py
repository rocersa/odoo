{
    "name": "Website Sale Category Images",
    "summary": "Add category-level images to the product image carousel",
    "version": "19.0.1.1.2",
    "category": "Website",
    "author": "Rocersa",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "website_sale",
        "udoo_ec_multi_site",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_public_category_views.xml",
    ],
}
