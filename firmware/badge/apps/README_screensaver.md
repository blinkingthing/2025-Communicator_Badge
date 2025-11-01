# Screensaver

Animated bouncing badge logo screensaver with color cycling effects.

## Controls

- **F5**: Exit to menu
- **Any other key**: Also exits screensaver

## Features

- Hackaday skull logo bounces around the screen
- Rainbow color cycling through the logo
- Smooth physics-based movement with wall bouncing
- Starts automatically when badge is idle (if configured)

## Technical Details

- **Animation Rate**: 30 FPS (33ms per frame)
- **Velocity**: Diagonal movement at ±4 pixels per frame
- **Color Cycle**: HSV color wheel rotation for smooth rainbow effect
- **Edge Detection**: Logo bounces when hitting screen boundaries

The screensaver uses LVGL image rendering with dynamic color recoloring. The bouncing physics reverses velocity on collision with screen edges, creating a DVD-player-style bounce effect.

## Common Questions

**Q: How do I enable automatic screensaver activation?**
A: This requires integration with the main badge idle detection system (not yet implemented in this version).

**Q: Can I change the bounce speed?**
A: Yes, modify `dx` and `dy` values in the code (currently set to ±4 pixels/frame).
