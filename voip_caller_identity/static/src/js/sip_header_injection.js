/** @odoo-module */
/* global SIP */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";
import { Session } from "@voip/core/session";
import { _t } from "@web/core/l10n/translation";

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
        const inviterOptions = {};
        if (extraHeaders.length > 0) {
            inviterOptions.extraHeaders = extraHeaders;
        }
        try {
            var inviter = new SIP.Inviter(
                this.__sipJsUserAgent,
                this.makeUri(phoneNumber),
                inviterOptions
            );
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
        inviter
            .invite({
                requestDelegate: session.inviteRequestDelegate,
                sessionDescriptionHandlerOptions,
            })
            .catch((error) => {
                if (error.name !== "NotAllowedError") {
                    throw error;
                }
            });
        return session;
    },
});
