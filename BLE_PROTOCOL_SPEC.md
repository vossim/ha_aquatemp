# AquaTemp Heat Pump — Direct BLE Control Protocol Specification

All commands sent over the BLE GATT write characteristic as **ASCII hex strings** (not binary).

---

## 1. BLE Setup

| Parameter | Value |
|-----------|-------|
| Service UUID | `0000fee7-0000-1000-8000-00805f9b34fb` |
| Write characteristic | `0000fec7-0000-1000-8000-00805f9b34fb` |
| Notify characteristic | `0000fec8-0000-1000-8000-00805f9b34fb` |
| CCCD UUID | `00002902-0000-1000-8000-00805f9b34fb` |
| Write type | `WRITE_TYPE_NO_RESPONSE` (2) |
| Allow long write | `true` |

**Connection sequence:**
1. Connect to device
2. Discover services
3. Subscribe to notifications on `0000fec8...` characteristic (write `0100` to its CCCD `00002902...`)
4. Begin polling with FC03 read frame

---

## 2. Frame Encoding

Frames are sent and received as **ASCII hex strings** — each Modbus byte is encoded as exactly two upper-case or lower-case hexadecimal ASCII characters.

For example, the binary frame `63 03 00 07 00 2D 3C 54` is transmitted as the string:
```
"63030007002D3C54"
```

CRC is **Modbus CRC-16** (polynomial 0xA001, init 0xFFFF), appended **little-endian** (low byte first, then high byte).

```python
def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def build_frame(msg: bytes) -> str:
    crc = crc16_modbus(msg)
    frame = msg + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    return frame.hex().upper()
```

Slave address is always **0x63** (99 decimal).

---

## 3. Polling — FC03 Read (Status + Control Registers)

Send this frame periodically to read all 45 registers:

```
63030007002D3C54
```

Decoded:
- `63` — slave address
- `03` — FC03 (Read Holding Registers)
- `0007` — start register: 7
- `002D` — quantity: 45
- `3C54` — CRC (little-endian: 3C=low, 54=high → CRC value 0x543C)

**Device response format:**
```
63 03 5A [reg0_hi] [reg0_lo] [reg1_hi] [reg1_lo] ... [reg44_hi] [reg44_lo] [crc_lo] [crc_hi]
```
As ASCII hex string: `"63035A[90 hex pairs][4 CRC chars]"` = 198 characters total.

- `63` — slave
- `03` — FC03 echo
- `5A` — byte count = 90 (= 45 × 2)
- 45 register values, each as 16-bit big-endian signed integer

---

## 4. Register Map

Registers are indexed 0–44 in the FC03 response (register 0 = first value after byte count).

