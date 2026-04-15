/** @odoo-module */
/* global SIP */

import { patch } from "@web/core/utils/patch";
import { UserAgent } from "@voip/core/user_agent_service";
import { Session } from "@voip/core/session";
import { _t } from "@web/core/l10n/translation";

/**
 * Maps ISO country code → international calling code and local trunk prefix.
 * The trunk prefix (e.g. leading "0") is stripped before prepending +callingCode.
 * Add new countries here as needed.
 */
const COUNTRY_DIAL_RULES = {
    NZ: { callingCode: "64", trunkPrefix: "0" },
    AU: { callingCode: "61", trunkPrefix: "0" },
    GB: { callingCode: "44", trunkPrefix: "0" },
    US: { callingCode: "1", trunkPrefix: "1" },
};

/**
 * Normalizes a dialed phone number to E.164 using the selected caller identity's
 * country to determine the calling code. If the number already starts with "+"
 * or no identity/country is available, it is returned unchanged.
 *
 * @param {string} phoneNumber - The raw dialed number
 * @param {Object|null} identity - The selected caller identity (with country_code)
 * @returns {string} The normalized number
 */
function normalizePhoneNumber(phoneNumber, identity) {
    if (!phoneNumber) {
        return phoneNumber;
    }
    // Already in international format
    if (phoneNumber.startsWith("+")) {
        return phoneNumber;
    }
    // International dialing prefix (00) → replace with +
    if (phoneNumber.startsWith("00")) {
        return "+" + phoneNumber.slice(2);
    }
    const countryCode = identity?.country_code;
    if (!countryCode) {
        return phoneNumber;
    }
    const rules = COUNTRY_DIAL_RULES[countryCode];
    if (!rules) {
        return phoneNumber;
    }
    // Strip trunk prefix if present, then prepend +callingCode
    if (rules.trunkPrefix && phoneNumber.startsWith(rules.trunkPrefix)) {
        return "+" + rules.callingCode + phoneNumber.slice(rules.trunkPrefix.length);
    }
    return "+" + rules.callingCode + phoneNumber;
}

patch(UserAgent.prototype, {
    async makeCall(data, options = {}) {
        const callerIdentityService = this.env.services.voip_caller_identity;
        if (callerIdentityService) {
            const validation = await callerIdentityService.validateAndResolve();
            if (!validation.allowed) {
                console.warn("[CallerIdentity] Call blocked:", validation.reason);
                return;
            }
            // Normalize the dialed number based on the selected caller identity's country
            if (data?.phone_number) {
                const identity = callerIdentityService.getSelectedIdentity();
                const original = data.phone_number;
                data.phone_number = normalizePhoneNumber(data.phone_number, identity);
                if (data.phone_number !== original) {
                    console.log(`[CallerIdentity] Normalized ${original} → ${data.phone_number}`);
                }
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
