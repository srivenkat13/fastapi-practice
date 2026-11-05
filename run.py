#!/usr/bin/env python
"""Run a lesson's API with auto-reload, then open http://127.0.0.1:8000/docs

    python run.py f01             # your exercise
    python run.py f01 --solution  # the reference solution
"""
import os
import subprocess
import sys

from curriculum import find


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__)
        return 1
    unit_id, _track, folder, title, app = find(args[0])
    if not app:
        raise SystemExit(f"{unit_id} has no API to run. Use `python check.py {unit_id}` instead.")
    kind = "solution" if "--solution" in sys.argv else "exercise"
    module, attr = app.split(":")
    target = f"{folder.replace('/', '.')}.{kind}.{module}:{attr}"
    print(f"{unit_id} · {title}\n→ http://127.0.0.1:8000/docs  (Ctrl+C to stop)\n")
    os.environ.setdefault("PYTHONPATH", os.getcwd())
    return subprocess.call([sys.executable, "-m", "uvicorn", target, "--reload", "--reload-dir", folder])


if __name__ == "__main__":
    sys.exit(main())
