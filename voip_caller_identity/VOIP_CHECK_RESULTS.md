# VoIP System Validation Results

**Checklist:** VOIP CHECK.md  
**Started:** 2026-04-16 09:52 AEST  
**System:** FreePBX + Asterisk 22.8.2 + Odoo 19.0

---

## Phase 1 — Setup & Baseline

**Status:** 🟢 Complete  
**Checked at:** 2026-04-16 09:52

**Evidence:**
- Asterisk version: `Asterisk 22.8.2 built by jenkins @ 9f8fbe1f9fdf on a x86_64 running Linux on 2026-03-16 06:15:45 UTC`
- PJSIP registrations (4 trunks, all Registered):
  - `au-telnyx` → `sip.telnyx.com:5060` — Registered (exp. 489s)
  - `nz-telnyx` → `sip.telnyx.com:5060` — Registered (exp. 358s)
  - `uk-telnyx` → `sip.telnyx.com:5060` — Registered (exp. 373s)
  - `us-telnyx` → `sip.telnyx.com:5060` — Registered (exp. 360s)
- Legacy SIP (`sip show registry`) not available — system is PJSIP-only.
- Odoo module versions:
  - `voip_caller_identity`: `19.0.1.0.24`
  - `voip` (core): `2.0`

**Anomalies:**
- None

**Actions:**
- Proceed to Phase 2.

---

## Item 1 — SIP / Trunk Registration (Core Connectivity)

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:55

**Evidence:**
- 4 PJSIP trunks all show `Registered` to `sip.telnyx.com:5060`.
- Trunk table:
  | trunkid | tech | channelid | name | outcid | disabled |
  |---|---|---|---|---|---|
  | 1 | pjsip | nz-telnyx | nz-telnyx | Gabion1 NZ | off |
  | 2 | pjsip | uk-telnyx | uk-telnyx | Gabion1 UK | off |
  | 3 | pjsip | us-telnyx | us-telnyx | Gabion1 USA | off |
  | 4 | pjsip | au-telnyx | au-telnyx | Gabion1 Australia | off |
- Asterisk logs show no repeated re-registration loops.
- PJSIP AOR configs show contacts registered to `sip:rocersa@sip.telnyx.com:5060`.

**Anomalies:**
- None

**Actions:**
- None

---

## Item 2 — DID → Inbound Routing Integrity

**Status:** 🟢 Pass (fixed)  
**Checked at:** 2026-04-16 09:55 (updated 10:05)

**Evidence:**
- All 8 documented DIDs are mapped in the `incoming` table:
  | DID | Destination | Description |
  |---|---|---|
  | +6448887440 | ext-group,2000,1 | NZ Gabions |
  | +6448887441 | ext-group,2000,1 | NZ Corten |
  | +61240620025 | ext-group,2000,1 | AU Gabions |
  | +61240620026 | ext-group,2000,1 | AU Corten |
  | +441793386000 | ext-group,2000,1 | UK Gabions |
  | +441793386001 | ext-group,2000,1 | UK Corten |
  | +13233002585 | ext-group,2000,1 | US Gabions |
  | +13233002558 | ext-group,2000,1 | US Corten |
- ~~There was a **"Catch All"** route: `extension=` (empty), `destination=from-did-direct,1000,1`, `description=Catch All`.~~
- **Fixed:** Catch All route deleted from `incoming` table and `fwconsole reload` executed. No catch-all remains in `/etc/asterisk/extensions_additional.conf`.

**Anomalies:**
- None remaining.

**Actions:**
- ✅ Removed catchall route.

---

## Item 3 — Ring Groups / Call Distribution Logic

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:55

**Evidence:**
- Ring Group 2000 ("Riverbank Office"):
  - Strategy: `ringall`
  - Timeout: `100` seconds
  - Members: `1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1009, 1011, 1010`
  - Post-dest (failover): `from-did-direct,1100,1` → Voicemail extension 1100
- All 11 extensions in the ring group have matching PJSIP endpoints in `/etc/asterisk/pjsip.endpoint.conf`.
- No orphaned extensions found.

**Anomalies:**
- None

**Actions:**
- None

---

## Item 4 — Queue Behaviour

**Status:** 🟢 Pass (N/A — no queues in use)  
**Checked at:** 2026-04-16 09:55

**Evidence:**
- `queues_config` table is empty.
- `queues_details` table is empty.
- System does not use queues; all inbound calls route directly to Ring Group 2000.

**Anomalies:**
- None

**Actions:**
- None

---

## Item 5 — Voicemail System Integrity

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:56 (updated 10:00)

**Evidence:**
- Voicemail config (`/etc/asterisk/voicemail.conf`):
  - `serveremail=notifications@rocersa.nz`
  - `attach=yes` (voicemail attachments enabled)
  - `forcegreetings=yes`, `forcename=yes`
  - Mailbox `1100=,Voicemail,admin@rocersa.nz,,attach=yes|saycid=no|envelope=no|delete=no`
