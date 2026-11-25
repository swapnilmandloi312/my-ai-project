"""Rule-based diagnostic hints; never mutate a workflow or weaken policy."""
HINTS={
"no eligible model":("routing","Review measured model estimates and host-approved budget; do not silently raise limits."),
"missing trusted request":("authorization","Obtain an independently authorized request from the trusted host."),
"host tenant mismatch":("authorization","Verify authenticated tenant binding; do not change tenant based on model output."),
"provider or proposal failure":("proposal","Check provider availability and strict versioned schema. Never disable validation."),
"proposal does not match host request":("authorization","Reject mismatched action and request a new independently authorized grant if appropriate."),
"invalid or expired session":("authorization","Obtain a new authenticated host session."),
"invalid expired or consumed grant":("authorization","Check expiry and replay; issue a new grant only after independent authorization."),
"budget exhausted":("budget","Stop; obtain separate budget approval if required."),
"invalid proposal":("proposal","Inspect schema and input shape without logging sensitive contents.")
}
def diagnose(result):
    if result.get("status")=="executed_read_only": return {"category":"success","recommendation":"No failure detected."}
    category,hint=HINTS.get(result.get("reason"),("unknown","Investigate a redacted trace; keep execution blocked."))
    return {"category":category,"recommendation":hint}
