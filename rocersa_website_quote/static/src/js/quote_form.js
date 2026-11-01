/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class QuoteForm extends Interaction {
    static selector = "#rocersa_quote_modal";

    dynamicContent = {
        "#rocersa_quote_country": { "t-on-change": this.onCountryChange },
    };

    setup() {
        const params = new URLSearchParams(window.location.search);
        for (const key of ["utm_source", "utm_medium", "utm_campaign"]) {
            const input = this.el.querySelector(`[name="${key}"]`);
            if (input && !input.value) {
                input.value = params.get(key) || "";
            }
        }
    }

    async onCountryChange(ev) {
        const countryId = ev.target.value;
        const stateSelect = this.el.querySelector("#rocersa_quote_state");
        stateSelect.replaceChildren(new Option("Select a state...", ""));
        if (!countryId) {
            return;
        }
        const data = await rpc(`/website/country_infos/${countryId}`);
        for (const [id, name] of data.states || []) {
            stateSelect.appendChild(new Option(name, id));
        }
    }
}

registry
    .category("public.interactions")
    .add("rocersa_website_quote.quote_form", QuoteForm);
