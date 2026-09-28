# Changelog

## 2.1.0
### Changed
- Split the single script into the `bluephone` package; `BluePhone.py` remains as a shim.
- Nothing is installed or changed at startup any more. Package installs, services, firewall and
  UxPlay are opt-in from the Setup menu, each confirmed, with `--dry-run` support.
- Firewall rules are limited to the local subnet, recorded, and removable.
- UxPlay is installed from the distro package or a pinned tag built in a temp dir.
- Commands run with timeouts and without a shell; missing binaries are reported clearly.

### Fixed
- Battery info (`shell=True` with a list ran bare `adb`).
- `adb` path was ignored; multi-device setups now prompt for a device (`-s` / `-u`).
- "Recording saved" printed on failure; screenshot temp file left on device on failure.
- Crash on invalid port; IP/port/filename are validated.
- Working directory changed by the UxPlay build.
- Pairing no longer unpairs silently.

### Added
- Android: `adb pair`, disconnect/USB revert, push/pull, APK install, app list, logcat.
- iOS: unmount, encrypted backup, restore, syslog, app list; private temp mount point.
- dnf and pacman support, `--version`, `--log-file`, tests and CI.
