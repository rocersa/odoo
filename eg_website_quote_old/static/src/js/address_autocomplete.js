/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.GuestAddressAutocomplete = publicWidget.Widget.extend({
    selector: '#guestQuoteModal',
    
    start: function () {
        this._super.apply(this, arguments);
        this._initAutocomplete();
    },
    
    _initAutocomplete: function () {
        const streetInput = this.el.querySelector('#guest_street');
        if (!streetInput || typeof google === 'undefined' || !google.maps) {
            // Google Maps not loaded or input not found
            return;
        }
        
        const autocomplete = new google.maps.places.Autocomplete(streetInput, {
            types: ['address'],
            fields: ['address_components', 'formatted_address', 'geometry']
        });
        
        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.address_components) {
                return;
            }
            
            // Parse address components
            let street = '';
            let city = '';
            let state = '';
            let zip = '';
            let country = '';
            
            place.address_components.forEach(component => {
                const types = component.types;
                
                if (types.includes('street_number')) {
                    street = component.long_name + ' ';
                }
                if (types.includes('route')) {
                    street += component.long_name;
                }
                if (types.includes('locality')) {
                    city = component.long_name;
                }
                if (types.includes('administrative_area_level_1')) {
                    state = component.long_name;
                }
                if (types.includes('postal_code')) {
                    zip = component.long_name;
                }
                if (types.includes('country')) {
                    country = component.short_name;
                }
            });
            
            // Fill in the form fields
            if (street) this.el.querySelector('#guest_street').value = street.trim();
            if (city) this.el.querySelector('#guest_city').value = city;
            if (state) this.el.querySelector('#guest_state').value = state;
            if (zip) this.el.querySelector('#guest_zip').value = zip;
            
            // Set country by code
            if (country) {
                const countrySelect = this.el.querySelector('#guest_country');
                const options = countrySelect.options;
                for (let i = 0; i < options.length; i++) {
                    const option = options[i];
                    // Match by country code in the option text or value
                    if (option.text.includes(`(${country})`) || option.getAttribute('data-code') === country) {
                        countrySelect.selectedIndex = i;
                        break;
                    }
                }
            }
        });
    },
});

export default publicWidget.registry.GuestAddressAutocomplete;
