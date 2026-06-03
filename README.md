# AquaTemp Heat Pump — Home Assistant Integration

[![CI](https://github.com/vossim/ha_auqatemp/actions/workflows/ci.yml/badge.svg)](https://github.com/vossim/ha_auqatemp/actions/workflows/ci.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Local Bluetooth (BLE) control for **AquaTemp heat pumps** — no cloud, no app, no account required.

The integration talks directly to the heat pump over BLE using its native Modbus-over-ASCII-hex protocol. All state is read every two seconds from the device itself; no internet connection is needed.

---

## Features

- **Full HVAC control** — heat, cool, auto, and off modes
- **Target temperature** — set independently for heating, cooling, and auto modes (5–32 °C, 0.5 °C steps)
- **Real-time temperature sensors** — inlet water, outlet water, and ambient air temperatures updated every poll cycle
- **HVAC action feedback** — reports heating, cooling, or idle based on actual inlet/outlet delta
- **Fault detection** — marks the entity unavailable when the device reports a fault
- **Fully local** — uses BLE directly; no AquaTemp cloud or third-party API
- **UI-only setup** — configured through the standard Home Assistant config flow (no YAML required)
- **HACS-installable**

---

## Supported Devices

Any AquaTemp heat pump that exposes the BLE service `0000fee7-0000-1000-8000-00805f9b34fb` and communicates over the Modbus-ASCII-hex protocol described in [BLE_PROTOCOL_SPEC.md](BLE_PROTOCOL_SPEC.md).

Known-compatible models include:

- AquaTemp linkedGo series
- AquaTemp mini series
- AquaTemp PC1006 series
- Several W’eau devices

If your device is not listed but uses the same BLE service UUID, it will very likely work. Open an issue and report your model so it can be added here.

### Requirements

- Home Assistant 2024.1 or newer
- A Bluetooth adapter visible to the HA host (built-in, USB dongle, or Bluetooth proxy)
- The heat pump powered on and within Bluetooth range (~10 m)

---

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → three-dot menu → **Custom repositories**.
3. Add `https://github.com/vossim/ha_auqatemp` with category **Integration**.
4. Find **AquaTemp Heat Pump** in the HACS integration list and click **Download**.
5. Restart Home Assistant.

### Manual

1. Download the [latest release](https://github.com/vossim/ha_auqatemp/releases/latest) ZIP.
2. Unzip and copy the `custom_components/auqatemp` folder into your HA `config/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for **AquaTemp Heat Pump**.
3. Enter the **Bluetooth MAC address** of your heat pump (format: `AA:BB:CC:DD:EE:FF`). The MAC address is usually printed on a sticker on the unit or visible in the AquaTemp mobile app under device details.
4. The integration will attempt a test connection. If it succeeds the device is added immediately.

The MAC address is stored in Home Assistant's encrypted config entry storage — it is never written to a file or logged.

---

## How to Use

### Climate card

After setup, a climate entity named **AquaTemp Heat Pump** appears under your device. Add it to a dashboard with the standard **Thermostat** card:

```yaml
type: thermostat
entity: climate.aquatemp_heat_pump
```

### HVAC modes

| HA mode | Heat pump mode |
|---|---|
| Heat | Single-heat (heating only) |
| Cool | Single-cool (cooling only) |
| Heat/Cool | Auto |
| Off | Off |

### Temperature sensors

The integration exposes three temperature readings as attributes on the climate entity:

| Attribute | Description |
|---|---|
| `current_temperature` | Inlet water temperature |
| `extra_state_attributes.outlet_temp` | Outlet water temperature |
| `extra_state_attributes.ambient_temp` | Ambient air temperature |

### Example automation

Turn the heat pump off when everyone leaves home:

```yaml
alias: Heat pump off when away
trigger:
  - platform: state
    entity_id: zone.home
    to: "0"
action:
  - service: climate.turn_off
    target:
      entity_id: climate.aquatemp_heat_pump
```

### Polling interval

The device is polled every 30 seconds by default (Home Assistant coordinator default). Reducing this below ~5 seconds is not recommended as the BLE connection needs time to settle between reads.

---

## Troubleshooting

**Entity shows unavailable**

- Ensure the heat pump is powered on and the BLE adapter can reach it.
- Check the HA logs (`Settings → System → Logs`) for `auqatemp` errors.
- If the device is far from the HA host, consider adding a [Bluetooth proxy](https://www.home-assistant.io/integrations/bluetooth/).

**"Failed to connect" during setup**

- Verify the MAC address is correct — check the sticker on the unit or the AquaTemp mobile app.
- The heat pump must not be actively connected to the AquaTemp app at the same time; close the app first.

**Fault state**

- If the climate entity reports a fault, check the physical unit for an error code on its display.
- The `fault_flags` attribute contains the raw bitmask from the device.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

[GPL v3](LICENSE)
