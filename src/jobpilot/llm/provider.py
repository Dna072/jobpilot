"""LLM provider protocol — implementations may be swapped without changing agents."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ValidationError


class LLMProvider(Protocol):
    name: str

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...


class HeuristicProvider:
    """Deterministic offline provider used in tests and when no API key exists."""

    name = "heuristic"

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        # Agents should not rely on the LLM for control flow. This provider
        # returns empty/default structured objects so pipelines stay testable.
        return schema.model_validate({})


class OpenAICompatibleProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        if not self.api_key:
            return HeuristicProvider().complete_json(prompt, schema)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai extra is not installed") from exc
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return schema.model_validate_json(content)
        except ValidationError:
            return HeuristicProvider().complete_json(prompt, schema)


def get_provider() -> Any:
    from jobpilot.config import get_settings

    settings = get_settings()
    provider = (settings.llm_provider or "heuristic").lower()
    if provider in {"openai", "azure", "compatible"}:
        return OpenAICompatibleProvider(
            settings.openai_api_key, settings.openai_model, settings.openai_base_url
        )
    return HeuristicProvider()
