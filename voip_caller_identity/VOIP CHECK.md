🤖 FreePBX + Asterisk VoIP System — AI Validation Checklist

1. SIP / Trunk Registration (Core Connectivity)
   All SIP trunks show Registered / OK in FreePBX
   No repeated re-registration loops in Asterisk logs
   Each trunk has:
   Correct SIP credentials
   Correct host / endpoint
   NAT settings appropriate for deployment
   Inbound routes correctly mapped per DID/trunk
   Outbound routes assigned and prioritized correctly

👉 AI should verify:

SIP registration state (Asterisk sip show registry / pjsip show registrations)
No failed auth attempts in logs 2. DID → Inbound Routing Integrity
Every DID maps to a defined inbound route
No “default route fallback” unless intentional
Correct destination per DID:
Ring Group / Queue / Extension / IVR
Caller ID is preserved correctly
No overlapping inbound route conflicts

👉 AI should check:

Route matching order (most specific → least specific)
No duplicate DID patterns 3. Ring Groups / Call Distribution Logic
Ring groups contain correct extensions only
Ring strategy is correct:
ringall / hunt / memoryhunt (as intended)
Call stops ringing when one user answers
Failover destination configured (voicemail / overflow)
Timeout value is defined and reasonable

👉 AI should validate:

Group membership consistency with user list
No orphaned extensions in ring groups 4. Queue Behaviour (if used)
Queue agents correctly assigned
Ring strategy matches business logic
Queue timeout + retry logic configured
Queue failover destination set
Penalty values (if used) make sense
No paused/stuck agents by default

👉 AI should inspect:

Queue config consistency vs extension state
Agent availability logic 5. Voicemail System Integrity
Voicemail enabled per required extensions/ring groups
Correct email address configured per mailbox
SMTP configured and working in FreePBX
Voicemail attachment enabled
Greetings exist and are not default placeholders
Voicemail timeout routing is correct

👉 AI should validate:

Voicemail context mapping
Email config in FreePBX notification system
No missing mailbox definitions
Postfix service is running (`systemctl is-active postfix`)
Postfix mail queue is not backed up (`mailq`)
Postfix recent logs show successful relay/delivery of voicemail messages 6. Outbound Routing (Critical)
Outbound routes correctly match dial patterns
Correct trunk order (least cost / preferred routing)
Caller ID is set per route or per extension
Emergency / local dial rules included (if applicable)
No accidental open routes (security risk)

👉 AI should check:

Dial pattern conflicts
Route precedence order
CallerID override logic 7. Extension Configuration (Users)
Each extension:
Has correct SIP/PJSIP configuration
Has voicemail assigned if needed
Is assigned to correct ring group/queue
Device NAT settings appropriate (remote vs local)
DND / call forwarding not misconfigured by default

👉 AI should verify:

Extension → group → route linkage consistency
No unused or duplicate extensions 8. NAT / Firewall / RTP Media Path
External IP configured correctly in FreePBX
Local networks defined properly
RTP port range open and consistent
No symmetric NAT issues in config
One-way audio risk indicators absent

👉 AI should inspect:

Asterisk RTP settings
SIP NAT configuration
External media address correctness
PJSIP endpoint `direct_media` setting — should be `no` for remote/WebRTC users 9. Call Flow End-to-End Validation (Logical Simulation)

AI should simulate:

Inbound call:
DID → Inbound Route → Ring Group/Queue → Extension → Voicemail fallback
Missed call:
Ring timeout → correct fallback behaviour
Outbound call:
Extension → Outbound Route → correct trunk → external number
Transfer scenario:
Internal transfer → no call drop → correct routing preserved 10. Call Logging / CDR Integrity
Call Detail Records (CDR) are being generated
Inbound/outbound calls logged correctly
Duration is accurate
Caller ID recorded properly
No missing call records

👉 AI should check:

