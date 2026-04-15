/** @odoo-module */
/* global SIP */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";

patch(UserAgent.prototype, {
    async makeCall(data, options = {}) {
        const callerIdentityService = this.env.services.voip_caller_identity;
        if (callerIdentityService) {
            const validation = await callerIdentityService.validateAndResolve();
            if (!validation.allowed) {
                console.warn("[CallerIdentity] Call blocked:", validation.reason);
                return;
            }
            this._pendingCallerIdentityHeaders = callerIdentityService.buildSipHeaders();
            const dialedNumber = data?.phone_number || "unknown";
            await callerIdentityService.logCall(dialedNumber, validation.reason);
        }
        return super.makeCall(data, options);
    },

    invite(call) {
        const extraHeaders = this._pendingCallerIdentityHeaders || [];
        delete this._pendingCallerIdentityHeaders;
        if (this.voip.mode === "demo" || extraHeaders.length === 0) {
            return super.invite(call);
        }
        const originalSipInvite = SIP.Inviter.prototype.invite;
        SIP.Inviter.prototype.invite = function (inviteOptions = {}) {
            if (!inviteOptions.requestOptions) {
                inviteOptions.requestOptions = {};
            }
            if (!inviteOptions.requestOptions.extraHeaders) {
                inviteOptions.requestOptions.extraHeaders = [];
            }
            inviteOptions.requestOptions.extraHeaders.push(...extraHeaders);
            return originalSipInvite.call(this, inviteOptions);
        };
        try {
            return super.invite(call);
        } finally {
            SIP.Inviter.prototype.invite = originalSipInvite;
        }
    },
});
