# Interview prep

Written for a React/TS developer with ~6 years of experience moving into (or adding) Python backend work.

| File | Use it for |
|---|---|
| [question-bank.md](question-bank.md) | ~80 questions with short model answers, tagged with the lesson where you practised each one (⭐ = most asked) |
| [python-for-js-devs.md](python-for-js-devs.md) | a one-page JS → Python translation table |
| [framework-comparison.md](framework-comparison.md) | FastAPI vs Flask vs Django: how to answer "why this framework?" |
| [system-design.md](system-design.md) | a design-round framework + 7 backend scenarios + a scaling cheat sheet |
| [live-coding.md](live-coding.md) | formats, a 60-minute "build an API" script, a take-home checklist, the drill schedule |

## How to position yourself
You aren't a "frontend dev who learned Python". You're a **product engineer who understands both sides of the API contract**. Use that:
- You know what frontend teams need from APIs: stable contracts (OpenAPI → generated TS types), consistent errors, pagination that works with infinite scroll, sensible CORS and auth for SPAs, and cache headers.
- Tell stories that cross the boundary: "I designed the error envelope so the React form layer could map `details[].field` to inputs."
- Be honest about depth: "I've built X with FastAPI (show the capstone). In production I'd also want Y (migrations, observability…)."

## Before the interview
- [ ] `python progress.py` shows everything green
- [ ] You can rebuild F09 (CRUD + pagination) from scratch in 45 min
- [ ] You can explain `def` vs `async def`, DI, N+1, idempotency and JWT pitfalls without notes
- [ ] The capstone is pushed to GitHub with a strong README (see capstone/README.md → "How to present this")
- [ ] One system-design scenario rehearsed end to end, out loud
