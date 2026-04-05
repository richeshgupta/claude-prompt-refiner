# engine.py
"""RefinerEngine: builds prompts for Claude and parses its JSON response."""

from __future__ import annotations

import json
import re

from techniques import detect_task_type, get_techniques_for_task

_REFINER_SYSTEM = """\
You are an expert prompt engineer. Your task is to improve the user's prompt \
by applying proven prompt engineering techniques.

You must return ONLY a valid JSON object — no markdown fences, no explanation, \
no text before or after the JSON. The JSON must have exactly this shape:

{{
  "refined_prompt": "<the improved prompt as a plain string>",
  "annotations": [
    {{"technique": "<technique name>", "reason": "<why this technique was applied>"}}
  ]
}}

Techniques to consider (apply only those that genuinely improve the prompt):
{technique_list}

Rules:
- Preserve the user's intent exactly — only improve structure and clarity
- Do not add fictional context or assumptions
- Keep the refined prompt concise — do not pad unnecessarily
- If the prompt is already excellent, still apply at least one technique\
"""

_USER_TEMPLATE = """\
Refine this prompt:

{prompt}{comment_section}
"""

_COMMENT_SECTION = "\n\nAdditional instructions from user: {comment}"


class RefinerEngine:
    """Builds the refiner prompt and parses Claude's JSON response."""

    def build_refiner_prompt(self, raw_prompt: str, comment: str | None) -> str:
        task_type = detect_task_type(raw_prompt)
        techniques = get_techniques_for_task(task_type)
        technique_list = "\n".join(
            f"- {t['name']}: {t['instruction']}" for t in techniques
        )
        system = _REFINER_SYSTEM.format(technique_list=technique_list)
        comment_section = (
            _COMMENT_SECTION.format(comment=comment) if comment else ""
        )
        user_msg = _USER_TEMPLATE.format(
            prompt=raw_prompt, comment_section=comment_section
        )
        return f"{system}\n\n---\n\n{user_msg}"

    def parse_response(self, raw: str) -> dict:
        # Try direct parse first
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code fence
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding any JSON object in the text
        obj_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback
        return {
            "refined_prompt": raw.strip() or "Claude returned an empty response.",
            "annotations": [
                {
                    "technique": "Parse error",
                    "reason": "Claude returned non-JSON. Showing raw output.",
                }
            ],
        }
