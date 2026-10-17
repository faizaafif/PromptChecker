# Contributing to PromptCheck

Thanks for your interest in contributing! This project is intentionally small and beginner-friendly.

## Quick start
1. Fork the repo and create a new branch.
2. Set up the environment:
   ```powershell
   D:\repos\PromptChecker\.venv\Scripts\python.exe -m pip install -e "D:\repos\PromptChecker[dev]"
   ```
3. Run tests:
   ```powershell
   D:\repos\PromptChecker\.venv\Scripts\python.exe -m pytest -v
   ```

## How to contribute
- Open an issue (or comment on an existing one) before big changes.
- Keep PRs small and focused.
- Add tests for new behavior.
- Update docs if you change user-facing behavior.

## Code style
- Prefer clear, readable Python over cleverness.
- Use type hints where they improve clarity.
- Keep functions small and single-purpose.

## Reporting bugs
Include:
- Steps to reproduce
- Expected vs actual behavior
- Python version (`python --version`)

## Review process
A maintainer will review your PR. Expect feedback and iteration  this is normal and welcome.
