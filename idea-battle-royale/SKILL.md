---
name: idea-battle-royale
description: Makes Claude think autonomously by pitting several radically different versions of itself against each other in an elimination tournament of ideas, then fusing the winner with the best loot from the losers into one super idea. Shows the fight live in the chat as an animated arena that updates phase by phase. Use when the user wants the best possible idea, strategy, design, name, plan or solution rather than the first one that comes to mind, or types /battle-royale.
---

# Idea Battle Royale

A self-contained tournament where Claude fights itself. Several "fighters" — each a version of Claude locked into a different way of thinking — propose competing ideas for the same problem. The ideas are attacked by a red team and by each other, scored blind, eliminated, mutated, and the survivors steal the best parts of the fallen. The last idea standing is fused with the best loot into a **super idea**, stress-tested, and presented with the full fight log.

The user watches it happen: an animated **live arena** opens in the chat as soon as the request arrives and updates at every phase, ending with a winner reveal and a full visual report.

The point is to escape the first plausible answer. A single pass of thinking converges early; a tournament forces real divergence, honest criticism and deliberate recombination.

## When to Use This Skill

- The user wants "the best idea", not "an idea": product concepts, business strategy, feature design, architecture choices, names, marketing angles, story plots, research directions
- A decision has several credible options and the user wants them fought out
- The user is stuck and wants Claude to think on its own and come back with a recommendation
- The user types `/battle-royale <problem>` or asks for a "battle royale", "tournament" or "fight" of ideas

Do not use it for questions with a single factual answer, or for trivial choices where the tournament would cost more than it gives.

## What This Skill Does

1. **Builds the arena**: restates the problem, reframes it three ways, surfaces hidden assumptions (and checks them when it can), and locks a weighted scoring rubric before any idea exists
2. **Drops in the fighters**: 6 versions of Claude, each forced into a distinct thinking style; each runs its own mini-tournament of 3 candidates and pitches only its best
3. **Runs the attack**: a red team and rival fighters strike each idea, blind scoring, bottom half eliminated
4. **Loots and mutates**: survivors absorb the strongest pieces of eliminated ideas, try mutations, and one fallen idea can make a comeback
5. **Holds the final duel**: the last two ideas steelman each other, then go head to head
6. **Fuses the super idea**: champion + best loot, a pre-mortem, a fresh-eyes check and a confidence level
7. **Delivers a verdict**: one clear recommendation, why it won, what would change the decision, and the first concrete steps
8. **Shows it all live**: an animated arena in the chat that updates at every phase, then the full visual report (charts, eliminations, duel, trophy reveal, replay button)

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
| `--quick` | 4 fighters, no mutation round, short log. For smaller decisions |
| `--deep` | 8 fighters, an extra attack → loot → mutate round, and — when a subagent tool (Agent/Task) is available — each fighter runs as its own parallel subagent so the ideas are truly independent |
| `--silent` | Show only the final verdict in text (the live arena is still shown) |
| `--text` | No live arena or visual report: plain text output only |
| `--criteria "a, b, c"` | Use the user's own scoring criteria instead of inferring them |

## The Live Arena (the animation in the chat)

Unless `--text` is set, the tournament is shown live. The template is `assets/arena.html` in this skill's folder. It renders from JSON blocks and has two modes:

- **Live mode** (stage 1 to 6): a sticky "LIVE" banner with a blinking dot, fencing animation and phase progress bar; every finished phase is shown; the phase being worked on appears as an animated "thinking" card with clashing fencers
- **Final mode** (stage 7): an "And the winner is…" trophy splash, then the full report revealed with animations — fighters dropping in, red "OUT" stamps, score bars, mutations, VS duel, confetti for the super idea, score-by-criterion chart, final ranking, pre-mortem, first moves — and a "Replay the battle" button that plays the full loading animation

It works on phones, in light and dark mode, and respects reduced-motion settings.

### How the data works

Data lives in `<script type="application/json" class="battle-step">` blocks placed just before the `<!--NEXT-STEP-->` marker. The page merges all blocks in order: objects are deep-merged, arrays of objects that carry an `id` are merged item by item (so a later block can add a score to fighter `f3` by sending `{"id": "f3", "score": 7.6}`), other arrays are replaced. The highest `"stage"` value decides the mode.

