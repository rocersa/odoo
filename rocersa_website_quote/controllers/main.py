# -*- coding: utf-8 -*-
import re

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

_GCLID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
_REQUIRED_GUEST_FIELDS = ("name", "email", "street", "city", "zip", "country_id")


class WebsiteQuote(http.Controller):
    """Cart -> RFQ flow for a website in quote mode."""

    def _cart(self):
        order = request.cart
        if not order or not order.website_order_line:
            return request.env["sale.order"]
        return order

    def _quote_enabled(self):
        return bool(request.website.is_disable_checkout)

    def _guest_partner(self, post):
        missing = [field for field in _REQUIRED_GUEST_FIELDS if not post.get(field)]
        if missing:
            raise UserError(
                _("Please fill in: %s", ", ".join(missing))
            )
        vals = {
            "name": post.get("name"),
            "email": post.get("email"),
            "phone": post.get("phone") or False,
            "street": post.get("street"),
            "street2": post.get("street2") or False,
            "city": post.get("city"),
            "zip": post.get("zip"),
            "country_id": int(post["country_id"]),
            "state_id": int(post["state_id"]) if post.get("state_id") else False,
            "type": "contact",
        }
        # Always create a new contact. Never look up and overwrite an existing
        # partner from an unauthenticated form.
        return request.env["res.partner"].sudo().create(vals)

    def _attribution(self, post):
        attribution = {}
        gclid = request.httprequest.cookies.get("gclid")
        if gclid and _GCLID_RE.match(gclid):
            attribution["rfq_gclid"] = gclid
        for key in ("utm_source", "utm_medium", "utm_campaign"):
            value = post.get(key)
            if value:
                attribution[f"rfq_{key}"] = value[:100]
        landing = post.get("landing_page") or request.httprequest.referrer
        if landing:
            attribution["rfq_landing_page"] = landing[:255]
        return attribution

    @http.route(
        ["/shop/quote"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        sitemap=False,
    )
    def shop_quote(self, **kwargs):
        if not self._quote_enabled():
            return request.redirect("/shop/cart")
        order = self._cart()
        if not order:
            return request.redirect("/shop")
        if request.env.user._is_public():
            # Guests use the cart modal; a direct visit has no contact details.
            return request.redirect("/shop/cart")
        order._apply_website_rfq(request.env.user.partner_id)
        return request.render(
            "rocersa_website_quote.quote_thank_you", {"order": order}
        )

    @http.route(
        ["/shop/quote/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
        sitemap=False,
    )
    def shop_quote_submit(self, **post):
        if not self._quote_enabled():
            return request.redirect("/shop/cart")
        order = self._cart()
        if not order:
            return request.redirect("/shop")
        try:
            if request.env.user._is_public():
                partner = self._guest_partner(post)
            else:
                partner = request.env.user.partner_id
            order._apply_website_rfq(
                partner,
                post.get("message"),
                self._attribution(post),
                company=post.get("company_name"),
            )
        except UserError as err:
            return request.render(
                "rocersa_website_quote.quote_error", {"error": str(err)}
            )
        return request.render(
            "rocersa_website_quote.quote_thank_you", {"order": order}
        )
