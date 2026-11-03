# -*- coding: utf-8 -*-
import os
from unittest.mock import patch

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

    def _enable_lead_write(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_str("rocersa_website_quote.lead_enabled", "True")
        params.set_str(
            "rocersa_website_quote.supabase_url", "https://example.supabase.co"
        )
        params.set_str("rocersa_website_quote.subdivision_id", "2")

    def _enable_posthog_event(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "rocersa_website_quote.posthog_event_enabled", "True"
        )
        self.website.sudo().write({
            "posthog_api_key": "phc_test",
            "posthog_host": "https://posthog.example",
        })

    def _submit(self, cookies=None, **overrides):
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
            cookies=cookies or {"gclid": "test-gclid"},
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

    def test_guest_quote_writes_supabase_lead(self):
        self._enable_lead_write()
        with patch.dict(os.environ, {"SUPABASE_SERVICE_KEY": "test-key"}):
            with patch(
                "odoo.addons.rocersa_website_quote.models.supabase_lead.requests.post"
            ) as post:
                post.return_value.json.return_value = [{"id": 42}]
                post.return_value.raise_for_status.return_value = None
                response = self._submit(
                    cookies={"gclid": "test-gclid", "_ga": "GA1.1.123.456"}
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.cart.supabase_lead_id, "42")
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://example.supabase.co/rest/v1/leads")
        self.assertEqual(kwargs["headers"]["apikey"], "test-key")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"], {
            "client_id": "123.456",
            "email": "guest@example.com",
            "subdivision_id": 2,
            "gclid": "test-gclid",
            "phone": "+61400000000",
        })

    def test_supabase_lead_write_is_off_by_default(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "rocersa_website_quote.lead_enabled", "False"
        )
        with patch(
            "odoo.addons.rocersa_website_quote.models.supabase_lead.requests.post"
        ) as post:
            response = self._submit()
        self.assertEqual(response.status_code, 200)
        post.assert_not_called()
        self.assertFalse(self.cart.supabase_lead_id)

    def test_supabase_lead_write_needs_the_service_key(self):
        self._enable_lead_write()
        with patch.dict(os.environ, {"SUPABASE_SERVICE_KEY": ""}):
            with patch(
                "odoo.addons.rocersa_website_quote.models.supabase_lead.requests.post"
            ) as post:
                response = self._submit()
        self.assertEqual(response.status_code, 200)
        post.assert_not_called()
        self.assertFalse(self.cart.supabase_lead_id)

    def test_supabase_lead_failure_does_not_fail_the_quote(self):
        self._enable_lead_write()
        with patch.dict(os.environ, {"SUPABASE_SERVICE_KEY": "test-key"}):
            with patch(
                "odoo.addons.rocersa_website_quote.models.supabase_lead.requests.post"
            ) as post:
                post.return_value.raise_for_status.side_effect = RuntimeError("down")
                response = self._submit()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.cart.supabase_lead_id)

    def test_guest_quote_fires_posthog_event(self):
        self._enable_posthog_event()
        with patch(
            "odoo.addons.rocersa_website_quote.models.posthog_quote.requests.post"
        ) as post:
            post.return_value.raise_for_status.return_value = None
            response = self._submit(posthog_distinct_id="ph-distinct-1")
        self.assertEqual(response.status_code, 200)
        args, kwargs = post.call_args
        self.assertEqual(args[0], "https://posthog.example/capture/")
        payload = kwargs["json"]
        self.assertEqual(payload["api_key"], "phc_test")
        self.assertEqual(payload["event"], "quote_request_submitted")
        properties = payload["properties"]
        self.assertEqual(properties["distinct_id"], "ph-distinct-1")
        self.assertTrue(properties["has_message"])
        self.assertEqual(
            properties["item_count"], len(self.cart.website_order_line)
        )

    def test_posthog_event_is_off_by_default(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "rocersa_website_quote.posthog_event_enabled", "False"
        )
        self.website.sudo().write({"posthog_api_key": "phc_test"})
        with patch(
            "odoo.addons.rocersa_website_quote.models.posthog_quote.requests.post"
        ) as post:
            self._submit(posthog_distinct_id="ph-distinct-1")
        post.assert_not_called()

    def test_posthog_event_needs_the_website_key(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "rocersa_website_quote.posthog_event_enabled", "True"
        )
        self.website.sudo().write({"posthog_api_key": False})
        with patch(
            "odoo.addons.rocersa_website_quote.models.posthog_quote.requests.post"
        ) as post:
            self._submit(posthog_distinct_id="ph-distinct-1")
        post.assert_not_called()

    def test_posthog_failure_does_not_fail_the_quote(self):
        self._enable_posthog_event()
        with patch(
            "odoo.addons.rocersa_website_quote.models.posthog_quote.requests.post"
        ) as post:
            post.return_value.raise_for_status.side_effect = RuntimeError("down")
            response = self._submit(posthog_distinct_id="ph-distinct-1")
        self.assertEqual(response.status_code, 200)

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
