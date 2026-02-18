from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request
import json


class Main(WebsiteSale):

    @http.route(['/shop/get/quote'], type='http', auth="public", website=True)
    def shop_get_quote(self):
        """Handle quote request for logged-in users"""
        order = request.cart
        if not order:
            return request.redirect('/shop')
        
        order.is_rfq_from_website = True
        value = {'order': order}
        return request.render("eg_website_quote.eg_website_quote_template", value)

    @http.route(['/shop/get/quote/submit'], type='http', auth="public", website=True, methods=['POST'], csrf=True)
    def shop_get_quote_submit(self, **post):
        """Handle quote request form submission for guest users"""
        order = request.cart
        if not order:
            return json.dumps({'success': False, 'error': 'No cart found'})
        
        try:
            # Get or create partner with provided information
            Partner = request.env['res.partner'].sudo()
            
            # Check if partner with this email already exists
            partner = Partner.search([('email', '=', post.get('email'))], limit=1)
            
            partner_vals = {
                'name': post.get('name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'street': post.get('street'),
                'street2': post.get('street2'),
                'city': post.get('city'),
                'zip': post.get('zip'),
                'country_id': int(post.get('country_id')) if post.get('country_id') else False,
                'state_id': int(post.get('state_id')) if post.get('state_id') else False,
                'type': 'contact',
            }
            
            if post.get('company_name'):
                partner_vals['company_name'] = post.get('company_name')
            
            if partner:
                # Update existing partner
                partner.write(partner_vals)
            else:
                # Create new partner
                partner = Partner.create(partner_vals)
            
            # Update the sale order with partner information
            order.sudo().write({
                'partner_id': partner.id,
                'partner_invoice_id': partner.id,
                'partner_shipping_id': partner.id,
                'is_rfq_from_website': True,
            })
            
            # Confirm the quote request
            order.sudo().action_quotation_sent()
            
            return request.render("eg_website_quote.eg_website_quote_template", {'order': order})
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})
