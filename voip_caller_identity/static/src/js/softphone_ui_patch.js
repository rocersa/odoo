/** @odoo-module */

/**
 * Patch the Softphone OWL component to add the CallerIdentityDropdown.
 *
 * In Odoo 18/19, the softphone is an OWL component (likely named "Softphone"
 * or "SoftPhone") registered in the component registry. We patch it to:
 * 1. Add CallerIdentityDropdown as a sub-component
 * 2. Override the call initiation to inject SIP headers
 *
 * The exact component name and template need to match the Enterprise module.
 * Common names: "Softphone", "SoftPhone", "PhoneWidget", "DialPad"
 *
 * If direct component patching isn't possible (because we can't import the
 * Enterprise component), we use a template inheritance approach instead
 * (see the XML templates).
 */

import { patch } from "@web/core/utils/patch";
import { CallerIdentityDropdown } from "./caller_identity_dropdown";
import { applyVoipPatches } from "./sip_header_injection";

/**
 * We use a startup service to apply patches after all other services
 * and components are loaded.
 */
import { registry } from "@web/core/registry";

const callerIdentityStartup = {
    dependencies: ["voip_caller_identity"],

    start(env) {
        // Apply VoIP service patches after a short delay to ensure
        // the voip service is fully initialized
        setTimeout(() => {
            applyVoipPatches(env);
        }, 1000);

        // Also try to patch on first user interaction (in case VoIP
        // service initializes lazily)
        let patched = false;
        const observer = () => {
            if (!patched && env.services.voip) {
                applyVoipPatches(env);
                patched = true;
            }
        };
        // Check periodically until voip service is available
        const interval = setInterval(() => {
            observer();
            if (patched) {
                clearInterval(interval);
            }
        }, 2000);
        // Stop checking after 30 seconds
        setTimeout(() => clearInterval(interval), 30000);
    },
};

registry
    .category("services")
    .add("voip_caller_identity_startup", callerIdentityStartup);

// Export the dropdown component for use in XML templates
// The template injection is handled via XML view inheritance
export { CallerIdentityDropdown };
