/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";

// Odoo core builds the incoming call with
// `phone_number: inviteSession.remoteIdentity.uri.user`, but `phone_number`
// is `required=True` on voip.call. A caller who withholds their number (or a
// synthetic test call) arrives with no user part, so the create fails and the
// user sees "Missing required value for the field 'Phone Number'".
// Substitute a fallback before core builds the record: the extension for an
// internal call, otherwise "Anonymous".
const ANONYMOUS_PHONE_NUMBER = "Anonymous";
const EXTENSION_RE = /^\d{2,6}$/;

function fallbackPhoneNumber(inviteSession) {
    const displayName = (inviteSession.remoteIdentity?.displayName || "").trim();
    if (EXTENSION_RE.test(displayName)) {
        return displayName;
    }
    return ANONYMOUS_PHONE_NUMBER;
}

patch(UserAgent.prototype, {
    async _onIncomingInvitation(inviteSession) {
        const displayName = inviteSession.remoteIdentity?.displayName || "";
        const remoteUri = inviteSession.remoteIdentity?.uri;
        if (remoteUri && !remoteUri.user) {
            remoteUri.user = fallbackPhoneNumber(inviteSession);
        }
        const previousSession = this.activeSession;
        await super._onIncomingInvitation(inviteSession);
        if (
            this.activeSession &&
            this.activeSession !== previousSession &&
            displayName
        ) {
            this.activeSession.call.update({ caller_id_name: displayName });
        }
    },
});
