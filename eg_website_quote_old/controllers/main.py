from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request


class Main(WebsiteSale):

    @http.route(['/shop/get/quote'], type='http', auth="public", website=True, methods=['GET', 'POST'])
    def shop_get_quote(self, **post):
        order = request.cart
        if not order:
            return request.redirect('/shop')
        
        # If it's a GET request (direct link from logged-in user)
        if request.httprequest.method == 'GET':
            # Check if user is logged in
            if not request.env.user._is_public():
                partner = request.env.user.partner_id
                
                # Check if partner has complete address information
                if not partner.street or not partner.city or not partner.zip or not partner.country_id:
                    # Redirect to address form/modal - render page with modal open
                    return request.render("eg_website_quote.quote_address_needed", {
                        'order': order,
                        'partner': partner,
                    })
                
                # Partner has address, create quote directly
                order.sudo().write({
                    'partner_id': partner.id,
                    'partner_invoice_id': partner.id,
                    'partner_shipping_id': partner.id,
                    'is_rfq_from_website': True,
                })
                
                # Show thank you page
                return request.render("eg_website_quote.eg_website_quote_template", {'order': order})
            else:
                # Public user tried to access via GET, redirect to cart
                return request.redirect('/shop/cart')
        
        # Handle POST request with form data
        if request.httprequest.method == 'POST':
            Partner = request.env['res.partner'].sudo()
            Country = request.env['res.country'].sudo()
            State = request.env['res.country.state'].sudo()
            
            # Determine if this is for current user or guest
            if not request.env.user._is_public():
                # Logged-in user updating their address
                partner = request.env.user.partner_id.sudo()
            else:
                # Guest user - search for existing partner with this email
                if not post.get('guest_name') or not post.get('guest_email'):
                    return request.redirect('/shop/cart')
                    
                partner = Partner.search([('email', '=', post.get('guest_email'))], limit=1)
            
            # Prepare partner values
            partner_vals = {
                'name': post.get('guest_name'),
                'email': post.get('guest_email'),
                'phone': post.get('guest_phone', ''),
                'street': post.get('street', ''),
                'city': post.get('city', ''),
                'zip': post.get('zip', ''),
            }
            
            # Only set company_type for new partners
            if not partner:
                partner_vals['company_type'] = 'person'
            
            # Handle country
            if post.get('country_id'):
                try:
                    country_id = int(post.get('country_id'))
                    partner_vals['country_id'] = country_id
                    
                    # Handle state if provided
                    if post.get('state_id'):
                        try:
                            state_id = int(post.get('state_id'))
                            partner_vals['state_id'] = state_id
                        except (ValueError, TypeError):
                            pass
                except (ValueError, TypeError):
                    pass
            
            if partner:
                # Update existing partner
                partner.write(partner_vals)
            else:
                # Create new partner for guest
                partner = Partner.create(partner_vals)
            
            # Update order with partner information
            order.sudo().write({
                'partner_id': partner.id,
                'partner_invoice_id': partner.id,
                'partner_shipping_id': partner.id,
                'is_rfq_from_website': True,
            })
            
            # Add message/note if provided
            if post.get('guest_message'):
                order.sudo().message_post(
                    body=f"Customer message: {post.get('guest_message')}",
                    message_type='comment',
                )
            
            # Show thank you page
            return request.render("eg_website_quote.eg_website_quote_template", {'order': order})
        
        # Fallback redirect
        return request.redirect('/shop/cart')