| Index | Modbus Addr | Name | Type | Notes |
|-------|-------------|------|------|-------|
| 0 | 7 | SetPVReadyMode | enum | PV solar ready mode |
| 1 | 8 | Power | bool | **0=off, 1=on** |
| 2 | 9 | SetFrequencyMode | enum | Compressor frequency mode |
| 3 | 10 | SetFanMode | enum | Fan speed mode |
| 4 | 11 | EnBoostMode | bool | Boost/turbo mode enable |
| 5 | 12 | EnAPPTimeUpdate | bool | Enable app time sync |
| 6 | 13 | Mode | enum | **Operating mode (see §6)** |
| 7 | 14 | SetCurrentTemp | temp×10 | Set temperature (general) |
| 8 | 15 | ModeType | enum | Single/dual system type |
| 9 | 16 | SetTempUnit | enum | **0=°C, 1=°F** |
| 10 | 17 | EnOutletWaterTempSensor | bool | Enable outlet sensor |
| 11 | 18 | EnSlient | bool | Silent mode enable |
| 12 | 19 | SetCoolTargetTemp | temp×10 | **Cooling setpoint** |
| 13 | 20 | SetHeatTargetTemp | temp×10 | **Heating setpoint** |
| 14 | 21 | SetAutoTargetTemp | temp×10 | Auto mode setpoint |
| 15 | 22 | SetCoolMinTargetTemp | temp×10 | Minimum cooling setpoint |
| 16 | 23 | SetCoolMaxTargetTemp | temp×10 | Maximum cooling setpoint |
| 17 | 24 | SetHeatMinTargetTemp | temp×10 | Minimum heating setpoint |
| 18 | 25 | SetHeatMaxTargetTemp | temp×10 | Maximum heating setpoint |
| 19 | 26 | InletWaterTemp | temp×10 | **Inlet water temp (read-only)** |
| 20 | 27 | OutletWaterTemp | temp×10 | **Outlet water temp (read-only)** |
| 21 | 28 | AT | temp×10 | **Ambient air temp (read-only)** |
| 22 | 29 | EnTimerSlient | bool | Timer-based silent mode |
| 23 | 30 | SetTimerSlientStartTime | time | Silent start time |
| 24 | 31 | SetTimerSlientStopTime | time | Silent stop time |
| 25 | 32 | EnTimer1On | bool | Timer 1 on-enable |
| 26 | 33 | EnTimer1Off | bool | Timer 1 off-enable |
| 27 | 34 | SetTimer1StartHour | int | Timer 1 start hour |
| 28 | 35 | SetTimer1StartMinute | int | Timer 1 start minute |
| 29 | 36 | SetTimer1StopHour | int | Timer 1 stop hour |
| 30 | 37 | SetTimer1StopMinute | int | Timer 1 stop minute |
| 31 | 38 | SetCompType | enum | Compressor type |
| 32 | 39 | Sys1CompWorkingFreq | int | System 1 compressor working frequency |
| 33 | 40 | SetHeatMaxFreq | int | Max heating frequency |
| 34 | 41 | SetCoolMaxFreq | int | Max cooling frequency |
| 35 | 42 | EnSupportAI | bool | AI support enable |
| 36 | 43 | SetAIMode | enum | AI mode setting |
| 37 | 44 | EnAIPower | bool | AI power enable |
| 38 | 45 | CompressorCurrentDetect | int | Compressor current |
| 39 | 46 | InverterBoardACInputVoltage | int | AC input voltage |
| 40 | 47 | Fault1 | bitmask | Fault flags |
| 41 | 48 | MainBoardSoftwareVer | int | Main board software version |
| 42 | 49 | MainBoardSoftwareCode | int | Main board software code |
| 43 | 50 | DisplaySoftwareVer | int | Display software version |
| 44 | 51 | DisplaySoftwareCode | int | Display software code |

---

## 5. Writing Registers — FC16 Single Register Write

To change a single register, send an FC16 Write Multiple Registers frame with quantity=1.

**Frame structure:**
```
63 10 [addr_hi] [addr_lo] 00 01 02 [val_hi] [val_lo] [crc_lo] [crc_hi]
```
= 11 bytes = 22 ASCII hex characters

Use the **Modbus address** from column 3 of the register table above (7–51 range, same as FC03 read).

### Common Write Commands

| Command | ASCII Hex Frame |
|---------|----------------|
| Power ON | `631000080001020001D7BA` |
| Power OFF | `631000080001020000167A` |
| Mode = singleCool | `6310000D0001020000162F` |
| Mode = singleHeat | `6310000D0001020001D7EF` |
| Mode = cool       | `6310000D000102000297EE` |
| Mode = heat       | `6310000D0001020003562E` |
| Mode = auto       | `6310000D000102000417EC` |
| SetHeatTargetTemp = 25.0°C | `6310001400010200FA9465` |
| SetHeatTargetTemp = 30.0°C | `63100014000102012C146B` |
| SetCoolTargetTemp = 20.0°C | `6310001300010200C81407` |
| SetAutoTargetTemp = 28.0°C | `631000150001020118146D` |

---

## 6. Value Encodings

### Power (register index 1)
| Value | Meaning |
|-------|---------|
| `0x0000` | Off |
| `0x0001` | On |

### Mode (register index 6)
| Value | Meaning |
|-------|---------|
| `0x0000` | singleCool — cooling only (single-circuit) |
| `0x0001` | singleHeat — heating only (single-circuit) |
| `0x0002` | cool — cooling |
| `0x0003` | heat — heating |
| `0x0004` | auto — automatic |

### Temperature registers (×10 encoding)
All temperature values are stored as signed 16-bit integers **multiplied by 10**:

| °C | Register value | Hex |
|----|---------------|-----|
| 25.0 | 250 | `0x00FA` |
| 30.0 | 300 | `0x012C` |
| 20.0 | 200 | `0x00C8` |
| -5.0 | -50 | `0xFFCE` |
| 0.5 | 5 | `0x0005` |

Applicable to: SetCoolTargetTemp, SetHeatTargetTemp, SetAutoTargetTemp, SetCoolMinTargetTemp, SetCoolMaxTargetTemp, SetHeatMinTargetTemp, SetHeatMaxTargetTemp, InletWaterTemp, OutletWaterTemp, AT (ambient).

