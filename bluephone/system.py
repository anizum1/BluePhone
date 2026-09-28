"""Opt-in system setup: packages, services, firewall and UxPlay.

Nothing here runs automatically. Every mutating step is confirmed by the user
and honours ``--dry-run``.
"""

from __future__ import annotations

import getpass
import ipaddress
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .utils import confirm, fail, info, ok, report_failure, run_command, warn, which

UXPLAY_REPO = "https://github.com/FDH2/UxPlay"
UXPLAY_TAG = os.environ.get("BLUEPHONE_UXPLAY_TAG", "v1.72")

FIREWALL_RULES: List[Tuple[str, str, str]] = [
    ("7000:7100", "tcp", "AirPlay TCP"),
    ("7000:7100", "udp", "AirPlay UDP"),
    ("5353", "udp", "mDNS"),
]
STATE_FILE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "bluephone" / "firewall.json"

# tool -> package name per package manager
PACKAGES: Dict[str, Dict[str, List[str]]] = {
    "apt": {
        "android": ["adb", "scrcpy"],
        "ios": ["libimobiledevice-utils", "usbmuxd", "ifuse", "libusbmuxd-tools"],
        "airplay": ["avahi-daemon", "avahi-utils", "gstreamer1.0-tools",
                    "gstreamer1.0-plugins-base", "gstreamer1.0-plugins-good",
                    "gstreamer1.0-plugins-bad"],
        "uxplay-build": ["cmake", "pkg-config", "libavahi-compat-libdnssd-dev", "libplist-dev",
                         "libssl-dev", "libgstreamer1.0-dev", "libgstreamer-plugins-base1.0-dev", "git"],
    },
    "dnf": {
        "android": ["android-tools", "scrcpy"],
        "ios": ["libimobiledevice-utils", "usbmuxd", "ifuse"],
        "airplay": ["avahi", "avahi-tools", "gstreamer1", "gstreamer1-plugins-base",
                    "gstreamer1-plugins-good", "gstreamer1-plugins-bad-free"],
        "uxplay-build": ["cmake", "pkgconf", "avahi-compat-libdns_sd-devel", "libplist-devel",
                         "openssl-devel", "gstreamer1-devel", "gstreamer1-plugins-base-devel", "git", "gcc-c++"],
    },
    "pacman": {
        "android": ["android-tools", "scrcpy"],
        "ios": ["libimobiledevice", "usbmuxd", "ifuse"],
        "airplay": ["avahi", "gst-plugins-base", "gst-plugins-good", "gst-plugins-bad"],
        "uxplay-build": ["cmake", "pkgconf", "libplist", "openssl", "gstreamer", "gst-plugins-base", "git",
                         "base-devel"],
    },
}

INSTALL_CMDS: Dict[str, List[str]] = {
    "apt": ["sudo", "apt-get", "install", "-y"],
    "dnf": ["sudo", "dnf", "install", "-y"],
    "pacman": ["sudo", "pacman", "-S", "--needed", "--noconfirm"],
}


def detect_package_manager() -> Optional[str]:
    for pm in ("apt", "dnf", "pacman"):
        exe = "apt-get" if pm == "apt" else pm
        if which(exe):
            return pm
    return None


def missing_tools(tools: Dict[str, str]) -> List[str]:
    """Return the names of tools not found on PATH."""
    return [t for t in tools if not which(t)]


def install_group(group: str) -> bool:
    """Install a package group after confirmation."""
    pm = detect_package_manager()
    if not pm:
        fail("No supported package manager (apt, dnf, pacman) found; install the tools manually")
        return False
    packages = PACKAGES[pm][group]
    info(f"Packages for '{group}': {', '.join(packages)}")
    if not confirm(f"Install these with sudo {pm}?"):
        warn("Skipped")
        return False
    if pm == "apt":
        run_command(["sudo", "apt-get", "update"], mutating=True, timeout=600)
    res = run_command(INSTALL_CMDS[pm] + packages, mutating=True, capture=False, timeout=1800)
    if res.ok:
        ok(f"Installed '{group}' packages")
        return True
    report_failure(res, f"Failed to install '{group}' packages")
    return False