- Extension 1100 is configured as the voicemail box.
- All other extensions have `voicemail=novm` in the users table.
- PJSIP endpoint 1100 has `mailboxes=1100@default`.
- **Postfix is `active`** and processing mail successfully.
- Postfix recent logs show successful external relay via `smtp.resend.com:2587`:
  - `to=<admin@rocersa.nz>, relay=smtp.resend.com[54.205.195.44]:2587, status=sent`
  - `to=<dev@rocersa.nz>, relay=smtp.resend.com[54.157.71.137]:2587, status=sent`
- Mail queue is empty (no backlog).

**Anomalies:**
- None. Voicemail-to-email path is confirmed working.

**Actions:**
- None

---

## Item 6 — Outbound Routing (Critical)

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:56

**Evidence:**
- Outbound routes configured per country:
  | Route | Pattern | Trunk |
  |---|---|---|
  | Internal | `XXXX` | — (intracompany) |
  | NZ Calls | `+64X.` | nz-telnyx (1) |
  | US Calls | `+1X.` | us-telnyx (3) |
  | UK Calls | `+44X.` | uk-telnyx (2) |
  | AU Calls | `+61X.` | au-telnyx (4) |
- Each route has exactly one trunk assignment; no overlapping/conflicting dial patterns.
- No wildcard open routes that would enable toll fraud.
- Emergency route flag is not set on any route (no explicit emergency dialing configured).

**Anomalies:**
- No emergency/local dial rules configured (if applicable for your regions, this may be a gap).

**Actions:**
- **Add emergency routes** (e.g. 111 for NZ, 000 for AU, 999 for UK, 911 for US) if required by business policy.

---

## Item 7 — Extension Configuration (Users)

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:56

**Evidence:**
- 11 user extensions + 1 voicemail extension (1100):
  | Ext | Name | Device | Voicemail |
  |---|---|---|---|
  | 1000 | Harry | PJSIP/1000 | novm |
  | 1001 | Panama - David | PJSIP/1001 | novm |
  | 1002 | Bolivia - Mariette | PJSIP/1002 | novm |
  | 1003 | Austria - Heather | PJSIP/1003 | novm |
  | 1004 | Guyana - Kat | PJSIP/1004 | novm |
  | 1005 | Cuba - Taupo | PJSIP/1005 | novm |
  | 1006 | Canada - Gemma | PJSIP/1006 | novm |
  | 1007 | Sardinia - Steff | PJSIP/1007 | novm |
  | 1009 | Malta - DB Laptop | PJSIP/1009 | novm |
  | 1010 | Gemma Laptop | PJSIP/1010 | novm |
  | 1011 | DWB Riverbank new | PJSIP/3 | novm |
  | 1100 | Voicemail | PJSIP/1100 | default |
- All devices are `fixed` type and mapped to users.
- PJSIP endpoints have NAT helpers: `force_rport=yes`, `rewrite_contact=yes`, `rtp_symmetric=yes`.

**Anomalies:**
- Device 1011 uses `dial=PJSIP/3` (unusual — most use matching extension ID). This may be intentional but is worth confirming.
- `direct_media=yes` on all endpoints. For remote/NAT users this can cause one-way audio.

**Actions:**
- **Confirm device 1011 mapping to PJSIP/3 is intentional.**
- **Consider setting `direct_media=no`** for endpoints that are used remotely.

---

## Item 8 — NAT / Firewall / RTP Media Path

**Status:** 🟢 Pass (fixed)  
**Checked at:** 2026-04-16 09:57 (updated 10:08)

**Evidence:**
- Transport config (`pjsip.transports.conf`):
  - External media address: `45.79.238.67`
  - External signaling address: `45.79.238.67`
  - Local nets: `45.79.238.0/24`, `100.108.0.0/16`
- RTP config (`rtp_additional.conf`):
  - Range: `10000`–`20000`
  - `rtpchecksums=yes`, `strictrtp=yes`
- All PJSIP endpoints have:
  - `force_rport=yes`
  - `rewrite_contact=yes`
  - `rtp_symmetric=yes`
- **Fixed via FreePBX database:** Updated `sip` table:
  ```sql
  UPDATE sip SET data="no" WHERE keyword="direct_media" AND id IN (1001,1002,1003,1004,1005,1006,1007,1009,1010,1011,1100);
  ```
  Then ran `fwconsole reload`.
- **Verified in generated config:** All endpoints in `pjsip.endpoint.conf` now show `direct_media=no`.
- **Verified in running Asterisk:** `asterisk -rx "pjsip show endpoint 1001"` reports `direct_media : false`.

**Anomalies:**
- None remaining.

**Actions:**
- ✅ Fixed `direct_media=yes` → `no` for all user extensions and voicemail via database.

