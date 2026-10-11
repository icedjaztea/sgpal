# Validation and remaining checks

## Completed in this environment

- 57 screen/state renders in Chromium without JavaScript page errors.
- All text glyph bounds stay inside the320x240 canvas.
- Exported native images are320x240; nearest-neighbour3x exports are960x720.
- Rotary-only onboarding selected Otter, rerolled to Pebble, and saved successfully.
- Reload reopened the adopted Pal's Home and retained species/name.
- Gallery samples, including discovery/quest success and shop/friend previews, did not mutate the actual save.
- Photo-file selection opened review; Analyse opened the explicit disconnected state and kept XP/coins at0.
- Desktop and390px mobile viewport screenshots inspected; kiosk canvas measured320x240 CSS pixels.
- Four backend tests passed: persistent adoption and409 on re-adoption; invalid input rejection; no rewards from unconnected AI endpoints; corrupt-save preservation.
- PDF page geometry and native PNG dimensions checked, representative PDF pages rendered and visually inspected.

## Not yet tested or implemented

- Actual Raspberry Pi3B+ runtime, screen driver/rotation/scaling, GPIO detents and click debounce.
- Actual iPhone Safari and its camera permissions/photo formats; mobile viewport emulation is not device validation.
- Live browser camera hardware was not available here; photo-file selection was tested.
- Real AI recognition, verification and transactional rewards; no live provider request was made.
- Shop, furniture save, room unlock rules, accounts, QR pairing, cloud sync and social services.
- Production sprite animation and pixel cleanup. The generated art retains some high-resolution detail.

Python packages tested: FastAPI0.143.0, Uvicorn0.54.0, httpx0.28.1 and pytest9.1.1 on Python3.12. One upstream Starlette TestClient deprecation warning was emitted; all tests passed.