### How to run it on claude.ai and the Claude apps

1. **Before any long thinking**, read `assets/arena.html` and create an HTML artifact from it: copy the file exactly, except replace the example JSON block (the whole `<script type="application/json" class="battle-step">…</script>` element above `<!--NEXT-STEP-->`) with a stage 1 block. The user sees the arena open in the chat immediately.
2. **After each phase**, update the artifact by replacing the marker `<!--NEXT-STEP-->` with a new block followed by the marker again:
   ```
   <script type="application/json" class="battle-step">
   {"stage": 3, "fighters": [{"id": "f1", "score": 6.9, "strike": "...", "strikeBy": "Red team", "rebuttal": "...", "eliminated": null}]}
   </script>
   <!--NEXT-STEP-->
   ```
   Each block carries only what is new in that phase. This keeps every update small and exact.
3. If artifacts cannot be updated in place, skip the live updates and create the artifact once at the end, with a single block containing all the data and `"stage": 7`.

### How to run it in Claude Code (or anywhere without artifacts)

Write the file to `battle-royale-<short-slug>.html` in the working directory at the start, give the user the path once, and insert a new block before the marker with the Edit tool after each phase. The user can refresh the page to follow along.

### Data per stage

| Stage | Phase | Fields to send |
|---|---|---|
| 1 | Arena | `lang`, `title`, `problem`, `constraints[]`, `reframes:[{label, text}]`, `assumptions:[{text, status: "verified" \| "assumed"}]`, `rubric:[{name, weight}]` |
| 2 | Drop | `fighters:[{id, archetype, emoji, idea, pitch}]` |
| 3 | Attack | `fighters:[{id, strike, strikeBy, rebuttal, score, eliminated, lossReason, loot}]` — `eliminated` is the round number it fell in, or `null` |
| 4 | Looting | `looting:[{to, from, loot, result}]`, `mutations:[{on, mutation, kept, why}]`, `fighters:[{id, scoreV2}]`, and `{id, revived: true, eliminated: null}` for a comeback |
| 5 | Duel | `duel:{a, scoreA, b, scoreB, champion, reason}` |
| 6 | Fusion | `superIdea:{name, oneLiner, howItWorks[], whyWon, scores:[{name, value, champion}], score, championScore, premortem:[{risk, safeguard}], confidence: "low" \| "medium" \| "high", changeMind}` |
| 7 | Verdict | `superIdea:{firstMoves:[{when, what}]}`, `runnerUp:{name, when}` |

Rules: `"lang"` is the user's language code (`"fr"` and `"en"` have built-in interface labels, others fall back to English) and all content is written in the user's language. JSON must be valid: escape double quotes inside strings, no trailing commas, no comments. Scores are numbers out of 10. Fighter ids are `f1`, `f2`, … in drop order.

The animation is the show, not the work: do the real thinking for each phase first, then write its block.

## The Tournament

Follow these phases in order. Think autonomously: do not stop to ask the user questions mid-fight. If the problem is ambiguous, state the assumption you are making in Phase 1 and carry on. Only ask before starting if the problem is so vague that any answer would be a guess (for example, `/battle-royale` with no topic).

Between artifact updates, write one compact progress line in the chat, so even the text moves:

```
⚔️ Phase 3/7 · The Attack ▰▰▰▰▱▱▱▱▱▱
🔄 Newsletter first   ▰▰▰▰▰▰▰▰▱▱ 7.6
🛠️ Reddit & FB        ▰▰▰▰▰▰▰▱▱▱ 6.9
✂️ 100 DMs            ▰▰▰▰▰▰▱▱▱▱ 6.2 ❌
```

Translate the labels into the user's language.

### Phase 1 — The Arena

Write down, briefly:

- **The problem**, in one sentence, as you understand it
- **Constraints** (budget, time, skills, audience, tech) — stated by the user or reasonably assumed, marked as assumptions
- **Three reframes** — the best ideas often come from asking a better question:
  - *Zoom out*: what is the real goal behind the request?
  - *Zoom in*: what is the narrowest bottleneck?
  - *Invert*: what would guarantee failure?
  Fighters may attack the original problem or any reframe, but every idea must still answer what the user asked.