---

## Item 9 — Call Flow End-to-End Validation (Logical Simulation)

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:57

**Evidence:**
- **Inbound call:** Every DID → `incoming` route → `ext-group,2000,1` → Ring Group 2000 rings extensions 1000–1011.
- **Missed call:** Ring Group 2000 timeout (100s) → `postdest=from-did-direct,1100,1` → Voicemail 1100.
- **Outbound call:** Extension dials number → outbound route matches prefix (`+64`, `+1`, `+44`, `+61`) → correct regional trunk (`nz-telnyx`, `us-telnyx`, `uk-telnyx`, `au-telnyx`).
- **Transfer scenario:** Odoo `user_agent_service.js` implements attended transfer via `REFER`; FreePBX PJSIP supports this natively.

**Anomalies:**
- None in the logical path.

**Actions:**
- None

---

## Item 10 — Call Logging / CDR Integrity

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:57

**Evidence:**
- CDR database (`asteriskcdrdb.cdr`) contains **8,453 records** from `2025-05-20` to `2026-04-15`.
- Recent sample (2026-04-15):
  | calldate | src | dst | duration | disposition |
  |---|---|---|---|---|
  | 23:52:24 | +64272409094 | 1100 | 2 | ANSWERED |
  | 22:19:02 | +61411589890 | 2000 | 115 | ANSWERED |
  | 22:19:02 | +61411589890 | 2000 | 4 | NO ANSWER |
  | 22:13:29 | +61411589890 | 2000 | 307 | ANSWERED |
- Inbound calls to 2000 create multiple CDR rows (one per ringing extension), with the answered row showing the full call duration.
- `/var/log/asterisk/cdr-csv/` exists but is empty (CDR is stored in MySQL, which is normal).

**Anomalies:**
- None

**Actions:**
- None

---

## Item 11 — Failover & Edge Case Handling

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:57

**Evidence:**
- If all extensions unavailable: Ring Group 2000 → `postdest=from-did-direct,1100,1` (Voicemail 1100).
- If trunk fails: No secondary trunk is configured per country; failover relies on Telnyx's upstream redundancy.
- No dialplan loops detected in `/etc/asterisk/extensions*.conf`.
- Invalid DID handling: The "Catch All" route (see Item 2) catches unmatched DIDs and sends them to extension 1000.

**Anomalies:**
- No secondary/trunk failover at the Asterisk level (acceptable if Telnyx provides redundant SIP paths).

**Actions:**
- None (unless business requires a secondary SIP provider per region).

---

## Item 12 — Security & Exposure Checks

**Status:** 🔴 Fail  
**Checked at:** 2026-04-16 09:58 (updated 10:00)

**Evidence:**
- Fail2Ban is **active** with 8 jails running.
- Asterisk logs show repeated failed auth attempts from external IPs (`208.3.195.65`, `51.38.52.190`) — they are being rejected:
  - `No matching endpoint found after 6 tries`
  - `Failed to authenticate`
- PJSIP global config (`pjsip.conf`):
  - `endpoint_identifier_order=ip,username,anonymous,header,auth_username`
  - `anonymous` is included but is the 3rd of 5 identifiers; this does not mean anonymous SIP calls are freely accepted.
- No `allowguest` setting found in PJSIP config (PJSIP does not use the legacy `allowguest` parameter).
- **Fail2Ban jail `asterisk-iptables`:**
  - Currently failed: 0
  - Total failed: 0
  - Currently banned: 0
  - Total banned: 0
  - **Log file:** `/var/log/asterisk/fail2ban` — **this file is empty (0 bytes since May 2025)**.
- **Fail2Ban `recidive` jail:**
  - Currently banned: 6 IPs (`2.57.122.189`, `2.57.122.195`, `2.57.122.197`, `23.239.188.12`, `24.199.98.66`, `45.148.10.151`).
  - These are repeat offenders from other jails (SSH/GUI), **not SIP attackers**.

**Anomalies:**
- **Critical:** The `asterisk-iptables` jail is watching `/var/log/asterisk/fail2ban`, which is empty. PJSIP auth failures are logged to `/var/log/asterisk/full`, so **SIP attackers are NOT being banned by the Asterisk jail**.
- External scanners are hitting the PBX continuously and are not being blocked by Asterisk-specific rules.

**Actions:**
- **Fix Fail2Ban log path** for the `asterisk-iptables` jail so it reads `/var/log/asterisk/full` (or ensure `/var/log/asterisk/fail2ban` is being populated by Asterisk logger).
- **Verify the Asterisk logger** writes security/auth failures to the file configured for fail2ban.
- **Reload fail2ban** after correcting the log path and confirm `Currently failed` / `Currently banned` become non-zero.

---

## Item 13 — Multi-Tenant / Multi-Region Logic

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:58

