# Contributing

Thank you for considering a contribution to this project. The guidelines below keep the codebase consistent and pull requests easy to review.

---

## Development environment

**Requirements:** Python 3.12 or 3.13, `git`.

```bash
git clone https://github.com/vossim/ha_auqatemp.git
cd ha_auqatemp

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

Run with coverage (must stay above 80 %):

```bash
pytest --cov=custom_components/auqatemp --cov-report=term-missing
```

---

## Project structure

```
custom_components/auqatemp/
  domain/          # Pure Python — no HA, no BLE imports
  application/     # Orchestration — depends on domain + port interfaces only
  infrastructure/  # Concrete adapters (BLE transport, HA platform setup)

tests/             # Mirrors the source tree
BLE_PROTOCOL_SPEC.md  # Protocol reverse-engineering notes
```

The domain layer must have **zero external dependencies**. Only `infrastructure/` may import `bleak` or `homeassistant`.

---

## Rules for contributions

### Tests

- Every new class or function needs a corresponding test file under `tests/`.
- Test behaviour, not implementation. Tests must break when contracts change, not when internals are refactored.
- No mocking of domain logic. Only mock I/O boundaries: BLE transport, HA callbacks, time.
- No `sleep` calls. Tests must be fast and deterministic.
- Coverage must remain at or above 80 %. Aim for 100 % on new code.

### Code style

- Names are intentions: `inlet_water_temp_celsius` not `t1`.
- Functions do one thing. If "and" appears in a description, split the function.
- No magic numbers inline — define named constants.
- No comments that restate the code. Only comment non-obvious invariants.
- Domain objects must be `frozen=True` dataclasses where possible.

### Security

- Never commit MAC addresses, tokens, or any credentials — not in source, not in tests, not in comments.
- All data received over BLE must pass CRC validation before use.
- Do not log MAC addresses or frame payloads.
- Before adding a dependency, check it against [OSV](https://osv.dev) and run `pip-audit`.

---

## Submitting a pull request

1. Fork the repo and create a feature branch from `main`.
2. Make your changes — small, focused PRs are easier to review than large ones.
3. Ensure `pytest` passes and coverage stays above 80 %.
4. Ensure `pip-audit --local` reports no vulnerabilities.
5. Open a pull request against `main`. Describe what the change does and why.

CI runs automatically on every PR. All checks must be green before merge.

---

## Reporting bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.yml) issue template. Include:

- Home Assistant version
- Integration version
- Your heat pump model (if known)
- Relevant log lines from `Settings → System → Logs` (filter for `auqatemp`)

Do **not** include your device's MAC address in any issue or log snippet.

---

## Requesting features

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.yml) template. Describe the use case, not just the desired behaviour — it helps evaluate whether the feature fits the scope of this integration.
