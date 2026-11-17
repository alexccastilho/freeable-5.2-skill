# Plan: find and fix the 4.2 crash spike

The order is: stop it spreading, identify the crash from Sentry data, ship a fix or a revert as 4.2.1, then confirm the rate is back to about 0.5%. At 120k monthly users, 3% is on the order of thousands of people hitting a crash, so I would set a hard time limit on diagnosis: if the cause is not clear within one working day, ship a revert of the suspect change instead of waiting for a clean fix.

## 1. Contain it (today, before any debugging)

- **Google Play:** if 4.2 is on a staged rollout, halt it. If it is at 100%, nothing can be pulled back; go to the hotfix path.
- **App Store:** pause the phased release if one is running. Apple has no rollback either.
- **Feature flags or over-the-air updates:** if 4.2's new features sit behind remote flags, turn off the likeliest one. If you ship JavaScript over the air (CodePush, EAS Update) and the crash turns out to be in JavaScript, that is the fastest fix path, hours instead of a store review.
- **Tell support** what is known so tickets get tagged and linked.

## 2. Find out which crash it is (first half day)

In Sentry, filtered to release 4.2:

1. **Confirm the number.** Check whether 3% is sessions or users, and compare with Play Console vitals and Xcode Organizer. Sentry misses crashes that happen before its SDK starts, and counts some things the stores do not.
2. **List issues first seen in 4.2,** sorted by users affected. A jump this size is usually one or two issues, not many small ones.
3. **Break the top issue down by:**
   - platform (iOS, Android, or both);
   - OS version, device model and manufacturer;
   - JavaScript error versus native crash;
   - time since app start: a crash at launch points at initialisation or migration code, one mid-session points at a screen or feature;
   - upgraded users versus fresh installs: upgrade-only crashes point at stored data or a migration from 4.1.
4. **Check the stack traces are readable.** If they are minified or show raw addresses, upload the 4.2 source maps, iOS dSYMs and Android mapping files first. Nothing else is worth doing until traces are symbolicated.
5. **Read the breadcrumbs** on a handful of events to get the last screen and action before the crash.

## 3. Match it to what changed in 4.2

Diff the 4.1 and 4.2 release tags and line the top crash up against:

- dependency upgrades, especially React Native itself and native modules (these cause most platform-specific native crashes);
- build configuration changes: Hermes, New Architecture, ProGuard/R8 rules, minimum OS versions, SDK target;
- new screens or features, and changes to startup code;
- changes to persisted data (storage schema, cached API responses) that old installs still carry;
- backend changes shipped the same week: a new response shape can crash a client even though the app release looks like the trigger.

Then reproduce on a device matching the worst-hit segment, using a release build, since several of these never show up in debug builds.

## 4. Fix and ship 4.2.1

- **Cause found and fix is small:** fix it, add a regression test for the path, ship.
- **Cause found but fix is risky, or cause not found within a day:** revert the suspect change (or the whole dependency upgrade) and ship that. The proper fix goes into 4.3.
- **Release path:**
  - JavaScript-only fix with over-the-air updates available: push it to a small percentage first, then everyone.
  - Otherwise: submit 4.2.1 to both stores, request an expedited review from Apple, and use a staged rollout on Play (for example 10%, 50%, 100%) and phased release on iOS.

## 5. Confirm it worked

- Crash-free sessions and users for 4.2.1 at or above the 4.1 level (about 99.5%) at each rollout step, with enough sessions to trust the number.
- The specific Sentry issue shows zero events on 4.2.1.
- Watch for a week, since 4.2 users only recover as they update. Consider an in-app update prompt for 4.2 if adoption of 4.2.1 is slow.

## 6. Stop the next one reaching everyone

- Sentry alert on crash-free rate per release, firing within hours of a rollout starting.
- Staged rollouts on both stores as the default, with a go/no-go check at each step.
- Symbol and source-map upload as a required step of the release build.
- Remote flags for new features, so the next one can be turned off without a release.

## Questions I would ask

1. **Was 4.2 rolled out in stages, and how far has it got?** *Default assumed:* it is at 100% on both stores, so containment is limited to flags and the hotfix.
2. **Is the spike on one platform or both?** *Default assumed:* unknown; the Sentry breakdown in step 2 answers it and I would not guess.
3. **Do you have over-the-air updates?** *Default assumed:* no, so the fix goes through store review.
4. **What went into 4.2?** *Default assumed:* a mix of features and dependency upgrades, with the upgrades as the first suspects.
5. **Is 3% of sessions or of users?** *Default assumed:* sessions, as Sentry reports by default.
