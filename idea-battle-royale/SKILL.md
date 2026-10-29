---
name: idea-battle-royale
description: Makes Claude think deeply and autonomously by pitting several radically different versions of itself against each other in an elimination tournament of ideas (reconnaissance, attacks, looting, a storm that tests the survivors, a final duel), then fusing the winner with the best loot from the losers into one super idea with its bets, safeguards and decision gate. Use when the user wants the best possible idea, strategy, design, name, plan or solution rather than the first one that comes to mind, or types /battle-royale.
---

# Idea Battle Royale

A self-contained tournament where Claude fights itself. Several "fighters", each a version of Claude locked into a different way of thinking, propose competing ideas for the same problem. The ideas are attacked, scored blind, eliminated round by round, and the survivors steal the best parts of the fallen. A storm then closes in on the survivors with a harsh real-world scenario. The last idea standing is fused with the best loot into a **super idea**, stress-tested, and presented with the full fight log.

The point is to escape the first plausible answer. A single pass of thinking converges early; a tournament forces real divergence, honest criticism, adversity and deliberate recombination.

## When to Use This Skill

- The user wants "the best idea", not "an idea": product concepts, business strategy, feature design, architecture choices, names, marketing angles, story plots, research directions
- A decision has several credible options and the user wants them fought out
- The user is stuck and wants Claude to think on its own and come back with a recommendation
- The user types `/battle-royale <problem>` or asks for a "battle royale", "tournament" or "fight" of ideas

Do not use it for questions with a single factual answer, or for trivial choices where the tournament would cost more than it gives.

## What This Skill Does

1. **Scouts the terrain**: digs under the question to find the real goal, the unknowns that could flip the answer, and the obvious answers everyone already gives
2. **Builds the arena**: constraints, dealbreakers, a weighted rubric with a fixed scoring scale, and The Bar to beat, all locked before any idea exists
3. **Drops in the fighters**: 6 versions of Claude, each forced into a distinct thinking style chosen for this problem, each pitching one idea and the bet it rests on
4. **Runs the attack**: two red-team strikes per idea, one rebuttal, blind scoring, the bottom half eliminated
5. **Allows looting**: survivors absorb the strongest pieces of eliminated ideas and evolve
6. **Sends the storm**: a harsh, realistic scenario hits the survivors; the ones that break are eliminated
7. **Holds the final duel**: each finalist must make the best case for its opponent before claiming the win
8. **Fuses the super idea**: champion + best loot, then a causal-chain check, a first-week walk-through, a pre-mortem, its bets and a decision gate
9. **Delivers a verdict**: one clear recommendation, why it won, how confident Claude is, and the first concrete moves

## How to Use

### Basic Usage

```
/battle-royale How can I get my first 100 users for my meal-planning app?
```

```
Run a battle royale of ideas on the best name for my bakery.
```

### Options

Options can be appended to the command or stated in plain words:

| Option | Effect |
|---|---|
| `--fighters N` | Number of fighters (3 to 10, default 6) |
| `--quick` | A lighter tournament for smaller decisions (see the depth table) |
| `--deep` | The heaviest tournament, for big decisions (see the depth table) |
| `--silent` | Show only the super idea and the verdict, not the fight log |
| `--visual` | Also render the tournament as a designed HTML page (see Visual Mode) |
| `--criteria "a, b, c"` | Use the user's own scoring criteria instead of inferring them |
| `--with "A \| B \| C"` | Enter the user's own options as fighters, so the tournament fights out the choices they already have alongside Claude's |

### Depth

| | `--quick` | Default | `--deep` |
|---|---|---|---|
| Fighters | 4 | 6 | 8 |
| Reconnaissance | Real goal + The Bar | Full | Full, and checks the unknowns with the tools available (files, web search) |
| Red-team strikes per idea | 1 | 2 | 2 |
| Storms | None | 1 | 2, with different scenarios |
| Independent subagents | No | No | One per fighter, plus a separate judge, when a subagent tool (Agent/Task) is available |
| Fusion checks | Pre-mortem | All | All |

