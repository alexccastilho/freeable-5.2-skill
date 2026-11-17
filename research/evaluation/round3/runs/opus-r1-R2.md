# Plan: crash rate 0.5% → 3% after v4.2

A sixfold jump right after a release almost always comes from a small number of specific new crashes, not a general decline. So the plan is: limit the damage first, let Sentry tell us which crashes are new, fix those, and ship a hotfix through both stores with a staged rollout.

## Questions I would ask

1. **Is the 3% crash-free sessions, or crash-free users? Which tool reports it (Sentry, Play Console, or Xcode Organizer)? Is it both platforms or mostly one?**
   *Default: Sentry crash-free sessions, on both platforms. Step 1 below checks the split anyway.*
2. **Is 4.2 a native release (new binary, RN upgrade, native modules), or have you also pushed JS-only updates since (CodePush / EAS Update)?**
   *Default: a binary release, possibly with a React Native or dependency upgrade, and no OTA updates since.*
3. **Are source maps and dSYMs / ProGuard (R8) mapping files uploaded to Sentry for 4.2?**
   *Default: unknown. I'd verify this first, because without them the stack traces are unreadable.*
4. **Do you have feature flags or remote config, and is OTA updating available?**
   *Default: some remote config exists, but no OTA.*
5. **What changed in 4.2?** I'd want the changelog, the diff `v4.1..v4.2`, and dependency changes (`package.json`, `Podfile.lock`, `build.gradle`).
   *Default: I can read the diff myself if you give me the repo.*

## Phase 0: contain it (day 0, first hours)

- **Android:** in Play Console, halt the staged rollout of 4.2 if it isn't at 100% yet. If it is at 100%, rolling back isn't possible (you can't ship a lower versionCode to existing users), so the move is a fast hotfix.
- **iOS:** pause phased release in App Store Connect if it's still in progress. That stops automatic updates, but users can still update manually. There's no rollback on iOS either.
- If the crash sits behind a feature that remote config or a flag can turn off, **turn it off now**. That's the fastest mitigation available.
- Give one person ownership of the incident, open a channel for it, and post updates there (support, product).

## Phase 1: find out what's actually crashing (day 0–1)

1. **Check the symbols first.** Confirm that Sentry has source maps for the 4.2 JS bundle, plus dSYMs (iOS) and mapping files (Android). Without these, the issues group badly and the stack traces mislead. Upload them if they're missing; Sentry will re-symbolicate new events.
2. **Sentry → Releases → 4.2 vs 4.1.** Sort issues by "new in release" and by user count. Usually 1–3 issues explain most of the delta. Write the list down with each issue's share of crashes.
3. **Slice each top issue by:**
   - platform and OS version (for example, only Android 14, only iOS 18)
   - device model and manufacturer (for example, low-memory Android, one vendor's skin)
   - JS crash vs native crash (Java/Kotlin/ObjC/Swift/C++). This changes where you look.
   - Hermes vs JSC, and New Architecture on or off, if 4.2 changed either
   - app state: cold start vs foreground vs background, and the screen or route (breadcrumbs)
   - fresh install vs upgrade from 4.1. If it's mostly upgrades, suspect data migration: persisted state, AsyncStorage/MMKV schema, cached API responses.
4. **Cross-check the stores' own consoles.** Google Play Console (Android vitals) and Xcode Organizer catch crashes Sentry misses: crashes before Sentry starts, OOM kills, ANRs, iOS watchdog terminations. If the stores show more than Sentry does, suspect startup or native-initialization crashes and memory.
5. **Check the backend too.** A new API response shape or a feature flag change around the same date can crash an app that doesn't handle the new data (an undefined property access, a bad date parse). Line the crash timeline up against backend deploys.
6. **Map each top issue to the diff.** Use `git diff v4.1..v4.2`, dependency bumps (React Native, react-navigation, reanimated, Firebase, any native SDK), native config changes (`minSdk`/`targetSdk`, permissions, Info.plist), and Hermes or New Architecture toggles.

**Output of Phase 1:** a short table of top issue → affected share → suspected cause → evidence.

## Phase 2: reproduce and fix (day 1–3)

- Reproduce each top issue on the specific OS and device combinations (a physical device, an emulator, or a device farm such as Firebase Test Lab or BrowserStack). Use the breadcrumbs as the reproduction script. For upgrade-path crashes, install 4.1, create state, then upgrade to the 4.2 build.
- Write a failing test where you can (a unit test for the JS logic, or a Detox/Maestro flow for the screen). Then fix the **root cause**, not just a try/catch around the symptom.
- If a dependency bump is the cause and the fix isn't obvious, pinning it back to the 4.1 version is a valid hotfix.
- Add defensive measures where they belong: an error boundary around the affected screen tree (it stops one screen from killing the app, but only for JS render errors), and validation of persisted or API data at the boundary.
- Have someone else review the fix, and verify it on the affected devices.

## Phase 3: ship the hotfix safely (day 2–5)

- Bump to **4.2.1** with only the fixes, no new features.
- Upload symbols for 4.2.1 as part of the build (automate this in CI if it isn't already).
- Request **expedited review** from Apple if the impact justifies it. Google review is usually fast.
- **Android:** staged rollout, e.g. 5% → 20% → 50% → 100%. **iOS:** phased release.
- Promotion gate: crash-free sessions on 4.2.1 back at or near 4.1's level (about 99.5%) at a meaningful sample size before each step up.
- If you have OTA updates and the fix is JS-only, you can push it to 4.2 users immediately while the store review is pending.
- Consider a soft prompt asking 4.2 users to update. Use a forced update only if a crash corrupts data or blocks core flows.

## Phase 4: make sure it doesn't happen again (the following week)

- **Release health gates:** a Sentry alert on crash-free sessions per release (for example, below 99% on a new release pages someone), and always use staged or phased rollouts with a rule to halt at a defined threshold.
- **CI:** automatic symbol upload, and a smoke E2E run on a small device matrix that includes the OS and device combinations that broke this time.
- **Upgrade-path tests:** for releases that change persisted state, test "install the previous version → upgrade".
- A blameless post-mortem: what changed, why tests and beta didn't catch it, and how long detection took. Make sure TestFlight and the internal Play testing track are used with real dogfooding before production.

## What I'd do in the first hour

1. Halt or pause the rollouts that are still in progress, and flip any kill switch.
2. Confirm source maps, dSYMs, and mapping files exist for 4.2 in Sentry.
3. Pull the new-in-4.2 issues ranked by users, split by platform.

That list usually points straight at the cause. If you share the Sentry issue links or the `v4.1..v4.2` diff, I can start on the triage table directly.
