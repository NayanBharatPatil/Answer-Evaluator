"""LLM integration + score calculation.

All supported providers (Groq, Gemini, OpenAI, Ollama) expose an
OpenAI-compatible endpoint, so a single client handles them all.
"""
import json
import os
import re
from dataclasses import dataclass, field


from prompts import SYSTEM_PROMPT, USER_TEMPLATE

PROVIDERS = {
    "Groq": {"base_url": "https://api.groq.com/openai/v1",
             "model": "llama-3.3-70b-versatile", "env": "GROQ_API_KEY"},
    "Gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
               "model": "gemini-2.5-flash", "env": "GEMINI_API_KEY"},
    "OpenAI": {"base_url": "https://api.openai.com/v1",
               "model": "gpt-4o-mini", "env": "OPENAI_API_KEY"},
    "Ollama (local)": {"base_url": "http://localhost:11434/v1",
                       "model": "llama3.1", "env": None},
}
WEIGHTS = {"content_accuracy": 50, "completeness": 30, "clarity": 20}


@dataclass
class Result:
    marks: float
    max_marks: float
    percent: float
    rubric: dict
    key_points: list = field(default_factory=list)
    missing_points: list = field(default_factory=list)
    incorrect_statements: list = field(default_factory=list)
    feedback: str = ""


def _extract_json(text: str) -> dict:
    """Parse JSON even if the model wraps it in fences or adds chatter."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("Model did not return JSON.")
        return json.loads(match.group(0))


def compute_marks(rubric: dict, max_marks: float) -> tuple[float, float, dict]:
    """Clamp rubric scores to their weights, scale to max_marks, round to 0.5."""
    clean = {}
    for key, weight in WEIGHTS.items():
        try:
            clean[key] = max(0, min(weight, int(rubric.get(key, 0))))
        except (TypeError, ValueError):
            clean[key] = 0
    percent = sum(clean.values())  # weights sum to 100
    marks = round(percent / 100 * max_marks * 2) / 2
    return min(marks, max_marks), float(percent), clean


def evaluate(question, model_answer, student_answer, max_marks,
             provider="Groq", model=None, api_key=None, temperature=0.0) -> Result:
    from openai import OpenAI  # imported lazily so tests run without the SDK

    cfg = PROVIDERS[provider]
    key = api_key or (os.getenv(cfg["env"]) if cfg["env"] else "ollama")
    if not key:
        raise ValueError(f"No API key for {provider}. Enter it in the sidebar or set {cfg['env']}.")
    if not student_answer.strip():
        return Result(0, max_marks, 0, {k: 0 for k in WEIGHTS},
                      feedback="No answer was written.")

    client = OpenAI(api_key=key, base_url=cfg["base_url"])
    user_msg = USER_TEMPLATE.format(question=question.strip(),
                                    model_answer=model_answer.strip(),
                                    student_answer=student_answer.strip(),
                                    max_marks=max_marks)
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}]
    kwargs = dict(model=model or cfg["model"], messages=messages, temperature=temperature)

    try:
        resp = client.chat.completions.create(response_format={"type": "json_object"}, **kwargs)
    except Exception:  # some endpoints reject response_format
        resp = client.chat.completions.create(**kwargs)

    data = _extract_json(resp.choices[0].message.content)
    marks, percent, rubric = compute_marks(data.get("rubric", {}), max_marks)
    return Result(marks, max_marks, percent, rubric,
                  data.get("key_points", []), data.get("missing_points", []),
                  data.get("incorrect_statements", []), data.get("feedback", ""))
