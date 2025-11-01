# Hardware Monitor

Multi-page system information display showing real-time badge hardware status.

## Controls

- **F1**: Previous page
- **F2**: Next page
- **Arrow Up/Down**: Scroll within page (if content exceeds screen)
- **F5**: Exit to menu

## Pages

1. **System** - CPU frequency, chip temperature, flash size, Python version, uptime
2. **Memory** - RAM usage, garbage collection stats, heap information
3. **Display** - Screen specs, backlight level, LVGL version
4. **LoRa** - Radio configuration, frequency, power, modulation parameters, signal stats
5. **I2C/GPIO** - Connected I2C devices, pin assignments
6. **Config** - Badge configuration values (alias, radio settings, etc.)

## Technical Details

- **Update Rate**: Refreshes every 1 second (20 iterations × 50ms)
- **Max Visible Lines**: 9 lines per screen
- **Scrolling**: Automatic when page content exceeds display height
- **Memory**: Forces garbage collection before displaying memory stats

The monitor reads hardware state from various badge subsystems including the ESP32, LoRa radio (SX1262), display controller, and I2C buses. It displays a scroll indicator (e.g., "1-9/15") when content is scrollable.

## Common Questions

**Q: Why does the memory usage change when I open this app?**
A: The app runs `gc.collect()` before displaying memory stats to show accurate available memory.

**Q: What does "Last RSSI" mean on the LoRa page?**
A: RSSI (Received Signal Strength Indicator) shows the signal strength of the last received packet in dBm. More negative = weaker signal.

**Q: Can I add custom monitoring pages?**
A: Yes, add new page names to `self.pages` and create corresponding `get_*_info()` methods.
