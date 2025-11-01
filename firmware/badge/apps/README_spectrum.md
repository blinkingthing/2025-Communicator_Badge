# Spectrum Analyzer

Real-time RF spectrum analyzer and waterfall display for the 902-928 MHz ISM band using the SX1262 LoRa radio.

## Controls

- **F1**: Hold/Resume scanning
- **F3**: Recalibrate baseline and dynamic range
- **F4**: Toggle between Spectrum and Waterfall modes
- **F5**: Exit to menu

## Display Modes

### Spectrum Mode
Shows instantaneous signal strength across all frequencies as vertical bars. Color indicates relative signal strength from blue (noise floor) to red (strongest signals). Great for finding active channels and identifying interference.

### Waterfall Mode
Displays signal activity over time with frequency on X-axis and time on Y-axis. Newest data appears at the bottom, older data scrolls upward. Ideal for visualizing intermittent signals, frequency hopping patterns, and temporal RF activity.

## Technical Details

- **Frequency Range**: 902-928 MHz (US ISM band)
- **Channels**: 52 frequencies, 0.5 MHz spacing
- **Scan Rate**: ~1-2 complete scans per second
- **RSSI Method**: Instantaneous RSSI via SX126X_CMD_GET_RSSI_INST
- **Calibration**: First 200 samples (~4 scans) learn noise floor and dynamic range
- **Color Coding**: Adaptive percentile-based (0-20% blue, 20-40% green, 40-60% yellow, 60-80% orange, 80-100% red)

### Radio Settling
The radio requires time to settle after frequency changes:
- 5ms delay after `setFrequency()`
- 2ms delay after entering RX mode

This ensures accurate RSSI measurements. Without proper settling, readings can be unreliable.

### Adaptive Baseline
The spectrum analyzer automatically learns the RF environment during initial calibration:
- **Baseline**: Minimum RSSI observed (noise floor)
- **Max**: Maximum RSSI observed (strongest signal)
- **Dynamic Range**: Automatically maintains at least 20 dB range

All colors and scales adjust relative to these learned values, making the display useful in both quiet and busy RF environments.

## Common Questions

**Q: Why does it show "Calibrating..." at startup?**
A: The analyzer needs to learn the noise floor and signal range of your RF environment. This takes about 4 full scans (~2-4 seconds).

**Q: Why do I need to recalibrate?**
A: If the RF environment changes significantly (e.g., moving locations, strong transmitter turns on/off), recalibrating resets the baseline and improves display sensitivity.

**Q: What RSSI values are normal?**
A: Noise floor is typically -110 to -120 dBm. Nearby LoRa transmitters appear around -40 to -80 dBm. Distant signals are -90 to -110 dBm.

**Q: Can this detect non-LoRa signals?**
A: Yes! The instantaneous RSSI measurement detects any RF energy in the band, regardless of modulation type. You'll see WiFi, Zigbee, LoRa, and other ISM band users.

**Q: Why are some channels always blue?**
A: Those frequencies are at or near the noise floor - no detectable signal activity. This is normal for unused channels.

**Q: Does this affect normal badge LoRa operation?**
A: The analyzer saves and restores the original radio frequency when entering/exiting. However, the radio cannot send/receive LoRa packets while spectrum scanning is active.
