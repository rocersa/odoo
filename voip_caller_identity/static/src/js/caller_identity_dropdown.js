/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class CallerIdentityDropdown extends Component {
    static template = "voip_caller_identity.CallerIdentityDropdown";
    static components = { Dropdown, DropdownItem };
    static props = {
        compact: { type: Boolean, optional: true },
    };

    setup() {
        this.callerIdentityService = useService("voip_caller_identity");
        this.state = useState({
            get identities() {
                return this.callerIdentityService?.state?.identities || [];
            }.bind(this),
        });
    }

    get identities() {
        return this.callerIdentityService.state.identities;
    }

    get selectedIdentity() {
        return this.callerIdentityService.getSelectedIdentity();
    }

    get selectedLabel() {
        const identity = this.selectedIdentity;
        if (!identity) {
            return "Select Caller ID";
        }
        if (this.props.compact) {
            return identity.country_code
                ? `${identity.country_code} ${identity.name}`
                : identity.name;
        }
        return `${identity.name} (${identity.phone_number})`;
    }

    get hasIdentities() {
        return this.identities.length > 0;
    }

    onSelectIdentity(identityId) {
        this.callerIdentityService.selectIdentity(identityId);
    }
}
