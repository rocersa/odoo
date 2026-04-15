/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Dialer } from "@voip/softphone/dialer";
import { CallerIdentityDropdown } from "./caller_identity_dropdown";

patch(Dialer, {
    components: {
        ...Dialer.components,
        CallerIdentityDropdown,
    },
});
