# AquaTemp HA Integration — Development Guidelines

## Testing

- All code must have unit tests. Minimum 80% coverage; aim for 100% wherever practical.
- Test behaviour, not implementation. Tests must break when contracts change, not when internals are refactored.
- Each class/function gets its own test file mirroring the source tree (e.g. `domain/heat_pump.py` → `tests/domain/test_heat_pump.py`).
- No mocking of domain logic. Only mock I/O boundaries: BLE transport, HA entity callbacks, time.
- Tests must be fast and deterministic. No sleeps, no real BLE hardware.

## SOLID

- **Single Responsibility**: one reason to change per class. BLE framing, register parsing, domain state, and HA entity wiring are separate concerns — keep them in separate classes.
- **Open/Closed**: extend behaviour through new types or strategies, not by editing existing classes. Adding a new operating mode must not require modifying the parser.
- **Liskov Substitution**: subtypes must be fully substitutable. If a test passes a stub transport, the domain code must not know or care.
- **Interface Segregation**: define narrow protocols/ABCs. The domain layer depends only on a `Transport` protocol, not a full BLE client object.
- **Dependency Inversion**: domain code depends on abstractions, never on concrete infrastructure. Inject dependencies; do not import infrastructure from domain modules.

## Clean Code

- Names are intentions: `inlet_water_temp_celsius` not `t1`, `set_heat_target` not `write_reg`.
- Functions do one thing. If you need "and" to describe it, split it.
- No magic numbers inline — define named constants (e.g. `SLAVE_ADDRESS = 0x63`, `REGISTER_COUNT = 45`).
- No comments that restate the code. Only comment non-obvious invariants (e.g. why a register value is divided by 10).
- Keep functions short. If a function doesn't fit on one screen, decompose it.
- Fail fast: validate inputs at boundaries and raise meaningful exceptions early.

## Domain-Driven Design

### Ubiquitous Language
Use the terms from the spec consistently in code and in tests:
- `HeatPump`, `OperatingMode`, `SetPoint`, `InletWaterTemp`, `OutletWaterTemp`, `AmbientTemp`
- `PowerState` (on/off), `FaultFlags`, `RegisterFrame`
- Modes: `SINGLE_COOL`, `SINGLE_HEAT`, `COOL`, `HEAT`, `AUTO`

### Layers

```
ha_aquatemp/
  domain/          # Pure Python — no HA, no BLE imports
    heat_pump.py   # HeatPump aggregate, value objects, domain events
    register_map.py
    commands.py    # Command value objects (SetPower, SetMode, SetTemperature)
    exceptions.py

  application/     # Orchestration — depends on domain + port interfaces
    heat_pump_service.py

  infrastructure/  # Concrete adapters — BLE transport, HA platform setup
    ble/
      transport.py      # Implements Transport protocol
      frame_codec.py    # Modbus CRC, ASCII hex encode/decode
    ha/
      climate_entity.py
      coordinator.py

  tests/
    domain/
    application/
    infrastructure/
```

### Rules
- The `domain/` layer has zero external dependencies (no `bleak`, no `homeassistant`).
- The `application/` layer depends on `domain/` and abstract port interfaces only.
- Only `infrastructure/` imports concrete libraries (`bleak`, `homeassistant`).
- Domain objects are immutable value objects where possible (dataclasses with `frozen=True`).
- Commands are explicit value objects — never pass raw register indices or magic ints across layer boundaries.
- Raise domain exceptions (`InvalidSetPoint`, `DeviceNotReady`) rather than leaking protocol errors upward.

---

## Security

### No secrets in the codebase
- Tokens, passwords, API keys, MAC addresses, and any other credentials must never be committed to the repository — not in source files, not in tests, not in comments.
- Use HA's config entry system (`entry.data`) for all user-supplied values such as device MAC addresses. The config flow stores these in HA's encrypted storage, not in code.
- `.gitignore` must exclude any local override files (e.g. `.env`, `secrets.yaml`, `local_settings.py`).
- If a secret is ever accidentally committed, treat it as compromised immediately.

### Dependency hygiene
- Pin dependencies to exact versions in `requirements.txt`. Use `>=` only in `manifest.json` for HA compatibility; lock to exact versions in the dev/CI environment.
- Before adding or upgrading any dependency, check it against the [OSV vulnerability database](https://osv.dev) or run `pip-audit`. No dependency with known CVEs may be introduced.
- Use only actively maintained packages. A package with no releases in 24 months or with open unpatched CVEs must not be added.
- Run `pip-audit` in CI on every pull request. A failing audit blocks the merge.
- Keep dependencies up to date. Dependabot or equivalent automated update tooling should be configured on the repository.

### Secure coding
- **Input validation at every boundary**: all data received over BLE (frame bytes, register values) and all user input from the config flow must be validated before use. Invalid input raises a domain exception — it is never silently ignored or passed further into the system.
- **No command injection**: never interpolate external data into shell commands, subprocesses, or eval calls. This codebase has no need for subprocess execution; if one is ever introduced it requires an explicit security review.
- **No SQL / template injection**: this codebase does not use a database or templating engine. If either is ever introduced, use parameterised queries and auto-escaping templates exclusively.
- **Frame integrity**: every incoming BLE frame must pass CRC validation (`validate_response_crc`) before its payload is parsed. A frame that fails CRC must raise `FrameError` and be discarded — never processed.
- **No sensitive data in logs**: do not log MAC addresses, register payloads, or any value that could identify a user's device or home. Log at `DEBUG` level only for frame-level diagnostics, and only without PII.
- **Minimal surface area**: the integration requests no HA permissions beyond what the `climate` platform requires. Do not add network listeners, HTTP endpoints, or shell access.
- **Frozen value objects**: domain value objects use `frozen=True`. This prevents accidental mutation of validated state after construction, closing a class of integrity bugs.
