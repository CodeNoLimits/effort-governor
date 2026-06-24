"""
effort_governor.core — single source of truth for dynamic, per-task effort.

Classifies a prompt into LOW / MEDIUM / HIGH / MAX and returns a calibrated
directive + a visible badge. Agent-agnostic: the same engine drives a Claude
Code hook, a Grok/tmux prefix, or any CLI/agent.

Bias is intentionally UPWARD (better to over-think a hard task than under-think).

Override the defaults without editing this file: drop a JSON at
$EFFORT_GOVERNOR_CONFIG (or ~/.config/effort-governor/config.json) with any of
the keys: max_kw, high_kw, low_kw, thresholds, directives.
"""
from __future__ import annotations
import json, os, unicodedata

# ──────────────────────────── DEFAULT CONSTANTS ────────────────────────────
# Keywords are matched accent-insensitively, lowercased. English + French ship
# by default — add your own language via the config override.
MAX_KW = [
    "architecture", "refactor", "refactoris", "migration", "migrate", "audit",
    "patent", "brevet", "security", "securit", "race condition", "root cause",
    "cause racine", "from scratch", "de zero", "production-grade", "prod-ready",
    "multi-agent", "multi agent", "exhaustive", "exhaustif", "deep dive",
    "deepdive", "the best possible", "le mieux possible", "a fond",
    "commercial", "commercialis", "valuation", "valoris", "do not get this wrong",
    "ne te trompe pas", "critical", "critique",
]
HIGH_KW = [
    "debug", "debogue", "why ", "pourquoi", "strategy", "strategie", "analyze",
    "analyse", "optimiz", "compare", "comparer", "trade-off", "tradeoff", "doesn't work",
    "not working", "marche pas", "fonctionne pas", "bug", "crash", "complex",
    "complexe", "plan", "planifie", "implement", "implemente", "diagnose",
    "diagnostiqu", "design", "concurrency", "concurrenc", "deploy", "deploie",
    "investigate", "investigat", "whole project", "tout le projet", "construis",
]
LOW_KW = [
    "typo", "rename", "renomme", "list ", "liste", "show ", "montre", "affiche",
    "what is", "c'est quoi", "cest quoi", "status", "statut", "quick", "merci",
    "thanks", "hi ", "hello", "salut", "bonjour", "read the", "lis le", "cat ",
    "open the", "ouvre le", "ok ", "yes ", "oui ", "no ", "non ",
]
THRESHOLDS = {
    "max_high_hits": 3, "max_len": 600, "max_qmarks": 4, "max_newlines": 12,
    "high_len": 280, "high_qmarks": 2, "high_newlines": 5, "low_len": 140,
}
DIRECTIVES = {
    "LOW": ("Trivial task. Answer/act directly and briefly. Use tools only if "
            "needed. No planning, no over-engineering, no sub-agents. Get to "
            "the point."),
    "MEDIUM": ("Standard task. Read the filesystem BEFORE editing. Briefly "
               "verify the result. No over-engineering or needless multi-agent."),
    "HIGH": ("Complex task. Deliberate carefully. Read the relevant files/"
             "sources BEFORE acting. Consider edge cases. Test/verify with "
             "evidence before claiming done — never say 'done' without proof."),
    "MAX": ("Critical / high-stakes task. Maximum rigor. Plan first, decompose, "
            "consider parallel sub-tasks. Verify everything with quantified "
            "proof; no claim without a test. Read the sources before strategy."),
}
ICON = {"LOW": "·", "MEDIUM": "◦", "HIGH": "▲", "MAX": "★"}

