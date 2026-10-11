# One repository, multiple runtimes

## Recommendation

Keep one shared GitHub repository. The Pi and public browser deployments are delivery targets of the same game, not independent products. Share UI components, culture IDs, schemas, economy rules and save migrations. Keep environment-specific input and camera code behind adapters.

| Part | Responsibility | Runs where |
| --- | --- | --- |
| Shared web frontend | 320x240 game UI, responsive framing, menus, collection views | Pi Chromium, laptop, phone |
| Shared domain rules | Culture IDs, quests, inventory schemas, progression definitions | Backend authoritative; client read-only display helpers |
| FastAPI service | Authenticated game operations, recognition gateway, validated rewards and data access | Local Pi prototype; cloud for multi-user game |
| Pi adapter | GPIO rotary events, CSI camera capture, device status | Pi only |
| Save adapter | Local prototype state; later cloud state plus durable pending operations | Pi/browser as appropriate |
| Deployment config | Pi service/kiosk launch; cloud HTTPS service | Separate config within same repo |

Suggested future folders, after inspecting the actual repo: `web/`, `api/`, `device/pi/`, `shared/`, `docs/`, `deploy/`. Do not force a restructure if the repo already has clear equivalents. This package uses a smaller self-contained layout for preview and transport.

## Accounts and friends: low-friction UI, real access control

1. Guest play is available immediately with a local save.
2. When enabling cross-device saves or friends, offer one managed passwordless method on phone/laptop, such as an email magic link. Google sign-in is an optional alternative, not a mandatory second system.
3. The Pi shows a short-lived pairing QR/code. The player signs in on their phone and explicitly approves that device. The Pi receives a revocable device credential. A displayed friend code never doubles as this credential.
4. A friend code or QR resolves a public player identifier. Send request, accept request, then permit room visits.
5. Server authorisation checks the accepted relationship on every room fetch and guestbook write. Revoking a friend removes future access. Guestbook starts with fixed stickers/messages.
6. A house visit is an asynchronous room snapshot with the Pal and allowed decorations, not real-time multiplayer. Personal scan photographs are private and excluded from this snapshot.

Use an existing auth provider's sessions and recovery. Do not build a homemade password database for the makeathon. Keep pairing tokens short-lived, single-use and separate from public friend identifiers. Rate-limit code lookup and pairing attempts. Exact auth vendor and deployment should be chosen after inspecting the repo and its existing services.

Guest-to-account linking must explicitly select/import the intended local save; never silently overwrite a cloud save with another device's state. Friendship requires a stable authenticated identity even if the visible experience is very simple.

## Server-owned game transactions

- Recognition returns a candidate culture ID plus confidence/context; the user can confirm or retry. Validate against the curated culture catalogue.
- Confirmed first discovery creates a record and grants XP/coins in one idempotent transaction. Duplicate `(player_id, culture_id)` earns no repeated reward.
- Quest evidence attaches to a quest attempt ID. Pass/fail comes from actual verification, not capture or a UI timer.
- A verified completion grants the quest reward once. A lost response is reconciled using the operation ID before retrying.
- Purchases atomically validate balance, debit coins and add the inventory item. XP is never a spending currency.
- Furniture placement validates item ownership and compatible slot ID; client coordinates are not authoritative.
- Offline changes have durable operation IDs. Reconnect sync must deduplicate and report conflicts. Do not merge coin/XP balances by blindly adding device totals.

The current prototype does none of these reward transactions: it deliberately provides no reward-writing endpoint.

## Deployment reality

Local development: one FastAPI process serves the shared UI and a device save. A phone opening that server shares that same save; it does not gain its own account.

Production browser: HTTPS, authenticated API, per-user database, private media storage. Provider API secrets stay on the backend. The user's existing Common Ground API credential can be connected during the real recognition integration; no secret belongs in frontend JavaScript or Git.

Pi: local UI/input/camera adapter with a device session to the same cloud API. Cache approved content/assets and local state for offline viewing. Hardware functionality needs testing against the actual display driver, camera interface, encoder pins and OS image.

## Scope by phase

Phase1: real scanner, confirmation, CultureDex, quests, verified rewards, one room and local save. This handoff supplies the UI structure, not the completed AI integration.

Phase2: transactional shop, inventory, slot decoration, accessories and room expansion.

Phase3: managed auth, phone pairing, cloud saves, offline reconciliation.

Phase4: consent-based friend requests, authorised snapshots and preset guestbook interactions.
