# Question bank by task type

Use this when filling part 3 of the output contract. The questions are the ones asked in the source traces. Most of them you would ask anyway; what this file adds is the form of the default and the filter that keeps the list short.

## Filter before you ask

Run each candidate through these in order. Stop at the first that applies.

1. **You can find the answer by looking** (repository, files, conversation). Look. Do not ask. If what you find contradicts or narrows the request, it is a premise fact and goes before the questions.
2. **The default is near-certain and a wrong guess is cheap.** Write it as a stated assumption in one line, not as a question. Example: "Assumed under a few thousand notes, so a full rebuild each time."
3. **The answer changes a detail only.** Take the default, state it, move on.
4. **The answer changes the structure of the plan, or a wrong guess does damage.** Ask it, with a default, and write the branch.

## The cap, and what it keeps

At most five questions. The cap removes detail questions. Fill it in this order, placing the first two kinds before anything else is considered:

1. **Driver**, when the answer changes scope.
2. **Tolerance**, when the answer selects the design.
3. **Harm or shrink.**
4. **Access and resources.**

If six questions pass the filter, the sixth becomes a stated assumption with its default. A driver or tolerance question that meets its condition keeps its place; the assumption is taken from the other kinds.

## Four kinds of question that earn their place

**Driver questions.** They ask why the request exists. Ask one as question 1 or 2 when the answer decides how far the work goes: which design, how much is migrated or deleted, where the work can stop. Write the branch beside it.

- "What is driving this (cost, speed, growth, new features)?" The answer chooses between a schema per customer and shared tables.
- "What prompted this?" The answer chooses between broad measurement and profiling the screens the user names.
- "What happened (which route, what rate, how many sources)?" The answer decides whether a per-IP limit covers the attack at all.

Test: sketch the plan for two different drivers. If the two differ in size or design, the question is in the top two.

**Tolerance questions.** They ask how much of a bad thing is acceptable: how stale, how slow, how long a pause, how much loss, how many legitimate requests blocked. The answer usually selects the mechanism, so take a default and write the branch.

- "What does 'zero downtime' allow?" Default: one hold of about 10 seconds. "If the answer is 'no pause at all', the cutover changes to application dual-writes."
- "Must a read after a write see it?" Default: yes, so reads stay on the old store until writes move.
- "What would count as good enough?" Default: targets proposed after the baseline.
- "Can consumers tolerate another night of bad data?" Default: no, so the guard goes in today.

Test: if two answers lead to two different mechanisms, it is a tolerance question and it is asked.

**Harm-or-shrink questions.** They ask about one fact that would make the default design harmful, or the plan much smaller.

- "Custom tool, or a thin setup around an existing generator?"
- "Do the warehouse staff share one office IP address?"
- "Is the load append-only, or can the vendor send corrections?"
- "Which tables have foreign keys to `users`, and which queries join to it or write to it inside a larger transaction?"
- "Are integer record IDs visible outside the app?"

- "From what client is this used (browser, phone, command line, another service)?" Ask it when the use walk in `gates-and-defaults.md` cannot be completed from what you read. Default: the most limited client.

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

"Ask" means it survived the filter in the traces. "Assume" means state it as an assumption unless the context makes it doubtful. Each table holds five "Ask" rows at most, in cap order (driver, tolerance, harm or shrink, access).

The rows come from one source task per type (a rate limit, a nightly load, a table migration, an offsite and so on). Take the kind of question, not its wording: for a webhook, "who are the legitimate callers" becomes "which senders, and do they retry"; for an export, "what is normal peak usage" becomes "how many rows in the largest export".

