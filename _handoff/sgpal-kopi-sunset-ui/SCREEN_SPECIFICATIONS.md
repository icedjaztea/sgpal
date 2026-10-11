# SG Pal - screen specifications

All views: exact 320 x 240 canvas; bitmap text 10 x 14 px, 12 px advance. Sample gallery state is isolated from real saved data.

## 01 - Hello, Singapore (phase 1)

- **Layout:** Header 0,0 320x24; logo panel 24,40 272x148; portraits 60x60; action rail y194.
- **Focus order:** Start > Help > Back
- **Press / destination:** Start opens character selection. Returning adopted saves open Home instead.
- **Back:** Back opens device options; it never erases a save.
- **Empty/error and integrity:** Returning save bypasses onboarding. Unreadable server save shows Save error.
- **Animation target:** Optional brief logo reveal, then still. Reduced motion skips reveal.

## 02 - Choose your Pal (phase 1)

- **Layout:** Three 96x116 cards at x8/112/216, y36; 64x64 portraits; description y170.
- **Focus order:** Merlion > Otter > Mynah > Back
- **Press / destination:** Press a species to open a confirmation. Adoption is not saved yet.
- **Back:** Returns to Hello.
- **Empty/error and integrity:** Confirmation offers Choose or Back; selection survives Back.
- **Animation target:** Focused sprite can tilt or blink; no animation required to perceive focus.

## 02confirm - Confirm companion (phase 1)

- **Layout:** 80x80 portrait at120,31; two-button rail.
- **Focus order:** Choose > Back
- **Press / destination:** Choose proceeds to suggested naming.
- **Back:** Returns to species selection.
- **Empty/error and integrity:** No saved-game mutation before naming confirmation.
- **Animation target:** Single happy reaction.

## 03 - A name for your Pal (phase 1)

- **Layout:** Portrait23,38 64x64; name104,61; 2 dialogue lines; 3 actions.
- **Focus order:** Keep > Reroll > Back
- **Press / destination:** Keep commits adoption and opens Home; Reroll cycles three preset names.
- **Back:** Returns to adoption confirmation.
- **Empty/error and integrity:** Save failure preserves previous save and offers Retry/Back. Phone naming belongs to phase3.
- **Animation target:** Name changes immediately; short success reaction after saved response.

## 04 - My BTO (phase 1)

- **Layout:** Header24px; room0,24 320x168; 56x56 sprite container147,112; actions y194.
- **Focus order:** Pal > Scan > Menu
- **Press / destination:** Pal opens interaction; Scan opens scanner; Menu opens scrolling menu.
- **Back:** Root screen; Settings remains available via Menu.
- **Empty/error and integrity:** Local save status appears in Settings. Offline play keeps local profile; no pending reward grants.
- **Animation target:** Target 4-frame idle at4fps, gentle fan 2-frame loop. Prototype remains still.

## 04menu - Pocket menu (phase 1)

- **Layout:** Four296x30 rows at y36/72/108/144. Footer y224.
- **Focus order:** CultureDex > Quests > Shop > Inventory > Decorate > Profile > Rooms > Friends > Settings > Back
- **Press / destination:** Press opens the focused destination; rotation scrolls four visible rows.
- **Back:** Explicit Back is the final row.
- **Empty/error and integrity:** Phase2-4 screens show empty/unconnected states in live mode.
- **Animation target:** No sliding transition; immediate page change avoids expensive redraw effects.

## 04pal - A moment with your Pal (phase 1)

- **Layout:** Dialogue12,131 296x57 over room; two-button rail.
- **Focus order:** Explore > Back
- **Press / destination:** Explore opens scanner.
- **Back:** Home.
- **Empty/error and integrity:** No hunger, decay or daily-care penalty.
- **Animation target:** A brief greeting reaction; no currency for repeat interactions.

## 05 - Camera scanner (phase 1)

