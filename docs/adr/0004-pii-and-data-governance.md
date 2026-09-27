# ADR 0004: Personally Identifiable Information (PII) & Data Governance in Municipal AI Triage

## Status
Accepted

## Context
CivicPulse collects natural language complaints from citizens containing Personally Identifiable Information (PII), including:
- Citizen names, phone numbers, and email addresses (`reporter_contact`).
- Specific home addresses, street numbers, and residential landmarks (`location`).
- Descriptions of daily household routines (e.g., "water entering ground floor since fajr").

When integrating with third-party hosted LLM providers on free tiers (such as Google Gemini free tier or Groq), vendor Terms of Service frequently state that prompts and outputs may be reviewed by human annotators or ingested into model training datasets. Transmitting sensitive citizen data to external public training sets violates privacy principles, municipal trust, and data protection regulations (e.g., GDPR, PECA).

## Decision
We adopted a multi-layered data protection and boundary sanitization strategy:

1. **Complete Isolation of Contact Information**:
   - Fields containing explicit citizen contact details (`reporter_contact`, phone numbers, email addresses) are strictly prohibited from being passed to external LLM providers.
   - The triage interface contract (`TriageProvider.triage(text: str, location: str)`) intentionally omits `reporter_contact`.
2. **Location Sanitization & Coarsening**:
   - The location input is sanitized to strip house numbers and private apartment identifiers before outbound transmission, retaining only municipal ward/sector level geographic context necessary for spatial classification.
3. **On-Premise / Local Fallback Guarantee**:
   - For highly sensitive civic complaints, operators can configure `TRIAGE_PROVIDER=llm:ollama` to run an entirely offline, zero-dependency model inside an air-gapped container (`ollama:0.5.4`), ensuring zero bytes leave the municipal network.
4. **Prompt Delimitation & Redaction**:
   - Complaint text is isolated inside `<complaint_text>` tags to block instruction leakage, and regex filters strip recognized Pakistani phone formats (`+92...`, `0300...`) before sending to cloud LLMs.

## Consequences
- **Positive**:
  - Full compliance with municipal data protection guidelines.
  - Citizen contact credentials never leave the internal database boundary.
  - Seamless toggle between cloud-hosted inference (speed) and local Ollama inference (total privacy).
- **Negative**:
  - Stripping granular address details slightly limits the LLM's ability to infer specialized hyper-local zoning, though coarse sector/ward information is sufficient for category classification.
