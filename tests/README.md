# tests/ — naming convention

pytest only collects `test_*.py`. Every other prefix is a manual script that
pytest ignores on purpose. **Pick the prefix before writing the file** — the
prefix is the contract.

| Prefix | Collected by pytest | Purpose | Run with |
|---|---|---|---|
| `test_*.py` | **yes** | Real regression tests | `.venv\Scripts\python.exe -m pytest` |
| `_diag_*.py` | no | Focused diagnostic of one system; prints `OK`/`FAIL`, exits 0/1 | `.venv\Scripts\python.exe tests\_diag_casino.py` |
| `_smoke_*.py` | no | Import / instantiation smoke check (GUI phase gates) | `.venv\Scripts\python.exe tests\_smoke_phase0.py` |
| `_temp_*.py` | no | Throwaway check for one change — delete it once the change ships | same |
| `_repro_*.py` | no | Minimal reproduction kept with a bug report | same |
| `_fix_*.py` | no | One-off savefile surgery; never imported by the game | same |
| `_sim_*.py` | no | Simulation harness (RNG / economy modelling) | same |
| `_tk_test_utils.py` | no | Shared helper: one process-wide withdrawn Tk root | imported, not run |

## Rules

1. **`test_*.py` must be import-safe.** No work at module scope, no `sys.exit()`,
   no `tk.Tk()` at import. A module-level `sys.exit()` aborts pytest collection
   with `INTERNALERROR ... SystemExit`. Put script bodies under
   `if __name__ == "__main__":`.
2. **GUI tests share one Tk root.** Use
   `from _tk_test_utils import shared_tk_root` and never call `root.destroy()`.
   Creating → destroying → creating a root in one process is flaky on some
   Windows builds (`_tkinter.TclError: invalid command name "tcl_findLibrary"`).
   Destroy your widget, not the root.
3. **`sys.path.insert(...)` is only needed for direct script runs.** pytest gets
   the repo root from `pyproject.toml` (`pythonpath = ["."]`). Direct
   `python tests\_diag_x.py` still needs the root-prepend if the script imports
   game modules.
4. **Choose the lightest form that proves the point.** One-off verification →
   `_temp_*`. Behaviour that must never regress → `test_*`.
5. **Not tests, but living here:** `enemy_audit.py` (data audit) and
   `gen_wiki_html.py` (wiki generator) are project tools — candidates to move
   to `scripts/` during the package reorg.

## Commands

```powershell
.venv\Scripts\python.exe -m pytest              # whole suite (testpaths = tests)
.venv\Scripts\python.exe -m pytest -q           # quiet
.venv\Scripts\python.exe -m pytest tests\test_phase4.py::TestPhase4Imports
.venv\Scripts\python.exe tests\_diag_karma.py   # manual diagnostic
```