- **Hidden assumptions**: the 2 or 3 beliefs everything rests on. If a web search tool is available and an assumption is checkable (a market, a price, a rule, a competitor), check it and mark it verified or assumed. Never present an unchecked fact as verified.
- **The rubric**: 4 to 5 criteria with weights adding up to 100%. Pick criteria that fit the problem. A good default:
  - Impact (how much it solves the real problem) — 30%
  - Feasibility (can the user actually do it with what they have) — 25%
  - Originality (does it beat the obvious answer) — 15%
  - Speed to first result — 15%
  - Risk (inverted: lower risk scores higher) — 15%

The rubric is locked once written. Never change it later to help an idea win.

### Phase 2 — The Drop

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

**Inner tournament:** each fighter first sketches 3 candidate ideas in its own style, privately, and pitches only the strongest. This is cheap and lifts the floor of every pitch.

Each fighter writes a pitch:

- **Name of the idea** (short and memorable)
- **The idea** in 2 to 3 sentences
- **Why it wins** (its strongest argument)
- **First move** (the very first concrete action)

**Specificity rule:** a pitch must be concrete enough to start tomorrow. "Leverage social media" is not an idea; "post a free weekly plan in three named communities" is.

**Diversity rule:** before moving on, compare the pitches. If two ideas are basically the same approach with different words, the weaker one must re-pitch something genuinely different. Collapse into sameness is the main failure mode of this skill; guard against it.

**Independence (with `--deep`):** if a subagent tool is available, launch one subagent per fighter in parallel, giving each only the arena (problem, reframes, constraints) and its archetype — not the other pitches. Collect the pitches, then run the rest of the tournament yourself. Without subagents, write each pitch as if the others did not exist.

### Phase 3 — The Attack

For each idea:

- **Strike**: the single most damaging objection — the real reason it would fail. It comes either from the **red team** (Claude as a ruthless critic with no stake in any fighter) or from the **rival** whose idea it threatens most, whichever hits harder. Name the attacker in `strikeBy`.
- **Rebuttal**: the fighter gets one answer — it may defend, or patch the idea
- **Score**: the judge scores the idea, after the rebuttal, on each rubric criterion from 1 to 10, then computes the weighted total out of 10

**Judging rules:**
- **Blind**: judge the idea by its content, not by which archetype proposed it
- **Justified**: every criterion score has a one-clause reason (keep it in your reasoning; show it when it decides an elimination)
- **Spread**: use the whole scale. If all totals fall within one point, re-rank by pairwise comparison (which of these two would you bet on?) and rescore
- A patch in the rebuttal counts only if it really fixes the objection
- No favoritism toward the "safe" fighter or the "flashy" one; ties are broken by the highest-weighted criterion

**Elimination:** the bottom half is eliminated (round down, keep at least 2 survivors). Each eliminated fighter gets one line: why it lost.

### Phase 4 — The Looting

Before dying, each eliminated idea drops its **best piece of loot**: the single element worth keeping (an insight, a mechanism, a channel, a framing). Each survivor may grab at most one or two pieces of loot that genuinely strengthen it, and rewrites its pitch as an evolved version (v2).

**Mutation:** each survivor tries one mutation — push it to the extreme, combine it with its opposite, or aim it at a different audience. Keep the mutation only if it raises the score; log it either way.

**Comeback:** the best eliminated idea, enriched with loot, may return once if its new score beats the weakest survivor. At most one comeback per tournament.

Survivors are re-attacked once and re-scored (`scoreV2`). With `--deep`, repeat attack → loot → mutate for one more round before the final. With `--quick`, skip mutation and comeback.

### Phase 5 — The Final Duel

The top 2 face off directly:

- **Steelman first**: each finalist states the strongest point of the other, in one sentence
- Each then argues in one paragraph why it still wins, specifically
- The judge picks a **champion** and explains the deciding factor in one or two sentences
- If the scores are within 0.3 points, consider whether the two ideas combine into something better than either; if so, merge them and say so

### Phase 6 — The Fusion

Forge the **super idea**: the champion, upgraded with the best remaining loot from everyone (including the finalist that lost). It must still be one coherent idea, not a list of everything. Cut anything that dilutes it.

Then:

