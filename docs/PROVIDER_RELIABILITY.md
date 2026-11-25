# Provider reliability — next research gate
The existing trusted runtime checks scope and reserves inference budget before a provider call. A synchronous provider can still hang indefinitely. The new optional POSIX subprocess adapter bounds elapsed time and stdout, does not inherit the parent environment, and returns explicit audited failure reasons. A failed attempt consumes its existing reservation. Retrying requires an explicitly new host request; there is no automatic duplicate execution.

Run `python -m unittest -v swapnil_ai_labs.test_isolated_provider`. Tests exercise real subprocesses, a sleeping worker, stdout flood, invalid bytes, closed stdout with a hanging process, same-group child termination, credential environment isolation, pre-inference denial, strict record binding and replay.

This is a trusted-worker transport, not a security sandbox, GPU serving stack or production API. It cannot guarantee time bounds on OS process creation or uninterruptible kernel I/O, prevent workers accessing files/network as the same user, limit CPU/memory outside elapsed/output controls, or contain a worker that deliberately escapes its process group. Run separately permissioned workers with OS/container resource limits; use external cancellation, authenticated service boundaries, egress controls and redaction. Intent remains potentially sensitive. Existing real-model pilot uses an in-process provider; this adapter's tests are deterministic worker fixtures and must not be described as a new real-model accuracy result.

## Next evidence work
1. Analyze raw v0.13 model outputs and identify legitimate failures.
2. Pre-register exact proposal and bounded normalization baselines; never infer authorization from model output.
3. Source a legally reusable independently authored dataset, record license/provenance, freeze holdout before tuning, include adversarial and legitimate requests, report utility, unsafe execution, false denial and latency separately.
4. Integrate bounded model-serving worker with warm lifecycle, then evaluate Work Relay's shared read-only request-to-resolution workflow under synthetic business fixtures. No actual approvals, writes or client data until external review and production gates.
