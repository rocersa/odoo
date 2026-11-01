# -*- coding: utf-8 -*-
from odoo.addons.website_sale.tests.common import WebsiteSaleCommon
from odoo.tests import HttpCase, tagged

from ..controllers.main import WebsiteQuote


@tagged("post_install", "-at_install")
class TestQuoteFlow(WebsiteSaleCommon, HttpCase):
    """Cart -> RFQ flow, exercised through the controller with a mock request."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website.sudo().write({"is_disable_checkout": True})
        cls.country_au = cls.env.ref("base.au")
        cls.state_au = cls.env["res.country.state"].search(
            [("country_id", "=", cls.country_au.id)], limit=1
        )
        cls.QuoteController = WebsiteQuote()

    def _submit(self, **overrides):
        data = {
            "name": "Guest Buyer",
            "email": "guest@example.com",
            "phone": "+61400000000",
            "company_name": "Guest Co",
            "street": "1 Test Street",
            "city": "Sydney",
            "zip": "2000",
            "country_id": str(self.country_au.id),
            "state_id": str(self.state_au.id) if self.state_au else "",
            "message": "Please quote freight to Sydney.",
        }
        data.update(overrides)
        with self.mock_request(
            sale_order_id=self.cart.id,
            user=self.public_user,
            cookies={"gclid": "test-gclid"},
        ):
            return self.QuoteController.shop_quote_submit(**data)

    def test_guest_quote_creates_contact_and_rfq(self):
        response = self._submit()
        self.assertEqual(response.status_code, 200)
        order = self.cart
        self.assertTrue(order.is_rfq_from_website)
        self.assertEqual(order.rfq_message, "Please quote freight to Sydney.")
        self.assertEqual(order.rfq_gclid, "test-gclid")
        self.assertEqual(order.rfq_company, "Guest Co")
        self.assertEqual(order.partner_id.email, "guest@example.com")
        self.assertEqual(order.partner_id.name, "Guest Buyer")
        self.assertEqual(order.partner_id.street, "1 Test Street")
        self.assertEqual(order.partner_id.country_id, self.country_au)

    def test_guest_does_not_overwrite_an_existing_partner(self):
        existing = self.env["res.partner"].sudo().create({
            "name": "Existing Customer",
            "email": "existing@example.com",
            "street": "Old Street",
        })
        self._submit(
            name="New Name",
            email="existing@example.com",
            street="New Street",
        )
        self.assertEqual(existing.name, "Existing Customer")
        self.assertEqual(existing.street, "Old Street")
        self.assertNotEqual(self.cart.partner_id, existing)
        self.assertEqual(self.cart.partner_id.email, "existing@example.com")

    def test_logged_in_quote_uses_the_user_partner(self):
        with self.mock_request(
            sale_order_id=self.cart.id, user=self.env.user
        ):
            response = self.QuoteController.shop_quote()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.cart.is_rfq_from_website)
        self.assertEqual(self.cart.partner_id, self.env.user.partner_id)

    def test_guest_quote_emails_customer_and_company(self):
        self.website.company_id.partner_id.sudo().write({"email": "company@example.com"})
        self._submit()
        mails = self.env["mail.mail"].sudo().search([
            ("model", "=", "sale.order"),
            ("res_id", "=", self.cart.id),
        ])
        recipients = {mail.email_to for mail in mails}
        self.assertIn("guest@example.com", recipients)
        self.assertIn("company@example.com", recipients)

    def test_cart_renders_quote_cta_and_guest_modal(self):
        self.website.sudo().write({"is_disable_checkout": True})
        self.cart.sudo().write({"access_token": "quote-test-token"})
        response = self.url_open(
            f"/shop/cart?id={self.cart.id}&access_token=quote-test-token"
        )
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("Get Delivery Quote", html)
        self.assertIn("rocersa_quote_modal", html)
        self.assertIn("rocersa_quote_country", html)

    def test_missing_required_field_is_a_clean_error(self):
        response = self._submit(email="")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.cart.is_rfq_from_website)
        self.assertFalse(self.cart.partner_id.email == "guest@example.com")
