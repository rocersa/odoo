# VoIP Caller Identity

This Odoo module lets users choose an outbound caller identity (DID / brand) for each call made through the Odoo softphone. The selected identity is passed to the Asterisk/FreePBX server (`root@freepbx`) via a custom SIP header so that the outbound trunk can present the correct caller ID.

## How it works — Odoo side

1. **Select an identity**  
   Before dialing, the user picks a caller identity from the softphone dropdown. Identities are filtered by user, CRM team, and company.

2. **Validation & normalisation**  
   The module validates that the user is allowed to use the chosen identity. The dialed number is normalised to E.164 using the identity’s country (e.g. `09 123 4567` → `+6491234567` for NZ).

3. **SIP header injection**  
   When the call is placed, the identity is injected as an extra SIP header on the outbound `INVITE`.  
   *Default header name:* `X-Outbound-CallerID`  
   *Default value:* the identity’s E.164 phone number (configurable in **Settings → VoIP**).

4. **Audit logging**  
   Every call logs the selected identity, resolved number, dialed number, and SIP header used.

## How it works — Asterisk/FreePBX side

The FreePBX server runs a custom dialplan in `/etc/asterisk/extensions_custom.conf` that intercepts trunk calls before they leave the system.

### Dialplan macros

```asterisk
[macro-dialout-trunk-predial-hook]
exten => s,1,Log(NOTICE,=== Caller Identity Predial Hook ===)
same => n,Set(ODOO_CID=${PJSIP_HEADER(read,X-Outbound-CallerID)})
same => n,ExecIf($[${LEN(${ODOO_CID})} > 0]?Set(CALLERID(num)=${ODOO_CID}))
same => n,ExecIf($[${LEN(${ODOO_CID})} > 0]?Set(CALLERID(ani)=${ODOO_CID}))
same => n,ExecIf($[${LEN(${ODOO_CID})} > 0]?Set(DIAL_TRUNK_OPTIONS=${DIAL_TRUNK_OPTIONS}b(macro-outbound-cid-override^s^1(${ODOO_CID}))))
same => n,Return()

[macro-outbound-cid-override]
exten => s,1,Log(NOTICE,Adding P-Asserted-Identity on outbound trunk: ${ARG1})
same => n,Set(PJSIP_HEADER(add,P-Asserted-Identity)=<sip:${ARG1:1}@sip.telnyx.com>)
same => n,Return()
```

### Step-by-step on the PBX

1. **Read the header**  
   `PJSIP_HEADER(read,X-Outbound-CallerID)` reads the custom header from the inbound PJSIP channel sent by Odoo and stores it in `${ODOO_CID}`.

2. **Override caller ID**  
   If the header is present, both `CALLERID(num)` and `CALLERID(ani)` are set to the received number. This ensures the trunk uses the requested DID as the outbound caller ID.

3. **Add P-Asserted-Identity**  
   The `DIAL_TRUNK_OPTIONS` flag triggers a post-answer macro that adds a `P-Asserted-Identity` header on the outbound leg. The macro strips the leading `+` and formats the value as `<sip:NUMBER@sip.telnyx.com>`, which is required by the upstream SIP provider.

4. **Fallback**  
   If no `X-Outbound-CallerID` header is received, FreePBX leaves the caller ID unchanged and uses the extension’s default outbound CID.

## Configuration

Go to **Settings → VoIP → Caller Identity** to change:

* SIP header name (default: `X-Outbound-CallerID`)
* SIP header format (`number_only`, `number_and_label`, `sip_uri`)
* Fallback behaviour when no identity is selected
* System default caller identity

Caller identities themselves are managed under **VoIP → Caller Identities**.
