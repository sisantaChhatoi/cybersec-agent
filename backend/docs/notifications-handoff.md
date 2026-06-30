# Push Notifications — status & handoff

Cross-cutting feature (app + backend). This doc is the source of truth for **what
is built** and **what is left** so the flow reaches a real phone.

## TL;DR

The **code path is complete** on both sides: the app registers an Expo push token
and sends it to the backend; the backend stores it and can push via the Expo Push
API; a `POST /test/notify` button exercises the whole loop. **What is missing is
infrastructure, not code** — the Expo → FCM credential chain and an EAS build are
not set up, so a real device never gets a token and nothing is delivered. That is
why it didn't work last time. **Start at [What's left](#whats-left).**

## The flow

```
App (dev build) ──get Expo push token──► POST /auth/push-token ──► stored on user.push_token
                                                                          │
                              (test button) POST /test/notify ───────────┤
                                                                          ▼
                          NotificationService.send_push ──► Expo Push API ──► FCM ──► phone
```

Expo is a relay; Android delivery goes through **FCM (Firebase)** underneath. No
FCM credentials wired into Expo → tokens may mint but deliveries silently fail.

> ### ⚠️ Expo Go cannot receive push — at all (read this first)
> **Why:** Expo Go is a *fixed, prebuilt* app from the Play Store, and the native
> remote-push module was **removed from it in SDK 53**. The receiving code simply
> isn't in the Expo Go binary anymore — so **no setup, FCM credential, or
> `projectId` makes push work in Expo Go.** This is almost certainly the silent
> "not supported" error seen last time.
>
> - **Remote push works only in a dev/prod build** (`eas build`) on a real Android
>   device or a **Play-Services-enabled** emulator — never Expo Go.
> - In Expo Go, `registerForPushToken()` **intentionally returns `null`** (guarded),
>   so it no-ops quietly instead of erroring.
> - Use **Expo Go** for everything else — UI, auth, and **local** notifications
>   (those *do* work) to build the alert screen. Use a **build** to test real push.

## What's built (done)

### Backend (`backend/server/`)
- `models/user.py` — `UserInDB.push_token: str | None`; `PushTokenRequest`.
- `repositories/user_repo.py` — `set_push_token(user_id, push_token)`.
- `routers/auth.py` — `POST /auth/push-token` (stores token for the JWT user).
- `services/notification_service.py` — `NotificationService.send_push(token, title,
  body, data)`; POSTs to the Expo Push API, raises `PushError` on a non-200 or an
  error **ticket**.
- `routers/test.py` — `POST /test/notify`; pushes a sample alert to the current
  user's stored token, `400` if none registered.
- `deps.py` / `app.py` — `get_notification_service` + test router are **wired**.
- `shared/config.py` — `expo_push_url`, `test_notification_phone`.

### App (`app/`)
- `lib/notifications.ts` — `registerForPushToken()`: permissions, Android channel,
  `getExpoPushTokenAsync({ projectId })`. Guarded to **return `null` in Expo Go**
  (see the callout above) so it only mints a token in a dev/prod build.
- `lib/api.ts` — `registerPushToken()`, `testNotify()`.
- `app/(tabs)/_layout.tsx` — registers the token on mount and POSTs it.
- `app/(tabs)/index.tsx` — "Send test notification" button → `/test/notify`.
- `app.json` / `package.json` — `expo-notifications`, `expo-device` added.

## What's left

### 1. Expo → FCM credentials + EAS build  ← the actual blocker
Expo can't deliver to Android without FCM credentials, and remote push needs a real
build (not Expo Go — see the callout above). Set up both:

1. **Firebase project** → add an **Android app** using the app's `android.package`
   (set this in `app.json`; it must match Firebase). Download `google-services.json`.
2. Reference it: `app.json` → `android.googleServicesFile: "./google-services.json"`.
3. **FCM V1 key:** Firebase Console → Project Settings → Service accounts →
   *Generate new private key* → download the service-account JSON.
4. **Upload it to Expo** so Expo can send to FCM on our behalf:
   `eas credentials` → Android → Push Notifications → FCM V1 → upload the key
   (or via the Expo dashboard → Credentials).
5. **Link the EAS project:** `eas init` — writes `extra.eas.projectId` into
   `app.json`. `getExpoPushTokenAsync` needs that `projectId`; without it the token
   call returns `null` and the backend never gets a token (→ `/test/notify` 400s).
6. **Build a real client:** `eas build:configure` (creates `eas.json`), then
   `eas build -p android --profile preview` (or a `development` dev client). Install
   the APK on a real device — **not Expo Go**.

After this, the existing test button delivers a real banner. **No app/backend code
change is required for the test loop — only this setup.**

### 2. Production send path (detector → push)  ← real feature, not yet built
Today only `/test/notify` exists (user pushes to themselves). The real alert — when
the call agent flags a scam mid-call — is **not wired**. Build the bridge:
- An intake the worker can call (e.g. `POST /alerts`) that loads the target user,
  reads `push_token`, and calls `NotificationService.send_push` with the real
  payload (`{scam, confidence, reason, red_flags, caller}` — shape in
  `app/CLAUDE.md`). Keep DB access in the repo and the send in the service (layering).
- App side: handle a received notification → route to / render the Alert screen.

### 3. Hardening (nice to have)
- **Stale tokens:** Expo returns a `DeviceNotRegistered` ticket when a token dies.
  Clear it (`set_push_token(user_id, None)` — make the column nullable in the setter)
  so we stop pushing to dead devices.
- **Receipts:** `send_push` only checks the immediate *ticket*. Expo confirms real
  delivery asynchronously via *receipts* (poll after a few seconds); add this only
  if delivery debugging needs it.
- **iOS** is out of scope (Android-only, per `app/CLAUDE.md`); APNs needs the paid
  Apple account.

## Running the backend (for testing)
- `cd backend && docker compose up` brings up server + worker + mongo + neo4j.
  Running the backend is fully containerized — no manual setup.
- Push **sends** are outbound HTTPS to Expo, so a local/Docker backend delivers
  real pushes fine — no public URL needed for delivery itself.
- **The phone must reach the backend's HTTP API** (`/auth/push-token`,
  `/test/notify`) — a device can't hit `localhost`. Pick one:
  - **Same Wi-Fi + LAN IP:** put the phone and the laptop on the same network and
    set `EXPO_PUBLIC_API_URL` to the **laptop's LAN IP** (e.g.
    `http://<your-ip>:8000`). The IP hardcoded in `app/constants/config.ts` is
    someone else's machine — **yours will differ, so you must change it**
    (`ip addr` / `ifconfig` to find it).
  - **ngrok:** `ngrok http 8000` and set `EXPO_PUBLIC_API_URL` to the ngrok URL —
    works across networks, no same-Wi-Fi requirement.
- **Set `EXPO_PUBLIC_API_URL` at build time for the APK.** `EXPO_PUBLIC_*` vars are
  **inlined when the app is built**, not read at runtime — so pass it in the build
  profile's `env` in `eas.json` (or via EAS env vars), pointing at the LAN-IP/ngrok
  URL the phone can reach. If you skip it, the APK bakes in the hardcoded default
  and you must rebuild to change it.
- A "broken notification" is usually really this: the app can't reach the API.

## How to test (once #1 is done)
1. `eas build` a preview/dev APK; install on a real Android phone.
2. Log in → the app registers a token (`/auth/push-token`); confirm `user.push_token`
   is set in Mongo.
3. Tap **Send test notification** → expect a banner. A `400 "no push token"` means
   step 5/6 above isn't complete (no token minted); a `502 push failed` means the
   FCM credentials (steps 1–4) are wrong.
