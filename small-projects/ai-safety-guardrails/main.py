"""AI Safety Guardrails — FastAPI service for content filtering and safety analysis."""

import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detectors import detect_pii, detect_injection, detect_toxicity
from policies import PolicyEngine
from audit import AuditLogger

app = FastAPI(title="AI Safety Guardrails", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

policy_engine = PolicyEngine()
audit_logger = AuditLogger()


class CheckRequest(BaseModel):
    text: str
    tenant_id: str = "default"
    context: str = ""  # "input" or "output"


class PolicyUpdate(BaseModel):
    tenant_id: str = "default"
    block_pii: bool = True
    block_injection: bool = True
    block_toxicity: bool = True
    content_rating: str = "strict"  # strict, moderate, permissive
    custom_blocked_terms: list[str] = []


@app.middleware("http")
async def safety_middleware(request: Request, call_next):
    """Log all requests for audit trail."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    audit_logger.log_request(request_id, request.url.path, duration, response.status_code)
    return response


@app.post("/check")
async def check_safety(req: CheckRequest):
    """Analyze text for safety violations."""
    policy = policy_engine.get_policy(req.tenant_id)
    findings = []
    risk_score = 0.0

    # PII Detection
    if policy.block_pii:
        pii_results = detect_pii(req.text)
        if pii_results:
            findings.extend([{"type": "pii", "subtype": r["type"], "snippet": r["snippet"]} for r in pii_results])
            risk_score += 0.3 * len(pii_results)

    # Prompt Injection Detection
    if policy.block_injection:
        injection_results = detect_injection(req.text)
        if injection_results:
            findings.extend([{"type": "injection", "pattern": r["pattern"], "confidence": r["confidence"]} for r in injection_results])
            risk_score += 0.5 * len(injection_results)

    # Toxicity Detection
    if policy.block_toxicity:
        tox_result = detect_toxicity(req.text)
        if tox_result["flagged"]:
            findings.append({"type": "toxicity", "score": tox_result["score"], "categories": tox_result["categories"]})
            risk_score += tox_result["score"]

    risk_score = min(risk_score, 1.0)
    blocked = risk_score >= _rating_threshold(policy.content_rating)

    decision = {
        "request_id": str(uuid.uuid4())[:8],
        "tenant_id": req.tenant_id,
        "text_preview": req.text[:100] + ("..." if len(req.text) > 100 else ""),
        "blocked": blocked,
        "risk_score": round(risk_score, 3),
        "findings": findings,
        "policy": policy.content_rating,
        "timestamp": time.time(),
    }

    audit_logger.log_check(decision)
    return decision


def _rating_threshold(rating: str) -> float:
    return {"strict": 0.2, "moderate": 0.5, "permissive": 0.8}.get(rating, 0.5)


@app.get("/policies")
async def get_policies(tenant_id: str = "default"):
    """Return the active policy for a tenant."""
    policy = policy_engine.get_policy(tenant_id)
    return policy.model_dump()


@app.post("/policies")
async def update_policy(update: PolicyUpdate):
    """Update safety policy for a tenant."""
    policy_engine.update_policy(update)
    return {"status": "ok", "tenant_id": update.tenant_id, "policy": update.model_dump()}


@app.get("/audit/recent")
async def recent_audits(limit: int = 20):
    """Return recent audit entries."""
    return audit_logger.recent(limit)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ai-safety-guardrails"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
