from __future__ import annotations

import sys
from pathlib import Path

from dataclasses import dataclass
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class FakeLLM:
    """Deterministic LLM mock used in agent unit tests."""

    response: str = "mocked LLM response"

    def call(self, *_args: Any, **_kwargs: Any) -> str:
        return self.response

    def invoke(self, *_args: Any, **_kwargs: Any) -> str:
        return self.response


class FakeAgent:
    """Small replacement for CrewAI Agent during tests."""

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.role = kwargs.get("role")
        self.goal = kwargs.get("goal")
        self.backstory = kwargs.get("backstory")
        self.llm = kwargs.get("llm")
        self.verbose = kwargs.get("verbose")


class FakeTask:
    """Small replacement for CrewAI Task during tests."""

    def __init__(self, **kwargs: Any) -> None:
        self.description = kwargs.get("description")
        self.expected_output = kwargs.get("expected_output")
        self.agent = kwargs.get("agent")
        self.context = kwargs.get("context", [])


class FakeCrew:
    """Small replacement for CrewAI Crew during tests."""

    def __init__(self, **kwargs: Any) -> None:
        self.agents = kwargs["agents"]
        self.tasks = kwargs["tasks"]
        self.process = kwargs["process"]
        self.verbose = kwargs["verbose"]

    def kickoff(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "mocked",
            "inputs": inputs,
        }


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def patch_agent_builder(monkeypatch: pytest.MonkeyPatch, fake_llm: FakeLLM):
    def _patch(module: Any) -> None:
        monkeypatch.setattr(module, "Agent", FakeAgent)
        monkeypatch.setattr(module, "get_llm", lambda: fake_llm)

    return _patch


@pytest.fixture
def patch_crew_dependencies(monkeypatch: pytest.MonkeyPatch):
    from app.agents import crew

    fake_agents = {
        "triage": object(),
        "diagnosis": object(),
        "remediation": object(),
        "severity": object(),
        "reporter": object(),
    }

    monkeypatch.setattr(crew, "Crew", FakeCrew)
    monkeypatch.setattr(crew, "Task", FakeTask)
    monkeypatch.setattr(crew, "build_triage_agent", lambda: fake_agents["triage"])
    monkeypatch.setattr(crew, "build_diagnosis_agent", lambda: fake_agents["diagnosis"])
    monkeypatch.setattr(crew, "build_remediation_agent", lambda: fake_agents["remediation"])
    monkeypatch.setattr(crew, "build_severity_agent", lambda: fake_agents["severity"])
    monkeypatch.setattr(crew, "build_reporter_agent", lambda: fake_agents["reporter"])

    return fake_agents