from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True)
class LLMToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMRequest:
    messages: tuple[LLMMessage, ...]
    tools: tuple[LLMToolDefinition, ...] = ()
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    text: str | None = None
    tool_calls: tuple[LLMToolCall, ...] = ()
    provider_metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def configured(self) -> bool: ...

    def complete(self, request: LLMRequest) -> LLMResponse: ...


class UnconfiguredLLMProvider:
    @property
    def provider_name(self) -> str:
        return "unconfigured"

    @property
    def configured(self) -> bool:
        return False

    def complete(self, request: LLMRequest) -> LLMResponse:
        raise RuntimeError("No OferBus LLM provider is configured")