**Evidence:**
- DIDs are grouped logically per region/brand (see Item 2 table).
- Outbound caller ID per region is set on each trunk:
  - NZ: `Gabion1 NZ`
  - UK: `Gabion1 UK`
  - US: `Gabion1 USA`
  - AU: `Gabion1 Australia`
- Separate outbound routes per country ensure correct trunk selection.
- Ring Group 2000 is shared across all regions, which is acceptable if the same team answers all brands.

**Anomalies:**
- **Corten brand outbound caller ID** is not represented on any trunk. All trunk `outcid` values say "Gabion1". If Corten calls need a different outbound CID, the current trunk setup will not support it unless Odoo's `X-Outbound-CallerID` header overrides it completely on the outbound leg.

**Actions:**
- **Confirm whether Corten outbound calls should present a different caller ID** than Gabions. If yes, verify that FreePBX dialplan correctly overrides the trunk CID using the `X-Outbound-CallerID` header for all brands.

---

## Item 14 — Configuration Consistency Check (AI "Lint" Layer)

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:58

**Evidence:**
- **Orphaned extensions:** None. All ring group members exist as devices/endpoints.
- **Unused trunks:** None. All 4 trunks are registered and assigned to outbound routes.
- **Unused inbound routes:** None. All 8 documented DIDs have routes.
- **Duplicate dial patterns:** None. Outbound route patterns are mutually exclusive by country prefix.
- **Misaligned ring groups vs extensions:** None.
- **Naming conventions:** Consistent (`nz-telnyx`, `uk-telnyx`, etc.).

**Anomalies:**
- None

**Actions:**
- None

---

## Item 15 — Full System Simulation Test (Final Gate)

**Status:** 🟡 Partial  
**Checked at:** 2026-04-16 09:58

**Evidence (synthesized from CDR + config):**
1. ✅ **Inbound DID** → hits correct inbound route.
2. ✅ **Ring group/queue** rings correctly (CDR shows multiple NO ANSWER rows for 2000, then ANSWERED).
3. ✅ **User answers successfully** (CDR shows ANSWERED calls with multi-minute durations).
4. ✅ **Call logs correctly** (CDR database populated, accurate durations).
5. 🟡 **Missed call fallback works** logically (config points to Voicemail 1100; CDR shows calls to 1100).
6. 🟡 **Voicemail sends email** — unverified (SMTP config not confirmed).
7. 🟡 **Callback outbound uses correct trunk + caller ID** — Odoo injects `X-Outbound-CallerID` and FreePBX dialplan reads it, but `direct_media=yes` introduces audio risk.
8. 🟡 **Transfer between users works** — supported by SIP.js `REFER`, but not directly observed in logs.

**Anomalies:**
- Fail2Ban `asterisk-iptables` is not banning SIP attackers because it watches an empty log file.

**Actions:**
- Fix Fail2Ban log path for `asterisk-iptables` and reload.

---

## Phase 5 — Odoo Integration Cross-Check

**Status:** 🟢 Pass  
**Checked at:** 2026-04-16 09:58

**Evidence:**
- `voip_caller_identity/static/src/js/sip_header_injection.js` patches `UserAgent.makeCall()` and `UserAgent.invite()` to:
  1. Normalize dialed numbers to E.164 based on selected identity's country.
  2. Build and inject a custom SIP header (default: `X-Outbound-CallerID: <number>`) into the INVITE.
- `voip_caller_identity/static/src/js/caller_identity_service.js` manages identity selection, validation against backend (`validate_identity_for_user`), fallback logic, and call logging.
- `voip_caller_identity/README.md` documents the FreePBX dialplan side:
  - Reads `X-Outbound-CallerID` via `PJSIP_HEADER(read,X-Outbound-CallerID)`.
  - Adds `P-Asserted-Identity` on the outbound trunk leg for Telnyx.
- `voip_caller_identity/models/voip_call_log.py` logs:
  - `resolved_phone_number`, `sip_header_method`, `validation_result`, `normalized`, `normalization_note`.

**Anomalies:**
- None in the Odoo code.

**Actions:**
- None

---

## Summary & Prioritized Action Items

| Priority | Issue | Impact | Recommended Action |
|---|---|---|---|
| **P1** | Fail2Ban `asterisk-iptables` jail watching empty log file | SIP attackers are NOT being banned | Fix log path to `/var/log/asterisk/full` and reload fail2ban |
| **P3** | Corten outbound CID on trunks | Caller ID may always show "Gabion1" | Confirm FreePBX overrides trunk CID using `X-Outbound-CallerID` for Corten |
| **P1** | Fail2Ban `asterisk-iptables` jail watching empty log file | SIP attackers are NOT being banned | Fix log path to `/var/log/asterisk/full` and reload fail2ban |

---

**End of Report** — Generated during AI validation pass on 2026-04-16.