# Map each level to a provider's NATIVE effort/thinking parameter. This is what
# turns the badge from cosmetic into a real budget lever for API callers.
# ⚠️ Param names & accepted values evolve fast — verify against current provider
# docs. These are sensible defaults you can override via config ("effort_params").
EFFORT_PARAMS = {
    "openai": {  # reasoning models: reasoning_effort
        "LOW": {"reasoning_effort": "low"},
        "MEDIUM": {"reasoning_effort": "medium"},
        "HIGH": {"reasoning_effort": "high"},
        "MAX": {"reasoning_effort": "high"},
    },
    "anthropic": {  # extended thinking: thinking.budget_tokens (LOW = off)
        "LOW": {},
        "MEDIUM": {"thinking": {"type": "enabled", "budget_tokens": 4096}},
        "HIGH": {"thinking": {"type": "enabled", "budget_tokens": 16384}},
        "MAX": {"thinking": {"type": "enabled", "budget_tokens": 32768}},
    },
    "gemini": {  # thinking_config.thinking_budget (0 = off, -1 = dynamic)
        "LOW": {"thinking_budget": 0},
        "MEDIUM": {"thinking_budget": 4096},
        "HIGH": {"thinking_budget": 16384},
        "MAX": {"thinking_budget": 24576},
    },
}


def _load_config():
    path = os.environ.get("EFFORT_GOVERNOR_CONFIG") or os.path.expanduser(
        "~/.config/effort-governor/config.json")
    cfg = {"max_kw": MAX_KW, "high_kw": HIGH_KW, "low_kw": LOW_KW,
           "thresholds": dict(THRESHOLDS), "directives": dict(DIRECTIVES),
           "effort_params": {p: dict(v) for p, v in EFFORT_PARAMS.items()}}
    try:
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k in ("max_kw", "high_kw", "low_kw"):
            if k in user:
                cfg[k] = user[k]
        if "thresholds" in user:
            cfg["thresholds"].update(user["thresholds"])
        if "directives" in user:
            cfg["directives"].update(user["directives"])
        if "effort_params" in user:
            for prov, mapping in user["effort_params"].items():
                cfg["effort_params"].setdefault(prov, {}).update(mapping)
    except Exception:
        pass  # no config / unreadable -> defaults
    return cfg


def _strip(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def classify(prompt: str, cfg=None):
    """Return (level, reason)."""
    cfg = cfg or _load_config()
    t = cfg["thresholds"]
    raw = (prompt or "").strip()
    p = _strip(raw.lower())
    length, qmarks, newlines = len(raw), raw.count("?"), raw.count("\n")

    max_hits = [k for k in cfg["max_kw"] if k in p]
    high_hits = [k for k in cfg["high_kw"] if k in p]
    low_hits = [k for k in cfg["low_kw"] if k in p]

    if (max_hits or len(high_hits) >= t["max_high_hits"] or length > t["max_len"]
            or qmarks >= t["max_qmarks"] or newlines >= t["max_newlines"]):
        level = "MAX"
        if max_hits:
            reason = f"keyword: {max_hits[0]}"
        elif len(high_hits) >= t["max_high_hits"]:
            reason = f"multiple signals ({len(high_hits)})"
        else:
            reason = "long / multi-question"
    elif (high_hits or length > t["high_len"] or qmarks >= t["high_qmarks"]
          or newlines >= t["high_newlines"]):
        level = "HIGH"
        reason = f"keyword: {high_hits[0]}" if high_hits else "substantial task"
    elif low_hits and length < t["low_len"] and not high_hits:
        level = "LOW"
        reason = f"keyword: {low_hits[0]}"
    else:
        level = "MEDIUM"
        reason = "standard task"
    return level, reason


def directive(level: str, cfg=None) -> str:
    cfg = cfg or _load_config()
    return cfg["directives"].get(level, cfg["directives"]["MEDIUM"])


def badge(level: str, reason: str) -> str:
    return f"{ICON.get(level, '◦')} EFFORT ⟶ {level}  ·  {reason}"


def effort_params(level: str, provider: str = "openai", cfg=None) -> dict:
    """Native effort/thinking kwargs for a provider — splat into your API call.

    >>> effort_params("HIGH", "openai")
    {'reasoning_effort': 'high'}
    """
    cfg = cfg or _load_config()
    return dict(cfg["effort_params"].get(provider, {}).get(level, {}))


def evaluate(prompt: str, provider: str = None):
    """One-shot convenience: return full dict (+ native params if provider given)."""
    cfg = _load_config()
    level, reason = classify(prompt, cfg)
    out = {"level": level, "reason": reason,
           "directive": directive(level, cfg), "badge": badge(level, reason)}
    if provider:
        out["params"] = effort_params(level, provider, cfg)
    return out
