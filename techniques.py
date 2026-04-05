"""Prompt engineering technique definitions and task detection."""

from __future__ import annotations

_CODE_KEYWORDS = {
    "write", "implement", "code", "function", "class", "script",
    "program", "algorithm", "method", "api", "endpoint", "build",
    "create a", "develop", "refactor", "unit test", "def ", "sql",
}
_DEBUG_KEYWORDS = {
    "fix", "bug", "error", "debug", "broken", "fails", "crash",
    "exception", "traceback", "not working", "issue", "problem",
}
_EXPLAIN_KEYWORDS = {
    "explain", "how does", "why does", "describe",
    "summarize", "what are", "define", "clarify", "tell me about",
}

TECHNIQUES: dict[str, dict] = {
    "role_prompting": {
        "name": "Role prompting",
        "instruction": "Prepend a role statement: 'You are an expert [relevant domain] professional.'",
        "applies_to": ["code", "debug", "explanation", "general"],
    },
    "chain_of_thought": {
        "name": "Chain-of-thought",
        "instruction": "Append 'Think step by step before answering.' to encourage reasoning.",
        "applies_to": ["code", "debug", "general"],
    },
    "xml_structuring": {
        "name": "XML structuring",
        "instruction": "Wrap distinct sections in XML tags: <instructions>, <context>, <constraints>, <output_format>.",
        "applies_to": ["code", "debug", "explanation", "general"],
    },
    "output_format": {
        "name": "Output format",
        "instruction": "Add an explicit <output_format> section specifying the expected structure, length, and style.",
        "applies_to": ["code", "explanation", "general"],
    },
    "constraint_injection": {
        "name": "Constraint injection",
        "instruction": "Add negative constraints relevant to common failure modes (e.g., 'Do not change unrelated code', 'Do not hallucinate imports').",
        "applies_to": ["debug", "code"],
    },
    "audience_injection": {
        "name": "Audience injection",
        "instruction": "Specify the audience level: 'Explain this to a senior software engineer who is unfamiliar with this domain.'",
        "applies_to": ["explanation"],
    },
}

_TASK_TECHNIQUE_MAP: dict[str, list[str]] = {
    "code": ["role_prompting", "chain_of_thought", "xml_structuring", "output_format", "constraint_injection"],
    "debug": ["role_prompting", "constraint_injection", "chain_of_thought", "xml_structuring"],
    "explanation": ["role_prompting", "audience_injection", "xml_structuring", "output_format"],
    "general": ["role_prompting", "xml_structuring", "output_format", "chain_of_thought"],
}


def detect_task_type(prompt: str) -> str:
    lower = prompt.lower()
    if any(kw in lower for kw in _DEBUG_KEYWORDS):
        return "debug"
    if any(kw in lower for kw in _CODE_KEYWORDS):
        return "code"
    if any(kw in lower for kw in _EXPLAIN_KEYWORDS):
        return "explanation"
    return "general"


def get_techniques_for_task(task_type: str) -> list[dict]:
    keys = _TASK_TECHNIQUE_MAP.get(task_type, _TASK_TECHNIQUE_MAP["general"])
    return [TECHNIQUES[k] for k in keys]
