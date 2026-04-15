# Refresh — mini-mapreduce module plugin loading

## Quick recall
1. `importlib.util.spec_from_file_location(...)` is still the right path for direct file loading.
2. `importlib.import_module("pkg.module")` loads an already importable module using normal package resolution.
3. Module packages generally need to be on `PYTHONPATH`, installed, or otherwise reachable from the interpreter environment.
4. Preserve the same plugin callable contract so module-based jobs and file-based jobs stay interchangeable.

## Self-test
- Why keep both loading modes? Because file paths are great for local demos, while dotted modules are better for reusable packaged jobs.
- What should the CLI expose? One plugin flag is enough if the loader can detect file path vs module reference automatically.
