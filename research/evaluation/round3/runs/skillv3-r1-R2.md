Rolling back is not an option for anyone who already has 4.2, because the stores cannot downgrade an installed app. So the work comes down to two things. First, find out quickly whether the new crashes really belong to 4.2. The jump happened in the same week, but a backend or remote-config change that week would also crash older versions. Second, get a fix to users faster than store review allows, by turning off a feature flag, changing a server response, or shipping an over-the-air update if you have one. A 4.2.1 through both stores comes last and is the slowest route. I have not seen your Sentry project, code or release pipeline, so the plan rests on the defaults below. I read "last week" as 9 to 15 November 2026. I am also reading "3%" as Sentry's crash rate for sessions. If 4.2 is only part of your user base, its own crash rate is higher than 3%.

## Questions I would ask

Q1. Is either store rollout still in progress (staged on Google Play, phased release on the App Store), and what share of active users is on 4.2? - Default: both are still rolling. Step 0 halts whatever is still rolling. If 4.2 is already at 100% on both stores, step 0 can only freeze other changes, and steps 5 and 7 become more urgent.
Q2. Do you have over-the-air updates (EAS Update, CodePush) or remote feature flags for what shipped in 4.2? - Default: remote flags, no over-the-air updates. A fix that needs new code then ships as 4.2.1 through both stores. If you do have over-the-air updates, a fix in the JavaScript layer reaches users in hours, and only native crashes need a store release.
Q3. How long can you live with this rate? Is it acceptable to switch off 4.2's new features remotely while the fix is made? - Default: yes, crashes are worse than a missing feature. Step 5 switches the feature off as soon as step 4 confirms it is the cause.
Q4. What else changed between 2 and 10 November: backend deploys, API responses, remote config, a React Native or native SDK upgrade inside 4.2? - Default: unknown. The first steps pull these change logs.
Q5. Who has access to Sentry, Play Console and App Store Connect, and who can ship a mobile release this week? - Default: one mobile engineer with access to all three, plus a backend engineer for step 5.

Answer first: Q1 and Q2. Together they set the fastest way to get a fix to users.

## Plan

### Step 0 - Contain and keep evidence (today, 16 November)

- If the Google Play rollout is staged and below 100%, halt it in Play Console (Release > Production > Halt rollout). If the App Store release is phased, pause it in App Store Connect. Neither helps users who have already updated. From memory, Apple lets you pause a phased release for up to 30 days in total; check the current limit in App Store Connect.
- Freeze other backend and remote-config changes to the mobile API until step 4 ends, so no second change muddies the data.
- Leave the 4.2 crash issues in Sentry as they are: do not resolve, merge or delete them. Export the top 20 issues by affected users into a spreadsheet, so a retention limit cannot erase the evidence.
- Tell support which symptoms are known, so incoming tickets can be matched to issues.

### Phase 1 - Locate (read-only, day 1)

1. **Is it 4.2?** In Sentry Release Health, compare crash-free sessions for 4.2 with the last 4.1.x, split by platform. Also check the stores' own numbers in Play Console (Android vitals > Crashes and ANRs, by app version) and Xcode Organizer > Crashes. Sentry misses crashes that happen before it starts, and on Android it does not count ANRs ("app not responding") as crashes by default. Where the evidence points:
   - **4.2 is high and older versions are flat:** the cause is in the release; go to step 2.
   - **Older versions rose too, starting on one date:** the cause is outside the app binary (an API response, remote config, a third-party service). Check the backend deploy log for that date before reading any app code.
   - **One OS version or device class dominates:** look first at native modules and permissions.
   - **The store consoles show the rise but Sentry does not:** a native crash before initialisation, running out of memory, or ANRs. Work from the console stack traces.
2. **Which issues?** In Sentry Issues, filter by `release:` 4.2 and `firstRelease:` 4.2 over 9-16 November, and sort by affected users. (Those search keys are from memory; Sentry's search bar suggests the exact names as you type.) Usually one to three issues account for most of the jump. Check that their stack traces are readable. If frames show minified JavaScript or memory addresses, upload the 4.2 source maps (Hermes bundle) and debug symbols (iOS dSYMs, the Android ProGuard/R8 mapping). Use the files from the original 4.2 build if your CI kept them; a rebuild may not match.
3. **What changed?** Run `git diff <4.1.x tag>..<4.2.0 tag> --stat` and `git diff <4.1.x tag>..<4.2.0 tag> -- package.json yarn.lock ios/Podfile.lock android/build.gradle android/app/build.gradle`. Match the top issues' stack frames and Sentry breadcrumbs (the last screens and requests before each crash) to that diff.

**First steps (need no answers):**
- Run the halt and pause above in Play Console and App Store Connect, and record the time of each.
- Export Sentry's top 20 issues for releases 4.2 and 4.1.x (users, events, platform, OS) for 9-16 November.
- Open Play Console Android vitals and Xcode Organizer for 4.2, and note crash and ANR rates next to Sentry's figures.
- Run the two `git diff` commands above between the release tags.
- Pull the backend and remote-config change log for 2-16 November.

### Phase 2 - Prove the cause (day 1 to 2)

4. **Reproduce.** Using the device, OS version and steps from the breadcrumbs, crash a 4.2 build. The cause is proven when the crash happens with the suspected change present and does not happen with it reverted or flagged off. "It matches the stack trace" is not proof. If you cannot reproduce it within a day, add Sentry breadcrumbs or tags around the suspected code in a diagnostic build, and keep looking at the data instead of shipping a guess.
5. **Mitigate before the fix, if step 4 allows.** If a feature flag guards the code, switch it off for everyone and watch 4.2's crash-free sessions over the next 2 to 4 hours. If the trigger is a server response (for example a field that is now null or has a new type), change the backend to send what 4.1 expected. That protects every installed version at once and needs no store review. Revert rule: a mitigation that does not lower 4.2's crash rate within 4 hours is undone, because it was not the cause.

### Phase 3 - Fix and release (day 2 onward)

6. **Fix it in code**, and add a test that reproduces the crash: a unit test for a JavaScript cause, a Detox or device test for a native one. If the crash happens while rendering React components, also put an error boundary around that screen, so a future render error shows a fallback screen instead of closing the app.
7. **Ship 4.2.1 with stops.** Release it staged on Google Play and phased on the App Store, and request an expedited App Store review, citing the crash. Before each widening:
   - 4.2.1 crash-free sessions are at or above 4.1's baseline (about 99.5%), measured over at least 24 hours and several thousand sessions;
   - the issues from step 2 show zero events on 4.2.1;
   - no new issue affects more than 0.2% of 4.2.1 users.
   Halt the rollout if any of these fails. If 4.2 users are slow to update after 4.2.1 is fully out, show an in-app update prompt. Force an update only if the crash loses user data.

### Phase 4 - Catch it in the staged rollout next time

8. Add a Sentry alert when a new release's crash-free sessions fall below 99%, and make CI fail the build when source map or symbol upload fails. Make staged and phased release the default for every version, so a regression like this one stops at a small share of users.

I am not suggesting rebuilding 4.1 and shipping it as 4.2.1 as the first move. It removes every 4.2 change, keeps the bug unexplained, and still takes a store review. It is the fallback only if step 4 finds no cause within two days and the rate stays above 2%.
