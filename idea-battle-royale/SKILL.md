---
name: idea-battle-royale
description: Makes Claude think autonomously by pitting several radically different versions of itself against each other in an elimination tournament of ideas, then fusing the winner with the best loot from the losers into one super idea. Use when the user wants the best possible idea, strategy, design, name, plan or solution rather than the first one that comes to mind, or types /battle-royale.
---

# Idea Battle Royale

A self-contained tournament where Claude fights itself. Several "fighters" — each a version of Claude locked into a different way of thinking — propose competing ideas for the same problem. The ideas are attacked, scored, eliminated round by round, and the survivors steal the best parts of the fallen. The last idea standing is fused with the best loot into a **super idea**, stress-tested, and presented to the user with the full fight log.

The point is to escape the first plausible answer. A single pass of thinking converges early; a tournament forces real divergence, honest criticism and deliberate recombination.

## When to Use This Skill

- The user wants "the best idea", not "an idea": product concepts, business strategy, feature design, architecture choices, names, marketing angles, story plots, research directions
- A decision has several credible options and the user wants them fought out
- The user is stuck and wants Claude to think on its own and come back with a recommendation
- The user types `/battle-royale <problem>` or asks for a "battle royale", "tournament" or "fight" of ideas

Do not use it for questions with a single factual answer, or for trivial choices where the tournament would cost more than it gives.

## What This Skill Does

1. **Builds the arena**: restates the problem, pins down constraints and defines a weighted scoring rubric before any idea exists, so the judging can't be rigged afterwards
2. **Drops in the fighters**: 6 versions of Claude, each forced into a distinct thinking style, each pitching one idea independently
3. **Runs elimination rounds**: red-team attacks, honest scoring, bottom fighters eliminated
4. **Allows looting**: survivors absorb the strongest pieces of eliminated ideas and evolve
5. **Holds the final duel**: the last two ideas go head to head
6. **Fuses the super idea**: champion + best loot, then a pre-mortem stress test
7. **Delivers a verdict**: one clear recommendation, why it won, its risks, and the first concrete steps

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
| `--quick` | 4 fighters, 1 elimination round, short log. For smaller decisions |
| `--deep` | 8 fighters, an extra evolution round, and — when a subagent tool (Agent/Task) is available — each fighter runs as its own parallel subagent so the ideas are truly independent |
| `--silent` | Show only the final verdict, not the fight log |
| `--criteria "a, b, c"` | Use the user's own scoring criteria instead of inferring them |

## The Tournament

Follow these phases in order. Think autonomously: do not stop to ask the user questions mid-fight. If the problem is ambiguous, state the assumption you are making in Phase 0 and carry on. Only ask before starting if the problem is so vague that any answer would be a guess (for example, `/battle-royale` with no topic).

### Phase 0 — The Arena

Write down, briefly:

- **The problem**, in one sentence, as you understand it
- **Constraints** (budget, time, skills, audience, tech) — stated by the user or reasonably assumed, marked as assumptions
- **The rubric**: 4 to 5 criteria with weights adding up to 100%. Pick criteria that fit the problem. A good default:
  - Impact (how much it solves the real problem) — 30%
  - Feasibility (can the user actually do it with what they have) — 25%
  - Originality (does it beat the obvious answer) — 15%
  - Speed to first result — 15%
  - Risk (inverted: lower risk scores higher) — 15%

The rubric is locked once written. Never change it later to help an idea win.

### Phase 1 — The Drop

Spawn the fighters. Each one is Claude thinking under a strict personality. Use these archetypes, in this order, taking the first N for the chosen fighter count:

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
- **First move** (the very first concrete action)

**Diversity rule:** before moving on, compare the pitches. If two ideas are basically the same approach with different words, the weaker one must re-pitch something genuinely different. Collapse into sameness is the main failure mode of this skill; guard against it.

**Independence (with `--deep`):** if a subagent tool is available, launch one subagent per fighter in parallel, giving each only the arena (problem, constraints) and its archetype — not the other pitches. Collect the pitches, then run the rest of the tournament yourself. Without subagents, write each pitch as if the others did not exist.

### Phase 2 — Round 1: The Attack

For each idea:

- The **red team** (Claude as a ruthless critic with no stake in any fighter) writes the single most damaging objection: the real reason this would fail
- The fighter gets **one rebuttal** — it may defend, or patch the idea
- The **judge** scores the idea, after the rebuttal, on each rubric criterion from 1 to 10, then computes the weighted total out of 10

**Judging rules:**
- Score against the rubric, not against your taste
- No favoritism toward the "safe" fighter or the "flashy" one
- A patch in the rebuttal counts only if it really fixes the objection
- Show scores in a table

**Elimination:** the bottom half is eliminated (round down, keep at least 2 survivors). Each eliminated fighter gets one line: why it lost.

### Phase 3 — The Looting

Before dying, each eliminated idea drops its **best piece of loot**: the single element worth keeping (an insight, a mechanism, a channel, a framing). Each survivor may grab at most one or two pieces of loot that genuinely strengthen it, and rewrites its pitch as an evolved version (v2).

Survivors are re-attacked once by the red team and re-scored. With `--deep`, repeat attack → loot → re-score for one more round before the final.

### Phase 4 — The Final Duel

The top 2 face off directly:

- Each argues in one paragraph why it beats the other, specifically
- The judge picks a **champion** and explains the deciding factor in one or two sentences
- If the scores are within 0.3 points, consider whether the two ideas combine into something better than either; if so, merge them and say so

