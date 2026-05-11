from __future__ import annotations

from log_correlation_agent.llm.gemini_adapter import extract_confidence
from log_correlation_agent.parsers.sanitizer import build_llm_prompt
from log_correlation_agent.state import LogCorrelationState


def llm_reasoner_node(state: LogCorrelationState) -> LogCorrelationState:
    if state.get("used_llm") is False:
        return state
    lines = [
        f"{event.get('effective_ts')} [{event.get('service')}] [{event.get('level')}] {event.get('message_preview')}"
        for event in state.get("windowed_events", [])
    ]
    prompt = build_llm_prompt("Explain the likely causal chain using only these logs.", lines)
    state["llm_response"] = prompt
    confidence = extract_confidence(prompt)
    state["causal_confidence"] = confidence.get("causal_confidence")
    state["evidence_types"] = confidence.get("evidence_types", [])
    return state