- **Pre-mortem**: "It is six months later and the super idea failed. Why?" List the 3 most likely causes and, for each, a concrete safeguard. Fold critical safeguards back into the idea.
- **Score** the super idea on the rubric. It should beat the champion; if it doesn't, the fusion added noise — strip it back to the champion plus only the loot that raised the score.
- **Fresh-eyes check**: re-read it as a judge who saw none of the fight. Is it clear in one read? Can this user start it this week with what they have? Is it clearly better than the runner-up? Fix whatever fails.
- **Confidence**: low, medium or high, with the reason — and the one signal that should make the user switch to the runner-up (`changeMind`).

### Phase 7 — The Verdict

Present the result to the user, in the user's language: the super idea, why it won, the confidence and what would change the decision, the first 3 moves, and the runner-up.

## Output Format

Order in the chat: the live arena (created first, updated each phase) with one progress line between updates, then the text verdict below. Unless `--silent` is set, also include the compact fight log. Keep everything scannable: tables and one-liners, not essays. With `--text`, the text log is the whole output.

```markdown
# Idea Battle Royale: [problem in a few words]

**Problem:** ... · **Reframed as:** ... · **Rubric:** Impact 30% · Feasibility 25% · ...

| Fighter | Idea | Strike (by) | Score |
|---|---|---|---|
| 🛠️ Pragmatist | [Name] | ... (Red team) | 6.9 |
| ... |

**Eliminated:** [Idea] — why · [Idea] — why
**Looting & mutations:** [Survivor] grabs "[loot]" from [fallen] · mutation "[…]" kept/dropped
**Final duel:** [A] (8.1) vs [B] (6.9) — Champion: [A], because ...

---

## 🏆 The Super Idea: [Name]

**In one sentence:** ...

**How it works:**
1. ...
2. ...
3. ...

**Why it won:** ... (and what it took from the fallen)

**Pre-mortem:** risk → safeguard · risk → safeguard · risk → safeguard

**Score:** 8.6/10 (champion alone: 8.1) · **Confidence:** high — ...
**What would change my mind:** ...

**Your first 3 moves:**
1. Today: ...
2. This week: ...
3. This month: ...

**Runner-up worth remembering:** [Idea] — when it would be the better choice
```

## Example

**User**: `/battle-royale --quick How do I get my first 100 users for my meal-planning app?`

**What happens:**

1. The live arena opens in the chat: "🔴 LIVE · Phase 1/7 · The Arena", with the problem, three reframes ("the real goal is a repeatable channel, not 100 users") and the rubric. A fencing animation shows that the Drop is being prepared.
2. Four fighters land: Pragmatist (Reddit & FB groups), Visionary (grocery chain partnership), Contrarian (newsletter first), Minimalist (100 personal DMs).
3. The attack: the Minimalist strikes the grocery partnership ("no leverage at 0 users", 4.1), the red team strikes the newsletter ("two products to maintain", patched: "generated from the app's own data", 7.6). Two red "OUT" stamps fall.
4. The newsletter loots "personal onboarding" from the DMs idea (8.1); a mutation into a live Sunday cook-along is dropped (too much founder time).
5. Final duel: newsletter 8.1 vs Reddit 6.9 — the newsletter compounds every week while Reddit effort resets daily.
6. Trophy splash: **"The Sunday Plan"** — a free Sunday email with a ready-to-cook weekly plan built from the app, shared in meal-prep communities. 8.6/10, confidence high; switch to the runner-up if fewer than 20% open the first 3 emails.
7. First moves: write the first Sunday Plan today, share it in 3 communities this week, reply personally to every subscriber this month.

## Tips

- Give constraints up front ("solo", "no budget", "must ship in 2 weeks") — they make the judging sharper
- Use `--criteria` when you know what matters most to you; the default rubric is generic
- Use `--deep` for big decisions; the independent subagent fighters produce noticeably more diverse ideas
- On a phone, open the arena card in the chat to watch the battle full screen; tap Replay at the end to watch it again
- If you dislike the winner, say why — Claude can rerun the tournament with that as a new constraint, and the runner-up may take the crown
- The log is the value too: the eliminated ideas and their loot often contain the second-best move

## Common Use Cases

- Choosing a product or startup idea among several directions
- Finding a growth or marketing strategy on a tight budget
- Designing a feature, an architecture or a technical approach
- Naming a product, brand, project or event
- Writing: plot twists, article angles, talk titles
- Personal decisions with several credible paths (career moves, learning plans)
