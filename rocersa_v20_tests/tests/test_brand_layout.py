# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install', '-at_install')
class TestBrandLayout(AccountTestInvoicingCommon):
    """The vendored striped layout must render an invoice without errors."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.external_report_layout_id = cls.env.ref(
            'brand_report_layout.external_layout_striped')

    def test_invoice_uses_brand_layout(self):
        invoice = self.init_invoice(
            'out_invoice', partner=self.partner_a,
            products=self.product_a, post=True)
        html, _ = self.env['ir.actions.report']._render_qweb_html(
            'account.account_invoices', invoice.ids)
        if isinstance(html, bytes):
            html = html.decode()
        self.assertIn('o_report_layout_striped', html)
        self.assertIn('o_table_striped', html)
        self.assertIn(invoice.name, html)
