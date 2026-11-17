# Question bank by task type

Use this when filling part 3 of the output contract. The questions are the ones asked in the source traces. Most of them you would ask anyway; what this file adds is the form of the default and the filter that keeps the list short.

## Filter before you ask

Run each candidate through these in order. Stop at the first that applies.

1. **You can find the answer by looking** (repository, files, conversation). Look. Do not ask.
2. **The default is near-certain and a wrong guess is cheap.** Write it as a stated assumption in one line, not as a question. Example: "Assumed under a few thousand notes, so a full rebuild each time."
3. **The answer changes a detail only.** Take the default, state it, move on.
4. **The answer changes the structure of the plan, or a wrong guess does damage.** Ask it, with a default, and write the branch.

Keep at most five questions. Order them so the one that can cancel others comes first: goal, then scope, then approach, then detail.

## Two kinds of question that earn their place

**Harm-or-shrink questions.** They ask about one fact that would make the default design harmful, or the plan much smaller.

- "Custom tool, or a thin setup around an existing generator?"
- "Do the warehouse staff share one office IP address?"
- "Is the load append-only, or can the vendor send corrections?"
- "Which tables have foreign keys to `users`, and which queries join to it or write to it inside a larger transaction?"
- "Are integer record IDs visible outside the app?"

**Resource and access questions.** They ask what you can see and who will do the work. Ask them before giving any estimate.

- "Can I see the repository?"
- "Can I query production read-only and read the job logs?"
- "Team size and timeline?"
- "Is there an archive of the source files, and how long is it retained?"

## How to write the default

State what the plan does about it. Add the reason only when the reader would not guess it.

| Form | Example |
|---|---|
| Default as a design consequence | "Default: project repository, so the tool must handle a base path." |
| Default as a setting | "Default: no proxy. Exposed as `TRUST_PROXY` so it can be corrected without a code change." |
| Default that removes a risky part | "Default: yes, they share one address. For that reason there is no strict limit on the shipping and import routes." |
| Admitted unknown plus the step that finds it | "Default: unknown, to be found in step 2." |
| Default tested before it is relied on | "Default: a stable vendor ID. Step 1 tests this before anything relies on it." |
| Structure in place of a number | "Not set. A percentage split is given below; you supply the total." |
| Branch for a structure-changing answer | "If the answer is 'no pause at all', the cutover changes to application dual-writes, which costs more and has more ways to diverge." |

Close the block with the ranking: "Answer first: 1, 2 and 4. With those I can skip most of the broad measurement and bring the first fix forward by several days."

## Questions by task type

"Ask" means it survived the filter in the traces. "Assume" means state it as an assumption unless the context makes it doubtful.

### Greenfield tool

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| Build this, or a thin setup around an existing tool? | Build, as requested | Ask, first |
| What does the input look like (formats, dialects)? | The common format plus the one widespread extension; the rest left out of version 1 | Ask |
| Is everything meant to be public or published? | Published unless marked `draft` or `publish: false`; an ignore list is accepted | Ask: a wrong guess leaks data |
| Where will it be hosted or run? | The case that needs more handling (for example a base path), so both cases work | Ask |
| Language or runtime? | One mainstream choice; design unchanged for others | Assume |
| Extra features (search, tags)? | None in version 1 | Assume |
| How large is the input? | Small enough for a full rebuild | Assume |

### Brownfield feature

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What sits between the client and the app (proxy, load balancer, CDN)? | The reading that fails safe, exposed as a setting, plus one check in the deployed environment | Ask, first |
| Who are the legitimate callers, and do they share an identity or address? | They may share one, so no strict limit where that would block them | Ask |
| What happened (which route, what rate, how many sources)? | The simplest reading; say what the change does not cover if it was worse | Ask |
| What is normal peak usage? | Unknown; parameters are settings, labelled as guesses, with an observe-only stage before enforcement | Ask |
| Is adding the standard dependency acceptable? | Yes | Assume |
| Can the adjacent problem you found be fixed in the same change? | No; it goes in "Found, not touched" | Do not ask; list it |

### Incident

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What identifies a record uniquely? | A stable source ID; the first step tests this | Ask |
| Is there a constraint on that identifier today? | No | Assume, then check |
| What changed around the start date? | Unknown; a named step finds it | Ask |
| Who consumes the affected data, and has anyone acted on it? | Consumers exist and have read bad data; they are told after cleanup | Ask |
| Can I read production and the logs? | Yes; otherwise someone with access runs the first step | Ask |
| Can the source legitimately send corrections? | No; if yes, the fix becomes update-on-conflict instead of skip | Ask: it changes the fix |
| Are the raw inputs still retrievable, and for how long? | Yes; check retention before relying on it | Ask |
| Can the job be paused today? | A guard yes; a pause only with the owner's go-ahead | Ask |

### Vague request ("make it faster", "make it better")

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What prompted this? | Complaints about specific parts, no measurements yet | Ask, first |
| Which part, and for whom? | Unknown; measure the most-used screens and endpoints, split by customer size | Ask |
| What would count as good enough? | Targets proposed after the baseline; none invented now | Ask |
| What is already measured? | Little; step 1 adds instrumentation | Ask |
| Can I see the code and the monitoring? | No access assumed; first step is getting it | Ask |
| How much time is this worth, and what is off limits? | No rewrites, framework changes or infrastructure moves | Ask |
| What is the stack underneath? | Mainstream choices | Assume |

### High-risk migration

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| Is this piece moving alone, or first of many? | First of many, so tooling is reusable | Ask, first |
| What does "zero downtime" allow (a few seconds of held writes, none failing)? | Yes, once, about 10 seconds; if no, the cutover design changes | Ask: it changes the cutover |
| What references, joins or shares a transaction with the thing being moved? | Several; they are decoupled first | Ask |
| Managed or self-hosted; is the change stream available? | Available; a preliminary phase checks it | Ask |
| What else writes to it? | A few jobs, all changeable; privileges revoked at cutover so a missed writer fails loudly | Ask |
| Is there one data-access layer? | No; it is consolidated first | Assume |
| Write rate, and tolerance for stale reads? | Reads after a write must see it | Assume |

### Large cross-cutting change

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What is driving this (cost, speed, growth, new features)? | The reading that justifies what was asked; name the cheaper design if the driver is cost alone | Ask, first |
| Do any contracts promise isolation, residency or customer-managed keys? | A few do; the old arrangement stays supported for them | Ask |
| Are identifiers visible outside the system? | Yes; changing them is a breaking change to manage | Ask |
| Team size and timeline? | Not assumed; no duration given until answered | Ask |
| Are all instances on the same version and schema? | Same code, small drift; converged in the first phase | Assume, then audit |
| Can each customer accept a short scheduled window? | Yes, about 30 minutes | Assume |
| Size of the largest relative to the rest? | One or two far larger; migrated last | Assume |

### Non-software project

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What is it for? | A stated mix | Ask, first |
| Total budget or per-person figure? | Not set; a percentage split is given and the user supplies the total | Ask |
| Where are the people based? | Mostly one place, a few travelling | Ask |
| Are the dates fixed or flexible? | A concrete window with the date written out | Ask |
| Who decides, and who does the work? | One sponsor, one organiser with a helper | Assume |
| Constraints (policy, access, people who cannot attend overnight)? | Standard policy; needs collected at registration | Assume |
| Preferences people rarely volunteer (for example sharing rooms)? | The option most people prefer; ask in the registration form | Assume |

### Trivial change

No questions. One offer for anything deliberately left alone, with the default of leaving it.
