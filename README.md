# JobTracker

Simple CLI to track job applications.

## Development setup ✅

1. Create and activate a virtual environment (recommended):

   python -m venv .venv
   source .venv/bin/activate

2. Install the package and test/dev extras:

   python -m pip install --upgrade pip
   pip install -e '.[test,dev]'

3. Install the pre-commit hooks (runs Black, Ruff, and basic checks):

   pre-commit install

4. To run all hooks and auto-fix where supported:

   pre-commit run --all-files

5. Run tests:

   pytest -q

6. Lint or format manually (if needed):

   ruff check . --fix
   black .

## Contributing

Please run `pre-commit run --all-files` before pushing PRs. CI runs pre-commit and tests on push/pull requests.
