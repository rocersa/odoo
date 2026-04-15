/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";

patch(UserAgent.prototype, {
    async _onIncomingInvitation(inviteSession) {
        const displayName = inviteSession.remoteIdentity?.displayName || "";
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
