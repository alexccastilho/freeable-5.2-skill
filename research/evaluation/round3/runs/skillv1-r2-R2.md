Two things matter more than the diagnosis. First, stop 4.2 from reaching more users today. Second, plan around the fact that you can't roll a store binary back: the fix ships as 4.2.1 through review and staged rollout, and users stuck on 4.2 keep crashing until they update. With Sentry installed, finding the cause is usually the shorter part, provided the 4.2 crashes are symbolicated. So the first technical check is whether source maps, dSYMs and the Android mapping file for 4.2 were uploaded. I read "last week" as the week of 9–15 November 2026.

**Not seen:** your Sentry project, the store consoles, or the 4.1 to 4.2 diff. The plan rests on the defaults below.

## Questions I would ask

Q1. Do you use over-the-air JS updates (EAS Update or CodePush)? - Default: no. If yes, and the cause is in JS, the fix can reach most users within hours without store review. Step 5 then becomes an OTA rollback or patch, with its own staged rollout.

Q2. Did 4.2 change React Native, Expo SDK, Hermes or the New Architecture, the Sentry SDK, the Android target SDK, or any native module? - Default: unknown; step 3 finds out from the diff. If the Sentry SDK version changed, step 1 first checks whether the crash rate is measured the same way in both versions.

Q3. Does the app have remote feature flags or a minimum-version / force-update mechanism? - Default: no flags and no force update. If flags exist, turning off the features that are new in 4.2 is part of step 0. If force update exists, it is used only once 4.2.1 is proven, and only for the 4.2 build.

Q4. Can I get read access to Sentry, App Store Connect, Play Console and the repository? - Default: someone with access runs steps 1 to 3 with me.

Answer first: Q1 and Q3. Either can turn a fix that takes days into containment within hours.

## Plan

**Step 0: Contain and keep the evidence (today).**
- Play Console: if 4.2's staged rollout is below 100%, **halt it**. App Store: if phased release is on, **pause it** (a pause lasts up to 30 days in total, as I remember it; check in App Store Connect). If 4.2 is already at 100% on a platform, nothing can be pulled back there. Go straight to step 1.
- If Q3 flags exist, turn off the features new in 4.2, starting with the one closest to the top crash.
- Don't delete or resolve Sentry issues. Note the 4.2 build numbers, and check that the release and dist tags in Sentry match them.
- Check: rollout status shows halted/paused, and new 4.2 installs per day level off in the consoles.

**Step 1: Confirm the number and split it (half a day).**
- Compare Sentry's crash-free session rate with Play Console Android vitals (crash rate and ANR rate) and App Store Connect / Xcode Organizer crashes. If only Sentry jumped, look first at whether 4.2 changed how sessions or crashes are counted (an SDK upgrade, changed sampling, a new handled-error setting).
- Split the 4.2 crashes by platform, OS version, device model, and JS crash vs native crash vs ANR. Check 4.1's rate over the same days. **If 4.1 also rose, the cause is not in the 4.2 binary.** Look at backend responses, remote config or a third-party SDK's server instead.
- Check: one table showing crash rate per platform per version, 1–15 November.

**Step 2: Rank the crashes (half a day).**
- In Sentry, filter to release 4.2 and sort issues by users affected, keeping those first seen in 4.2. Usually one to three issues explain most of a jump this size. Write down what share each accounts for.
- If stack traces are minified or unsymbolicated: upload the source maps, dSYMs (from App Store Connect if built in the cloud) and the R8/ProGuard mapping for exactly these builds, then reprocess.
- Check: the top issues add up to most of the excess over 0.5%. If they don't, the jump is spread out (a memory or startup regression, for example), and the next step looks at startup and OOM rates instead.

**Step 3: Link each top issue to a change.** Diff 4.1 to 4.2: `package.json`/lockfile, `Podfile.lock`, Gradle files, native config, and the screens in each top stack trace. Read each issue's breadcrumbs for the last screen and action before the crash.

**Step 4: Prove the cause.** The cause counts as proven when the crash reproduces on the 4.2 release build with the suspected change present, on the device/OS combination Sentry points to, and does not reproduce with that change reverted. Use the release build, not a debug build, because Hermes, minification and R8 behave differently. If it can't be reproduced, you don't have the cause yet. Add targeted logging or Sentry breadcrumbs for 4.2.1 instead of guessing a fix.

**Step 5: Fix and release 4.2.1.**
- The smallest fix for each proven cause, or revert the change behind it. Bump the version and build numbers.
- iOS: ask for expedited review, citing the crash rate. Release with phased release on.
- Android: staged rollout at 1%, 10%, 50%, then 100%.
- **Stop rule for each stage:** wait for enough sessions to compare (start with a few thousand per platform; it's a setting, not a fixed number). Move to the next stage only when 4.2.1's crash rate is at or below 4.1's rate over the same days and none of the step 2 issues shows up in 4.2.1. If a step 2 issue appears, or the rate is above 4.1's, halt and go back to step 4.

**Step 6: Get users off 4.2.** If Q3 force update exists, set the minimum version to 4.2.1 for 4.2 users only, and only after 4.2.1 reaches 100% on that platform and passes the stop rule. Otherwise use an in-app update prompt if there is one. Check: 4.2's share of sessions falling day by day in Sentry.

**Step 7: Close out.** Mark the issues as resolved in 4.2.1 so Sentry flags any regression. Add a release gate for the future: every release goes out staged, with the stop rule above, and a Sentry alert fires when a new release's crash-free rate falls below the previous release's.

Order reason: containment comes before diagnosis because every hour 4.2 keeps rolling out adds users who can only be fixed by a store update.

## Found, not touched

- If the 4.2 build was not symbolicated, the build pipeline is missing an artifact-upload step. Fix that in CI, not by hand, or 4.3 will repeat this.
- Roughly 3% of sessions crashing means many one-star reviews this week. A short reply template for affected reviewers, sent once 4.2.1 is live, is worth considering.

## Need from you

- Sentry, App Store Connect and Play Console access (or someone at the keyboard).
- The git tags or commits for 4.1 and 4.2.
- Answers to Q1 and Q3.
