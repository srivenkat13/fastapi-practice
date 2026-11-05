# D3 · Drill: debug a broken API (⏱ 25 min)

> "Here's a service with failing tests. Talk me through it." This format tests reading unfamiliar code, forming hypotheses, and knowing the classic Python and FastAPI pitfalls.

## Brief
`exercise/main.py` has **7 bugs**. Run the tests, read each failure, and fix the **code**, not the tests.
```bash
python check.py d3 -v
```
Spoiler-free hints, in case you get stuck: a Python default argument, two HTTP status-code issues, a leaked field, route declaration order, a slicing mistake, case sensitivity, and PATCH semantics. (`solution/main.py` labels each fix.)

## What interviewers listen for
- A **method**: reproduce, read the assertion, form a hypothesis, make a minimal fix, re-run. Don't rewrite everything.
- Naming the underlying concept: "mutable default argument", "route shadowing", "response_model as an allow-list", "exclude_unset for PATCH".
- Spotting **adjacent** problems the tests don't cover yet (here: `len(NOTES) + 1` reuses IDs after a delete, and DELETE doesn't check the owner), and saying so without going down a rabbit hole.
