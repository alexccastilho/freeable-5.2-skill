# Plan: finding and fixing the 4.2 crash regression

Crash rate going from 0.5% to 3% (six times worse) with roughly 120k monthly users means thousands of people are hitting crashes every week. So the plan runs two tracks in parallel: **stop the bleeding**, and **find the root cause**. Don't hold back mitigation until the root cause is fully understood.

## Questions I would ask

1. **Is the jump on both platforms, or mostly one?** *Default:* unknown. Step 1 answers it in minutes.
2. **What changed in 4.2?** That means the RN version, Hermes/New Architecture flags, native SDK bumps, Expo SDK, and big features. *Default:* there's a changelog or git range `v4.1.x..v4.2.0` we can diff.
3. **Do you use OTA updates (EAS Update or CodePush)?** *Default:* no. Fixes ship through store releases, so phased rollout and expedited review matter.
4. **Is the Play rollout still staged, and is the iOS phased release still running?** *Default:* both are at or near 100%.
5. **Are dSYMs, ProGuard/R8 mappings and JS source maps uploaded to Sentry for 4.2?** *Default:* JS source maps yes, native symbols unsure. Check in step 1, because without them native stacks are unreadable.
6. **Is there a remote feature-flag system (LaunchDarkly, Firebase Remote Config, home-grown)?** *Default:* there is something for some features, not all.

## Phase 0: first hour, triage and contain

1. **Pause rollouts.** On Google Play, halt the staged rollout of 4.2 if it isn't at 100%. In App Store Connect, pause the phased release. That caps how many more users get the bad build. (Neither store lets you pull an installed version back, so the real fix is a new build.)
2. **Confirm the metric is real.** Compare Sentry's crash-free sessions/users for 4.2 against 4.1.x, and cross-check with Play Console Android Vitals and Xcode Organizer / App Store Connect crashes. Make sure the 3% isn't an artefact: changed sampling, a new `Sentry.init` config, or JS errors now counted as crashes after an SDK upgrade.
3. **Set up a war-room channel and one owner.** Write a short status update each day.

## Phase 1: same day, locate the regression

In Sentry, filter `release:4.2.*`:

1. **Issues → sort by users affected, "first seen in 4.2".** Usually one to three issues account for most of a jump like this. List the top five with event counts, platform split and share of the delta.
2. **Slice each top issue by tags:** `os`, `os.version`, `device.family`/model, `release`/`dist`, Hermes or JSC, New Arch on or off, app start vs. in-session, and `handled`/`mechanism`. Patterns tell you a lot. If it only happens on Android 8–9, think of a native lib or API-level issue. If it's iOS 18 only, an SDK incompatibility. If it's low-RAM devices, an OOM. If it happens at launch, startup or config, a migration, or a native module init.
3. **Read the native vs. JS split.**
   - *JS exceptions* (the red screen equivalent in production, `TypeError: undefined is not an object`). Check that source maps resolve. Breadcrumbs usually point straight at a screen or API response.
   - *Native crashes* (SIGABRT, SIGSEGV, `NSInvalidArgumentException`, `UnsatisfiedLinkError`, ANRs). Upload any missing dSYMs or mappings first, then look at which native module is in the stack.
   - *OOMs / watchdog kills* often show up only in the store consoles (Xcode Organizer "terminations", Android Vitals "low memory"), not in Sentry. Check there if Sentry's issue list doesn't add up to the delta.
4. **Diff 4.1 → 4.2** with the top stacks in hand. The usual suspects in RN releases:
   - React Native, Hermes, New Architecture (Fabric/TurboModules) upgrade, or a toggle flipped
   - native dependency bumps (navigation, reanimated, gesture-handler, maps, camera, payments, Firebase, the Sentry SDK itself)
   - targetSdk / minSdk change, a new Android 14+ permission or foreground-service requirement, iOS privacy manifest changes
   - persisted-state migrations (redux-persist, MMKV, AsyncStorage schema) that crash on upgraded installs but not fresh ones
   - new API fields the app assumes are always present (backend and app out of sync, or older cached data)
   - a new feature screen with heavy lists/images (memory)
5. **Check whether the backend changed at the same time.** If 4.1 users also crash more since that date, the cause is server-side data, not the binary.

**Outcome of Phase 1:** a ranked list of the crash signatures that explain the 0.5 → 3% delta, each with a hypothesis.

## Phase 2: days 1–3, reproduce and fix

1. **Reproduce each top issue.** Match the device/OS from the tags (use a device farm such as BrowserStack/Firebase Test Lab if you don't own it). Replay the breadcrumb path. **Test the upgrade path 4.1 → 4.2 with existing data**, not just fresh installs. Migration crashes hide there.
2. **Mitigate remotely where you can.** If the crash is in a flagged feature, turn the flag off. If you have OTA and the bug is JS-only, ship a JS fix through OTA to the 4.2 binary (staged to 10% first).
3. **Fix with a regression test** for each signature: a unit test for the null-handling or migration, or an E2E test (Detox/Maestro) for the flow.
4. **Decide between fix-forward and revert.** If the root cause is a big upgrade (RN/New Arch/native SDK) and a fix isn't obvious within a day or two, build **4.2.1 that reverts that specific change** and keeps the rest. Don't spend a week debugging while thousands of users crash.

## Phase 3: release the fix safely

1. Build 4.2.1 with symbols uploaded (verify in Sentry that a test crash symbolicates).
2. **Android:** staged rollout 5% → 20% → 50% → 100%, with a 24h check of crash-free rate at each step versus 4.1.
3. **iOS:** request an **expedited review** with a crash-fix justification, then use phased release (you can still release to everyone early once the numbers are good).
4. Consider **minimum-version or soft-update prompts** to move 4.2 users onto 4.2.1 quickly, if you have an in-app update mechanism (or Play In-App Updates).
5. Success criterion: crash-free users back at about 99.5% or better for 4.2.1 within a week of 100% rollout, and no top issue newly introduced.

## Phase 4: make sure it doesn't happen again

- **Sentry release health alerts:** alert when a new release's crash-free sessions fall more than X points below the previous release in its first hours, and when a new issue passes N users.
- **Rollout policy:** every release starts at 1–5% on Play and with phased release on iOS, and moves up only if it passes a crash-free gate.
- **Release checklist:** symbols uploaded, upgrade-path test from the previous version, smoke test on a low-end Android device and on the oldest supported iOS.
- **Feature flags for risky features** (and a kill switch for big native upgrades where feasible).
- **Short blameless post-mortem:** what changed, why tests missed it, which guardrail would have caught it.

## What I'd need from you to start

Sentry org/project access (or exports of the top 4.2 issues), the 4.1→4.2 diff or changelog, and Play Console / App Store Connect access to check rollout state and vitals. With those, Phase 1 is usually a half-day job.
