# PromptCheck

PromptCheck is a lightweight, extensible toolkit for running repeatable prompt tests against AI model providers.

> Status: **working CLI + core engine** (mock provider only).

## Goals (initial)
- Define prompt test suites in YAML
- Run tests against a provider interface (mock first)
- Evaluate responses with simple evaluators
- Produce machine-readable JSON reports

## Requirements
- Python 3.13+ (current project target)

## Installation (development)
```powershell
# From the repo root
D:\repos\PromptChecker\.venv\Scripts\python.exe -m pip install -e "D:\repos\PromptChecker[dev]"
```

## Usage
### Run a suite
```powershell
D:\repos\PromptChecker\.venv\Scripts\python.exe -m promptcheck run D:\repos\PromptChecker\examples\basic-suite.yaml
```

**Expected output (example):**
```
Suite: basic-suite
Provider: mock
Total: 1  Passed: 1  Failed: 0  Errors: 0
Duration: 0.0001s
  [PASS] greet
```

### Write a JSON report
```powershell
D:\repos\PromptChecker\.venv\Scripts\python.exe -m promptcheck run D:\repos\PromptChecker\examples\basic-suite.yaml --report D:\repos\PromptChecker\reports\result.json
```

## Minimal YAML schema (v0)
```yaml
suite_name: "basic-suite"
provider:
  name: "mock"
  config:
    responses:
      hello: "Hello world"
tests:
  - name: "greet"
    prompt: "hello"
    expect:
      evaluator: "exact_match"
      value: "Hello world"
```

## Evaluators (current)
- `exact_match` — pass if the response exactly equals the expected value
- `contains` — pass if the expected value appears in the response

## Provider (current)
- `mock` — deterministic responses from YAML config (no network)

## Tests
```powershell
D:\repos\PromptChecker\.venv\Scripts\python.exe -m pytest -v
```

## License
MIT
