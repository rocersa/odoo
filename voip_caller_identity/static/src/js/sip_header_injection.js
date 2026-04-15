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
 * Infers an ISO country code from an E.164 phone number when the identity's
 * country_code field is not set.
 */
function inferCountryCodeFromPhoneNumber(phoneNumber) {
    if (!phoneNumber || !phoneNumber.startsWith("+")) {
        return null;
    }
    for (const [country, rules] of Object.entries(COUNTRY_DIAL_RULES)) {
        if (phoneNumber.startsWith("+" + rules.callingCode)) {
            return country;
        }
    }
    return null;
}

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
    let countryCode = identity?.country_code;
    let inferred = false;
    if (!countryCode && identity?.phone_number) {
        const inferredCode = inferCountryCodeFromPhoneNumber(identity.phone_number);
        if (inferredCode) {
            countryCode = inferredCode;
            inferred = true;
        }
    }
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
            let originalNumber = null;
            let normalized = false;
            let normalizationNote = null;
            if (data?.phone_number) {
                const identity = callerIdentityService.getSelectedIdentity();
                originalNumber = data.phone_number;
                const normalizedNumber = normalizePhoneNumber(data.phone_number, identity);
                if (normalizedNumber !== originalNumber) {
                    normalized = true;
                    if (!identity?.country_code && identity?.phone_number) {
                        normalizationNote = `Normalized from ${originalNumber} using country inferred from identity number ${identity.phone_number}`;
                    } else {
                        normalizationNote = `Normalized from ${originalNumber} using identity country ${identity?.country_code || "none"}`;
                    }
                    console.log(`[CallerIdentity] Normalized ${originalNumber} → ${normalizedNumber}`);
                } else {
                    if (!identity) {
                        normalizationNote = "Skipped: no caller identity selected";
                    } else if (!identity.country_code && !identity.phone_number) {
                        normalizationNote = `Skipped: identity ${identity.name} has no country code or phone number to infer from`;
                    } else if (!identity.country_code && identity.phone_number) {
                        normalizationNote = `Skipped: could not infer country from identity number ${identity.phone_number}`;
                    } else if (originalNumber.startsWith("+")) {
                        normalizationNote = "Skipped: number already in international format";
                    } else if (!COUNTRY_DIAL_RULES[identity.country_code]) {
                        normalizationNote = `Skipped: unknown country code ${identity.country_code}`;
                    } else {
                        normalizationNote = "Skipped: unexpected normalization result";
                    }
                    console.warn(`[CallerIdentity] Number not normalized: ${originalNumber}. ${normalizationNote}`);
                }
                data.phone_number = normalizedNumber;
                if (!data.phone_number.startsWith("+")) {
                    console.warn(`[CallerIdentity] Dialed number lacks country code: ${data.phone_number}`);
                }
            }
            this._pendingCallerIdentityHeaders = callerIdentityService.buildSipHeaders();
            const dialedNumber = data?.phone_number || "unknown";
            await callerIdentityService.logCall(
                dialedNumber,
                validation.reason,
                originalNumber,
                normalized,
                normalizationNote
            );
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
