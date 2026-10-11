# Continue SG Pal in the shared repository

Inspect this repository and its AGENTS.md, README, current FastAPI backend, frontend, culture catalogue and persistence before editing. Use a feature branch and preserve my teammate's work.

We approved the **Kopi Sunset** design: a cosy Singapore BTO, parchment/navy/teak/terracotta/jade palette, original Merlion/Otter/Mynah Pals, exact320x240 handheld-first Canvas or HTML/CSS UI. The Pi3B+ has a2.8-inch320x240 landscape display and one rotary encoder with click. Rotation changes focus; click activates; each non-root screen must expose Back. Laptop and phone browsers use the same game logic and visual assets, with keyboard/touch adapters.

Use ONE repo with shared frontend and backend, plus a Pi-only input/camera adapter. Separate deployment configuration does not need separate repositories. Keep the existing HTML/CSS/JS and FastAPI architecture unless inspection shows otherwise.

The attached prototype is a design and interaction reference, not a drop-in replacement for the entire repo. It contains runnable onboarding, local adoption persistence, camera preview/upload, native-size UI layouts, sample screen gallery and explicit disconnected states. Its generated images are concept assets; preserve their identity but clean them for production pixels. It has no implemented AI recognition, verified reward economy, real shop, cloud auth/sync or social service. Do not mistake gallery sample data for working features.

First integrate one complete real flow: first boot > choose Pal > name > home > camera capture > real recognition candidate > user confirmation > atomic first-discovery save and reward > CultureDex detail > relevant quest > actual evidence verification > exactly-once completion reward. Never grant coins or XP on camera capture, AI timeout, a timer, uncertain candidate or duplicate scan. Keep photographs normal inside pixel-art frames and display timestamps in Asia/Singapore.

Keep guest play possible. When we later add sync/friends, use simple managed passwordless sign-in on phone/laptop, and short-lived approved QR/code pairing for the Pi. Friend codes are public identifiers, not credentials. Accepted requests grant access to private room snapshots; CultureDex photos must not be included in visits. Use preset guestbook messages, not unrestricted chat. Accounts/sync are phase3, social is phase4.

I have an existing OpenAI API key named Common Ground; do not create a new key or put any secret in the browser/repo. Check safe credential presence and agree the real backend setup with me when implementing live AI.

Before claiming completion, run the repo's existing checks and test navigation with only turn/press, persisted reload, scan failure/duplicate cases, exactly-once verified rewards and mobile layout. Verify the actual Pi display/camera/encoder and actual iPhone Safari separately; desktop viewport emulation does not prove those work.

Report what works, what is simulated, what was tested and what still needs hardware or deployment setup. Do not deploy publicly or send social messages merely as a test.
