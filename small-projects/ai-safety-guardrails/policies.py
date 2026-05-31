"""Configurable safety policies per tenant."""

from pydantic import BaseModel


class SafetyPolicy(BaseModel):
    tenant_id: str = "default"
    block_pii: bool = True
    block_injection: bool = True
    block_toxicity: bool = True
    content_rating: str = "strict"  # strict | moderate | permissive
    custom_blocked_terms: list[str] = []


# In-memory policy store (replace with DB/Redis in production)
_policies: dict[str, SafetyPolicy] = {
    "default": SafetyPolicy(),
}


class PolicyEngine:
    """Manages per-tenant safety policies."""

    def get_policy(self, tenant_id: str) -> SafetyPolicy:
        return _policies.get(tenant_id, _policies["default"]).model_copy()

    def update_policy(self, update: "SafetyPolicy | BaseModel") -> SafetyPolicy:
        """Create or update a tenant policy from an update model."""
        data = update.model_dump() if hasattr(update, "model_dump") else update
        tenant_id = data.get("tenant_id", "default")
        existing = _policies.get(tenant_id, SafetyPolicy(tenant_id=tenant_id))
        merged = existing.model_copy(update=data)
        _policies[tenant_id] = merged
        return merged

    def list_tenants(self) -> list[str]:
        return list(_policies.keys())

    def delete_policy(self, tenant_id: str) -> bool:
        if tenant_id in _policies and tenant_id != "default":
            del _policies[tenant_id]
            return True
        return False
