# BluePhone

Interactive Linux CLI for managing **your own** Android and iOS devices. It wraps `adb`, `scrcpy`,
libimobiledevice, `ifuse` and UxPlay (AirPlay mirroring).

> Use only on devices you own or have explicit permission to access.

## Features
- **Android:** list devices, screen mirror/record, screenshot, device info, Wi-Fi pairing (`adb pair`,
  Android 11+) and legacy tcpip connect, file push/pull, APK install, app list, logcat.
- **iOS:** list, pair, device info, screenshot, AirPlay mirroring (UxPlay), mount/unmount, encrypted
  backup and restore, syslog, app list, AirPlay network diagnostics.
- Multi-device selection, input validation, command timeouts, optional action log.

## Requirements
Python 3.8+, Linux. Tools: `adb`, `scrcpy` (Android); `libimobiledevice-utils`, `usbmuxd`, `ifuse`,
`uxplay` (iOS). The Setup menu can install them via apt, dnf or pacman.

## Install & run
```bash
pip install .            # provides the `bluephone` command
bluephone                # or: python BluePhone.py / python -m bluephone
bluephone --setup        # install dependencies (asks before each step)
bluephone --dry-run --setup   # show system commands without running them
```
Flags: `--version`, `--setup`, `--dry-run`, `-y/--yes`, `--no-check`, `--log-file PATH`.

## Safety notes
- BluePhone never changes your system on startup. Package installs, `usbmuxd`/`avahi` services,
  `plugdev` membership, firewall rules and the UxPlay build all use `sudo`, are shown first and need
  confirmation.
- Firewall rules only allow AirPlay ports from your **local subnet**, and can be removed from the Setup menu.
- Wi-Fi ADB exposes a debugging port on your network. Use "Disconnect wireless / back to USB" when done.
- iOS backups contain personal data; prefer the encrypted option.
- UxPlay is installed from your distro package, or built from a pinned tag
  (override with `BLUEPHONE_UXPLAY_TAG`).

## Development
```bash
pip install -e .[dev]
ruff check . && pytest -q
```

Licensed under MIT.