**Temperature min/max constraints observed in app code:**
- Max target temp: 32.0°C (320 = `0x0140`) — app enforces upper bound
- Min target temp: 31.5°C lower limit also referenced (315 = `0x013B`)

---

## 7. FC16 Bulk Write (45 Registers)

The app also supports writing all 45 registers at once to device-type-specific bank addresses.  
This is used after connecting (device configuration sync) and potentially when changing modes.

**Frame structure:**
```
63 10 [bank_hi] [bank_lo] 00 2D 5A [reg0_hi] [reg0_lo] ... [reg44_hi] [reg44_lo] [crc_lo] [crc_hi]
```
Total: 1+1+2+2+1+90+2 = **99 bytes** = **198 ASCII hex characters**

### Bank addresses by device type

| Bank | Start Addr | Device type | Expected device response |
|------|-----------|-------------|--------------------------|
| 0 | 1001 (0x03E9) | linkedGo | `631003E9002DD9E6` |
| 1 | 1046 (0x0416) | mini | `63100416002DE8A2` |
| 2 | 1091 (0x0443) | pc1006 | `63100443002DF8B2` |
| 3 | 1136 (0x0470) | (unknown) | `63100470002D08BD` |
| 4 | 2001 (0x07D1) | (unknown) | `631007D1002D591B` |
| 5 | 2046 (0x07FE) | (unknown) | `631007FE002D68D2` |

The device echoes back the FC16 response (8 bytes = 16 ASCII hex chars):
`63 10 [bank_hi] [bank_lo] 00 2D [crc_lo] [crc_hi]`

The register data order in the bulk write payload matches the FC03 response order (index 0 = SetPVReadyMode ... index 44 = DisplaySoftwareCode).

---

## 8. Recommended Polling Loop

```
1. Connect + subscribe to notifications
2. Loop every ~2 seconds:
   a. Write "63030007002D3C54" to write characteristic
   b. Wait for notification on notify characteristic
   c. Parse 45-register response (strip leading "63035A", trailing CRC)
   d. Extract values: Power=[1], Mode=[6], InletTemp=[19], OutletTemp=[20], AT=[21]
3. On user command: send appropriate single-register FC16 write
```

---

## 9. Example: Parse FC03 Response

```python
def parse_fc03_response(hex_string: str) -> dict:
    data = bytes.fromhex(hex_string)
    # Validate: slave=0x63, FC=0x03, byte_count=0x5A
    assert data[0] == 0x63 and data[1] == 0x03 and data[2] == 0x5A
    regs = []
    for i in range(45):
        hi = data[3 + i*2]
        lo = data[3 + i*2 + 1]
        val = (hi << 8) | lo
        # Treat as signed 16-bit
        if val >= 0x8000:
            val -= 0x10000
        regs.append(val)
    
    return {
        'power': regs[1],                       # 0=off, 1=on
        'mode': regs[6],                         # 0-4
        'setHeatTemp_C': regs[13] / 10.0,        # e.g., 250 → 25.0°C
        'setCoolTemp_C': regs[12] / 10.0,
        'inletWaterTemp_C': regs[19] / 10.0,
        'outletWaterTemp_C': regs[20] / 10.0,
        'ambientTemp_C': regs[21] / 10.0,
        'fault': regs[40],
    }
```

---

## 10. Notes and Uncertainties

1. **Single vs bulk write addressing**: Single register writes use addresses 7–51 (the FC03 read address space). Bulk writes use bank-specific addresses (1001+). The app uses single-register writes for real-time control changes and may use bulk writes for initial device sync.

2. **Device type detection**: The app selects the write bank based on device type (fP enum: linkedGo, mini, pc1006, + 3 unknown). The device type is likely negotiated during BLE pairing or read from a device descriptor. Reading register [42] (MainBoardSoftwareCode) or [43] (DisplaySoftwareCode) may identify the model.

3. **Frame encoding confirmation**: All observed pre-computed frames in the app binary are ASCII hex strings. The BLE write characteristic receives ASCII hex bytes, not raw Modbus binary.

4. **Temperature unit**: Check register [9] (SetTempUnit). If value=1 (°F mode), temperature display is in Fahrenheit but the register values remain in °C×10 (the app converts for display only — confirmed by app code showing Fahrenheit display conversion without changing the underlying ×10 integer).

5. **Fault register**: Register [40] (Fault1) is a bitmask. Individual bit meanings are not yet decoded from this analysis.
