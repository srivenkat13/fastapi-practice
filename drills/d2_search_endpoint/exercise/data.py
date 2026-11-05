from datetime import datetime, timedelta, timezone

BASE = datetime(2025, 1, 1, tzinfo=timezone.utc)
TAGS = ["python", "fastapi", "react", "devops"]

# 50 articles; some share a timestamp (ties!) so the cursor must include the id.
ARTICLES = [
    {
        "id": i,
        "title": f"{'FastAPI' if i % 3 == 0 else 'Python'} tips #{i}",
        "author": ["ada", "bob", "eve"][i % 3],
        "published_at": BASE + timedelta(hours=i // 2),
        "tags": [TAGS[i % 4], TAGS[(i + 1) % 4]],
    }
    for i in range(1, 51)
]
