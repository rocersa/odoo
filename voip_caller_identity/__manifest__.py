{
    "name": "VoIP Caller Identity",
    "summary": "Select outbound caller ID (DID/brand) per call, transmitted to FreePBX via SIP headers",
    "description": """
        Extends Odoo Phone/VoIP to allow users to select an outbound caller identity
        before placing a call. The selected identity is transmitted to FreePBX via
        configurable SIP headers (e.g. X-Outbound-CallerID) so FreePBX can set the
        outbound caller ID dynamically per call.

        Features:
        - Manage outbound caller identities (DID numbers) with labels and country tags
        - Assign allowed identities to users, teams, and companies
        - Caller ID selector in the Phone/VoIP softphone widget
        - Custom SIP header injection on outbound INVITE
        - Per-call audit logging of selected caller identity
        - Configurable fallback behaviour for missing/invalid selections
    """,
    "author": "Harry",
    "category": "Productivity/Phone",
    "version": "19.0.1.0.0",
    "depends": ["voip", "crm"],
    "data": [
        "security/voip_caller_identity_security.xml",
        "security/ir.model.access.csv",
        "views/caller_identity_views.xml",
        "views/res_users_views.xml",
        "views/res_config_settings_views.xml",
        "views/voip_call_log_views.xml",
        "data/voip_caller_identity_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "voip_caller_identity/static/src/**/*",
        ],
    },
    "application": False,
    "installable": True,
    "license": "LGPL-3",
}
