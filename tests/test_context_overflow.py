"""
A prompt that does not fit must not look like a wrong answer.

This is a grading-integrity test, not a plumbing test. llama.cpp answers an
oversized prompt with HTTP 400, and the obvious `raise_for_status()` throws away
the one part of that response which says why. The failure then reaches the eval
as an opaque "400 Bad Request", scores as an ordinary wrong answer, and silently
deflates the accuracy figure this project exists to report -- with nothing in the
output hinting that the model never saw the question.

So: the typed error, the classification on AgentResult, and the separate bucket
in summarize() are all pinned here. No GPU and no network -- the llama.cpp error
shapes are replayed through a mock transport, captured from a real b10934 server
on 2026-09-19.

    .venv\\Scripts\\python -m pytest tests/test_context_overflow.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from eval.run import summarize  # noqa: E402
from harness import agent  # noqa: E402
from harness.llm import ContextOverflowError, LocalLLM  # noqa: E402

# Verbatim from a real llama-server b10934 running -c 16384.
OVERFLOW_BODY = {
    "error": {
        "code": 400,
        "message": "request (22010 tokens) exceeds the available context size "
                   "(16384 tokens), try increasing it",
        "type": "exceed_context_size_error",
        "n_prompt_tokens": 22010,
        "n_ctx": 16384,
    }
}


def _llm(handler) -> LocalLLM:
    llm = LocalLLM(base_url="http://stub/v1")
    llm._client = httpx.Client(transport=httpx.MockTransport(handler))
    return llm


def test_overflow_raises_typed_error_with_token_counts():
    llm = _llm(lambda r: httpx.Response(400, json=OVERFLOW_BODY))
    with pytest.raises(ContextOverflowError) as exc:
        llm.chat([{"role": "user", "content": "anything"}])
    # The counts are the point: they tell you how much to raise -c by.
    assert exc.value.n_prompt_tokens == 22010
    assert exc.value.n_ctx == 16384
    assert "16384" in str(exc.value)


def test_other_errors_are_not_mistaken_for_overflow():
    """A malformed-tools 500 is a bug in us, not a context budget problem."""
    body = {"error": {"code": 500, "message": "Failed to parse tools",
                      "type": "server_error"}}
    llm = _llm(lambda r: httpx.Response(500, json=body))
    with pytest.raises(RuntimeError) as exc:
        llm.chat([{"role": "user", "content": "anything"}])
    assert not isinstance(exc.value, ContextOverflowError)
    assert "Failed to parse tools" in str(exc.value)


def test_non_json_error_body_does_not_crash_the_client():
    """A proxy error page or truncated write must still raise something useful."""
    llm = _llm(lambda r: httpx.Response(502, text="<html>bad gateway</html>"))
    with pytest.raises(RuntimeError) as exc:
        llm.chat([{"role": "user", "content": "anything"}])
    assert not isinstance(exc.value, ContextOverflowError)
    assert "502" in str(exc.value)


def test_successful_reply_still_parses():
    """Guards the raise_for_status() -> is_error swap against over-reach."""
    body = {"choices": [{"message": {"content": "SELECT 1"}}],
            "usage": {"total_tokens": 7}}
    llm = _llm(lambda r: httpx.Response(200, json=body))
    resp = llm.chat([{"role": "user", "content": "anything"}])
    assert resp.text == "SELECT 1"
    assert resp.usage["total_tokens"] == 7


class _OverflowingLLM:
    name = "stub"

    def chat(self, messages, tools=None, temperature: float = 0.0):
        raise ContextOverflowError("request (22010 tokens) exceeds the available "
                                   "context size (16384 tokens)", 22010, 16384)


def test_agent_classifies_overflow_and_does_not_claim_an_answer():
    from harness.db import DbConfig

    res = agent.run_baseline(_OverflowingLLM(), "how many?", DbConfig(), ddl="CREATE TABLE t (a INT);")
    assert res.error_kind == "context_overflow"
    assert res.answered is False          # nothing to grade -- it never ran
    assert not res.rows


def test_summarize_reports_overflows_outside_the_graded_set():
    records = [
        {"correct": True,  "defect_ids": [], "error_kind": None},
        {"correct": False, "defect_ids": [], "error_kind": None},
        {"correct": False, "defect_ids": [], "error_kind": "context_overflow"},
    ]
    s = summarize(records)
    assert s["context_overflow"] == 1
    assert s["graded"] == 2
    # `accuracy` keeps the full denominator so runs stay comparable; the graded
    # figure is what you quote once you know a prompt did not fit.
    assert s["accuracy"] == pytest.approx(1 / 3, abs=1e-4)
    assert s["accuracy_graded"] == pytest.approx(1 / 2, abs=1e-4)


def test_summarize_is_unchanged_when_nothing_overflowed():
    records = [{"correct": True, "defect_ids": [], "error_kind": None}]
    s = summarize(records)
    assert s["context_overflow"] == 0
    assert s["graded"] == s["total"] == 1
    assert s["accuracy"] == s["accuracy_graded"] == 1.0
