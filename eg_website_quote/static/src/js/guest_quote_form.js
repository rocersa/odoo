/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.GuestQuoteForm = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click #get_quote_btn': '_onGetQuoteClick',
        'change #guest_country': '_onCountryChange',
        'submit #guest_quote_form': '_onFormSubmit',
    },

    start: function () {
        this._super.apply(this, arguments);
        // Initialize autocomplete when modal is shown
        const modal = document.getElementById('guestQuoteModal');
        if (modal) {
            $(modal).on('shown.bs.modal', () => {
                this._initGoogleAutocomplete();
                this._setDefaultCountry();
            });
        }
        return this._super(...arguments);
    },

    /**
     * Set default country based on website domain
     */
    _setDefaultCountry: function () {
        const countrySelect = document.getElementById('guest_country');
        if (!countrySelect || countrySelect.value) {
            return; // Already has a value
        }

        // Get country code from domain or website settings
        const domain = window.location.hostname;
        let countryCode = null;

        // Map common TLDs to country codes
        const tldToCountry = {
            '.au': 'Australia',
            '.nz': 'New Zealand',
            '.uk': 'United Kingdom',
            '.us': 'United States',
            '.ca': 'Canada',
            '.de': 'Germany',
            '.fr': 'France',
            '.it': 'Italy',
            '.es': 'Spain',
            '.nl': 'Netherlands',
            '.be': 'Belgium',
            '.ch': 'Switzerland',
            '.at': 'Austria',
            '.se': 'Sweden',
            '.no': 'Norway',
            '.dk': 'Denmark',
            '.fi': 'Finland',
            '.ie': 'Ireland',
            '.pt': 'Portugal',
            '.pl': 'Poland',
            '.cz': 'Czech Republic',
            '.gr': 'Greece',
            '.jp': 'Japan',
            '.cn': 'China',
            '.in': 'India',
            '.br': 'Brazil',
            '.mx': 'Mexico',
            '.ar': 'Argentina',
            '.cl': 'Chile',
            '.co': 'Colombia',
            '.sg': 'Singapore',
            '.my': 'Malaysia',
            '.th': 'Thailand',
            '.za': 'South Africa',
        };

        // Check TLD
        for (const [tld, country] of Object.entries(tldToCountry)) {
            if (domain.endsWith(tld)) {
                countryCode = country;
                break;
            }
        }

        // If no TLD match, try to get from user's locale or default to first country
        if (!countryCode && navigator.language) {
            const locale = navigator.language.split('-');
            if (locale.length > 1) {
                const localeCountry = locale[1].toUpperCase();
                // This is a country code like US, AU, etc.
                // We'd need to match it, but for simplicity, just use the country name mapping
            }
        }

        // Select the country in the dropdown
        if (countryCode) {
            const options = countrySelect.options;
            for (let i = 0; i < options.length; i++) {
                if (options[i].text.includes(countryCode)) {
                    countrySelect.value = options[i].value;
                    countrySelect.dispatchEvent(new Event('change'));
                    break;
                }
            }
        }
    },

    /**
     * Initialize Google Places Autocomplete
     */
    _initGoogleAutocomplete: function () {
        const self = this;
        const input = document.getElementById('guest_street');
        
        if (!input || typeof google === 'undefined' || !google.maps || !google.maps.places) {
            console.log('Google Maps API not loaded');
            return;
        }

        const autocomplete = new google.maps.places.Autocomplete(input, {
            types: ['address'],
        });

        autocomplete.addListener('place_changed', function () {
            const place = autocomplete.getPlace();
            
            if (!place.geometry) {
                return;
            }

            self._fillAddressFields(place);
        });
    },

    /**
     * Fill address fields from Google Places result
     */
    _fillAddressFields: function (place) {
        const addressComponents = place.address_components;
        const addressMap = {
            street_number: '',
            route: '',
            locality: '',
            administrative_area_level_1: '',
            country: '',
            postal_code: '',
        };

        for (let component of addressComponents) {
            const type = component.types[0];
            if (addressMap.hasOwnProperty(type)) {
                addressMap[type] = component.long_name;
            }
        }

        // Fill street
        const street = (addressMap.street_number + ' ' + addressMap.route).trim();
        if (street) {
            document.getElementById('guest_street').value = street;
        }

        // Fill city
        if (addressMap.locality) {
            document.getElementById('guest_city').value = addressMap.locality;
        }

        // Fill zip
        if (addressMap.postal_code) {
            document.getElementById('guest_zip').value = addressMap.postal_code;
        }

        // Fill country
        if (addressMap.country) {
            this._selectCountryByName(addressMap.country).then(() => {
                // Fill state after country is selected
                if (addressMap.administrative_area_level_1) {
                    this._selectStateByName(addressMap.administrative_area_level_1);
                }
            });
        }
    },

    /**
     * Select country by name
     */
    _selectCountryByName: function (countryName) {
        const countrySelect = document.getElementById('guest_country');
        const options = countrySelect.options;
        
        for (let i = 0; i < options.length; i++) {
            if (options[i].text === countryName) {
                countrySelect.value = options[i].value;
                // Trigger change event to load states
                countrySelect.dispatchEvent(new Event('change'));
                return Promise.resolve();
            }
        }
        return Promise.resolve();
    },

    /**
     * Select state by name (called after states are loaded)
     */
    _selectStateByName: function (stateName) {
        setTimeout(() => {
            const stateSelect = document.getElementById('guest_state');
            const options = stateSelect.options;
            
            for (let i = 0; i < options.length; i++) {
                if (options[i].text.includes(stateName) || stateName.includes(options[i].text)) {
                    stateSelect.value = options[i].value;
                    break;
                }
            }
        }, 500);
    },

    /**
     * Handle Get Quote button click
     */
    _onGetQuoteClick: function (ev) {
        const btn = ev.currentTarget;
        const isLoggedIn = btn.getAttribute('data-user-logged-in') === 'True';
        
        // For guests, prevent default and show modal
        if (!isLoggedIn) {
            ev.preventDefault();
            const modalElement = document.getElementById('guestQuoteModal');
            if (modalElement) {
                // Use jQuery's Bootstrap modal (Odoo uses jQuery's Bootstrap)
                $(modalElement).modal('show');
            }
        }
        // For logged-in users, let the default link behavior work
    },

    /**
     * Handle country change to load states
     */
    _onCountryChange: function (ev) {
        const countryId = ev.target.value;
        const stateSelect = document.getElementById('guest_state');
        
        stateSelect.innerHTML = '<option value="">Select a state...</option>';
        
        if (!countryId) {
            return;
        }

        rpc('/shop/country_infos/' + countryId).then((data) => {
            if (data.states && data.states.length > 0) {
                data.states.forEach((state) => {
                    const option = document.createElement('option');
                    option.value = state[0];
                    option.textContent = state[1];
                    stateSelect.appendChild(option);
                });
            }
        });
    },

    /**
     * Handle form submission
     */
    _onFormSubmit: function (ev) {
        ev.preventDefault();
        const form = ev.target;
        const formData = new FormData(form);
        
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        fetch(form.action, {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (response.headers.get('content-type')?.includes('text/html')) {
                // If response is HTML, redirect to it
                return response.text().then(html => {
                    // Close modal first
                    $('#guestQuoteModal').modal('hide');
                    // Create a temporary container and insert the response
                    document.open();
                    document.write(html);
                    document.close();
                });
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success === false) {
                alert(data.error || 'An error occurred. Please try again.');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    },
});

export default publicWidget.registry.GuestQuoteForm;
