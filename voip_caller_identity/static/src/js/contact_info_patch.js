/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ContactInfo } from "@voip/softphone/contact_info";

patch(ContactInfo, {
    props: {
        ...ContactInfo.props,
        callerIdName: { type: String, optional: true },
    },
});

patch(ContactInfo.prototype, {
    get contactName() {
        const baseName = this.contact?.voipName || this.props.phoneNumber;
        if (this.props.callerIdName) {
            return `${this.props.callerIdName} ${baseName}`;
        }
        return baseName;
    },
});
