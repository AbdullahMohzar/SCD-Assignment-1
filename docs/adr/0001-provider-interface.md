# ADR 0001: Pluggable AI Triage Provider Interface and Resilience Architecture

## Status
Accepted

## Context
CivicPulse ingests unstructured natural language complaints from citizens. To automate ticket routing and priority assessment, an AI triage component must parse complaint text, determine a category, assign an urgency priority, and summarize the issue in one line.

However, external AI services are inherently unreliable:
- Rate limits on free tiers can exhaust unexpectedly under burst traffic.
- Cloud providers suffer network latency fluctuations, timeouts, and outages.
- Input data can contain malicious prompt injections designed to derail triage.
- Third-party models are probabilistic, making test pipelines brittle if tightly coupled.

## Decision
We defined an explicit, decoupled protocol interface `TriageProvider` backed by `TriageResult`:
```python
class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)

class TriageProvider(Protocol):
    name: str
    async def triage(self, text: str, location: str) -> TriageResult: ...
```

We implemented four concrete providers selected at runtime via `TRIAGE_PROVIDER`:
1. `LLMTriage` (Groq / Gemini): Hosted API provider enforcing structured JSON mode and Pydantic validation.
2. `OllamaTriage`: Local self-hosted LLM running in a container for complete offline isolation.
3. `RuleBasedTriage`: Deterministic keyword heuristic that operates purely in memory with zero dependencies and never fails.
4. `SimulatedTriage`: Deterministic fake for CI with configurable failure injection modes.

### Resilience Wrapper
Calls to hosted providers are wrapped in a resilient orchestration pipeline:
- **10s Hard Cap Timeout**: Prevents hanging requests from exhausting worker pools.
- **Single Jittered Retry**: Retries transient 429, 5xx, or network drops once; never retries 400 client errors.
- **Fail-Safe Fallback**: Any unrecoverable failure immediately falls back to `RuleBasedTriage`, logs a structured `WARNING` with the error class, and records `triaged_by = "rules:fallback"`. Citizens never receive a 500 error due to upstream AI failures.
- **Redis Content-Hash Caching**: Complaints are hashed (SHA-256) and cached for 24 hours to eliminate redundant AI calls.

## Consequences
- **Positive**: Zero coupling to any single AI vendor; seamless offline operation; completely deterministic CI pipelines; guaranteed graceful degradation.
- **Negative**: Rule-based fallback summary is simpler than generative LLM output; caching adds a Redis read hop.
