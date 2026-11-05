#!/usr/bin/env python
"""Grade one lesson.

    python check.py p1            # grade your exercise
    python check.py 05            # same as f05
    python check.py f05 -v        # verbose pytest output
    python check.py f05 --solution  # run the tests against the reference solution
"""
import os
import subprocess
import sys

from curriculum import find

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    if not args:
        print(__doc__)
        return 1
    unit_id, _track, folder, title, _app = find(args[0])
    env = dict(os.environ)
    if "--solution" in flags:
        env["SOLUTIONS"] = "1"
    print(f"{BOLD}{unit_id} · {title}{RESET}  {DIM}({'solution' if '--solution' in flags else 'exercise'}){RESET}\n")
    cmd = [sys.executable, "-m", "pytest", folder, "--tb=short" if "-v" in flags else "--tb=line"]
    if "-v" in flags:
        cmd.append("-v")
    code = subprocess.call(cmd, env=env)
    if code == 0:
        print(f"\n{GREEN}✔ {unit_id} passes.{RESET} Read the 'Interview angle' section of its README before moving on.")
    else:
        print(f"\n{RED}✘ {unit_id} not done yet.{RESET} Re-run with -v for full tracebacks. README: {folder}/README.md")
    return code


if __name__ == "__main__":
    sys.exit(main())
