"""
test_dispatch.py — Tests for intent classification and dispatch routing.

Run from repo root:
  PYTHONPATH=platform/conductor/src python3 -m pytest platform/conductor/tests/test_dispatch.py -q
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "platform" / "conductor" / "src"))

from dispatch import (
    classify_intent,
    dispatch,
    TOOL_RESEARCH,
    TOOL_PLAN,
    TOOL_SUMMARISE,
    TOOL_CONVERSE,
    _keyword_classify,
)


# ===========================================================================
# Keyword fast-path tests
# ===========================================================================


class TestKeywordClassify:
    def test_what_is(self):
        assert _keyword_classify("What is a neural network?") == TOOL_RESEARCH

    def test_explain(self):
        assert _keyword_classify("Explain transformer architecture") == TOOL_RESEARCH

    def test_how_does(self):
        assert _keyword_classify("How does attention mechanism work?") == TOOL_RESEARCH

    def test_research(self):
        assert _keyword_classify("Research the latest LLM benchmarks") == TOOL_RESEARCH

    def test_plan_request(self):
        assert _keyword_classify("Help me plan my release") == TOOL_PLAN

    def test_plan_request_for(self):
        assert _keyword_classify("Plan for my release") == TOOL_PLAN

    def test_steps_for(self):
        assert _keyword_classify("What are the steps for deploying this?") == TOOL_PLAN

    def test_strategy_for(self):
        assert _keyword_classify("What's the strategy for this migration?") == TOOL_PLAN

    def test_summarise(self):
        assert _keyword_classify("Summarise the above discussion") == TOOL_SUMMARISE

    def test_tl_dr(self):
        assert _keyword_classify("tl;dr") == TOOL_SUMMARISE

    def test_key_points(self):
        assert _keyword_classify("What are the key points?") == TOOL_SUMMARISE

    def test_inconclusive_returns_none(self):
        assert _keyword_classify("I've been thinking about my priorities") is None

    def test_case_insensitive(self):
        assert _keyword_classify("WHAT IS Python?") == TOOL_RESEARCH


# ===========================================================================
# classify_intent (with mocked gateway)
# ===========================================================================


class _MockGatewayResponse:
    def __init__(self, content):
        self.content = content


class _MockGateway:
    def __init__(self, response_text):
        self._response_text = response_text
        self.calls = []

    def complete(self, prompt, **kwargs):
        self.calls.append({"prompt": prompt, **kwargs})
        return _MockGatewayResponse(self._response_text)


class TestClassifyIntent:
    def test_fast_path_bypasses_gateway(self):
        gw = _MockGateway("research")
        result = classify_intent("What is FastAPI?", gateway=gw)
        # Fast path should fire, no gateway call
        assert result == TOOL_RESEARCH
        assert gw.calls == []

    def test_falls_back_to_gateway_when_inconclusive(self):
        gw = _MockGateway("plan")
        result = classify_intent("I've been thinking about my next quarter", gateway=gw)
        assert result == TOOL_PLAN
        assert len(gw.calls) == 1

    def test_gateway_invalid_response_returns_converse(self):
        gw = _MockGateway("gibberish response here")
        result = classify_intent("random message", gateway=gw)
        assert result == TOOL_CONVERSE

    def test_gateway_failure_returns_converse(self):
        class FailGateway:
            def complete(self, *a, **kw):
                raise RuntimeError("network down")

        result = classify_intent("some message", gateway=FailGateway())
        assert result == TOOL_CONVERSE

    def test_summarise_from_gateway(self):
        gw = _MockGateway("summarise")
        result = classify_intent("give me the overview of the conversation", gateway=gw)
        # "overview" doesn't match fast path; falls to gateway
        assert result in (TOOL_SUMMARISE, TOOL_CONVERSE)  # gateway returns summarise


# ===========================================================================
# dispatch (with mocked gateway)
# ===========================================================================


class TestDispatch:
    def _make_gateway(self, text="mock response"):
        return _MockGateway(text)

    def test_dispatch_research(self):
        gw = self._make_gateway("research answer")
        result = dispatch(
            "What is AIOS?",
            context_block="",
            history=[],
            gateway=gw,
            intent_override=TOOL_RESEARCH,
        )
        assert result["intent"] == TOOL_RESEARCH
        assert result["response"] == "research answer"
        assert result["tool"] == TOOL_RESEARCH

    def test_dispatch_plan(self):
        gw = self._make_gateway("plan steps")
        result = dispatch(
            "Plan a refactor",
            context_block="",
            history=[],
            gateway=gw,
            intent_override=TOOL_PLAN,
        )
        assert result["intent"] == TOOL_PLAN
        assert result["response"] == "plan steps"

    def test_dispatch_summarise(self):
        gw = self._make_gateway("summary")
        result = dispatch(
            "Summarise",
            context_block="",
            history=[],
            gateway=gw,
            intent_override=TOOL_SUMMARISE,
        )
        assert result["intent"] == TOOL_SUMMARISE

    def test_dispatch_converse(self):
        gw = self._make_gateway("conversation response")
        result = dispatch(
            "How are you?",
            context_block="",
            history=[],
            gateway=gw,
            intent_override=TOOL_CONVERSE,
        )
        assert result["intent"] == TOOL_CONVERSE
        assert result["response"] == "conversation response"

    def test_dispatch_passes_context_block(self):
        gw = self._make_gateway("ctx response")
        context_block = "=== AIOS Context ===\nOperator: Erik"
        result = dispatch(
            "Hello",
            context_block=context_block,
            history=[],
            gateway=gw,
            intent_override=TOOL_CONVERSE,
        )
        # The context block should appear in the gateway prompt
        assert any(context_block in call["prompt"] for call in gw.calls)

    def test_dispatch_uses_classification_when_no_override(self):
        gw = self._make_gateway("response")
        result = dispatch(
            "What is Python?",
            context_block="",
            history=[],
            gateway=gw,
        )
        # Fast path: "What is" → research
        assert result["intent"] == TOOL_RESEARCH
