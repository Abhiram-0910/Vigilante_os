# Evaluation / Winning Checklist

Use this to confirm the API meets judge and “NEXT PART” requirements.

## Phase 1-4 (Gatekeeper + Infra + Intelligence + Wow)
- [x] Dumb fallback: 200 + JudgeResponse on any crash (no 500)
- [x] Judge whitelist: no rate limit on /analyze
- [x] Output sanitization: sanitize_agent_reply() strips markdown
- [x] Fire-and-forget: DB/observability in BackgroundTasks
- [x] Normalization: UPI lowercase, phones +91, URLs http(s)
- [x] False positive: neutral reply when confidence < 0.3
- [x] Root GET /: HTML landing; /health JSON
- [x] Warm-up: scripts/warmup.py; PORT from env (see DEPLOY.md)

## API & Stability
- [x] API never crashes (global exception handler + `safe_fallback_response()`)
- [x] Always returns JSON (JudgeResponse schema on all paths, including errors)
- [x] Handles bad input (RequestValidationError → 200 + safe schema)
- [x] Handles missing API key (403 + `{"error": "Invalid API key"}`)
- [x] Handles timeout (1.2s timeout on orchestrator + CompetitionEngine fallback)
- [x] Load test: `locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host=http://127.0.0.1:8000`

## Authentication
- [x] Header: `X-API-KEY: <key>`
- [x] Missing/wrong key → 403, body exactly `{"error": "Invalid API key"}`
- [x] No logging of secrets (InvalidAPIKeyError, no key in logs)

## Response Schema
- [x] All responses use JudgeResponse: `session_id`, `scam_detected`, `confidence_score`, `agent_reply`, `extracted_intelligence` (upi_ids, bank_accounts, phone_numbers, urls), `conversation_turns`, `engagement_duration_seconds`
- [x] No raw text, stack traces, null, or missing fields (enforced via `safe_fallback_response()`)

## Detection
- [x] Conservative classification: `scam_detected = confidence >= 0.4`
- [x] Ensemble in fusion (regex + behavioral + optional semantic)

## Engagement
- [x] Session memory by `session_id` (load_from_db_fallback / save_to_db_fallback)
- [x] Optional `conversation_history` in request
- [x] Always returns an `agent_reply` (never “this is a scam” or exit)

## Extraction
- [x] Regex-based in `extract_scam_data()` (UPI, bank, phone, URLs)
- [x] Deobfuscation (spoken digits, spaces, hyphens, “at”/“dot”)
- [x] `verify_intelligence()` for context; deobfuscated UPIs allowed when message has payment context
- [x] Space-collapsed UPI extraction; `validate_extracted_format()` for strict format
- [x] Tests: `python simulate_competition.py`

## 100% Accuracy Refinements
- [x] Detection battery: `python simulate_competition.py`
- [x] Engagement sim: `python simulate_competition.py`
- [x] JSON stress: `python simulate_competition.py`

## Performance
- [x] &lt;2s target (1.2s timeout + fast path)
- [x] Fallback reply on timeout/failure: “Sorry beta, network is slow. Can you resend your UPI?”

## How to run
```bash
# Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Full Competition Simulation (Detection + Extraction + Engagement)
python simulate_competition.py

# Load test
locust -f locustfile.py --host=http://127.0.0.1:8000
```
