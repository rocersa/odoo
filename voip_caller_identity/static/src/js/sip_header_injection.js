/** @odoo-module */

/**
 * SIP Header Injection for Outbound Calls
 *
 * This module patches the Odoo VoIP/Phone module's SIP session layer to
 * inject custom SIP headers (e.g. X-Outbound-CallerID) into outbound
 * INVITE requests.
 *
 * Architecture:
 * Odoo's VoIP module uses SIP.js where outbound calls are initiated by
 * creating an Inviter and calling inviter.invite(). The SIP.js Inviter
 * accepts an `extraHeaders` option in the InviterInviteOptions.
 *
 * Approach:
 * We patch the voip service's method that initiates calls. In Odoo 18/19,
 * this is typically within a "softphone" or "voip" service. Since we can't
 * see the Enterprise source, we use Odoo's patch() utility to extend the
 * service/component methods.
 *
 * The patch intercepts call initiation, validates the selected identity,
 * builds the SIP headers, and passes them to the original call method.
 *
 * IMPORTANT: The exact patch targets (service names, method names) may need
 * to be adjusted after inspecting the actual Enterprise VoIP module on the
 * odoo.sh instance. Common patterns:
 *   - voip service: makeCall(), call()
 *   - softphone component: _onClickCall(), _makeCall()
 *   - sip_js service: _createSession(), _invite()
 *
 * NOTE ON SIP.js API:
 * SIP.js Inviter constructor: new Inviter(userAgent, targetURI, options)
 * SIP.js inviter.invite({
 *     requestOptions: {
 *         extraHeaders: ["X-Custom-Header: value"]
 *     }
 * })
 */

import { patch } from "@web/core/utils/patch";

/**
 * Utility: wrap any function to inject SIP headers.
 * This is used as a generic wrapper that can be applied to whatever
 * call-initiation method exists in the VoIP module.
 */
export function wrapWithCallerIdentity(originalFn, callerIdentityService) {
    return async function (...args) {
        // Validate the selected identity before proceeding
        const validation = await callerIdentityService.validateAndResolve();

        if (!validation.allowed) {
            // Call blocked by policy
            console.warn("[CallerIdentity] Call blocked:", validation.reason);
            return;
        }

        // Build extra SIP headers
        const extraHeaders = callerIdentityService.buildSipHeaders();

        // If extra headers exist, try to inject them into the call args.
        // The injection method depends on how the VoIP module passes options
        // to SIP.js. We handle common patterns:

        if (extraHeaders.length > 0) {
            // Pattern 1: If first arg is an options object with requestOptions
            if (args[0] && typeof args[0] === "object" && !Array.isArray(args[0])) {
                if (!args[0].requestOptions) {
                    args[0].requestOptions = {};
                }
                if (!args[0].requestOptions.extraHeaders) {
                    args[0].requestOptions.extraHeaders = [];
                }
                args[0].requestOptions.extraHeaders.push(...extraHeaders);
            }
            // Pattern 2: SIP headers stored on `this` or service state
            // for the SIP session to pick up
            if (this && this._callerIdentityHeaders !== undefined) {
                this._callerIdentityHeaders = extraHeaders;
            }
        }

        // Log the call
        const dialedNumber =
            typeof args[0] === "string"
                ? args[0]
                : args[0]?.number || args[0]?.phoneNumber || "unknown";
        await callerIdentityService.logCall(dialedNumber, validation.reason);

        // Call the original function
        return originalFn.apply(this, args);
    };
}

/**
 * This function attempts to patch the VoIP service at runtime.
 * It's called after the page loads and all services are registered.
 *
 * Since we don't have access to the Enterprise source, we look for
 * known service/component names and patch them.
 */
export function applyVoipPatches(env) {
    const callerIdentityService = env.services.voip_caller_identity;
    if (!callerIdentityService) {
        console.warn("[CallerIdentity] Caller identity service not found");
        return;
    }

    // Try to patch the voip service's call method
    const voipService = env.services.voip;
    if (voipService) {
        // Look for common method names
        const methodNames = ["makeCall", "call", "makeOutgoingCall", "startCall"];
        for (const methodName of methodNames) {
            if (typeof voipService[methodName] === "function") {
                const original = voipService[methodName].bind(voipService);
                voipService[methodName] = wrapWithCallerIdentity(
                    original,
                    callerIdentityService
                );
                console.info(
                    `[CallerIdentity] Patched voip.${methodName} for SIP header injection`
                );
                break;
            }
        }
    }
}