def setup_services() -> None:
    """Start usbmuxd/avahi and add the user to plugdev, each after confirmation."""
    if confirm("Enable and start usbmuxd and avahi-daemon services?"):
        for svc in ("usbmuxd", "avahi-daemon"):
            run_command(["sudo", "systemctl", "enable", "--now", svc], mutating=True)
            res = run_command(["systemctl", "is-active", svc])
            if res.stdout.strip() == "active" or res.dry_run:
                ok(f"{svc} is running")
            else:
                warn(f"{svc} may not be running")
    user = os.environ.get("USER") or getpass.getuser()
    if confirm(f"Add {user} to the plugdev group (needed for USB access)?"):
        run_command(["sudo", "usermod", "-a", "-G", "plugdev", user], mutating=True)


def lan_subnet() -> Optional[str]:
    """Return the first global IPv4 subnet (e.g. 192.168.1.0/24)."""
    res = run_command(["ip", "-o", "-4", "addr", "show", "scope", "global"])
    for line in res.stdout.splitlines():
        parts = line.split()
        if "inet" in parts:
            cidr = parts[parts.index("inet") + 1]
            try:
                return str(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                continue
    return None


def firewall_commands(subnet: str) -> List[List[str]]:
    return [
        ["ufw", "allow", "from", subnet, "to", "any", "port", port, "proto", proto]
        for port, proto, _ in FIREWALL_RULES
    ]


def _save_state(subnet: str) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"subnet": subnet}))


def configure_firewall() -> bool:
    """Allow AirPlay ports from the local subnet only (never from everywhere)."""
    if not which("ufw"):
        warn("ufw is not installed, nothing to configure")
        return False
    status = run_command(["sudo", "ufw", "status"])
    if "inactive" in status.stdout.lower():
        info("Firewall is inactive, no configuration needed")
        return True
    subnet = lan_subnet()
    if not subnet:
        fail("Could not determine the local subnet")
        return False
    print(f"Rules to add (source limited to {subnet}):")
    for cmd in firewall_commands(subnet):
        print("  sudo " + " ".join(cmd))
    if not confirm("Add these firewall rules?"):
        warn("Skipped")
        return False
    good = True
    for cmd in firewall_commands(subnet):
        good &= run_command(["sudo"] + cmd, mutating=True).ok
    if good:
        _save_state(subnet)
        ok("Firewall rules added (undo from the setup menu)")
    else:
        warn("Some rules failed to apply")
    return good


def remove_firewall_rules() -> bool:
    try:
        subnet = json.loads(STATE_FILE.read_text())["subnet"]
    except (OSError, ValueError, KeyError):
        warn("No BluePhone firewall rules recorded")
        return False
    if not confirm(f"Remove AirPlay rules for {subnet}?"):
        return False
    good = True
    for cmd in firewall_commands(subnet):
        good &= run_command(["sudo", "ufw", "delete"] + cmd[1:], mutating=True).ok
    if good:
        STATE_FILE.unlink(missing_ok=True)
        ok("Firewall rules removed")
    return good


def check_uxplay() -> bool:
    return which("uxplay") is not None


def install_uxplay() -> bool:
    """Install UxPlay from the distro if possible, else build a pinned tag."""
    pm = detect_package_manager()
    if pm == "apt":
        cache = run_command(["apt-cache", "show", "uxplay"])
        if cache.ok and confirm("UxPlay is available as a distro package. Install it?", True):
            cmd = ["sudo", "apt-get", "install", "-y", "uxplay"]
            if run_command(cmd, mutating=True, capture=False, timeout=900).ok:
                ok("UxPlay installed")
                return True
    info(f"Building UxPlay {UXPLAY_TAG} from {UXPLAY_REPO}")
    if not confirm("Install build dependencies, compile and `sudo make install`?"):
        warn("Skipped")
        return False
    if pm and not install_group("uxplay-build"):
        return False
    tmp = tempfile.mkdtemp(prefix="bluephone-uxplay-")
    try:
        src = os.path.join(tmp, "UxPlay")
        steps = [
            (["git", "clone", "--depth", "1", "--branch", UXPLAY_TAG, UXPLAY_REPO, src], tmp, False),
            (["cmake", "-S", src, "-B", os.path.join(src, "build")], src, False),
            (["cmake", "--build", os.path.join(src, "build"), "-j2"], src, False),
            (["sudo", "cmake", "--install", os.path.join(src, "build")], src, True),
        ]
        for cmd, cwd, mutating in steps:
            res = run_command(cmd, mutating=mutating, cwd=cwd, timeout=1800)
            if not res.ok:
                report_failure(res, f"{cmd[0]} failed")
                return False
        ok("UxPlay installed")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