- **Layout:** Preview16,36 288x145; rail194. Photo pixels are not filtered as pixel art.
- **Focus order:** Camera > Upload > Back
- **Press / destination:** Camera requests browser camera only after press; Upload opens system photo picker.
- **Back:** Home. Stops active camera tracks.
- **Empty/error and integrity:** No assumption of Pi camera. Permission or insecure-context error offers Upload/Retry/Back.
- **Animation target:** No camera frames until permission granted. Actual preview capped near10fps.

## 05ai - AI not connected (phase 1)

- **Layout:** Status portrait; three14px lines; Back.
- **Focus order:** Back
- **Press / destination:** Returns to photo review.
- **Back:** Review photo.
- **Empty/error and integrity:** Backend /api/scan and /api/verify return501. No credentials or API calls included.
- **Animation target:** Static integration-needed state.

## 05error - Camera unavailable (phase 1)

- **Layout:** Icon and three lines; three actions.
- **Focus order:** Upload > Retry > Back
- **Press / destination:** Upload uses picker; Retry requests permission again if browser allows.
- **Back:** Scanner.
- **Empty/error and integrity:** Distinct permission denial/insecure context/device absence message.
- **Animation target:** No indefinite loading spinner.

## 05live - Camera ready (phase 1)

- **Layout:** Image16,32 288x152; fit/letterbox with normal photo interpolation.
- **Focus order:** Capture > Back
- **Press / destination:** Capture freezes the real frame for review; no AI request is made in this prototype.
- **Back:** Scanner and release camera.
- **Empty/error and integrity:** Gallery is explicitly a camera placeholder, not a fake photograph.
- **Animation target:** Live preview10fps; stop tracks on exit and page hide.

## 05photo - Review your photo (phase 1)

- **Layout:** Fit photograph in20,34 280x128; three-action rail.
- **Focus order:** Analyse > Retry > Back
- **Press / destination:** Analyse currently shows integration-needed state. It never saves a discovery.
- **Back:** Scanner. Captured photo remains memory-only until replaced or page closes.
- **Empty/error and integrity:** Oversized/unsupported files rejected before decode. No upload to external services.
- **Animation target:** Still photograph, no artificial pixel filter.

## 05starting - Camera permission (phase 1)

- **Layout:** 76x76 portrait; centered status; one action.
- **Focus order:** Cancel
- **Press / destination:** Cancels pending request in app; late media streams are immediately stopped.
- **Back:** Cancel returns to scanner.
- **Empty/error and integrity:** Browser permission dialog owns approval. No success while permission unresolved.
- **Animation target:** Optional two-frame thinking loop.

## 06 - Discovery saved (phase 1)

- **Layout:** Item64x40, title; reward strip12,108 296x38; quest alert y161.
- **Focus order:** Dex > Quest > Home
- **Press / destination:** Dex opens saved detail; Quest opens board. This is a sample success state only.
- **Back:** Home.
- **Empty/error and integrity:** Show only after atomic save+reward commit in future backend. Duplicate uses06duplicate.
- **Animation target:** Target brief sparkle and one coin tick; reduced motion uses static reward strip.

## 06check - Check the AI suggestion (phase 1)

- **Layout:** 64x40 item illustration24,42; title110,40; 3 lines at121.
- **Focus order:** Yes > No > Back
- **Press / destination:** In future integrated flow, Yes confirms a vetted ID; No retakes/corrects without reward. Gallery only here.
- **Back:** Scanner/review.
- **Empty/error and integrity:** Uncertain/no cultural match must not auto-save. Correction UI offers retry; no free-text requirement.
- **Animation target:** Small thinking reaction before decision, not a reward animation.

## 06duplicate - Already discovered (phase 1)

- **Layout:** Item art and three lines.
- **Focus order:** Dex > Quest > Home
- **Press / destination:** Open existing entry or quest; no reward transaction.
- **Back:** Home.
- **Empty/error and integrity:** Duplicate recognition must not create another reward event or overwrite original photo silently.
- **Animation target:** Gentle acknowledgement, no celebration.