### Greenfield tool

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| Build this, or a thin setup around an existing tool? | Build, as requested: the build takes days and nothing in it is irreversible, so predicate (a) fails | Ask, first |
| What does the input look like (formats, dialects)? | The common format plus the one widespread extension; the rest left out of version 1 | Ask |
| Is everything meant to be public or published? | Published unless marked `draft` or `publish: false`; an ignore list is accepted | Ask: a wrong guess leaks data |
| Where will it be hosted or run? | The case that needs more handling (for example a base path), so both cases work | Ask |
| Language or runtime? | One mainstream choice; design unchanged for others | Assume |
| Extra features (search, tags)? | None in version 1 | Assume |
| How large is the input? | Small enough for a full rebuild | Assume |

### Brownfield feature

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What prompted this (an incident, a customer, a planned feature; for an attack: which route, what rate, how many sources)? | The simplest reading; say what the change does not cover if it was worse | Ask, first: driver |
| What sits between the client and the app (proxy, load balancer, CDN)? | The reading that fails safe, exposed as a setting, plus one check in the deployed environment | Ask |
| Who are the legitimate callers, and do they share an identity or address? | They may share one, so no strict limit where that would block them | Ask |
| What is normal peak usage? | Unknown; parameters are settings, labelled as guesses, with an observe-only stage before enforcement | Ask |
| Is adding the standard dependency acceptable? | Yes | Assume |
| Can the adjacent problem you found be fixed in the same change? | No; it goes in "Found, not touched" | Do not ask; list it |

### Incident

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| Who consumes the affected data, and can they tolerate another bad night? | Consumers exist and cannot; a guard goes in today, and they are told after cleanup | Ask, first: tolerance |
| What identifies a record uniquely? | A stable source ID; the first step tests this | Ask |
| Can the source legitimately send corrections? | No; if yes, the fix becomes update-on-conflict instead of skip | Ask: it changes the fix |
| What changed around the start date? | Unknown; a named step finds it | Ask |
| Are the raw inputs still retrievable, and for how long? | Yes; check retention before relying on it | Ask |
| Is there a constraint on that identifier today? | No | Assume, then check |
| Can I read production and the logs? | Yes; otherwise someone with access runs the first step | Assume |
| Can the job be paused today? | A guard yes; a pause only with the owner's go-ahead | Assume |

### Vague request ("make it faster", "make it better")

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What prompted this? | Complaints about specific parts, no measurements yet | Ask, first: driver |
| What would count as good enough? | Targets proposed after the baseline; none invented now | Ask: tolerance |
| Which part, and for whom? | Unknown; measure the most-used screens and endpoints, split by customer size | Ask |
| What is already measured? | Little; step 1 adds instrumentation | Assume, then check |
| Can I see the code and the monitoring? | No access assumed; first step is getting it | Ask |
| How much time is this worth, and what is off limits? | No rewrites, framework changes or infrastructure moves | Ask |
| What is the stack underneath? | Mainstream choices | Assume |

### High-risk migration

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| Is this piece moving alone, or first of many? | First of many, so tooling is reusable | Ask, first |
| What does "zero downtime" allow (a few seconds of held writes, none failing)? | Yes, once, about 10 seconds; if no, the cutover design changes | Ask: tolerance, it changes the cutover |
| What references, joins or shares a transaction with the thing being moved? | Several; they are decoupled first | Ask |
| Managed or self-hosted; is the change stream available? | Available; a preliminary phase checks it | Ask |
| What else writes to it? | A few jobs, all changeable; privileges revoked at cutover so a missed writer fails loudly | Assume, then check |
| Is there one data-access layer? | No; it is consolidated first | Assume |
| Must a read after a write see it? | Yes; reads stay on the old store until writes move | Ask: tolerance, it sets the read order |
| Write rate? | Measured in the preliminary phase | Assume |

### Large cross-cutting change

| Question | Default, as a plan action | Ask or assume |
|---|---|---|
| What is driving this (cost, speed, growth, new features)? | Set by SKILL.md step 3. When predicates (a) to (c) hold: the cheaper, reversible design, with the requested design as the branch. Otherwise: the requested design | Ask, first: driver |
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
