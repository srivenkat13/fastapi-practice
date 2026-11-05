import importlib
import subprocess
import sys

from support import ROOT, target

pkg = target(__file__)


def test_package_exposes_public_api():
    assert sorted(getattr(pkg, "__all__", [])) == ["Inventory", "Product", "load_products"]
    for name in ("Product", "Inventory", "load_products", "build_inventory"):
        assert hasattr(pkg, name), f"{name} should be importable from the package"


def test_inventory_module_uses_relative_import():
    inventory = target(__file__, "inventory")  # fails with ModuleNotFoundError if the import is absolute
    importlib.reload(inventory)


def test_data_file_does_not_depend_on_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # run "from somewhere else"
    products = pkg.load_products()
    assert [p.sku for p in products] == ["KB-1", "MS-2", "MN-3"]


def test_build_inventory():
    inv = pkg.build_inventory()
    assert [p.sku for p in inv.available()] == ["KB-1", "MN-3"]
    assert inv.total_value_cents() == 12900 * 4 + 39900 * 2


def test_main_block_runs_as_module():
    module = pkg.__name__ + ".storage"
    out = subprocess.run([sys.executable, "-m", module], cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "Mechanical keyboard" in out.stdout


def test_importing_storage_prints_nothing(capsys):
    importlib.reload(target(__file__, "storage"))
    assert capsys.readouterr().out == ""
