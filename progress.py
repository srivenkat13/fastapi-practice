#!/usr/bin/env python
"""Show which lessons pass:  python progress.py   (add --solution to verify the reference code)."""
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from curriculum import TRACKS, UNITS

GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"


def main() -> int:
    env = dict(os.environ)
    if "--solution" in sys.argv:
        env["SOLUTIONS"] = "1"
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.xml"
        subprocess.call(
            [sys.executable, "-m", "pytest", "--tb=no", "-q", f"--junitxml={report}", "-o", "addopts="],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not report.exists():
            print("pytest did not produce a report; run `python -m pytest` to see what's wrong.")
            return 1
        totals = defaultdict(lambda: [0, 0])  # folder -> [passed, total]
        for case in ET.parse(report).getroot().iter("testcase"):
            classname = case.get("classname", "")
            failed = any(child.tag in ("failure", "error") for child in case)
            for unit in UNITS:
                if classname.startswith(unit[2].replace("/", ".") + "."):
                    totals[unit[2]][1] += 1
                    totals[unit[2]][0] += 0 if failed else 1
                    break

    done, next_up = 0, None
    for track, label in TRACKS.items():
        print(f"\n{BOLD}{label}{RESET}")
        for unit_id, unit_track, folder, title, _ in UNITS:
            if unit_track != track:
                continue
            passed, total = totals[folder]
            ok = total > 0 and passed == total
            done += ok
            if not ok and next_up is None:
                next_up = unit_id
            mark = f"{GREEN}✔{RESET}" if ok else f"{RED}·{RESET}"
            print(f"  {mark} {unit_id:<4} {title:<58} {DIM}{passed}/{total}{RESET}")
    print(f"\n{BOLD}{done}/{len(UNITS)} complete.{RESET}", f"Next: python check.py {next_up}" if next_up else "All done! 🎉")
    return 0


if __name__ == "__main__":
    sys.exit(main())
