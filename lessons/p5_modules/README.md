# P5 · Modules, packages, imports, venvs

> Every FastAPI project bigger than one file breaks on imports at some point. This lesson explains how Python finds code so that you can fix those errors quickly.

## 🧠 Concepts

### Modules & packages
- A **module** is one `.py` file. A **package** is a folder of modules. `__init__.py` runs when the package is imported, and it's where you define the package's public API.
- `import x` runs `x`'s top-level code **once** and caches it in `sys.modules`, similar to ES modules.
- `from .models import Product` is a **relative** import (a sibling module in the same package). `from app.models import Product` is **absolute** and is resolved from `sys.path`.
- `__all__ = [...]` controls what `from pkg import *` exports, and it documents the public API.
- `if __name__ == "__main__":` runs only when the file is executed directly, never when it's imported (similar to `require.main === module`).

### How Python finds imports (`sys.path`)
1. The directory of the script you ran, or the **current directory** with `python -m`
2. `PYTHONPATH`
3. site-packages of the active environment (installed libraries)

So `python app/main.py` and `python -m app.main` behave differently. In real projects, run from the project root with `-m` (this is also what `uvicorn app.main:app` does).

### Common import errors
| Error | Usual cause |
|---|---|
| `ModuleNotFoundError: No module named 'models'` | an absolute import of a sibling; use `from .models import ...` |
| `ImportError: attempted relative import with no known parent package` | you ran a file inside a package directly (`python pkg/x.py`); run `python -m pkg.x` instead |
| `ImportError: cannot import name 'X' (most likely due to a circular import)` | a imports b and b imports a; move the shared code into a third module, or import inside the function |

### File paths
Relative paths in `open("data.json")` are resolved against the **current working directory**, not against the file. Use `pathlib`:
```python
from pathlib import Path
DATA = Path(__file__).parent / "data.json"
DATA.read_text(); DATA.exists(); DATA.with_suffix(".bak")
```

### Virtual environments (vs node_modules)
| Node | Python |
|---|---|
| `node_modules/` per project (automatic) | `.venv/` per project, which you create and **activate** |
| `npm install x` | `pip install x` (inside the venv) |
| `package.json` | `pyproject.toml` (or `requirements.txt`) |
| `package-lock.json` | `uv.lock` / `poetry.lock` / a pinned `requirements.txt` (`pip freeze`) |
| `nvm` | `pyenv` (which you're using) or `uv python` |
| `npx` | `python -m tool` / `pipx` / `uvx` |

This repo: `source .venv/bin/activate`, after which `python` and `pip` point at the venv.

## 🏋️ Exercise
The package in `exercise/` is broken:
1. `inventory.py` uses an absolute import of a sibling module. Make it relative.
2. `storage.py` reads its JSON from a cwd-relative path. Use `Path(__file__).parent`.
3. Add an `if __name__ == "__main__":` block to `storage.py` that prints each product's name.
4. In `__init__.py`, re-export `Product`, `Inventory` and `load_products`, define `__all__`, and add `build_inventory()`.

```bash
python check.py p5
python -m lessons.p5_modules.exercise.storage     # try your __main__ block
```

## 💼 Interview angle
- *"What does `if __name__ == '__main__'` do?"*: it runs code only when the file is the entry point, so importing the module has no side effects.
- *"How do you fix a circular import?"*: extract the shared code into a third module, import inside the function, or depend on an interface (`TYPE_CHECKING` imports for type hints only).
- *"Why use a virtualenv?"*: it gives each project its own dependency versions, because the global site-packages is shared by everything.
- *"requirements.txt vs pyproject.toml?"*: pyproject is the standard project metadata (deps, tooling config). A lock file or pinned requirements gives reproducible installs.
- *"How are modules cached?"*: in `sys.modules`. A second import doesn't re-run the module, so module-level state behaves like a singleton.
