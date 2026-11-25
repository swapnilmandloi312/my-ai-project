package gateway_benchmark
import rego.v1

default permit(_) := false

permit(x) := true if {
    x.action == "lookup_invoice"
    x.tenant == "demo"
    x.exact_shape
    x.within_budget
}

permit(x) := true if {
    x.action == "prepare_report"
    x.tenant == "demo"
    x.exact_shape
    x.within_budget
    x.evidence_count >= 2
    x.approval_matches
}

decisions := [permit(x) | some i; x := input[i]]
