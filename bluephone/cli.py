"""Command-line entry point and interactive menus."""

from __future__ import annotations

import argparse
import sys
from typing import Callable, List, Optional, Tuple

from . import VERSION, system
from .android import AndroidAccess
from .ios import IOSAccess
from .utils import (
    SETTINGS,
    Colors,
    clear_screen,
    confirm,
    fail,
    info,
    log,
    ok,
    prompt,
    setup_logging,
    warn,
    which,
)

BANNER = f"""{Colors.HEADER}BluePhone v{VERSION} - manage YOUR OWN Android & iOS devices{Colors.ENDC}
{Colors.WARNING}Only use on devices you own or have explicit permission to access.
Nothing is installed or changed on your system without asking.{Colors.ENDC}
"""

Action = Tuple[str, Callable[[], object]]


def check_tools() -> None:
    """Report (never install) missing tools."""
    for tool in ("adb", "scrcpy", "idevice_id", "ifuse", "uxplay"):
        (ok if which(tool) else warn)(f"{tool} {'found' if which(tool) else 'missing (see Setup menu)'}")


def run_menu(title: str, actions: List[Action]) -> None:
    while True:
        print(f"\n{Colors.OKBLUE}== {title} =={Colors.ENDC}")
        for i, (label, _) in enumerate(actions, 1):
            print(f"{Colors.OKGREEN}[{i}]{Colors.ENDC} {label}")
        print(f"{Colors.OKGREEN}[0]{Colors.ENDC} Back")
        choice = prompt("Select an option")
        if choice == "0":
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(actions):
            fail("Invalid option")
            continue
        label, func = actions[int(choice) - 1]
        log.info("action: %s", label)
        try:
            func()
        except ValueError as exc:
            fail(str(exc))
        except KeyboardInterrupt:
            print()
            info("Cancelled")
        prompt("Press Enter to continue")


def android_menu(a: AndroidAccess) -> None:
    run_menu("Android", [
        ("List devices", a.list_devices),
        ("Mirror screen (scrcpy)", a.screen_mirror),
        ("Screenshot", lambda: a.screenshot(prompt("Output file", "android_screenshot.png"))),
        ("Record screen", lambda: a.screen_record(prompt("Output file", "android_record.mp4"))),
        ("Device info", a.device_info),
        ("Pair wireless debugging (Android 11+)", lambda: a.pair_wireless(
            prompt("Device IP"), prompt("Pairing port"), prompt("Pairing code"))),
        ("Connect over Wi-Fi", lambda: a.connect_wireless(
            prompt("Device IP"), prompt("Port", "5555"),
            use_tcpip=confirm("Switch a USB device to legacy tcpip mode first?"))),
        ("Disconnect wireless / back to USB", a.disconnect_wireless),
        ("Push file to device", lambda: a.push_file(prompt("Local path"), prompt("Remote path", "/sdcard/"))),
        ("Pull file from device", lambda: a.pull_file(prompt("Remote path"), prompt("Local path", "."))),
        ("Install APK", lambda: a.install_apk(prompt("APK path"))),
        ("List installed apps", a.list_apps),
        ("Stream logcat", a.logcat),
    ])


def ios_menu(d: IOSAccess) -> None:
    mounted: List[str] = []

    def mount() -> None:
        mp = d.mount_device(prompt("Mount point (blank = private temp dir)") or None)
        if mp:
            mounted.append(mp)

    def unmount() -> None:
        if mounted:
            d.unmount_device(mounted.pop())
        else:
            warn("Nothing mounted in this session")

    run_menu("iOS", [
        ("List devices", d.list_devices),
        ("Pair device", d.pair_device),
        ("Device info", d.device_info),
        ("Screenshot", lambda: d.screenshot(prompt("Output file", "ios_screenshot.png"))),
        ("Screen mirror (AirPlay / UxPlay)", d.screen_mirror_airplay),
        ("Mount filesystem", mount),
        ("Unmount filesystem", unmount),
        ("Backup", lambda: d.backup_device(prompt("Backup path", "./ios_backup"),
                                           encrypt=confirm("Encrypt the backup?", True))),
        ("Restore backup", lambda: d.restore_backup(prompt("Backup path"))),
        ("Stream syslog", d.syslog),
        ("List installed apps", d.list_apps),
        ("AirPlay network diagnostics", d.network_diagnostics),
    ])


def setup_menu() -> None:
    run_menu("Setup (asks before every change)", [
        ("Install Android tools (adb, scrcpy)", lambda: system.install_group("android")),
        ("Install iOS tools (libimobiledevice, ifuse, usbmuxd)", lambda: system.install_group("ios")),
        ("Install AirPlay support packages", lambda: system.install_group("airplay")),
        ("Enable usbmuxd/avahi services & plugdev group", system.setup_services),
        ("Allow AirPlay ports from LAN only (ufw)", system.configure_firewall),
        ("Remove AirPlay firewall rules added by BluePhone", system.remove_firewall_rules),
        ("Install UxPlay", system.install_uxplay),
    ])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bluephone", description="Manage your own Android and iOS devices.")
    p.add_argument("--version", action="version", version=f"bluephone {VERSION}")
    p.add_argument("--setup", action="store_true", help="open the setup menu directly")
    p.add_argument("--dry-run", action="store_true", help="print system-changing commands instead of running them")
    p.add_argument("-y", "--yes", action="store_true", help="answer yes to confirmations")
    p.add_argument("--no-check", action="store_true", help="skip the startup tool check")
    p.add_argument("--log-file", help="write an action log to this file")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    SETTINGS.dry_run, SETTINGS.assume_yes = args.dry_run, args.yes
    setup_logging(args.log_file)
    print(BANNER)
    try:
        if not args.no_check and not args.setup:
            check_tools()
        if args.setup:
            setup_menu()
            return 0
        android, ios = AndroidAccess(), IOSAccess()
        while True:
            print(f"\n{Colors.OKBLUE}== MAIN MENU =={Colors.ENDC}")
            print("[1] Android\n[2] iOS\n[3] Setup / install dependencies\n[0] Exit")
            choice = prompt("Select an option")
            clear_screen()
            if choice == "1":
                android_menu(android)
            elif choice == "2":
                ios_menu(ios)
            elif choice == "3":
                setup_menu()
            elif choice == "0":
                return 0
            else:
                fail("Invalid option")
    except (KeyboardInterrupt, EOFError):
        print()
        info("Exiting...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