/var/log/asterisk/cdr-csv/
FreePBX CDR module status 11. Failover & Edge Case Handling
If all extensions unavailable → voicemail or overflow triggers
If trunk fails → secondary trunk used (if configured)
No dialplan loops or infinite redirects
Invalid DID handling is defined 12. Security & Exposure Checks
No anonymous SIP allowed (unless intentional)
Fail2Ban enabled (if used)
Fail2Ban jail for Asterisk/PJSIP is active and has non-zero log matches (`fail2ban-client status asterisk-iptables` or equivalent)
Fail2Ban banned IP list is populated for SIP attacks
Fail2Ban is watching the correct Asterisk log file (e.g. `/var/log/asterisk/full` or `/var/log/asterisk/fail2ban`)
Strong SIP credentials enforced
No exposed admin interfaces publicly without protection
No open dial patterns enabling toll fraud 13. Multi-Tenant / Multi-Region Logic (If Applicable)

Given your multi-country setup:

DIDs grouped logically per region
Correct caller ID per region outbound
Separate ring groups or queues per country
Failover routing does not break locality rules
No cross-region leakage of routing rules 14. Configuration Consistency Check (AI “Lint” Layer)

AI should flag:

Orphaned extensions
Unused trunks
Unused inbound routes
Duplicate dial patterns
Misaligned ring groups vs extensions
Inconsistent naming conventions 15. Full System Simulation Test (Final Gate)

AI should confirm a full lifecycle works:

Call DID inbound
Route hits correct inbound rule
Ring group or queue rings correctly
User answers successfully
Call logs correctly
Missed call fallback works
Voicemail works and sends email
Callback outbound uses correct trunk + caller ID
Transfer between users works
---

## Reference Locations

- **Odoo Softphone Code:** `odoo/addons/voip*` and `voip_caller_identity/`
- **Asterisk / FreePBX Config:** Accessible via `ssh root@freepbx`

## Active DIDs

| Region    | Brand   | DID             | Destination       | No-Answer Failover  |
|-----------|---------|-----------------|-------------------|---------------------|
| NZ        | Gabions | 04 888 7440     | Ring Group 2000   | Voicemail 1100      |
| NZ        | Corten  | 04 888 7441     | Ring Group 2000   | Voicemail 1100      |
| Australia | Gabions | 02 4062 0025    | Ring Group 2000   | Voicemail 1100      |
| Australia | Corten  | 02 4062 0026    | Ring Group 2000   | Voicemail 1100      |
| UK        | Gabions | 01793 386000    | Ring Group 2000   | Voicemail 1100      |
| UK        | Corten  | 01793 386001    | Ring Group 2000   | Voicemail 1100      |
| USA       | Gabions | 323 300 2585    | Ring Group 2000   | Voicemail 1100      |
| USA       | Corten  | 323 300 2558    | Ring Group 2000   | Voicemail 1100      |

---

## Execution Approach

The validation should be performed as a single, structured pass through the 15 checklist items, executed remotely on `root@freepbx` via SSH and locally via Odoo code inspection. Work is grouped into phases for efficiency.

### Phase 1 — Setup & Baseline
1. Record baseline system info on FreePBX:
   - `asterisk -rx "core show version"`
   - `asterisk -rx "pjsip show registrations"` (or `sip show registry` if chan_sip)
   - `fwconsole show sysinfo` (if available)
2. Inspect Odoo module versions (`voip_caller_identity/__manifest__.py`, `odoo/addons/voip/__manifest__.py`).

### Phase 2 — FreePBX Configuration Validation (Items 1–8)
Run targeted SQL queries against the FreePBX `asterisk` MySQL database and Asterisk CLI commands.

| Item | Validation Method |
|------|-------------------|
| **1. SIP / Trunk Registration** | `pjsip show registrations` / `sip show registry`; `SELECT * FROM trunks WHERE disabled != 'on';` check for credentials in `/etc/asterisk/pjsip*.conf` or `sip_additional.conf` |
| **2. DID → Inbound Routing** | `SELECT extension, cidnum, destination, description FROM incoming ORDER BY extension, cidnum;` verify each Active DID maps to a route; check for duplicates/overlaps |
| **3. Ring Groups** | `SELECT grpnum, strategy, grptime, grplist, postdest, description FROM ringgroups;` verify Ring Group 2000 contains correct extensions; check no orphans |
| **4. Queue Behaviour** | `SELECT * FROM queues_config; SELECT * FROM queues_details;` verify agents, strategy, timeout, failover |
| **5. Voicemail** | Check voicemail config in `/etc/asterisk/voicemail.conf`; verify Postfix is running and delivering; check mailboxes map to extensions |
| **6. Outbound Routing** | `SELECT * FROM outbound_routes JOIN outbound_route_patterns USING (route_id) JOIN outbound_route_trunks USING (route_id);` check dial patterns, trunk order, caller ID, emergency routes |
| **7. Extension Configuration** | Query FreePBX users/devices; inspect `/etc/asterisk/pjsip*.conf` for NAT/settings; verify linkage to ring groups/queues |
| **8. NAT / Firewall / RTP** | Inspect `rtp.conf` and `pjsip.conf`/`pjsip.transports.conf` for external IP, local nets, port range; verify `direct_media` on endpoints |

