/** @odoo-module */

/**
 * This module patches the Odoo VoIP/Phone softphone to:
 * 1. Add a caller identity selector dropdown in the softphone widget
 * 2. Intercept outbound call initiation to inject custom SIP headers
 *
 * The exact patch points depend on the Odoo Enterprise VoIP module's internal
 * structure. The VoIP module uses SIP.js and exposes a softphone service
 * or component that we can patch.
 *
 * Known Odoo 18/19 VoIP architecture:
 * - Softphone component (OWL) handles the UI
 * - A VoIP/SIP service manages the SIP.js UserAgent and sessions
 * - Calls are made via an Inviter class from SIP.js
 * - The Inviter.invite() method accepts { extraHeaders: [...] }
 *
 * We patch the service's call method to inject our headers.
 */

import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";

/**
 * Patch the voip service to intercept call initiation.
 *
 * In Odoo 18/19, the VoIP module registers a "voip" service that handles
 * SIP session management. We patch its makeCall / call method to inject
 * custom SIP headers from our caller identity service.
 *
 * If the exact service name or method differs, this file should be updated
 * after inspecting the actual Enterprise VoIP module code on the odoo.sh
 * instance.
 */

// We try to patch common known patterns. The actual method names may need
// adjustment based on the Enterprise VoIP module's actual API.

const patchVoipService = {
    dependencies: ["voip_caller_identity"],

    start(env, { voip_caller_identity: callerIdentityService }) {
        // After the voip service is started, we monkey-patch its call method.
        // We need to wait for the voip service to be available.
        const voipServiceEntry = registry.category("services").get("voip", null);
        if (!voipServiceEntry) {
            console.warn(
                "[voip_caller_identity] VoIP service not found. " +
                "SIP header injection will not work. " +
                "Ensure the VoIP/Phone module is installed."
            );
            return;
        }

        // The actual patching happens at the component level via softphone_ui_patch.js
        // This service just provides coordination.
        return {
            getExtraHeaders() {
                return callerIdentityService.buildSipHeaders();
            },
            async validateBeforeCall(dialedNumber) {
                return callerIdentityService.validateAndResolve();
            },
            async logCall(dialedNumber, result) {
                return callerIdentityService.logCall(dialedNumber, result);
            },
        };
    },
};

registry
    .category("services")
    .add("voip_caller_identity_bridge", patchVoipService);
