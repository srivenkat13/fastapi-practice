"""Grades YOUR test suite with mutation testing:
it must pass on the correct app, and fail on every mutant (an app with one planted bug)."""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from support import ROOT, using_solutions

SUITE = Path(__file__).parent / ("solution" if using_solutions() else "exercise") / "tests_cart_api.py"
MUTANTS = {
    "shared_cart": "all users share one cart",
    "qty_replaces": "adding an existing SKU replaces the quantity instead of incrementing",
    "min_order_exclusive": "coupon minimum uses > instead of >=",
    "ignores_expiry": "expired coupons are accepted",
    "flat_negative": "flat discounts can push the total below zero",
    "no_auth_on_delete": "DELETE /cart/items/{sku} works without X-User",
}


def run_suite(bugs: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "F11_BUGS": bugs}
    cmd = [sys.executable, "-m", "pytest", str(SUITE), "-q", "--tb=no", "-p", "no:cacheprovider", "-o", "addopts="]
    return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)


def test_suite_passes_on_the_correct_app():
    result = run_suite()
    assert result.returncode == 0, f"your tests must pass on the real app:\n{result.stdout[-2000:]}"
    passed = int(re.search(r"(\d+) passed", result.stdout).group(1))
    assert passed >= 8, f"only {passed} tests: write more (aim for one per rule in the spec)"


@pytest.mark.parametrize("mutant", MUTANTS)
def test_suite_catches_mutant(mutant):
    result = run_suite(mutant)
    assert result.returncode == 1, f"mutant survived ({MUTANTS[mutant]}): no test failed. Add a test for that rule."
