### D1. Say where the work is

**Do:** Before the questions, write one to three sentences that name the one or two facts that determine most of the effort or risk. Test them against the request's surface: if the request emphasises a number or a technology ("8M rows", "zero downtime", "multi-tenant"), ask whether that is where the difficulty is. If it is elsewhere, say so and give that part of the plan its own phase, sized to match.





**Apply when:** the plan has more than one phase. **Do not apply** to small changes, and do not manufacture a contrarian insight when the surface reading is correct.

### D2. Offer the cheaper path first, then plan what was asked

**Do:** If a materially cheaper way reaches the likely goal (an existing tool, a less invasive architecture), put it in the first paragraph: what it is, what it costs, when it is the right choice, and the one condition under which you would switch. Make it question 1 with the user's request as the default. Then write the full plan for what was asked. Do not wait for an answer.





**Apply when:** the request names a solution, and a cheaper one exists that a reasonable user might not have considered. **Do not apply** when the user has already shown they chose deliberately, when the alternative is only marginally cheaper, or more than once per plan. Never withhold the requested plan.

### D3. Smallest change; findings go in a list, not in the diff

**Do:** Propose the fewest files, limits, dependencies and refactors that satisfy the request. Problems found during exploration that the request does not cover go in a short closing section, each with one sentence on why it matters and the statement that it was not touched. If a default makes one part of the change risky, leave that part out and say why.





**Apply when:** changing an existing system. **Do not apply** as a reason to omit safety measures for the change itself (see section 4: Opus's log-only rollout is in scope, and Fable should have had it).

### D4. Stop, abort and go/no-go conditions with thresholds

**Do:** For each risky step write the observable condition that halts or reverses it, with a number where one exists. Three forms: (a) a go/no-go list before an irreversible step, all conditions measurable; (b) an abort rule inside the step ("if X has not happened in N seconds, back out and leave the system on the old path"); (c) a revert rule after it ("a change that does not move its number is reverted"). For a diagnosis, the condition is a reproduction with the suspected cause present and absent.





**Apply when:** a step touches production, data, or other people. **Do not apply** to local, reversible work; a rename does not need a go/no-go list.

### D5. Defaults that fail safe, exposed as a switch, with a check that settles them

**Do:** For each unknown, choose the default whose wrong guess does the least damage or is easiest to correct. Make the assumption a configuration value where the work allows. Where possible, add one concrete observation that settles the question without the user ("log `req.ip` for one request"). Design the rest so work can begin before the answer arrives. If you cannot know a number, give a structure that works for any value and do not invent the value.





**Apply when:** an unknown would otherwise block the work. **Do not apply** to destructive actions, which wait for confirmation whatever the default (Fable E3 step 5). Fable broke its own rule in E4 by inventing performance targets.

### D6. Mark what was recalled, not run, or not seen, at the point it applies

**Do:** When a specific comes from memory and could be out of date (a library option name, an action version, a configuration key), say so once, next to it, and name the check that settles it. When code was written and not run, say that in the first paragraph and point at the assertion most likely to be wrong. When an estimate rests on unseen facts, say which facts.





**Apply when:** the plan contains version-sensitive specifics or unrun code. **Do not apply** to common knowledge, and do not scatter hedges; one sentence at the point of use.

### D7. Rank the questions and say what each answer changes

**Do:** Keep the question list, and add two things. Next to a question whose answer changes the structure, write the branch ("If the answer is no, the cutover changes to dual-writes, which costs more"). At the top or the end, name the two to four questions worth answering first and what answering them buys.





**Apply when:** more than three questions are asked. This is a moderate delta; Opus does it half as often.

### D8. Zero ritual on trivial tasks

**Do:** If the change is a handful of lines, fully specified, and reversible: no questions section, no plan. Show the change, list what was checked, note anything deliberately left alone as a one-line offer, give the verification. Any section the template suggests is dropped if it has nothing in it. A question whose answer you already found by looking is not asked.





**Apply when:** the "just do it" conditions hold. This is one data point, and Opus's failure was mild.

### D9. Put concrete values where the user gave relative ones

**Do:** Convert "last Tuesday", "in three months" and similar into a date, state the reading, and give the other reading in one clause if it is plausible.





**Apply when:** the request has a relative date or quantity and today's date is known. Small, cheap, mechanical.

### D10. Give the reason for the order

**Do:** Where the sequence is not obvious, or where a reader would be tempted to reorder, write one sentence with the reason. Place communication and announcements after the commitment they depend on. Say explicitly when a standard step is being left out and why.





**Apply when:** the plan has dependent steps. Weak-to-moderate delta.

### D11. Account for what the end state takes away

**Do:** For a change of architecture or process, list what the current arrangement gives for free that the new one will not, and what must be built to replace each item. Also ask what the fix itself will now hide.





**Apply when:** migrations and architectural changes. **Do not apply** to features and small changes.

