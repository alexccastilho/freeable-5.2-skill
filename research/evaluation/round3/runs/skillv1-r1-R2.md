A sixfold jump right after one release almost always comes from one to three new crash groups, and Sentry already sorts them by release. Finding the cause is likely the quicker part. Most of the calendar time goes into getting a fix onto phones, because store binaries cannot be rolled back, only replaced by a higher version number that has to pass review. So the plan first stops 4.2 from reaching more people, then finds the cause from release data, and then ships a narrow 4.2.1 in stages.

I read "last week" as Monday 9 to Sunday 15 November 2026. The release date in Sentry pins it exactly. I have not seen your Sentry project, store consoles or code, so the steps rest on the defaults below.

## Questions I would ask

1. **Do you have over-the-air JS updates set up (EAS Update or CodePush)?** Default: no, so every fix ships through store review. If yes, and the crash is in JS, the fix can reach existing 4.2 installs within a day through OTA, and the store build becomes a follow-up.
2. **Did anything else change that week: a backend deploy, a feature flag, remote config, an API response shape?** Default: unknown. Step 1 tests this by checking whether older app versions also got worse. If they did, the cause is on the server side and can be reverted without any app release.
3. **Where does the 3% come from: Sentry crash-free sessions, crash-free users, or the store consoles?** Default: Sentry crash-free sessions. Step 1 cross-checks it against Play Console Android vitals and Xcode Organizer.
4. **Do you have remote feature flags around the features that are new in 4.2?** Default: none. If you do, turning off the suspect feature is the fastest containment there is.
5. **Who can change rollouts in App Store Connect and Play Console, and request expedited review?** Default: someone on the team has access and acts on step 0 today.

Answer first: 1 and 2. Question 2 can make this a server rollback with no release at all. Question 1 decides whether the fix ships in hours or days.

## Plan

**Step 0: contain and preserve evidence (today).**
- If 4.2 is still on a phased or staged rollout, pause it: App Store Connect "Pause Phased Release" and Play Console "Halt rollout". Pausing does not remove 4.2 from people who already have it, but it stops new installs from getting it. If 4.2 is already at 100%, this step does nothing.
- If question 4 is a yes, turn off the new features behind flags. Watch the crash rate for a few hours to see whether it falls.
- Check that the 4.2 source maps (JS) and dSYMs / ProGuard or R8 mapping files (native) are uploaded to Sentry for this exact release and build. Without them the stack traces are unreadable. Find and upload the missing ones now, from the CI artefacts of the 4.2 build. Do not rebuild them, because a rebuild's maps may not match.
- Do not ship any speculative "might fix it" build. It uses up a review cycle and muddies the before/after comparison.

**Step 1: confirm the regression and narrow it down (day 1).**
- In Sentry Releases, compare 4.2 with 4.1 on crash-free sessions and crash-free users, split by platform. Expect the jump on one platform, or concentrated on one OS version or device class.
- Check whether 4.1 and older also got worse during the same days. If yes, go to question 2's branch: the cause is server-side or config, so look at backend deploys and flag changes.
- Issues view: filter `release:4.2` with "first seen" in 4.2 and sort by events and users affected. Usually the top one to three groups account for the gap.
- Cross-check the store consoles. Native crashes during startup, before Sentry initialises, and out-of-memory kills on iOS often never reach Sentry but do appear in Xcode Organizer and Android vitals. ANRs on Android show up in Play vitals too.
- Check that 4.2 did not change the Sentry SDK version or session-tracking settings. If it did, part of the jump may be a change in how crashes are counted, not in how often they happen.
*Check:* you can say what fraction of the excess comes from each top crash group. Proceed when the named groups cover most of the jump from 0.5% to 3%.

**Step 2: link each group to a change in 4.2 (days 1-2).** Diff the 4.1 and 4.2 tags, focusing on React Native or Expo SDK upgrades, native dependency bumps, `targetSdkVersion` or iOS deployment-target changes, New Architecture or Hermes toggles, new permissions, and new native modules. Match each top crash group's stack trace, OS versions and devices against that diff. Breadcrumbs show the screen and the action just before the crash.

**Step 3: reproduce it, then prove it.** The cause is proven when the crash reproduces on a 4.2 build with the suspect change, and does not reproduce on the same build with only that change reverted. Use a real device that matches the affected OS and model from Sentry; Firebase Test Lab or a device farm can stand in. If it does not reproduce, you do not have the cause yet. Add targeted Sentry breadcrumbs or context in the fix build rather than guessing.

**Step 4: build the hotfix (4.2.1).** Branch from the 4.2 tag, not from `main`, so unrelated work in progress stays out. Include only the fix, plus any breadcrumbs from step 3. Add a test for the crashing path where one is practical. Upload maps and dSYMs as part of the build.

**Step 5: release in stages, with a stop rule at every stage.**
- Android: staged rollout at 1%, then 10%, 50%, 100%. iOS: phased release (it follows Apple's fixed 7-day schedule, and you can pause it). Request expedited review on iOS and give the crash rate as the reason. Apple grants these at its discretion.
- Hold each stage until it has enough sessions for 4.1's rate to have produced a few dozen crashes, so the comparison means something.
- **Stop rule:** halt the rollout if 4.2.1's crash-free session rate is not better than 4.2's, or if a crash group appears that was not in 4.2. Go to 100% once 4.2.1 is back at or near 4.1's 0.5% on both platforms.
- If OTA is available (question 1) and the fix is JS-only, push it to the 4.2 binary as a staged OTA rollout with the same stop rule. The store build follows.

**Step 6: move people off 4.2.** Users on 4.2 keep crashing until they update. If you have a minimum-version or soft-update prompt, point it at 4.2.1 once 4.2.1 is at 100%. Without one, watch the share of sessions on 4.2 fall in Sentry. If it falls slowly, adding a soft-update prompt is worth putting in this release.

**Step 7: make the next one smaller.** Add a Sentry alert on crash-free session rate per release, with the threshold set a little below your normal 99.5%. Make staged rollout with a hold-and-check at 10% the default for every release. Add a release-checklist item that verifies maps and dSYMs are uploaded.

## Found, not touched

- A release can only be rolled back by shipping a higher version number. Keep a "last known good" branch you can rebuild quickly as 4.2.2 if 4.2.1 makes things worse.
- If crashes also hit a backend because clients retry, check server load for that week too.

## Need from you

- Read access to the Sentry project, or screenshots of the 4.2 vs 4.1 release comparison and the top issues filtered to `release:4.2`.
- The git range between the 4.1 and 4.2 tags (or the changelog).
- Answers to questions 1 and 2.