## 06wrong - Try a clearer view (phase 1)

- **Layout:** Three short lines and two actions.
- **Focus order:** Retry > Back
- **Press / destination:** Retry opens scanner without granting anything.
- **Back:** AI suggestion.
- **Empty/error and integrity:** Future alternative candidates may replace retry when available.
- **Animation target:** Calm reaction; no punitive failure animation.

## 07 - CultureDex (phase 1)

- **Layout:** Four rows296x30 at36/72/108/144; 2 action buttons.
- **Focus order:** Visible entries in numeric order > Next > Back
- **Press / destination:** Open entry; Next shows next catalogue page. Empty live state offers Scan.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Unknowns remain numbered with???; empty Dex uses invitation, not an empty grid.
- **Animation target:** Immediate focus move; no list bounce.

## 07next - CultureDex next page (phase 1)

- **Layout:** One row plus Prev/Back.
- **Focus order:** #005 > Prev > Back
- **Press / destination:** Unknown entry opens locked page.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Pages never contain fake unlocked entries.
- **Animation target:** None.

## 08 - CultureDex story (phase 1)

- **Layout:** Title24px; illustration64x40; 3 lines; two actions.
- **Focus order:** Next > Back
- **Press / destination:** Next opens Photo, then Quest metadata, then Story.
- **Back:** Catalogue with previous focus restored in future implementation.
- **Empty/error and integrity:** Explanation is curated example text. Actual approved recognition supplies entry ID.
- **Animation target:** Static reading page.

## 08locked - Unknown CultureDex entry (phase 1)

- **Layout:** Lock icon and three lines.
- **Focus order:** Scan > Back
- **Press / destination:** Scan opens camera selector.
- **Back:** Catalogue.
- **Empty/error and integrity:** Do not reveal private or undiscovered details.
- **Animation target:** Optional subtle question-mark idle.

## 08photo - CultureDex photograph (phase 1)

- **Layout:** Photo20,34 280x108; timestamp16,161; two actions.
- **Focus order:** Next > Back
- **Press / destination:** Next opens quest metadata.
- **Back:** Catalogue.
- **Empty/error and integrity:** Placeholder is explicitly not an actual scan. Real photo must display the captured timestamp in Asia/Singapore.
- **Animation target:** No pixel filter applied to photos.

## 08quest - CultureDex quest (phase 1)

- **Layout:** Four metadata lines at47/69/91/113; 3 actions.
- **Focus order:** Story > Quest > Back
- **Press / destination:** Open story or associated quest detail.
- **Back:** Catalogue.
- **Empty/error and integrity:** XP shown belongs to discovery event; quest reward remains unclaimed.
- **Animation target:** None.

## 09 - Quest board (phase 1)

- **Layout:** Three296x30 rows at36/78/120; Back below.
- **Focus order:** Active quest > Completed > Locked > Back; empty: Scan > Back
- **Press / destination:** Open quest detail or selected status list.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Empty real save has no invented quest. Completed entry is non-claimable.
- **Animation target:** New quest can receive a brief marker, not constant flashing.

## 09done - Completed quest (phase 1)

- **Layout:** Four lines with claim status.
- **Focus order:** Back
- **Press / destination:** No claim action for completed quest.
- **Back:** Quest board.
- **Empty/error and integrity:** Sample only; no additional reward on revisit.
- **Animation target:** No repeated celebration.

## 09locked - Locked quest (phase 1)

- **Layout:** Lock and three lines.
- **Focus order:** Back
- **Press / destination:** Read prerequisite.
- **Back:** Quest board.
- **Empty/error and integrity:** Prerequisite explicit; no selectable Verify.
- **Animation target:** None.

## 10 - Quest verification (phase 1)

