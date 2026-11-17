Finding the cause is probably the quicker part. A jump from 0.5% to 3% after one release almost always comes down to one to three crash groups, and Sentry can rank those within an hour, provided 4.2's crashes are symbolicated. The harder part is that a store binary cannot be rolled back. Every fix ships forward as 4.2.1 through review. So the plan freezes the rollout first, has a revert build ready to go while the diagnosis runs, and ships the real fix in stages. I have not seen your code, Sentry project or store consoles, so the plan rests on the defaults below. I read "last week" as the week of 9 November 2026, and I write 9 November into the queries below as the start of the window.

## Questions I would ask

Q1. Do you use over-the-air JavaScript updates (EAS Update, CodePush)? Default: no, so every fix goes through store review. If yes and the crash is in JavaScript, you can roll the JS bundle back to 4.1's today, and the fix ships in hours.

Q2. How long can 3% continue? Default: if there is no proven cause by the end of the second working day, ship a revert build: 4.1's code under a higher version number. If you would rather tolerate it for longer, the revert build is still prepared but held back.

Q3. Which tool reports the 3%: Sentry crash-free sessions, Play Console vitals or Xcode Organizer? Default: Sentry sessions. The tools count differently. App-not-responding events (ANRs) and out-of-memory kills often do not show in Sentry, so if the number comes from a store console, step 2 starts there.

Q4. Can I get read access to Sentry, both store consoles and the repository? Default: no, so someone with access runs the queries I give.

Answer first: Q1 and Q3. Q1 decides whether rollback takes hours or days. Q3 decides which tool holds the evidence.

## Plan

### Step 0: contain the damage and keep the evidence (today, 16 November)

- **Halt the rollout on both stores.** In Google Play Console, halt the staged rollout of 4.2 if it is not at 100%. On App Store Connect, pause the phased release if one is running. Neither removes 4.2 from devices that already have it, but both stop new installs of it. Check: the Play rollout percentage and the App Store phased-release status, recorded with the time.
- **Keep the crash data.** Make sure Sentry is not dropping events for 4.2. Check spike protection and your quota usage on the Stats page, and raise the quota for this week if events are being rate-limited. Do not delete or merge issues until the diagnosis is done. Check: Sentry Stats shows no dropped events since 9 November.
- **Hold back other releases.** Ship no new feature release until this one is understood, so a second change cannot hide the first.

### Step 1: size the problem and rank the crash groups

**First steps** (none needs an answer):

1. Open the release comparison in Sentry: Releases, then 4.2 against 4.1, by crash-free sessions and crash-free users, split by platform. This shows whether the jump is on iOS, Android or both.
2. Run a Discover query covering 9 November to today: `release:<4.2 build> error.unhandled:true`, grouped by issue, with counts of events and users, `os.name`, `device.model` and `os.version`. Run the same query for 4.1 over the same window. If 4.1 crashes rose too, the cause is likely a backend or config change, not the binary. The field names are as I remember them from Sentry's search syntax; check them in the Discover query builder.
3. Under Project Settings, Debug Files and Source Maps, confirm that dSYMs (iOS), ProGuard/R8 mappings (Android) and JS source maps were uploaded for 4.2's exact build. If stack traces show minified frames or hex addresses, re-upload them from the CI artefacts of that build, then re-process.
4. Diff the release: `git diff v4.1.0..v4.2.0 --stat`, then `git diff v4.1.0..v4.2.0 -- package.json yarn.lock ios/Podfile.lock android/build.gradle android/app/build.gradle`. React Native or SDK version bumps, a New Architecture switch and native module changes are the usual suspects. The tag names are guesses; `git tag --list` gives the real ones.
5. Pull store-side crashes that Sentry misses: Play Console, Android vitals, crashes and ANRs for 4.2; Xcode Organizer, Crashes and Energy, for 4.2.
6. Ask your backend owner whether any API, feature flag or remote config changed between 8 and 16 November.

Step 1 ends with a table: crash group, share of 4.2 crashes, platform, top devices or OS versions, first-seen release. Groups first seen in 4.2 that account for most of the excess are the targets. Everything else waits.

### Step 2: prove the cause of each target group

- Read the symbolicated stack, the breadcrumbs and the device context. Then reproduce the crash on a matching device or OS, from a 4.2 release build. Debug builds hide many release-only crashes: minification, Hermes bytecode, the New Architecture. Use Play's internal testing track or TestFlight to put it on a real device.
- **Proof:** the crash reproduces on a 4.2 build and does not reproduce with the suspected change reverted, on the same device. Until that happens, the cause is a hypothesis.
- If the stack trace points into a third-party native SDK, check that SDK's issue tracker for the exact version before writing a workaround.

### Step 3: decision point at the end of the second working day (18 November)

- **Cause proven:** go to step 4.
- **No proven cause:** ship the revert build. That is 4.1's code with a higher build number, since both stores reject a lower version, plus anything 4.2 changed in a backend contract. First check that 4.1 still works against today's backend. Check: the revert build passes the same smoke test as a normal release.

### Step 4: ship the fix forward in stages

- The fix branch is 4.2 plus the minimal change, with a regression test where the crash is reachable from JavaScript. Leave unrelated changes out, so a new crash cannot be blamed on the fix.
- Request expedited review on iOS and give the crash as the reason. On Play, start the staged rollout at about 5%.
- **Stop criteria for every stage:** crash-free sessions for 4.2.1 below 4.1's baseline (about 99.5%) after at least a few thousand sessions, or any new crash group first seen in 4.2.1 that affects more than about 0.1% of sessions. If either is met, halt and go back to step 2. With 120k monthly users, a 5% stage reaches a few thousand sessions within a day or two. Wait for that count, not for a set time.
- Widen to 100% once each stage holds its numbers. Keep prompting users to update, so the 4.2 population shrinks.

### Step 5: close it out

- Add a Sentry alert on crash-free sessions per release, with the threshold set just below 4.1's baseline, so the next regression is caught at the first rollout stage.
- Make staged rollout plus a release-health check part of every release. A 1-5% first stage would have caught this at a few hundred affected users instead of thousands.
- Check symbol and source-map upload in CI, so the next diagnosis does not start by re-uploading them.

I have left out a broad review of 4.2's code, because the ranked crash groups say where to look and the rest of the diff is noise until they are explained.
