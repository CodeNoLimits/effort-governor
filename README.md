# effort-governor

**Dynamic, per-task reasoning-effort for coding agents.** One small engine that
reads each prompt, classifies its complexity (`LOW` / `MEDIUM` / `HIGH` / `MAX`),
injects a calibrated effort directive, and **shows you the level it picked** — the
same logic across Claude Code, Grok, or any agent.

```
· EFFORT ⟶ LOW     · keyword: thanks
◦ EFFORT ⟶ MEDIUM  · standard task
▲ EFFORT ⟶ HIGH    · keyword: optimize
★ EFFORT ⟶ MAX     · keyword: refactor
```

> Built by [DreamNova](https://github.com/CodeNoLimits). Apache-2.0.

---

## Why

Coding agents tend to run at one fixed reasoning effort. Set it high and you burn
budget/latency on "rename this variable"; set it low and the agent under-thinks a
gnarly migration. There's also **no visibility** — you can't see how hard the
agent decided to think.

`effort-governor` fixes both:

- **Per-task calibration** — each prompt gets a directive matched to its
  complexity (go-straight-to-the-point ⟶ plan-and-prove).
- **Visible** — the chosen level is surfaced on every turn.
- **One source of truth** — the keyword/threshold/directive constants live in
  **one file**; every agent adapter reads it, so behavior stays consistent.
- **Upward bias** — when in doubt it picks the *higher* effort. Over-thinking a
  hard task is cheaper than shipping a wrong answer to one.

## An honest note on "thinking budgets"

A tempting idea is to have a hook inject a keyword like `ultrathink` to bump the
model's thinking budget. **It doesn't work**: in tools like Claude Code the
thinking-keyword detector runs on *your typed text*, before hooks, so an injected
keyword is ignored. The real budget is a setting (`effortLevel`, `/effort`, the
native effort toggle, or your API `thinking`/`reasoning_effort` parameter).

So `effort-governor` does **not** claim to change the token budget per turn. It
**governs engagement** (how the agent approaches the task), makes the level
**visible**, and keeps the policy **consistent across agents** — and for agents
you fully control (CLI/API), you can wire the level straight to the real effort
parameter. That's the whole, honest pitch.

## How classification works

| Level | Triggered by (defaults) | Directive (gist) |
|-------|-------------------------|------------------|
| `· LOW` | `typo`, `rename`, `list`, `show`, `status`, greetings, short | answer directly, no over-engineering |
| `◦ MEDIUM` | anything not matched below | read before edit, brief verify |
| `▲ HIGH` | `debug`, `why`, `optimize`, `analyze`, `bug`, `deploy`, longer | deliberate, read sources, verify with proof |
| `★ MAX` | `architecture`, `refactor`, `migration`, `audit`, `security`, 3+ signals, very long | plan, decompose, quantified proof |

English + French keywords ship by default. Everything is overridable (below).

## Install

```bash
git clone https://github.com/CodeNoLimits/effort-governor ~/Projects/Active/effort-governor
```

### Try it

```bash
echo "why is the deploy failing, debug it" | bin/effort-select --badge
#  ★ EFFORT ⟶ MAX  ·  multiple signals (3)
bash examples/demo.sh
python3 tests/test_core.py
```

### Claude Code

Copy the hook reference and merge `adapters/claude_code/settings.snippet.json`
into `~/.claude/settings.json` (keep your existing hooks). The hook prints a
badge at the top of each reply and injects the directive. It fails *open* — on
any error it exits 0 and never blocks your input.

Disable anytime: `touch ~/.claude/auto_effort.OFF` · Log: `~/.claude/auto_effort.log`

### Grok / tmux (or any controller)

```bash
source adapters/grok_tmux/grok_effort_prefix.sh
task="refactor the auth module"
grok -p "$(effort_prefix "$task") $task"
```

### Any agent / API — wire to the *real* budget (v0.2)

Providers now expose native effort/thinking knobs. `effort-governor` maps each
level straight to them, so the decision stops being cosmetic:

```python
from effort_governor import evaluate
import anthropic

e = evaluate(user_prompt, provider="anthropic")
# e == {"level": "HIGH", "reason": "...", "directive": "...",
#       "badge": "...", "params": {"thinking": {"type": "enabled",
#                                                "budget_tokens": 16384}}}

anthropic.Anthropic().messages.create(
    model="claude-...", max_tokens=4096,
    messages=[{"role": "user", "content": user_prompt}],
    **e["params"],            # ← native thinking budget, chosen per task
)
```

Native parameter mapping (defaults — override via config; **verify against
current provider docs**, these evolve):

| Level | OpenAI `reasoning_effort` | Anthropic `thinking.budget_tokens` | Gemini `thinking_budget` |
|-------|---------------------------|------------------------------------|--------------------------|
| LOW   | `low` | off | `0` |
| MEDIUM| `medium` | `4096` | `4096` |
| HIGH  | `high` | `16384` | `16384` |
| MAX   | `high` | `32768` | `24576` |

CLI: `echo "refactor X" | bin/effort-select --params anthropic` →
`{"thinking": {"type": "enabled", "budget_tokens": 32768}}`

## Configure (no code edit)

Drop a JSON at `~/.config/effort-governor/config.json` (or point
`$EFFORT_GOVERNOR_CONFIG` at one). Any subset is merged over the defaults:

```json
{
  "high_kw": ["regression", "flaky"],
  "thresholds": { "high_len": 200 },
  "directives": { "MAX": "Plan, write a failing test first, then implement." }
}
```

## Limitations (read these)

- Classification is **per message**, heuristic and keyword-based. A one-word
  "yes" confirming a huge task reads as `MEDIUM` — it has no conversation memory.
- The badge depends on the agent obeying the injected display instruction
  (re-injected every turn, so reliable in practice — but not a UI guarantee).
- It governs *engagement and visibility*, not the underlying token budget,
  unless you wire the level to a real effort parameter yourself.

## License

Apache-2.0 © 2026 DreamNova (David Amor). See [LICENSE](./LICENSE).
