/** @odoo-module */
/* global SIP */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";
import { Session } from "@voip/core/session";
import { _t } from "@web/core/l10n/translation";

patch(UserAgent.prototype, {
    async makeCall(data, options = {}) {
        console.log("[CallerIdentity] makeCall invoked", data, options);
        const callerIdentityService = this.env.services.voip_caller_identity;
        if (callerIdentityService) {
            const validation = await callerIdentityService.validateAndResolve();
            console.log("[CallerIdentity] validation result:", validation);
            if (!validation.allowed) {
                console.warn("[CallerIdentity] Call blocked:", validation.reason);
                return;
            }
            this._pendingCallerIdentityHeaders = callerIdentityService.buildSipHeaders();
            console.log("[CallerIdentity] built headers:", this._pendingCallerIdentityHeaders);
            const dialedNumber = data?.phone_number || "unknown";
            await callerIdentityService.logCall(dialedNumber, validation.reason);
        }
        return super.makeCall(data, options);
    },

    invite(call) {
        const extraHeaders = this._pendingCallerIdentityHeaders || [];
        console.log("[CallerIdentity] invite() extraHeaders:", extraHeaders);
        delete this._pendingCallerIdentityHeaders;
        if (this.voip.mode === "demo") {
            const session = new Session(call);
            this.demoTimeout = setTimeout(() => {
                session._onOutgoingInviteAccepted();
            }, 3000);
            return session;
        }
        const phoneNumber = this.voip.willCallFromAnotherDevice
            ? this.voip.store.settings.external_device_number
            : call.phone_number;
        try {
            var inviter = new SIP.Inviter(this.__sipJsUserAgent, this.makeUri(phoneNumber));
        } catch (error) {
            console.error(error);
            this.voip.triggerError(
                _t(
                    "An error occurred trying to invite the following number: %(phoneNumber)s\n\nError: %(error)s",
                    { phoneNumber, error: error.message }
                )
            );
            throw error;
        }
        const session = new Session(call, inviter);
        if (this.voip.willCallFromAnotherDevice) {
            session.transferTarget = call.phone_number;
        }
        const sessionDescriptionHandlerOptions = { constraints: Session.mediaConstraints };
        const inviteOptions = {
            requestDelegate: session.inviteRequestDelegate,
            sessionDescriptionHandlerOptions,
        };
        if (extraHeaders.length > 0) {
            inviteOptions.requestOptions = { extraHeaders };
        }
        console.log("[CallerIdentity] inviter.invite options:", JSON.parse(JSON.stringify(inviteOptions)));
        inviter
            .invite(inviteOptions)
            .catch((error) => {
                if (error.name !== "NotAllowedError") {
                    throw error;
                }
            });
        return session;
    },
});
