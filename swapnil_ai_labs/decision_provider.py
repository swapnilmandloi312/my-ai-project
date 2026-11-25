"""Alternative experiment: model decides READ or REFUSE, host supplies exact target.
A trusted host must independently authorize the task AND target. This is not a consent detector.
"""
import json
def decision_provider(classify):
    def provider(expected,intent):
        raw=classify(intent)
        if type(raw) is not str or len(raw)>64:return "{}"
        # No target or action parsing, no fuzzy matching, no repairing arbitrary JSON.
        return json.dumps(expected) if raw.strip()=="READ" else "{}"
    return provider