## How to Think in This Tournament

The depth of this skill comes from the reasoning, not from the length of the log. These rules apply to every phase:

- **Reason fully, show compactly.** Work each phase out properly before writing its rows. The log is the summary of the thinking, never a first draft that gets rationalized afterwards
- **Specific beats general.** Every pitch, strike, piece of loot and move names something concrete: a channel, a number, a person, a date, a mechanism. "It might not work" or "there is competition" is not a strike; find the real reason
- **Follow consequences one step further.** For every idea, ask "and then what?" at least once. Many ideas look good at step one and fail at step two
- **Disagree with yourself.** If the fighters agree, someone is not doing their job. Ideas that look alike are a failure of the tournament, not a sign of a good answer
- **Update honestly.** When a strike lands, the score drops. Never protect a favorite, including the idea you liked first

Think autonomously: do not stop to ask the user questions mid-fight. If the problem is ambiguous, state the assumption you are making in the reconnaissance and carry on. Only ask before starting if the problem is so vague that any answer would be a guess (for example, `/battle-royale` with no topic).

## The Tournament

Follow these phases in order.

### Phase 0 — Reconnaissance

Before any idea exists, understand the terrain:

- **The ask**: the user's literal question, in one sentence
- **The real goal**: ask "why does the user want this?" up to three times, and write the chain in one line (for example: 100 users → enough people to see whether they stay → decide whether the app deserves more of my time). The fighters aim at the deepest goal that the user would recognize as theirs; the verdict must still answer the literal question
- **Reframes**: 2 or 3 other ways to pose the problem: bigger, smaller, or sideways. If one of them clearly matters more than the literal question, fight on it and say so in one line
- **The unknowns**: the 2 or 3 facts that would most change the answer. Check them when the material is at hand (files, the conversation, and with `--deep` a web search tool if one exists); otherwise state the assumption you are making
- **Known answers**: the 3 answers most people would give first. They are off-limits as pitches for the Visionary, the Contrarian, the Alchemist and the Wildcard, who must go beyond them, and the best of them becomes The Bar

### Phase 1 — The Arena

Write down, briefly:

- **The problem**, in one sentence, as the tournament will fight it
- **Constraints** (budget, time, skills, audience, tech): stated by the user or reasonably assumed, assumptions marked
- **Dealbreakers**: the hard constraints (illegal, over budget, needs skills the user doesn't have, breaks a stated requirement). An idea that hits a dealbreaker is eliminated on the spot, without scoring. Keep this list short; anything negotiable belongs in the rubric
- **The rubric**: 4 to 5 criteria with weights adding up to 100%. Pick criteria that fit the problem. A good default:
  - Impact (how much it solves the real goal) — 30%
  - Feasibility (can the user actually do it with what they have) — 25%
  - Originality (does it beat the known answers) — 15%
  - Speed to first result — 15%
  - Risk (inverted: lower risk scores higher) — 15%
- **The Bar**: the best of the known answers, scored on the rubric. It does not fight, but the super idea must clearly beat it. If the tournament can't beat the obvious answer, say so honestly; that is a useful result too

**Score calibration**, used by every judge for every criterion:

| Score | Meaning |
|---|---|
| 1–2 | Fails this criterion; would sink the idea on its own |
| 3–4 | Weak; a real problem that needs fixing |
| 5–6 | Acceptable; what a competent but ordinary idea gets |
| 7–8 | Strong; clearly better than the usual answer |
| 9–10 | Exceptional; rare, needs a specific reason |

The rubric and the calibration are locked once written. Never change them later to help an idea win.

### Phase 2 — The Drop

Spawn the fighters. Each one is Claude thinking under a strict personality. Pick the N archetypes from the list below:

- **Always include the Pragmatist and the Contrarian**: one anchors the tournament in reality, the other guarantees at least one idea that breaks the frame
- **Fill the other slots with the archetypes that fit the problem best**, and say in one line why you chose them. Rough guide:
  - Growth, marketing, business: Hacker, User's Advocate, Systems Thinker, Minimalist
  - Product and feature design: User's Advocate, Minimalist, Visionary, Alchemist
  - Technical and architecture choices: Minimalist, Skeptic, Systems Thinker, Visionary
  - Names, writing, creative work: Alchemist, Wildcard, Visionary, User's Advocate
  - Personal decisions: Skeptic, User's Advocate, Minimalist, Visionary

The archetypes:

1. **The Pragmatist** — the most reliable path with what exists today. Proven, boring, effective.
2. **The Visionary** — the 10x moonshot. Ignores current limits and asks what would make the problem disappear entirely.
3. **The Contrarian** — inverts the common wisdom. What if the obvious approach is exactly wrong?
4. **The Minimalist** — the smallest possible move that captures most of the value. Removes instead of adds.
5. **The Alchemist** — steals a solution from a completely unrelated field (biology, games, logistics, music, military history…) and transplants it.
6. **The User's Advocate** — starts from the end person's emotions, frustrations and habits, not from the solution.
7. **The Hacker** — finds a loophole, an unfair advantage, a shortcut others ignore (always legal and ethical).
8. **The Systems Thinker** — looks for the lever: the one change that sets off a chain reaction or a flywheel.
9. **The Skeptic** — proposes the idea that survives the worst case best.
10. **The Wildcard** — deliberately absurd at first glance, then made serious.

Each fighter writes a pitch:

- **Name of the idea** (short and memorable)
- **The idea** in 2 to 3 sentences
- **Why it wins** (its strongest argument)
- **The bet**: the one assumption that must be true for this idea to work
- **First move** (the very first concrete action)

For creative problems (names, titles, slogans, plots), adapt the pitch: the idea is the candidate itself plus two variants, "why it wins" is how it lands with the audience, the bet is what the audience must feel or understand, and "first move" becomes **how to test it** (say it out loud, check the domain and trademark, show it to five people).

**User's contenders (with `--with`):** each option the user gave enters as a fighter labeled "User's pick", counting toward N. Write its pitch in its strongest possible form: steelman it, never strawman it so Claude's ideas look better.

**Diversity rule:** before moving on, compare the pitches. Every idea must differ from every other on at least one of: the mechanism, the target person, the channel, or the time horizon. If two ideas fail that test, the weaker one re-pitches something genuinely different. Collapse into sameness is the main failure mode of this skill; guard against it.

**Independence (with `--deep`):** if a subagent tool is available, launch one subagent per fighter in parallel, giving each only the reconnaissance, the arena and its archetype, not the other pitches. Collect the pitches, then run the rest of the tournament yourself. Without subagents, write each pitch as if the others did not exist.

### Phase 3 — Round 1: The Attack

For each idea:

- The **red team** (Claude as a ruthless critic with no stake in any fighter) strikes twice (once with `--quick`):
  - **Fatal flaw**: the real reason this would fail
  - **Second-order effect**: what this idea causes later that hurts (cost that grows, audience it burns, door it closes)
- The **bet check**: the red team rates the fighter's bet as *plausible*, *uncertain* or *doubtful*, with a reason. A doubtful bet weighs on the Risk score
- The fighter gets **one rebuttal**: it may defend, or patch the idea
- The **judge** scores the idea, after the rebuttal, on each rubric criterion from 1 to 10 using the calibration table, then computes the weighted total out of 10

**Judging rules:**
- **Judge blind**: refer to the ideas by letter (A, B, C…) while scoring, not by archetype, so "the safe one" or "the flashy one" gets no bonus. Reveal the fighters after the scores are written
- Score against the rubric and the calibration, not against your taste
- A patch in the rebuttal counts only if it really fixes the strike
- **Check the spread**: if every total sits within 1.5 points of the others, the judge is being polite. Re-read the calibration and rescore; real ideas are not all "a 7"
- With `--deep` and a subagent tool, hand the judging to one separate subagent that sees only the arena, the rubric, the calibration and the anonymized pitches, strikes and rebuttals
- Show scores in a table, with the weakest criterion of each idea named

**Elimination:** the bottom half is eliminated (round down, keep at least 2 survivors). Ties are broken by Feasibility, then by Risk. Each eliminated fighter gets one line in the kill feed: why it lost.

### Phase 4 — The Looting

Before dying, each eliminated idea drops its **best piece of loot**: the single element worth keeping (an insight, a mechanism, a channel, a framing). Each survivor may grab at most one or two pieces of loot that genuinely strengthen it, and rewrites its pitch as an evolved version (v2). Loot that would turn an idea into a list of features stays on the ground.

With `--quick`, the survivors are re-scored after looting and the top 2 go straight to the final duel.

### Phase 5 — The Storm

The zone closes. Pick the **storm**: the harsh scenario most likely to hit this problem in real life. For example:

- The budget or the time available is cut in half
- The bet of the leading idea turns out to be false
- A competitor copies the idea the week after launch
- It works twice as well as planned: can it scale without breaking?
- The user's motivation drops after week two

Each survivor answers in one or two sentences: how it adapts. It either **bends** (adapts and keeps most of its value) or **breaks** (its core no longer works). Re-score every survivor under the storm. The lowest scorer is eliminated, keeping at least 2 for the final.

With `--deep`, a second storm hits with a different scenario.

### Phase 6 — The Final Duel

The top 2 face off directly:

- Each finalist first states the **strongest case for its opponent**, honestly, in one or two sentences
- Then it argues in one paragraph why it still wins, specifically
- The judge picks a **champion** and names the deciding factor in one or two sentences
- If the scores are within 0.3 points, consider whether the two ideas combine into something better than either; if so, merge them and say so

### Phase 7 — The Fusion

Forge the **super idea**: the champion, upgraded with the best remaining loot from everyone, including the finalist that lost. It must still be one coherent idea, not a list of everything. Cut anything that dilutes it.

Then put it through four checks, and fold what they reveal back into the idea:

1. **Causal chain**: write the chain from the first action to the real goal (action → effect → result) and check every arrow. The weakest arrow becomes a safeguard or a bet to test first
2. **First-week walk-through**: mentally run the first seven days of doing it, step by step, as the user with their real constraints. Whatever jams becomes a safeguard
3. **Pre-mortem**: "It is six months later and the super idea failed. Why?" List the 3 most likely causes and, for each, a concrete safeguard
4. **The bets**: the 2 or 3 assumptions the super idea rests on, riskiest first, each with the cheapest test that gives an answer within a week or two. The first move tests the riskiest bet

Then set a **decision gate**: a measurable signal, a threshold and a deadline that say "this is not working, switch to the runner-up" (for example: fewer than 30 subscribers after 3 issues).

Finally, score the super idea on the rubric. Every criterion that scores higher than the champion's must name the piece of loot or safeguard that earned the point; an increase with no reason is inflation, so drop it. The super idea should beat the champion; if it doesn't, the fusion added noise: strip it back to the champion plus only the loot that raised the score. Compare it with The Bar as well.

### Phase 8 — The Verdict

Before presenting, check:

- The super idea is one coherent idea, explainable in one sentence
- It answers the user's literal question, not only the reframed one
- It beats The Bar, or the verdict says plainly that it doesn't
- The first 3 moves are concrete enough to start today, not "do research", and the first one tests the riskiest bet
- No fighter crossed a dealbreaker or proposed anything illegal or unethical

Then present the result to the user. Reply in the user's language, and translate the headings and labels of the output format too.

## Output Format

The output is read on a screen, often a phone. Design it to scan:

- **Score bars**: every score is shown as a 10-cell bar followed by the number, in inline code so it lines up: `████████▌░ 8.6`. One `█` per whole point, one `▌` if the rest is 0.5 or more, then `░` up to 10 cells
- **Status markers**: 🏆 champion, 🥈 runner-up, 💀 eliminated, 🎁 loot, 🌪️ storm. Use them only to mark a status, never as decoration
- **Tables and one-liners**, not paragraphs. A cell holds one sentence at most
- **The verdict stands out**: a horizontal rule before it, the super idea's one-liner in a quote block, and the score comparison in a small code block so the bars align

Unless `--silent` is set, show the fight log, then the verdict. With `--quick`, drop the Reconnaissance and Storm sections and keep one strike per idea.

````markdown
# Idea Battle Royale: [problem in a few words]

**6 ideas → 3 → 2 → 🏆 1** · Default depth · Rubric locked before the drop

## Reconnaissance
| | |
|---|---|
| **You asked** | ... |
| **The real goal** | ... → ... → ... |
| **Unknowns** | ... *(assumed: ...)* |
| **Known answers** | ... · ... · ... |

## The Arena
| | |
|---|---|
| **Problem** | ... |
| **Constraints** | ... *(assumed)* |
| **Dealbreakers** | ... |
| **Rubric** | Impact 30 · Feasibility 25 · Originality 15 · Speed 15 · Risk 15 |
| **The Bar** | [best known answer] `█████▌░░░░ 5.6` |

## The Drop
| | Fighter | Idea | Pitch | The bet |
|---|---|---|---|---|
| A | Pragmatist | **[Name]** | ... | ... |
| B | ... | ... | ... | ... |

*Picked for this problem:* [archetypes] because ...

## Round 1 — The Attack
| | Idea | Fatal flaw | Second-order | Rebuttal | Score |
|---|---|---|---|---|---|
| A | [Name] | ... | ... | ... | `███████░░░ 7.2` |

💀 **[Idea]** — why it lost · 💀 **[Idea]** — why · 💀 **[Idea]** — why

## The Looting
- 🎁 **[Survivor]** takes "[loot]" from [fallen idea] → **v2:** ...

## 🌪️ The Storm — [scenario]
| Survivor | How it adapts | | Score |
|---|---|---|---|
| [Name] | ... | Bends | `███████▌░░ 7.9` |
| [Name] | ... | Breaks | `█████░░░░░ 5.2` |

💀 **[Idea]** — didn't survive the storm: why

## The Final Duel
| | [Idea A] `███████▌░░ 7.9` | [Idea B] `██████▌░░░ 6.5` |
|---|---|---|
| **Best case for the opponent** | ... | ... |
| **Why it still wins** | ... | ... |

**🏆 Champion: [Idea A]** — deciding factor: ...

---

## 🏆 The Super Idea: [Name]

> **In one sentence:** ...

**How it works**
1. ...
2. ...
3. ...

**Built from:** [champion] + 🎁 [loot] (from [idea]) + 🎁 [loot] (from [idea])

**Why it won:** ...

```
Super idea  ████████░░ 8.4
Champion    ███████▌░░ 7.9
The Bar     █████░░░░░ 5.4
```

**What it bets on**
| Bet | Cheapest test | Risk |
|---|---|---|
| ... | ... | High |

**Pre-mortem**
| How it could fail | Safeguard |
|---|---|
| ... | ... |

**Decision gate:** if [signal] is below [threshold] by [deadline], switch to [runner-up].

**Confidence:** High / Medium / Low — why

**What would change the verdict:** the one fact that, if true, would put the runner-up ahead

**Your first 3 moves**
1. **Today** (tests the riskiest bet): ...
2. **This week:** ...
3. **This month:** ...

**🥈 Runner-up worth remembering:** [Idea] — when it would be the better choice
````

## Visual Mode

With `--visual`, also render the tournament as a designed HTML page: a verdict-first fight card with the super idea on top, score bars drawn to scale, the fighter roster, the kill feed, the loot, the storm and the final duel.

1. Copy `assets/arena.html` from this skill's folder
2. Replace the JSON inside `<script type="application/json" id="battle-data">` with this tournament's data. The example data already in the file shows every field; keep the same shape. Fields that a mode skips (no storms with `--quick`, for example) can be left as empty lists
3. When the user's language is not English, fill the `labels` object with translated labels (the keys are listed in the file) and set `lang`
4. Set the `<title>` to a name for this tournament, two to four words (for example "Sunday Plan Battle")
5. Present it: as an artifact when the environment supports artifacts (if the artifact tool wraps pages in its own document, remove the `<!doctype>`, `<html>`, `<head>` and `<body>` tags and keep their contents), otherwise as a saved `.html` file the user can open in a browser

In visual mode, keep the chat answer short: the super idea section only, plus where to find the page.

## Example

**User**: `/battle-royale How do I get my first 100 users for my meal-planning app?`

**Output** (abridged):

````markdown
# Idea Battle Royale: first 100 users for a meal-planning app

**6 ideas → 3 → 2 → 🏆 1** · Default depth · Rubric locked before the drop

## Reconnaissance
| | |
|---|---|
| **You asked** | How do I get my first 100 users? |
| **The real goal** | 100 users → enough people to see whether they stay → decide whether the app deserves more of my time |
| **Unknowns** | Does the app keep people after week one? *(assumed: yes, retention is decent)* |
| **Known answers** | Launch on Product Hunt · Ask friends and family · Run ads |

## The Arena
| | |
|---|---|
| **Problem** | Reach 100 active users in 8 weeks with no marketing budget |
| **Constraints** | Solo founder · about 5h a week *(assumed)* · app live on iOS and Android *(assumed)* |
| **Dealbreakers** | Paid ads · more than 5h a week |
| **Rubric** | Impact 30 · Feasibility 30 · Speed 25 · Originality 15 |
| **The Bar** | Launch on Product Hunt `█████░░░░░ 5.4` |

## The Drop
| | Fighter | Idea | Pitch | The bet |
|---|---|---|---|---|
| A | Pragmatist | **Community Helper** | Answer meal-prep questions daily in Reddit and Facebook groups, app link in profile | Groups tolerate a helpful member with a link |
| B | Visionary | **Grocery Partner** | Get the app featured in a supermarket loyalty program | A chain would partner with a 0-user app |
| C | Contrarian | **The Sunday Plan** | Don't market the app: market a free weekly meal plan email; the app is the upsell | People subscribe to a free plan from an unknown sender |
| D | Minimalist | **100 DMs** | Personally onboard 100 people from your own network | Your network contains the target audience |
| E | User's Advocate | **Fridge Photo** | Aim at the 6pm "what's for dinner" panic: snap your fridge, get tonight's meal | The panic moment drives installs |
| F | Hacker | **Creator Swap** | Give food micro-creators free white-label plans built in the app | Creators share a free tool with their followers |

## Round 1 — The Attack
| | Idea | Fatal flaw | Second-order | Rebuttal | Score |
|---|---|---|---|---|---|
| C | The Sunday Plan | Two products to maintain | Builds an email list, not app users | The email is generated from the app's own recipes | `███████░░░ 7.4` |
| A | Community Helper | Self-promotion gets banned | Effort resets every day, nothing compounds | Value first, link only in profile | `██████▌░░░ 6.6` |
| E | Fridge Photo | Needs a photo feature first | — | Start with a manual version | `██████░░░░ 6.4` |
| D | 100 DMs | Friends aren't the target | Polite installs, early churn | Ask each for 2 referrals | `█████▌░░░░ 5.9` |
| F | Creator Swap | Creators want to be paid | Cold outreach at 0 users | — | `█████▌░░░░ 5.7` |
| B | Grocery Partner | Months of sales cycles | No leverage at 0 users | — | `████░░░░░░ 4.1` |

💀 **100 DMs** — doesn't reach the real audience · 💀 **Creator Swap** — no leverage yet · 💀 **Grocery Partner** — far too slow

## The Looting
- 🎁 **The Sunday Plan** takes "personal onboarding" from 100 DMs → **v2:** every new subscriber gets a personal reply asking about their diet goal
- 🎁 **Fridge Photo** takes "creators share results" from Creator Swap → **v2:** shareable "tonight's dinner" cards

## 🌪️ The Storm — your time drops to 2h a week
| Survivor | How it adapts | | Score |
|---|---|---|---|
| The Sunday Plan v2 | One issue a week, generated from the app in under an hour | Bends | `███████▌░░ 7.9` |
| Fridge Photo v2 | Ships a no-code version on top of the app's search | Bends | `██████▌░░░ 6.5` |
| Community Helper | Daily presence is no longer possible | Breaks | `█████░░░░░ 5.2` |

💀 **Community Helper** — can't survive without daily time

## The Final Duel
| | The Sunday Plan v2 `███████▌░░ 7.9` | Fridge Photo v2 `██████▌░░░ 6.5` |
|---|---|---|
| **Best case for the opponent** | The panic moment is more emotional and more shareable | The Sunday Plan compounds every week for one hour of work |
| **Why it still wins** | Testable this Sunday, no build needed | It hooks people at the moment they need the app most |

**🏆 Champion: The Sunday Plan v2** — deciding factor: it can be tested this week, while Fridge Photo needs a build before the first user sees it.

---

## 🏆 The Super Idea: The Sunday Plan

> **In one sentence:** a free Sunday email with a ready-to-cook weekly plan built from the app, shared in meal-prep communities, with a personal reply to every new subscriber and a "panic button" link for weeknight dinners.

**Built from:** The Sunday Plan + 🎁 personal onboarding (from 100 DMs) + 🎁 the 6pm panic moment (from Fridge Photo) + 🎁 value-first posting (from Community Helper)

```
Super idea  ████████░░ 8.4
Champion    ███████▌░░ 7.9
The Bar     █████░░░░░ 5.4
```

**What it bets on**
| Bet | Cheapest test | Risk |
|---|---|---|
| People subscribe to a free plan from an unknown sender | Post plan #1 in 3 communities, aim for 30 sign-ups in 7 days | High |
| Subscribers click through to the app | Count clicks on "cook this week in the app" in issue #2, aim for 20% | Medium |

**Decision gate:** fewer than 30 subscribers after 3 issues → switch to Fridge Photo as the hook.

**Confidence:** Medium — the format works in other niches; nobody knows yet whether this audience opens an email from an app maker.

**Your first 3 moves**
1. **Today** (tests the riskiest bet): write Sunday Plan #1 from the app's own recipes
2. **This week:** share it in 3 meal-prep communities, the full plan in the post, the link at the bottom
3. **This month:** reply personally to every subscriber and ask about their diet goal

**🥈 Runner-up worth remembering:** Fridge Photo — the better choice once the app has a photo feature and you have more than 2h a week
````

## Tips

- Give constraints up front ("solo", "no budget", "must ship in 2 weeks"): they make the dealbreakers and the storm sharper
- Use `--criteria` when you know what matters most to you; the default rubric is generic
- Use `--deep` for big decisions: independent subagent fighters produce noticeably more diverse ideas, and two storms test the winner harder
- Use `--with` when you are already torn between a few options: they fight Claude's ideas on equal terms, and you see exactly where each one breaks
- Use `--visual` when you want to share the result: the page reads well on a phone and shows the whole fight at a glance
- If you dislike the winner, say why: Claude can rerun the tournament with that as a new constraint or a new storm, and the runner-up may take the crown
- The log is the value too: the eliminated ideas and their loot often contain the second-best move

## Common Use Cases

- Choosing a product or startup idea among several directions
- Finding a growth or marketing strategy on a tight budget
- Designing a feature, an architecture or a technical approach
- Naming a product, brand, project or event
- Writing: plot twists, article angles, talk titles
- Personal decisions with several credible paths (career moves, learning plans)
