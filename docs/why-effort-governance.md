# Stop running your coding agents at one fixed effort

*Why per-task effort governance matters — and the honest version of what's
actually worth building.*

---

Your coding agent probably runs at a single reasoning effort. Pick a high one and
you burn budget and latency on "rename this variable." Pick a low one and the
agent under-thinks a tricky migration and ships something subtly wrong. And in
both cases you have **no idea how hard it decided to think** — there's no dial,
no readout.

That's the problem [`effort-governor`](https://github.com/CodeNoLimits/effort-governor)
addresses. But before the pitch, two honest caveats — because the space is full
of overclaiming, and the honest version is more useful.

## The trick that doesn't work

The obvious idea: write a hook that, when your prompt looks complex, injects a
keyword like `ultrathink` to bump the model's thinking budget.

It doesn't work. In tools like Claude Code, the thinking-keyword detector runs on
**your typed text, before hooks fire**. A keyword a hook injects afterward is
simply ignored. If you build an "effort selector" on that premise, you've built
a placebo.

## The thing the providers already do

Here's the part most "LLM routing" projects won't tell you: **the model
providers now do complexity-based effort allocation natively, server-side.**

- **Anthropic — Adaptive Thinking**: the model *"evaluates the complexity of each
  request and decides how much to think."*
- **OpenAI — `reasoning_effort`**: `low` / `medium` / `high` per request.
- **Gemini — dynamic `thinking_budget`** (`-1`): the API *"automatically assesses
  the complexity of each request."*

So "classify the prompt, then think harder on hard ones" is, increasingly, a
first-party feature. A standalone tool that only re-implements that — with a text
directive, which is strictly weaker than calling the native parameter — isn't
worth much. Said plainly: **routing-by-difficulty is becoming a commodity.**

## So what's actually left to build?

The gap the providers *don't* fill: **a consistent, visible effort policy across
all the surfaces you actually work in.** Native params live inside one API. But a
working developer drives several agents — Claude Code in one terminal, Grok in a
tmux pane, a couple of homemade scripts hitting different providers. Each has its
own effort story, none of them shows you anything, and there's no shared policy.

`effort-governor` is that thin layer:

- **One engine, one policy.** Keyword/threshold/directive constants live in a
  single file. The Claude Code hook, the Grok prefix, and your API calls all read
  the same logic — so "what counts as a HIGH task" is consistent everywhere.
- **Visible.** Every turn surfaces the level it chose:
  `▲ EFFORT ⟶ HIGH · keyword: optimize`. You can finally *see* the dial.
- **Wired to the real knob.** It maps each level to the provider's native
  parameter (`reasoning_effort`, `thinking.budget_tokens`, `thinking_budget`),
  so for code you control it's a real budget lever, not a cosmetic badge.
- **Logged.** Every decision is written to a log you can grep and tune against.
- **Fails open.** The Claude Code hook runs on every prompt; on any error it
  exits silently and never blocks your input.

Four levels — `LOW / MEDIUM / HIGH / MAX` — with an intentional **upward bias**:
when unsure it picks the higher effort, because over-thinking a hard task is
cheaper than shipping a wrong answer to one.

## Honest limitations

- Classification is per-message and heuristic. A one-word "yes" confirming a huge
  task reads as `MEDIUM` — it has no conversation memory.
- The visible badge depends on the agent obeying the injected display
  instruction (re-injected every turn, so reliable in practice — not a UI
  guarantee).
- It governs *engagement, visibility and consistency*. It only moves the real
  token budget where you wire it to a native parameter yourself.

That's the whole, honest scope. It's a small, Apache-2.0 convenience layer — not
a routing breakthrough, and it doesn't pretend to be one.

## Try it

```bash
git clone https://github.com/CodeNoLimits/effort-governor
echo "why is the deploy failing, debug it" | bin/effort-select --badge
#  ★ EFFORT ⟶ MAX  ·  multiple signals
```

---

*Built by **[DreamNova](https://dreamnova-agents.vercel.app)**. We engineer and
govern AI-agent workflows for teams — cheaper, observable, predictable. If you're
running coding agents in production and want help,
**[book a call →](https://dreamnova-agents.vercel.app)**.*
