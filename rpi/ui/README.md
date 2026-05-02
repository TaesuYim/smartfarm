# SFES Lab UI

Shows the SmartFarm dashboard for `GH1`. `GH2` is a future expansion target.

The target display is `1024x600`, but the UI should stay usable on other browser sizes. The final UI is tab-based:

- Monitoring
- Control
- Graph
- Settings

The UI is display/input only. Background services such as logger, sensor hub, and weather service should be started by supervisor/systemd.

## Run

```powershell
python -m rpi.ui.app --db-dir data --host 127.0.0.1 --port 8000
```

For fixed-file debugging:

```powershell
python -m rpi.ui.app --db smartfarm_2026_05.sqlite3 --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Production goal:

```bash
chromium-browser --kiosk http://127.0.0.1:8000
```
