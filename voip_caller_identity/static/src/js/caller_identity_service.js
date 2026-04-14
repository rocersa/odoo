/** @odoo-module */

import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";

export const callerIdentityService = {
    dependencies: ["orm", "user", "notification"],

    start(env, { orm, user, notification }) {
        const state = reactive({
            identities: [],
            selectedIdentityId: null,
            defaultIdentityId: null,
            sipHeaderName: "X-Outbound-CallerID",
            sipHeaderFormat: "number_only",
            fallbackBehaviour: "user_default",
            invalidIdentityAction: "fallback",
            loaded: false,
        });

        async function loadIdentities() {
            try {
                const identities = await orm.call(
                    "voip.caller.identity",
                    "get_allowed_identities",
                    []
                );
                state.identities = identities;

                // Load user's default identity
                const userData = await orm.read(
                    "res.users",
                    [user.userId],
                    ["voip_default_caller_identity_id"]
                );
                if (userData.length && userData[0].voip_default_caller_identity_id) {
                    state.defaultIdentityId = userData[0].voip_default_caller_identity_id[0];
                    // Pre-select default
                    if (!state.selectedIdentityId) {
                        state.selectedIdentityId = state.defaultIdentityId;
                    }
                }

                // Load SIP configuration
                const configKeys = [
                    "voip_caller_identity.sip_header_name",
                    "voip_caller_identity.sip_header_format",
                    "voip_caller_identity.fallback_behaviour",
                    "voip_caller_identity.invalid_identity_action",
                ];
                const params = await orm.call(
                    "ir.config_parameter",
                    "get_param",
                    ["voip_caller_identity.sip_header_name"],
                );
                if (params) {
                    state.sipHeaderName = params;
                }
                const format = await orm.call(
                    "ir.config_parameter",
                    "get_param",
                    ["voip_caller_identity.sip_header_format"],
                );
                if (format) {
                    state.sipHeaderFormat = format;
                }
                const fallback = await orm.call(
                    "ir.config_parameter",
                    "get_param",
                    ["voip_caller_identity.fallback_behaviour"],
                );
                if (fallback) {
                    state.fallbackBehaviour = fallback;
                }
                const invalidAction = await orm.call(
                    "ir.config_parameter",
                    "get_param",
                    ["voip_caller_identity.invalid_identity_action"],
                );
                if (invalidAction) {
                    state.invalidIdentityAction = invalidAction;
                }

                state.loaded = true;
            } catch (e) {
                console.error("Failed to load caller identities:", e);
                state.loaded = true;
            }
        }

        function selectIdentity(identityId) {
            state.selectedIdentityId = identityId;
        }

        function getSelectedIdentity() {
            if (!state.selectedIdentityId) {
                return null;
            }
            return state.identities.find((i) => i.id === state.selectedIdentityId) || null;
        }

        function buildSipHeaders() {
            const identity = getSelectedIdentity();
            if (!identity) {
                return [];
            }
            let headerValue;
            switch (state.sipHeaderFormat) {
                case "number_and_label":
                    headerValue = `"${identity.name}" <${identity.phone_number}>`;
                    break;
                case "sip_uri":
                    headerValue = `<sip:${identity.phone_number.replace("+", "")}@unknown>`;
                    break;
                case "number_only":
                default:
                    headerValue = identity.phone_number;
                    break;
            }
            return [`${state.sipHeaderName}: ${headerValue}`];
        }

        async function validateAndResolve() {
            const identity = getSelectedIdentity();
            if (!identity) {
                if (state.fallbackBehaviour === "block") {
                    notification.add(
                        "No caller identity selected. Call blocked by policy.",
                        { type: "danger" }
                    );
                    return { allowed: false, reason: "no_identity_blocked" };
                }
                // Try user default
                if (state.defaultIdentityId) {
                    state.selectedIdentityId = state.defaultIdentityId;
                    return {
                        allowed: true,
                        reason: "fallback_default",
                        identity: getSelectedIdentity(),
                    };
                }
                // No default either - allow call without header
                return { allowed: true, reason: "no_identity_proceed", identity: null };
            }

            // Validate via backend
            const result = await orm.call(
                "voip.caller.identity",
                "validate_identity_for_user",
                [identity.id]
            );
            if (result.valid) {
                return { allowed: true, reason: "success", identity };
            }

            // Invalid identity
            if (state.invalidIdentityAction === "block") {
                notification.add(
                    `Caller identity "${identity.name}" is not valid. Call blocked.`,
                    { type: "danger" }
                );
                return { allowed: false, reason: "invalid_blocked" };
            }

            // Fallback
            if (state.defaultIdentityId && state.defaultIdentityId !== identity.id) {
                state.selectedIdentityId = state.defaultIdentityId;
                notification.add(
                    `Falling back to default caller identity.`,
                    { type: "warning" }
                );
                return {
                    allowed: true,
                    reason: "fallback_default",
                    identity: getSelectedIdentity(),
                };
            }
            return { allowed: true, reason: "fallback_no_default", identity: null };
        }

        async function logCall(dialedNumber, validationResult) {
            const identity = getSelectedIdentity();
            try {
                await orm.call("voip.call.log", "log_call", [
                    {
                        caller_identity_id: identity ? identity.id : false,
                        resolved_phone_number: identity ? identity.phone_number : false,
                        dialed_number: dialedNumber,
                        validation_result: validationResult,
                        sip_header_method: state.sipHeaderName,
                    },
                ]);
            } catch (e) {
                console.error("Failed to log call:", e);
            }
        }

        // Load identities when service starts
        loadIdentities();

        return {
            state,
            loadIdentities,
            selectIdentity,
            getSelectedIdentity,
            buildSipHeaders,
            validateAndResolve,
            logCall,
        };
    },
};

registry
    .category("services")
    .add("voip_caller_identity", callerIdentityService);
