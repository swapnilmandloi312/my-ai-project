# Swapnil AI Labs — pilot launch
## LinkedIn
An AI agent should propose actions, not automatically earn permission to execute them. At Swapnil AI Labs, we built an experimental contract language and gateway, then tested it on 144 synthetic policy cases. The simple action-name allowlist accepted 89 of 137 disallowed cases; our reference validator accepted none. This is a deliberately scoped fixture test, not proof of real-world security. We are now developing a read-only finance pilot and looking for developers to challenge the design. Code and raw evidence: https://github.com/swapnilmandloi312/my-ai-project/pull/1

## Reel (30 seconds)
0–4s: Your AI agent knows how to call a tool. Does it know when it must not?
4–12s: Show an invoice request for the correct tenant and a cross-tenant request.
12–20s: Show gateway decisions and read-only SQLite output. Label synthetic demo throughout.
20–26s: Show 89 versus zero disallowed fixture actions accepted, with denominator 137 and baseline label.
26–30s: Invite engineers to challenge the experiment on GitHub. No claim of zero vulnerabilities.

## Founder outreach draft
Subject: A controlled tool-execution pilot for your AI agent
Hi [name], I am building Swapnil AI Labs' experimental agent gateway to enforce explicit action contracts outside the model. I would like to understand one tool-execution boundary in [verified product] and propose a narrowly scoped, non-sensitive read-only pilot. Our initial synthetic results and source are public in the draft PR. Would a short technical discussion be useful? No production or security assurance is implied.
