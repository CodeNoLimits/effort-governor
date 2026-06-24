#!/usr/bin/env python3
"""
Claude Code adapter — UserPromptSubmit hook.

Classifies each prompt and (1) injects a calibrated effort directive into the
model's context, (2) tells the model to print a visible badge at the top of its
reply (Claude Code does not render the hook `systemMessage` field in some
versions), (3) logs the decision.

SAFETY: runs on EVERY prompt. On any problem (package not found, bad input) it
exits 0 silently — it must NEVER block your input.

Install: see README. Set EFFORT_GOVERNOR_HOME if the repo lives elsewhere.
Disable: touch ~/.claude/auto_effort.OFF        Log: ~/.claude/auto_effort.log
"""
import sys, os, json
from datetime import datetime

HOME = os.path.expanduser("~")
OFF = os.path.join(HOME, ".claude", "auto_effort.OFF")
LOG = os.path.join(HOME, ".claude", "auto_effort.log")

# locate the package
for cand in (os.environ.get("EFFORT_GOVERNOR_HOME"),
             os.path.join(HOME, "Projects", "Active", "effort-governor"),
             os.path.join(HOME, "effort-governor")):
    if cand and os.path.isdir(os.path.join(cand, "effort_governor")):
        sys.path.insert(0, cand)
        break


def main():
    if os.path.exists(OFF):
        sys.exit(0)
    try:
        from effort_governor.core import classify, directive, badge
    except Exception:
        sys.exit(0)
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        sys.exit(0)
    try:
        level, reason = classify(prompt)
        b, d = badge(level, reason), directive(level)
    except Exception:
        sys.exit(0)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts} | {level:<6} | {reason:<24} | {prompt[:80]}\n")
    except Exception:
        pass
    context = (
        f"[EFFORT: {level}] {d}\n"
        f"→ DISPLAY: begin your reply with EXACTLY this line, then a blank "
        f"line (the systemMessage field is not rendered here, so you must "
        f"surface it):\n`{b}`"
    )
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                               "additionalContext": context},
        "systemMessage": b,
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