- **Layout:** Three instructions; reward strip12,118 296x37; requirement y168.
- **Focus order:** Verify > Back
- **Press / destination:** Integrated version captures fresh evidence for this quest ID. Gallery opens checking sample.
- **Back:** Quest board.
- **Empty/error and integrity:** No success without verifier pass. In runnable prototype no live active quests exist.
- **Animation target:** Thinking loop only while an actual request is pending.

## 10fail - Evidence needs another try (phase 1)

- **Layout:** Four short actionable lines.
- **Focus order:** Retry > Back
- **Press / destination:** Retry requests fresh evidence; Back retains quest.
- **Back:** Quest detail.
- **Empty/error and integrity:** Needs-more-evidence differs from system error. No blame or punishment.
- **Animation target:** Quiet curious reaction, no red flashing.

## 10pass - Quest verified (phase 1)

- **Layout:** Portrait; title; reward strip; two actions.
- **Focus order:** Done > Home
- **Press / destination:** Show completed record. Sample UI only; never reachable from a real unverified request.
- **Back:** Home.
- **Empty/error and integrity:** Render only after verified and committed, not from client timer or capture event.
- **Animation target:** One6-frame celebration; reduced motion still reward strip.

## 10wait - Evidence being checked (phase 1)

- **Layout:** 80x80 sprite and 3 lines.
- **Focus order:** Cancel
- **Press / destination:** Cancels request view; late response must be reconciled by backend operation ID.
- **Back:** Quest detail.
- **Empty/error and integrity:** Static sample does not auto-transition to success. Request timeout offers Retry/Back.
- **Animation target:** Target four-frame thinking loop; timer cannot imply a pass.

## 11 - Kopi shop (phase 2)

- **Layout:** Item art40x60; label/price right; affordability line141.
- **Focus order:** Buy > Next > Back
- **Press / destination:** Buy opens confirmation only if affordable; actual purchase is not enabled in prototype.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Insufficient coins and unavailable stock have separate states. Categories can reuse paged lists.
- **Animation target:** Focused item can rise1px; never jiggle disabled actions.

## 11confirm - Confirm purchase (phase 2)

- **Layout:** Item; price/balance/quantity; two actions.
- **Focus order:** Confirm > Back
- **Press / destination:** Prototype reports not connected; future backend atomically debits25 and adds item.
- **Back:** Shop, no purchase.
- **Empty/error and integrity:** Recheck balance/owned state on server; reject duplicate transaction IDs.
- **Animation target:** Purchase reaction only after committed response.

## 11poor - Insufficient coins (phase 2)

- **Layout:** Four lines plus two actions.
- **Focus order:** Explore > Back
- **Press / destination:** Explore opens scanner; no negative balance.
- **Back:** Shop.
- **Empty/error and integrity:** Price and gap visible before confirmation.
- **Animation target:** None.

## 11unavailable - Shop item unavailable (phase 2)

- **Layout:** Lock and three lines.
- **Focus order:** Prev > Back
- **Press / destination:** Browse available item or leave.
- **Back:** Pocket menu.
- **Empty/error and integrity:** No active Buy control when unavailable.
- **Animation target:** None.

## 12 - Inventory (phase 2)

- **Layout:** Three category rows, then Back.
- **Focus order:** Furniture > Accessories > Special > Back; empty: Shop > Back
- **Press / destination:** Owned furniture opens placement. Empty categories give informative state.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Show Owned/Placed/Equipped distinctions in future item list; no duplication.
- **Animation target:** None.

## 13 - Decorate by slots (phase 2)

- **Layout:** Room;62x64 highlight at238,86;slot label12,151 214x36.
- **Focus order:** Place > Next > Back
- **Press / destination:** Next cycles compatible fixed slots; Place opens confirmation, never drag-and-drop.
- **Back:** Inventory.
- **Empty/error and integrity:** Sample window plant only; live save has no item and cannot commit placement.
- **Animation target:** Solid slot outline; target brief before/after swap after save.

