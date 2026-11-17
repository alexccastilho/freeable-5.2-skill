# Plan: find and fix the 4.2 crash spike

The order is: stop more users getting the bad build, identify the crash from Sentry, ship a fix or a revert as 4.2.1, then close the gap that let it through. Because store releases cannot be rolled back, limiting exposure today matters more than a perfect diagnosis.

I have not seen your Sentry data or your code, so this is the route I would take and the decision points along it, not a diagnosis.

## Step 1: limit exposure (today)

- **Google Play:** if 4.2 is on a staged rollout, halt it. If it is at 100%, nothing can be pulled back; the fix has to go out as a new version.
- **App Store:** if phased release is on, pause it. This only stops automatic updates; manual updaters still get 4.2.
- **Feature flags:** if 4.2 introduced features behind remote flags, be ready to turn off the suspect one as soon as step 2 points at it.
- **Over-the-air updates:** if you use EAS Update or CodePush and the crash turns out to be in JavaScript, a fix can reach 4.2 users within hours without store review. It cannot fix a native crash.

## Step 2: identify the crash from Sentry (today, one to two hours)

Open Sentry's Releases view for 4.2 and answer these in order. Each answer narrows the search.

1. **Is it one issue or many?** Sort issues by "first seen in 4.2" and by events. A jump from 0.5% to 3% is usually one or two new issues. If so, everything below applies to those.
2. **Which platform?** Compare crash-free rate for iOS and Android separately. One platform only points to native code, a native dependency or platform-specific configuration.
3. **Native or JavaScript?** A JavaScript error has a JS stack trace. A native crash shows a signal such as SIGABRT or SIGSEGV on iOS, or a Java/Kotlin exception or ANR on Android.
4. **Which users?** Break the top issue down by OS version, device model, locale, and whether the app was freshly installed or upgraded. A crash confined to upgraded installs suggests a storage or data migration problem. A crash confined to one OS version suggests an API or permission change.
5. **When in the session?** Check breadcrumbs and the last screen. A crash at launch is more severe than the rate suggests, because those users cannot use the app at all.
6. **Are the stack traces readable?** If they show minified JS or raw memory addresses, the source maps, dSYMs or ProGuard mappings for 4.2 were not uploaded. Upload them first; Sentry can re-process existing events.

Cross-check the rate against Play Console's Android vitals and Xcode Organizer. They catch crashes that happen before Sentry initialises, plus ANRs and out-of-memory kills, which Sentry can miss.

## Step 3: find the cause

Go through what changed between 4.1 and 4.2, guided by step 2:

- **Dependency changes:** diff `package.json`, the lockfile, `Podfile.lock` and the Gradle files. A React Native upgrade, a new or upgraded native module, or switching on the New Architecture or Hermes settings are the most common sources of a release-wide jump.
- **Build configuration:** minification rules, SDK target versions, permissions, signing.
- **Code changes:** the commits touching the screen or module named in the stack trace.

Then reproduce it on a release build, not a debug one, on a device matching the affected profile from step 2. For an upgrade-only crash, install 4.1, use it, then upgrade to 4.2. If the cause is still unclear, bisect the commits between the two releases.

## Step 4: fix and ship 4.2.1

- **If the cause is clear and the fix is small:** fix it, with a test that reproduces the crash.
- **If it is not clear within about a day:** revert the suspect change (or the dependency upgrade) and ship that. A known-good revert beats a speculative fix, and the feature can return in 4.3.
- **Release:** request an expedited review from Apple, citing the crash. On Play, stage the rollout at 10 to 20% for a few hours, watch the crash-free rate for 4.2.1 in Sentry, then go to 100%.
- **Confirm:** the work is done when 4.2.1's crash-free rate is back at or above the 4.1 level and the specific Sentry issue shows no events from 4.2.1. Watch for a few days; users who stay on 4.2 will keep the overall number raised until they update.

If the crash is at launch, consider a forced-update prompt for 4.2 once 4.2.1 is live, if your app has that mechanism.

## Step 5: stop it happening again (the following week)

- Use staged rollout on Play and phased release on iOS for every release.
- Add a Sentry alert on crash-free rate for a new release, so a jump is seen within hours instead of at the weekly review.
- Fail the build in CI when source maps, dSYMs or ProGuard mappings are not uploaded.
- Add an upgrade test to the release checklist: install the previous version, then upgrade.
- Put risky features behind remote flags.

## Questions I would ask

1. **What does the 3% measure, and where is it from?** Crashed sessions or affected users, from Sentry or the store consoles?
   Assumed default: Sentry's crash-free sessions. If it is users, that is roughly 3,600 of your 120k monthly users affected, up from about 600.
2. **Is 4.2 at 100% on both stores?**
   Assumed default: yes, so step 1 offers little and the hotfix is the main lever.
3. **What went into 4.2?** In particular, any React Native or native dependency upgrade?
   Assumed default: a mix of feature work and dependency bumps.
4. **Do you have over-the-air updates or remote feature flags?**
   Assumed default: neither, so the fix goes through the stores.
5. **Is the jump on both platforms?**
   Assumed default: unknown; step 2 answers it in minutes.
