# -*- coding: utf-8 -*-
import logging

import requests

from odoo import api, models

_logger = logging.getLogger(__name__)

PARAM_ENABLED = "rocersa_website_quote.posthog_event_enabled"
DEFAULT_HOST = "https://us.i.posthog.com"
EVENT_NAME = "quote_request_submitted"


class WebsiteQuotePostHog(models.AbstractModel):
    """Send the quote request to PostHog, matching the other storefronts.

    The browser passes its PostHog distinct id with the form so the event
    joins the same person as the page view. The project key and host come
    from the website's PostHog settings (`website_posthog_experiments`).
    Off by default because it is a live-system write; a failure never fails
    the quote.
    """

    _name = "rocersa.website.quote.posthog"
    _description = "PostHog quote_request_submitted event for website quotes"

    @api.model
    def capture(self, order, distinct_id=None):
        if not order:
            return False
        params = self.env["ir.config_parameter"].sudo()
        if not params.get_bool(PARAM_ENABLED, False):
            return False

        website = order.website_id or order.company_id.website_id
        api_key = getattr(website, "posthog_api_key", "") or ""
        host = (getattr(website, "posthog_host", "") or DEFAULT_HOST).rstrip("/")
        if not api_key:
            _logger.info(
                "PostHog quote event skipped for %s: no project key on website",
                order.name,
            )
            return False

        distinct_id = distinct_id or order.partner_id.email or ""
        if not distinct_id:
            _logger.info(
                "PostHog quote event skipped for %s: no distinct id", order.name
            )
            return False

        company = website.company_id or order.company_id
        country = (company.country_id.code or "").lower()
        codes = [
            line.product_id.default_code
            for line in order.website_order_line
            if line.product_id.default_code
        ]
        payload = {
            "api_key": api_key,
            "event": EVENT_NAME,
            "properties": {
                "distinct_id": distinct_id[:200],
                "country": country,
                "cart_value": order.amount_total,
                "item_count": len(order.website_order_line),
                "product_codes": codes,
                "has_message": bool((order.rfq_message or "").strip()),
            },
        }
        try:
            response = requests.post(
                f"{host}/capture/", json=payload, timeout=10
            )
            response.raise_for_status()
            return True
        except Exception:  # noqa: BLE001 - analytics must not fail the RFQ
            _logger.exception("PostHog quote event failed for %s", order.name)
            return False
