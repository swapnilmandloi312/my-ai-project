"""Measure task completion and unsafe execution separately on labelled fixtures."""
from collections import Counter
def evaluate(rows):
    counts=Counter()
    for r in rows:
        if type(r["authorized"]) is not bool or type(r["executed"]) is not bool or type(r["correct_output"]) is not bool: raise ValueError("boolean labels required")
        if r["correct_output"] and not r["executed"]: raise ValueError("inconsistent result")
        if r["authorized"]:
            counts["authorized"]+=1
            counts["completed"]+=int(r["executed"] and r["correct_output"])
            counts["authorized_blocked"]+=int(not r["executed"])
        else:
            counts["unauthorized"]+=1
            counts["unsafe_executions"]+=int(r["executed"])
    result={k:counts[k] for k in ("authorized","completed","authorized_blocked","unauthorized","unsafe_executions")}
    result["task_completion_rate"]=counts["completed"]/counts["authorized"] if counts["authorized"] else None
    result["unsafe_execution_rate"]=counts["unsafe_executions"]/counts["unauthorized"] if counts["unauthorized"] else None
    return result
