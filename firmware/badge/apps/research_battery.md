# Battery Monitoring Research

## Hardware: MCP73831 Li-Ion Battery Charger

The badge uses the MCP73831 battery charge management controller for charging a single Li-Ion/Li-Polymer cell.

### MCP73831 Features
- Linear charge management controller
- 4.20V regulation voltage (standard Li-Ion)
- Programmable charge current: 15mA to 500mA
- Integrated pass transistor and current sense
- Charge status output (STAT pin)
- Thermal regulation

### Available Pins

**STAT Pin** - Tri-state charge status output:
- **High-Z** - Shutdown or No Battery Present
- **Low** - Charging (Preconditioning, Constant Current, or Constant Voltage modes)
- **High** - Charge Complete / Standby

**VBAT Pin** - Battery voltage output:
- Connected to positive terminal of battery
- Voltage range: ~3.0V (empty) to 4.2V (full)
- Can be monitored via ADC with voltage divider

### Potential Hardware Monitor Features

#### 1. Battery Voltage Monitoring
- Read VBAT via ESP32-S3 ADC (if connected to GPIO)
- Display actual voltage in System page
- Typical Li-Ion voltages:
  - 4.20V = 100% charged
  - 3.70V = ~50% charged
  - 3.00V = Empty (cutoff)

#### 2. Charge Status
- Read STAT pin as digital GPIO
- Display charging state:
  - "Charging" (Low)
  - "Complete" (High)
  - "No Battery/Shutdown" (High-Z)

#### 3. Battery Percentage Estimation
- Calculate % from voltage using Li-Ion discharge curve
- Formula (approximate):
  ```python
  if voltage >= 4.2:
      percent = 100
  elif voltage >= 3.7:
      percent = 50 + ((voltage - 3.7) / 0.5) * 50
  elif voltage >= 3.0:
      percent = ((voltage - 3.0) / 0.7) * 50
  else:
      percent = 0
  ```

## TODO: Identify GPIO Pin Assignments

Need to determine which ESP32-S3 GPIO pins are connected to:
1. **MCP73831 STAT pin** - For charge status
2. **VBAT monitoring** - For battery voltage (with voltage divider)

### Investigation Steps:
1. Check schematic (if available in documentation/)
2. Test ADC-capable pins (GPIO 1-10) for voltage in 3.0-4.2V range
3. Test digital pins for STAT signal behavior during charging

### ESP32-S3 ADC Channels
The ESP32-S3 has two ADC units:
- **ADC1:** GPIO 1-10 (preferred - doesn't conflict with WiFi)
- **ADC2:** GPIO 11-20 (may conflict with WiFi)

### Implementation Location
Add battery info to **System page** in hwmonitor.py:
- `get_system_info()` method
- Display battery voltage, charge status, and estimated %

## References
- Datasheet: `documentation/datasheets/MCP73831-Family-Data-Sheet-DS20001984H.pdf`
- Pages 3-4: Electrical characteristics and pin functions
- Page 13: Functional block diagram and charge states
