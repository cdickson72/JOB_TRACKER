# JobTracker

A simple Python CLI tool for tracking job applications, resumes, cover letters, and notes.

This project is maintained as a **personal portfolio example** and is not intended for external contributions.

---

## Features

- Track job applications with status updates
- Manage multiple resumes and cover letters
- Add notes and reminders for each application
- Simple command-line interface

## Installation
```bash
pip install jobtracker
```

## Usage
```bash
# Add a new job application
jobtracker job add

# List all applications
jobtracker job list

# Update application
jobtracker job update <id>

# Update application status
jobtracker job status <id> <applied|recruiter|video_interview|1st_interview|2nd_interview|final_interview|offer|rejected|ghosted>

# Delete job application
jobtracker job remove <id>

# Add a new resume
jobtracker resume add

# List all new resume
jobtracker resume list

# Add a new cover letter
jobtracker cover-letter add

# List all new cover letter
jobtracker cover-letter list

# Add note
jobtracker note add <id>

# list note
jobtracker note list <id>
```

---

## Development Setup

1. **Create and activate a virtual environment (recommended):**
```bash
   python -m venv .venv
   source .venv/bin/activate
```

2. **Install the package and test/dev extras:**
```bash
   python -m pip install --upgrade pip
   pip install -e '.[test,dev]'
```

3. **Install the pre-commit hooks** (runs Black, Ruff, and basic checks):
```bash
   pre-commit install
```

4. **Run all hooks and auto-fix where supported:**
```bash
   pre-commit run --all-files
```

5. **Run tests:**
```bash
   pytest -q
```

6. **Lint or format manually:**
```bash
   ruff check . --fix
   black .
```

## CI/CD & Quality Gates

This project uses GitHub Actions to enforce code quality and reliability.

### Pipeline Overview
- Runs on every push and pull request
- Tested across Python 3.10, 3.11, and 3.12

### Quality Controls
- **Pre-commit hooks** (formatting, linting)
- **Ruff** for linting
- **Black** for code formatting
- **Pytest** for unit testing
- **SonarCloud** for:
  - Static code analysis
  - Security vulnerability detection
  - Code smell detection
  - Maintainability and reliability scoring

### Branch Protection
The `main` branch is protected and requires:
- Passing CI checks
- Passing SonarCloud quality gate

Merges are blocked if quality gates fail.

---

## License

MIT

## Contact

cam_stacy@yahoo.com
