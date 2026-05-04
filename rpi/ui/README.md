# SFES Lab UI

Shows the SmartFarm dashboard and control screen for `GH1`. `GH2` is a future expansion target.

## Direction

The UI should be implemented as:

- FastAPI backend
- Static HTML/CSS frontend
- Vanilla JavaScript running in Chromium

Node.js is not required on Raspberry Pi for this approach. The JavaScript files are served as static files and executed by the browser.

React/Vite is not part of the current implementation target. It can be revisited later if the frontend becomes large enough to need a component build system.

## Target Screen

- 10.1" IPS capacitive touch display
- 1280x800 resolution
- Chromium kiosk mode
- Tabs: Monitoring, Control, Graph, Settings

## Control UX

- Slider, toggle, and radio changes publish MQTT commands immediately.
- The UI should not require a separate Apply button for normal actuator control.
- The frontend should still avoid duplicate events and excessive slider spam.
- For PWM sliders, prefer `change`/release events or a short debounce.

## Window Startup Calibration

The greenhouse windows do not have position sensors. To calculate opening percentage reliably, the system needs a known fully-closed reference point.

On UI/backend startup, run a startup calibration:

1. Drive windows in the close direction for about 5 seconds.
2. Send `stop`.
3. Treat this fully closed state as the opening-rate reference.

This is intentional operating behavior, not an accidental startup side effect.

## Run

Planned FastAPI entrypoint:

```powershell
uvicorn rpi.ui.server:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Production kiosk goal:

```bash
chromium-browser --kiosk http://127.0.0.1:8000
```