## 13confirm - Confirm placement (phase 2)

- **Layout:** Confirmation overlay16,120 288x68.
- **Focus order:** Save > Back
- **Press / destination:** Prototype shows integration needed. Future save validates ownership and slot.
- **Back:** Placement.
- **Empty/error and integrity:** Save failure must preserve original room and retryable edit.
- **Animation target:** Swap preview only; commit animation follows successful save.

## 13slot - Alternate furniture slot (phase 2)

- **Layout:** 48x64 highlight14,78; label below.
- **Focus order:** Place > Next > Back
- **Press / destination:** Select next compatible placement slot.
- **Back:** Inventory.
- **Empty/error and integrity:** Production save references stable slot IDs, not browser coordinates.
- **Animation target:** None.

## 14 - Pal profile (phase 1)

- **Layout:** 70x70 portrait, labels;288x12 XP bar; 2 metadata lines.
- **Focus order:** More > Back
- **Press / destination:** More shows accessories/personality/achievements.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Live level1/0XP; example level3 uses140/200. XP never spent.
- **Animation target:** Idle portrait; progress animates only on actual earned XP.

## 14more - Profile details (phase 2)

- **Layout:** Four14px lines.
- **Focus order:** Back
- **Press / destination:** Read profile details.
- **Back:** Profile.
- **Empty/error and integrity:** Personality copy will vary by species. No invented unlocked achievements.
- **Animation target:** None.

## 15 - Room expansion (phase 2)

- **Layout:** Three room rows; short level requirement in each.
- **Focus order:** Living room > Bedroom > Kitchen > Back
- **Press / destination:** Enter unlocked room; locked room explains milestone.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Thresholds5/8 are proposed balancing, not committed economy. Study/balcony future pages.
- **Animation target:** Room transition as brief fade optional; reduced motion immediate.

## 15locked - Room milestone (phase 2)

- **Layout:** Lock and three lines.
- **Focus order:** Back
- **Press / destination:** Return to room list.
- **Back:** Rooms.
- **Empty/error and integrity:** Use actual selected room requirement in production.
- **Animation target:** None.

## 16 - Friends (phase 4)

- **Layout:** Three list rows or explicit unconnected state.
- **Focus order:** Friend > Requests > Add > Back; live: Back
- **Press / destination:** Gallery previews asynchronous social UI. Live has no social calls.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Future friend rooms are private by default; authorised friends only.
- **Animation target:** Small status marker; no live-presence assumption.

## 16pair - Add friend by phone (phase 4)

- **Layout:** 88x88 QR region plus2 lines. Real QR may need larger region after device tests.
- **Focus order:** Back
- **Press / destination:** Production replaces labelled placeholder with actual short-lived server QR.
- **Back:** Friends.
- **Empty/error and integrity:** Never display decorative QR as usable code; no unauthorised room URL.
- **Animation target:** Pairing expiry shows Refresh, no polling when not paired.

## 16request - Friend request (phase 4)

- **Layout:** Portrait and single identity line.
- **Focus order:** Accept > Decline > Back
- **Press / destination:** Future server-backed consent action; prototype does not change social state.
- **Back:** Friends.
- **Empty/error and integrity:** Show verified account identity in production, not only pet name.
- **Animation target:** No reward for accepting.

## 17 - Visit a friend (phase 4)

- **Layout:** Friend room snapshot; greeting overlay12,153 296x34.
- **Focus order:** Greet > Leave
- **Press / destination:** Greet opens preset guestbook choices; no room editing.
- **Back:** Leave returns to Friends.
- **Empty/error and integrity:** Sample house only. Real snapshot requires permission and excludes CultureDex scan photos.
- **Animation target:** Friend sprite can idle locally; does not imply real-time presence.

## 17greet - Leave a greeting (phase 4)