### Phase 3 — Call Flow & Logical Simulation (Items 9–11)
- **Item 9 (Call Flow E2E):** Trace each Active DID through inbound route → destination (Ring Group 2000) → extensions → failover (Voicemail 1100). Document the complete path.
- **Item 10 (CDR):** Verify `/var/log/asterisk/cdr-csv/` exists and has recent entries; query `asteriskcdrdb` CDR table for recent calls per DID.
- **Item 11 (Failover & Edge Cases):** Confirm Ring Group 2000 `postdest` points to Voicemail 1100; verify trunk failover order; check for dialplan loops in `/etc/asterisk/extensions*.conf`.

### Phase 4 — Security & Multi-Tenant (Items 12–14)
- **Item 12 (Security):** Check PJSIP global config for anonymous access; verify Fail2Ban status, jails, and correct log paths; review exposed admin interfaces.
- **Item 13 (Multi-Tenant/Region):** Map each DID to its region/brand; verify outbound caller ID per region; confirm no cross-region routing leakage.
- **Item 14 (Consistency Lint):** Cross-reference all tables to flag orphaned extensions, unused trunks/routes, duplicate dial patterns, naming inconsistencies.

### Phase 5 — Odoo Integration Cross-Check
- Review `voip_caller_identity/models/caller_identity.py` to confirm outbound caller ID selection logic aligns with FreePBX SIP header expectations.
- Check `voip_caller_identity/models/voip_call_log.py` to ensure audit logging captures resolved caller ID.
- Verify Odoo `voip` module softphone code sends the configured SIP header(s) on outbound calls.

### Phase 6 — Final System Simulation Summary (Item 15)
- Synthesize findings into a logical pass/fail narrative for the full lifecycle:
  1. Inbound DID → Route → Ring Group → Extension
  2. Missed call → Voicemail 1100
  3. Outbound call → correct trunk + caller ID
  4. CDR logging accuracy
  5. Transfer integrity

## Known Operational Constraints

- **Emergency dialling routes are not required** for this deployment.
- **All DIDs that travel over a Telnyx trunk must have a specific inbound endpoint** in the `incoming` table. No catch-all/default route fallback should exist unless explicitly required.

## Remediation Playbook

### Fix `direct_media` for WebRTC / remote endpoints
Update the FreePBX `sip` table directly (preferred over custom conf files):
```sql
UPDATE sip SET data="no" WHERE keyword="direct_media" AND id IN (1001,1002,1003,1004,1005,1006,1007,1009,1010,1011,1100);
```
Then reload Asterisk: `fwconsole reload`

Verify with: `asterisk -rx "pjsip show endpoint 1001" | grep direct_media`

### Remove a Catch All inbound route
If a catch-all route exists (`extension=''` in the `incoming` table), delete it and reload FreePBX:
```sql
DELETE FROM incoming WHERE extension='' AND description='Catch All';
```
Then run: `fwconsole reload`

### Fix Fail2Ban Asterisk log path
1. Review `/etc/fail2ban/jail.local` and `/etc/fail2ban/filter.d/asterisk.conf`.
2. If `/var/log/asterisk/fail2ban` is empty, change the `asterisk-iptables` jail `logpath` to `/var/log/asterisk/full`.
3. Restart fail2ban: `systemctl restart fail2ban`.
4. Verify: `fail2ban-client status asterisk-iptables` should show non-zero failed/banned counts after the next scan cycle.

---

⚠️ Key AI Focus Areas (Important)

The agent should prioritise detecting:

Routing mismatches (most common failure)
SIP NAT / audio issues (second most common)
Caller ID misconfiguration (business-critical)
Voicemail email failures (silent failure risk)
Dialplan conflicts or overlapping routes
