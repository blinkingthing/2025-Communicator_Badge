"""Spectrum Analyzer app - displays RF spectrum activity."""

import lvgl
import gc
from apps.base_app import BaseApp
from ui import styles
from net._sx126x import SX126X_CMD_GET_RSSI_INST


class SpectrumAnalyzer(BaseApp):
    """RF spectrum analyzer using the SX1262 LoRa radio."""

    def __init__(self, name: str, badge):
        super().__init__(name, badge)
        self.foreground_sleep_ms = 100  # Update 10 times per second

        # Spectrum settings for 915 MHz ISM band
        self.start_freq = 902.0  # MHz
        self.end_freq = 928.0    # MHz
        self.num_channels = 52   # Number of frequency steps (0.5 MHz apart)
        self.channel_width = (self.end_freq - self.start_freq) / self.num_channels

        # Display settings
        self.graph_x_offset = 35  # Left margin for dBm scale
        self.bar_width = 7  # Width of each frequency bar (52 × 7 = 364 pixels)
        self.graph_height = 95  # Height of the spectrum graph
        self.graph_y_offset = 25  # Y position where graph starts

        # RSSI history for each channel (for averaging/smoothing)
        self.rssi_history = [[-120.0] * 3 for _ in range(self.num_channels)]
        self.current_channel = 0

        # Adaptive baseline tracking
        self.baseline_rssi = -120.0  # Noise floor
        self.max_rssi = -40.0  # Strongest signal seen
        self.baseline_samples = 0
        self.baseline_calibrated = False

        # Peak tracking
        self.peak_rssi = -120.0
        self.peak_channel = 0

        # LVGL objects
        self.title_label = None
        self.status_label = None
        self.info_label = None
        self.freq_labels = []
        self.scale_labels = []
        self.grid_lines = []
        self.spectrum_bars = []

        # Radio state
        self.original_freq = None
        self.scanning_active = False

    def switch_to_foreground(self):
        """Set up the spectrum analyzer screen."""
        super().switch_to_foreground()
        self.badge.display.clear()
        self.badge.display.screen.set_style_bg_color(lvgl.color_hex(0x000000), 0)

        # Set up function key labels
        self.badge.display.f1("Hold", styles.hackaday_yellow)
        self.badge.display.f3("Recal", styles.hackaday_yellow)
        self.badge.display.f5("Exit", styles.hackaday_yellow)

        # Create title label
        self.title_label = lvgl.label(self.badge.display.screen)
        self.title_label.set_text("Spectrum Analyzer - 902-928 MHz")
        self.title_label.set_style_text_color(styles.hackaday_yellow, 0)
        self.title_label.set_style_text_font(lvgl.font_montserrat_12, 0)
        self.title_label.set_pos(10, 2)

        # Create status label
        self.status_label = lvgl.label(self.badge.display.screen)
        self.status_label.set_text("Scanning...")
        self.status_label.set_style_text_color(lvgl.color_hex(0x00FF00), 0)
        self.status_label.set_style_text_font(lvgl.font_montserrat_12, 0)
        self.status_label.set_pos(360, 2)

        # Create info label (shows peak and current info)
        self.info_label = lvgl.label(self.badge.display.screen)
        self.info_label.set_text("Peak: --- dBm")
        self.info_label.set_style_text_color(lvgl.color_hex(0xFFFFFF), 0)
        self.info_label.set_style_text_font(lvgl.font_montserrat_12, 0)
        self.info_label.set_pos(10, 16)

        # Draw frequency labels at bottom
        self.draw_freq_labels()

        # Create spectrum bars
        for i in range(self.num_channels):
            bar = lvgl.obj(self.badge.display.screen)
            bar.set_size(self.bar_width - 1, 1)  # Start with minimal height
            bar.set_pos(self.graph_x_offset + i * self.bar_width, self.graph_y_offset + self.graph_height)
            bar.set_style_bg_color(lvgl.color_hex(0x00FF00), 0)
            bar.set_style_border_width(0, 0)
            self.spectrum_bars.append(bar)

        # Save original radio frequency
        try:
            self.original_freq = self.badge.lora.frequency
            self.scanning_active = True
        except:
            pass

    def draw_freq_labels(self):
        """Draw frequency labels and grid lines."""
        # Draw vertical grid lines and labels every 5 MHz
        # 902, 905, 910, 915, 920, 925 MHz
        grid_freqs = [902, 905, 910, 915, 920, 925, 928]

        for freq in grid_freqs:
            # Calculate channel position for this frequency
            ch = int((freq - self.start_freq) / self.channel_width)
            if ch < 0 or ch >= self.num_channels:
                continue

            x_pos = self.graph_x_offset + ch * self.bar_width

            # Draw vertical grid line (subtle, behind the bars)
            line = lvgl.obj(self.badge.display.screen)
            line.set_size(1, self.graph_height)
            line.set_pos(x_pos, self.graph_y_offset)
            line.set_style_bg_color(lvgl.color_hex(0x333333), 0)  # Dark gray
            line.set_style_border_width(0, 0)
            self.grid_lines.append(line)

            # Draw frequency label at bottom
            label = lvgl.label(self.badge.display.screen)
            label.set_text(f"{freq}")
            label.set_style_text_color(lvgl.color_hex(0xAAAAAA), 0)  # Light gray
            label.set_style_text_font(lvgl.font_montserrat_12, 0)
            label.set_pos(x_pos - 10, 123)  # Position below graph with margin
            self.freq_labels.append(label)

    def draw_scale_labels(self):
        """Draw dBm scale on the left side."""
        # Clear old scale labels
        for label in self.scale_labels:
            try:
                label.delete()
            except:
                pass
        self.scale_labels = []

        # Draw scale at top, middle, and bottom
        scale_values = [
            (self.max_rssi, self.graph_y_offset),  # Top
            ((self.baseline_rssi + self.max_rssi) / 2, self.graph_y_offset + self.graph_height // 2),  # Middle
            (self.baseline_rssi, self.graph_y_offset + self.graph_height - 10),  # Bottom
        ]

        for rssi, y_pos in scale_values:
            label = lvgl.label(self.badge.display.screen)
            label.set_text(f"{rssi:.0f}")
            label.set_style_text_color(lvgl.color_hex(0x888888), 0)
            label.set_style_text_font(lvgl.font_montserrat_12, 0)
            label.set_pos(2, y_pos)
            self.scale_labels.append(label)

    def recalibrate(self):
        """Reset calibration to start fresh."""
        self.baseline_rssi = -120.0
        self.max_rssi = -40.0
        self.baseline_samples = 0
        self.baseline_calibrated = False
        self.peak_rssi = -120.0
        self.peak_channel = 0
        # Clear RSSI history
        self.rssi_history = [[-120.0] * 3 for _ in range(self.num_channels)]
        # Clear scale labels (will be redrawn after recalibration)
        for label in self.scale_labels:
            try:
                label.delete()
            except:
                pass
        self.scale_labels = []

    def get_instantaneous_rssi(self):
        """Get instantaneous RSSI from the radio."""
        try:
            # Call the low-level command to get instantaneous RSSI
            rssi_buf = bytearray(1)
            rssi_buf_mv = memoryview(rssi_buf)

            # Send GET_RSSI_INST command
            self.badge.lora.radio.SPIreadCommand([SX126X_CMD_GET_RSSI_INST], 1, rssi_buf_mv, 1)

            # Convert to dBm (same formula as packet RSSI)
            rssi_raw = rssi_buf[0]
            rssi_dbm = -1.0 * rssi_raw / 2.0

            return rssi_dbm
        except Exception as e:
            # If we can't get RSSI, return a very low value
            return -120.0

    def scan_spectrum(self):
        """Scan one channel and update the display."""
        if not self.scanning_active:
            return

        try:
            import time

            # Calculate frequency for current channel
            freq = self.start_freq + (self.current_channel * self.channel_width)

            # Set radio to this frequency and let it settle
            self.badge.lora.radio.setFrequency(freq)
            self.badge.lora.radio.standby()
            time.sleep_ms(5)  # Let frequency settle

            # Put radio in RX mode briefly to measure RSSI
            self.badge.lora.radio.setRx(0)  # Continuous RX
            time.sleep_ms(2)  # Brief delay to start receiving

            # Get instantaneous RSSI
            rssi = self.get_instantaneous_rssi()

            # Return to standby
            self.badge.lora.radio.standby()

            # Add to history and average
            self.rssi_history[self.current_channel].pop(0)
            self.rssi_history[self.current_channel].append(rssi)
            avg_rssi = sum(self.rssi_history[self.current_channel]) / len(self.rssi_history[self.current_channel])

            # Auto-calibrate baseline during first few scans
            if self.baseline_samples < 200:  # Calibrate over ~4 full scans
                if self.baseline_samples == 0:
                    self.baseline_rssi = avg_rssi
                    self.max_rssi = avg_rssi
                else:
                    # Track minimum (noise floor) and maximum
                    self.baseline_rssi = min(self.baseline_rssi, avg_rssi)
                    self.max_rssi = max(self.max_rssi, avg_rssi)
                self.baseline_samples += 1

                if self.baseline_samples == 200:
                    self.baseline_calibrated = True
                    # Add some margin to the range
                    range_db = self.max_rssi - self.baseline_rssi
                    if range_db < 20:  # Ensure minimum 20dB dynamic range
                        self.max_rssi = self.baseline_rssi + 20
            else:
                # Update max if we see something stronger
                self.max_rssi = max(self.max_rssi, avg_rssi)

            # Scale relative to adaptive baseline
            # Map from baseline to max_rssi across the full height
            dynamic_range = max(20, self.max_rssi - self.baseline_rssi)  # At least 20dB range
            rssi_clamped = max(self.baseline_rssi, min(self.max_rssi, avg_rssi))
            bar_height = int((rssi_clamped - self.baseline_rssi) * self.graph_height / dynamic_range)
            bar_height = max(2, min(self.graph_height, bar_height))

            # Color based on signal strength relative to baseline
            rssi_above_baseline = avg_rssi - self.baseline_rssi
            if rssi_above_baseline > dynamic_range * 0.8:
                color = 0xFF0000  # Red - very strong (top 20%)
            elif rssi_above_baseline > dynamic_range * 0.6:
                color = 0xFF8000  # Orange - strong (60-80%)
            elif rssi_above_baseline > dynamic_range * 0.4:
                color = 0xFFFF00  # Yellow - moderate (40-60%)
            elif rssi_above_baseline > dynamic_range * 0.2:
                color = 0x00FF00  # Green - weak signal (20-40%)
            else:
                color = 0x0088FF  # Blue - near baseline (bottom 20%)

            # Update bar
            bar = self.spectrum_bars[self.current_channel]
            try:
                bar.set_size(self.bar_width - 1, bar_height)
                bar.set_pos(self.graph_x_offset + self.current_channel * self.bar_width,
                           self.graph_y_offset + self.graph_height - bar_height)
                bar.set_style_bg_color(lvgl.color_hex(color), 0)
            except:
                pass

            # Track peak RSSI
            if avg_rssi > self.peak_rssi:
                self.peak_rssi = avg_rssi
                self.peak_channel = self.current_channel

            # Update info label every full scan (when returning to channel 0)
            if self.current_channel == 0 and self.info_label:
                try:
                    if not self.baseline_calibrated:
                        # Show calibration progress
                        progress = int(self.baseline_samples * 100 / 200)
                        self.info_label.set_text(f"Calibrating... {progress}%")
                    else:
                        # Show peak and baseline info
                        peak_freq = self.start_freq + (self.peak_channel * self.channel_width)
                        self.info_label.set_text(f"Peak:{self.peak_rssi:.0f}dBm @ {peak_freq:.0f}MHz | Base:{self.baseline_rssi:.0f}dBm")
                        # Update scale labels after calibration
                        self.draw_scale_labels()
                except:
                    pass

            # Move to next channel
            self.current_channel = (self.current_channel + 1) % self.num_channels

        except Exception as e:
            # If scanning fails, just continue
            pass

    def run_foreground(self):
        """Main loop - scan spectrum."""
        # Check for hold (pause scanning)
        if self.badge.keyboard.f1():
            self.scanning_active = not self.scanning_active
            if self.scanning_active:
                try:
                    self.status_label.set_text("Scanning...")
                    self.status_label.set_style_text_color(lvgl.color_hex(0x00FF00), 0)
                except:
                    pass
            else:
                try:
                    self.status_label.set_text("Held")
                    self.status_label.set_style_text_color(lvgl.color_hex(0xFFFF00), 0)
                except:
                    pass
            return

        # Check for recalibrate
        if self.badge.keyboard.f3():
            self.recalibrate()
            return

        # Check for exit
        if self.badge.keyboard.f5():
            self.switch_to_background()
            return

        # Scan next channel
        if self.scanning_active:
            self.scan_spectrum()

    def switch_to_background(self):
        """Clean up when going to background."""
        super().switch_to_background()

        # Stop scanning
        self.scanning_active = False

        # Restore original radio frequency
        if self.original_freq:
            try:
                self.badge.lora.radio.setFrequency(self.original_freq)
                self.badge.lora.radio.standby()
            except:
                pass

        # Clear all bars
        for bar in self.spectrum_bars:
            try:
                bar.delete()
            except:
                pass
        self.spectrum_bars = []

        # Clear grid lines
        for line in self.grid_lines:
            try:
                line.delete()
            except:
                pass
        self.grid_lines = []

        # Clear labels
        for label in self.freq_labels:
            try:
                label.delete()
            except:
                pass
        self.freq_labels = []

        for label in self.scale_labels:
            try:
                label.delete()
            except:
                pass
        self.scale_labels = []

        if self.title_label:
            try:
                self.title_label.delete()
            except:
                pass
            self.title_label = None

        if self.status_label:
            try:
                self.status_label.delete()
            except:
                pass
            self.status_label = None

        if self.info_label:
            try:
                self.info_label.delete()
            except:
                pass
            self.info_label = None

        # Clear display
        try:
            self.badge.display.clear()
        except:
            pass


# Export the app class
App = SpectrumAnalyzer