- **Layout:** Three296x30 rows and Back.
- **Focus order:** Three preset greetings > Back
- **Press / destination:** Future sends selected sticker/message once with confirmation. No unrestricted chat.
- **Back:** Friend visit.
- **Empty/error and integrity:** Sending must show pending, sent or failed. Prototype sends nothing.
- **Animation target:** One sticker pop only after successful send.

## 18 - Settings and save (phase 1)

- **Layout:** Four296x30 rows; Back rail.
- **Focus order:** Save/status > Sound > Pairing/privacy > Help > Back
- **Press / destination:** Sound saves local preference. Other rows open details.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Browser cannot reliably read Wi-Fi SSID. OS-managed network info shown explicitly.
- **Animation target:** Optional click sound only when enabled.

## 18lost - Connection lost (phase 3)

- **Layout:** Three lines.
- **Focus order:** Retry > Back
- **Press / destination:** Future checks request operation ID before repeating any mutation.
- **Back:** Settings.
- **Empty/error and integrity:** Ambiguous completion must not be retried as a fresh reward grant.
- **Animation target:** Stop analysing animation when network is lost.

## 18offline - Offline (phase 3)

- **Layout:** Four lines.
- **Focus order:** Home > Back
- **Press / destination:** Continue local experience.
- **Back:** Settings.
- **Empty/error and integrity:** Future offline actions need durable operation IDs; no reward before validation.
- **Animation target:** Static offline icon, no error flashing.

## 18pair - Pairing and privacy (phase 3)

- **Layout:** Four policy/status lines.
- **Focus order:** Back
- **Press / destination:** Informational until authenticated cloud service exists.
- **Back:** Settings.
- **Empty/error and integrity:** Prototype photos remain memory only; no third-party upload. LAN access is not authenticated cloud pairing.
- **Animation target:** None.

## 18pending - Sync pending (phase 3)

- **Layout:** Four status lines.
- **Focus order:** Retry > Back
- **Press / destination:** Future retries operation queue; not implemented in this prototype.
- **Back:** Settings.
- **Empty/error and integrity:** Do not upload capture photos by default. Server deduplicates operation/reward IDs.
- **Animation target:** Brief spinner only during real retry.

## 18status - Save and connection (phase 1)

- **Layout:** Four status lines.
- **Focus order:** Back
- **Press / destination:** Read actual save adapter and browser network signal.
- **Back:** Settings.
- **Empty/error and integrity:** Browser online is not proof AI/cloud reachable. Remote unavailable never reported synced.
- **Animation target:** No perpetual sync indicator.

## blocked - Feature not connected (phase 2)

- **Layout:** Three lines, two actions.
- **Focus order:** Home > Back
- **Press / destination:** Return safely without mutating sample or live state.
- **Back:** Pocket menu.
- **Empty/error and integrity:** Used for deferred commerce, decoration and social mutations.
- **Animation target:** None.

## bootback - Device options (phase 1)

- **Layout:** Two lines and two actions.
- **Focus order:** Start > Back
- **Press / destination:** Start continues onboarding.
- **Back:** Hello.
- **Empty/error and integrity:** No browser-exit or OS-shutdown action is simulated.
- **Animation target:** None.

## help - Rotary help (phase 1)

- **Layout:** Four short14px instructions.
- **Focus order:** Back
- **Press / destination:** Return to Settings or Hello.
- **Back:** Context return.
- **Empty/error and integrity:** Keyboard and touch preserve the same ordered focus model.
- **Animation target:** Optional illustrated pointer move, not required to understand controls.

## saveerror - Save could not finish (phase 1)

- **Layout:** Four lines and two actions.
- **Focus order:** Retry > Back
- **Press / destination:** Returns to original profile/save action; never clears corrupt file automatically.
- **Back:** Home or Hello according to adoption state.
- **Empty/error and integrity:** Corrupt server save results503. User must restore backup externally.
- **Animation target:** None.
