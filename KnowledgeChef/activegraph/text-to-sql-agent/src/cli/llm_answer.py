"""Optional LLM answer composition for Text-to-SQL runs."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
DEFAULT_TIMEOUT_SECONDS = 30.0


class LLMAnswerComposerError(RuntimeError):
    """Raised when an optional LLM answer composer cannot produce an answer."""


@dataclass(frozen=True)
class LLMAnswerComposition:
    answer: str
    rationale: str | None
    raw_response: str
    latency_ms: int


def resolve_llm_config(
    pack: Any | None,
    *,
    enabled_override: bool | None = None,
    base_url_override: str | None = None,
    model_override: str | None = None,
    timeout_override: float | None = None,
) -> dict[str, Any]:
    raw = dict(getattr(pack, "llm", {}) or {}) if pack is not None else {}
    provider = str(raw.get("provider") or "ollama")
    enabled = bool(raw.get("enabled", False))
    if enabled_override is not None:
        enabled = enabled_override

    env = dict(getattr(pack, "env", {}) or {}) if pack is not None else {}
    base_url_env = raw.get("base_url_env") or "OLLAMA_BASE_URL"
    model_env = raw.get("model_env") or "OLLAMA_MODEL"
    timeout_seconds = timeout_override if timeout_override is not None else raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)

    return {
        "enabled": enabled,
        "provider": provider,
        "mode": raw.get("mode") or "answer_composer",
        "base_url": base_url_override
        or os.environ.get(str(base_url_env))
        or env.get(str(base_url_env))
        or raw.get("base_url")
        or DEFAULT_OLLAMA_BASE_URL,
        "model": model_override
        or os.environ.get(str(model_env))
        or env.get(str(model_env))
        or raw.get("model")
        or DEFAULT_OLLAMA_MODEL,
        "timeout_seconds": float(timeout_seconds),
        "fallback": raw.get("fallback") or "deterministic_answer",
        "response_format": raw.get("response_format") or "json_object",
    }


def build_answer_composer_messages(context: dict[str, Any]) -> list[dict[str, str]]:
    system = (
        "You are an answer composer for an ActiveGraph Text-to-SQL runtime. "
        "The SQL result is already validated and is the source of truth. "
        "Do not invent facts, do not change numbers, and answer in Korean. "
        "Return only JSON with keys answer and rationale."
    )
    user = json.dumps(context, ensure_ascii=False, sort_keys=True)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_openai_compatible_chat(
    messages: list[dict[str, str]],
    *,
    base_url: str,
    model: str,
    timeout: float,
) -> str:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise LLMAnswerComposerError(f"Ollama request failed: {exc}") from exc

    try:
        data = json.loads(response_body)
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise LLMAnswerComposerError(f"Unexpected Ollama response: {response_body}") from exc


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMAnswerComposerError(f"LLM response did not contain a JSON object: {text}")
    try:
        parsed = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMAnswerComposerError(f"LLM response JSON could not be parsed: {text}") from exc
    if not isinstance(parsed, dict):
        raise LLMAnswerComposerError("LLM response JSON must be an object")
    return parsed


def compose_answer_with_llm(context: dict[str, Any], config: dict[str, Any]) -> LLMAnswerComposition:
    provider = config.get("provider")
    started = time.monotonic()
    if provider == "fake":
        raw_response = json.dumps(
            {
                "answer": config.get("fake_answer") or context["deterministic_answer"],
                "rationale": "fake adapter response",
            },
            ensure_ascii=False,
        )
    elif provider == "ollama":
        raw_response = call_openai_compatible_chat(
            build_answer_composer_messages(context),
            base_url=str(config["base_url"]),
            model=str(config["model"]),
            timeout=float(config["timeout_seconds"]),
        )
    else:
        raise LLMAnswerComposerError(f"Unsupported LLM provider: {provider}")

    parsed = extract_json_object(raw_response)
    answer = parsed.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise LLMAnswerComposerError("LLM response must include a non-empty answer")
    rationale = parsed.get("rationale")
    return LLMAnswerComposition(
        answer=answer.strip(),
        rationale=rationale if isinstance(rationale, str) else None,
        raw_response=raw_response,
        latency_ms=int((time.monotonic() - started) * 1000),
    )