### Phase 5 — The Fusion

Forge the **super idea**: the champion, upgraded with the best remaining loot from everyone (including the finalist that lost). It must still be one coherent idea, not a list of everything. Cut anything that dilutes it.

Then run a **pre-mortem**: "It is six months later and the super idea failed. Why?" List the 3 most likely causes and, for each, a concrete safeguard. Fold critical safeguards back into the idea.

Finally, score the super idea on the rubric. It should beat the champion; if it doesn't, the fusion added noise — strip it back to the champion plus only the loot that raised the score.

### Phase 6 — The Verdict

Present the result to the user. Reply in the user's language.

## Output Format

Unless `--silent` is set, show the fight log compactly, then the verdict. Keep the log scannable: tables and one-liners, not essays.

```markdown
# Idea Battle Royale: [problem in a few words]

## The Arena
**Problem:** ...
**Constraints:** ... (assumptions marked)
**Rubric:** Impact 30% · Feasibility 25% · Originality 15% · Speed 15% · Risk 15%

## The Drop — 6 fighters
| # | Fighter | Idea | In one line |
|---|---|---|---|
| 1 | Pragmatist | [Name] | ... |
| ... |

## Round 1 — The Attack
| Idea | Red team's strike | Rebuttal | Score /10 |
|---|---|---|---|
| ... |

**Eliminated:** [Idea] — why · [Idea] — why · [Idea] — why

## The Looting
- [Survivor] grabs "[loot]" from [fallen idea] → v2: ...

## The Final Duel
[Idea A] (7.8) vs [Idea B] (7.4) — **Champion: [Idea A]**, because ...

---

## 🏆 The Super Idea: [Name]

**In one sentence:** ...

**How it works:**
1. ...
2. ...
3. ...

**Why it won:** ... (and what it took from the fallen)

**Pre-mortem — how it could fail, and the safeguards:**
- Risk → safeguard
- Risk → safeguard
- Risk → safeguard

**Final score:** 8.6/10 (champion alone: 7.8)

**Your first 3 moves:**
1. Today: ...
2. This week: ...
3. This month: ...

**Runner-up worth remembering:** [Idea] — when it would be the better choice
```

## Example

**User**: `/battle-royale --quick How do I get my first 100 users for my meal-planning app?`

**Output** (abridged):

```markdown
# Idea Battle Royale: first 100 users for a meal-planning app

## The Arena
**Problem:** Acquire the first 100 active users with no marketing budget.
**Constraints:** Solo founder, ~5h/week, app already live (assumed: iOS + Android).
**Rubric:** Impact 30% · Feasibility 30% · Speed 25% · Originality 15%

## The Drop — 4 fighters
| # | Fighter | Idea | In one line |
|---|---|---|---|
| 1 | Pragmatist | Reddit & Facebook groups | Answer meal-prep questions daily, link the app when relevant |
| 2 | Visionary | Grocery chain partnership | Get the app featured in a supermarket's loyalty program |
| 3 | Contrarian | Don't market the app | Market a free weekly meal plan newsletter; the app is the upsell |
| 4 | Minimalist | 100 DMs | Personally onboard 100 people from your own network, one by one |

## Round 1 — The Attack
| Idea | Red team's strike | Rebuttal | Score |
|---|---|---|---|
| Reddit & FB groups | Self-promo gets banned fast | Lead with value, link only in profile | 6.9 |
| Grocery partnership | Months of sales cycles, no leverage at 0 users | — | 4.1 |
| Newsletter first | Two products to maintain | Newsletter is generated from the app's own data | 7.6 |
| 100 DMs | Friends aren't the target, churn later | Ask each for 2 referrals in the target group | 6.2 |

**Eliminated:** Grocery partnership — no leverage yet · 100 DMs — doesn't reach the real audience

## The Looting
- Newsletter grabs "personal onboarding" from 100 DMs → v2: every new subscriber gets a personal reply asking about their diet goal
- Reddit grabs nothing — the partnership's loot (retail credibility) doesn't fit yet

## The Final Duel
Newsletter v2 (8.1) vs Reddit (6.9) — **Champion: Newsletter v2**, because it compounds every week while Reddit effort resets daily.

---

## 🏆 The Super Idea: "The Sunday Plan"
**In one sentence:** A free Sunday email with a ready-to-cook weekly plan, built from the app, distributed through meal-prep communities, with one-click "cook this week in the app".
...
**Your first 3 moves:**
1. Today: write the first Sunday Plan using the app's own recipes
2. This week: share it as a free resource in 3 meal-prep communities (value first, no hard sell)
3. This month: reply personally to every subscriber and ask their goal
```

## Tips

- Give constraints up front ("solo", "no budget", "must ship in 2 weeks") — they make the judging sharper
- Use `--criteria` when you know what matters most to you; the default rubric is generic
- Use `--deep` for big decisions; the independent subagent fighters produce noticeably more diverse ideas
- If you dislike the winner, say why — Claude can rerun the tournament with that as a new constraint, and the runner-up may take the crown
- The log is the value too: the eliminated ideas and their loot often contain the second-best move

## Common Use Cases

- Choosing a product or startup idea among several directions
- Finding a growth or marketing strategy on a tight budget
- Designing a feature, an architecture or a technical approach
- Naming a product, brand, project or event
- Writing: plot twists, article angles, talk titles
- Personal decisions with several credible paths (career moves, learning plans)
