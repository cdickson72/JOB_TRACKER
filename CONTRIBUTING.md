## Contributing to JobTracker

Thanks for your interest in contributing! This file describes the developer workflow and expectations to keep the repository consistent and high-quality.

### Setup

1. Create and activate a virtual environment:

   python -m venv .venv
   source .venv/bin/activate

2. Install the project with developer and test extras:

   python -m pip install --upgrade pip
   pip install -e '.[test,dev]'


### Pre-commit & Formatting

- Install pre-commit hooks locally (run once per checkout):

  pre-commit install

- Before pushing your changes, run the hooks across all files (this will auto-fix where supported):

  pre-commit run --all-files

- You can run linters and formatters directly:

  ruff check . --fix
  black .


### Tests

- Run the test suite locally before pushing:

  pytest -q

- The CI pipeline will run tests and linters; please make sure your branch passes these checks.


### Pull Requests

- Keep changes small and focused; open a PR with a clear description of the problem and the proposed fix.
- Make sure tests cover new behaviors or edge cases introduced by the change.
- Address review comments and ensure pre-commit hooks and tests pass.


### Coding style

- Use Black and Ruff for formatting and linting. The repository enforces formatting and lint rules in CI.
- If you introduce significant refactoring or add complexity, include tests and consider adding short notes in your PR description.
