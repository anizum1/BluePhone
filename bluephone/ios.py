"""iOS access via libimobiledevice, ifuse and UxPlay (AirPlay)."""

from __future__ import annotations

import os
import tempfile
import time
from typing import List, Optional

from . import system
from .base import BaseDevice
from .utils import (
    confirm,
    fail,
    info,
    ok,
    report_failure,
    run_command,
    validate_filename,
    warn,
    which,
)

INFO_FIELDS = (
    "DeviceName", "ProductType", "ProductVersion", "ModelNumber",
    "SerialNumber", "WiFiAddress", "BluetoothAddress",
)


class IOSAccess(BaseDevice):
    label = "iOS"

    def _u(self) -> List[str]:
        return ["-u", self.serial] if self.serial else []

    def _need(self, tool: str) -> bool:
        if which(tool):
            return True
        fail(f"{tool} not found. Install iOS tools from the Setup menu.")
        return False

    # -- devices -----------------------------------------------------------
    def device_ids(self) -> List[str]:
        if not which("idevice_id"):
            return []
        res = run_command(["idevice_id", "-l"])
        return [l.strip() for l in res.stdout.splitlines() if l.strip()]

    def list_devices(self) -> Optional[str]:
        if not self._need("idevice_id"):
            return None
        ids = self.device_ids()
        print("\nConnected iOS devices:")
        if ids:
            print("\n".join(ids))
            return "\n".join(ids)
        warn("No iOS devices found. Connect via USB, unlock the device and tap 'Trust'.")
        return None

    def pair_device(self) -> bool:
        if not self._need("idevicepair") or not self.select_device():
            return False
        info("Tap 'Trust' on the device when prompted")
        validate = run_command(["idevicepair"] + self._u() + ["validate"])
        if validate.ok and "SUCCESS" in validate.stdout:
            ok("Already paired")
            if not confirm("Unpair and re-pair anyway?"):
                return True
            run_command(["idevicepair"] + self._u() + ["unpair"])
        res = run_command(["idevicepair"] + self._u() + ["pair"], timeout=90)
        if res.ok:
            ok("Pairing successful")
            return True
        report_failure(res, "Pairing failed. Make sure you tapped 'Trust'.")
        return False

    def device_info(self) -> None:
        if not self._need("ideviceinfo") or not self.select_device():
            return
        res = run_command(["ideviceinfo"] + self._u())
        if not res.ok:
            report_failure(res, "Could not read device info. Is the device trusted?")
            return
        print("\niOS device information:")
        for line in res.stdout.splitlines():
            key = line.split(":", 1)[0].strip()
            if key in INFO_FIELDS:
                print(line)

    def screenshot(self, output_file: str = "ios_screenshot.png") -> bool:
        output_file = validate_filename(output_file)
        if not self._need("idevicescreenshot") or not self.select_device():
            return False
        res = run_command(["idevicescreenshot"] + self._u() + [output_file])
        if res.ok:
            ok(f"Screenshot saved to {output_file}")
            return True
        report_failure(res, "Screenshot failed (the Developer Disk Image may need to be mounted)")
        return False

    # -- AirPlay -----------------------------------------------------------
    def screen_mirror_airplay(self) -> None:
        if not system.check_uxplay():
            warn("UxPlay is not installed")
            if not confirm("Install UxPlay now?") or not system.install_uxplay():
                return
        avahi = run_command(["systemctl", "is-active", "avahi-daemon"])
        if avahi.stdout.strip() != "active":
            warn("avahi-daemon is not running (needed for discovery)")
            if confirm("Start it with sudo?"):
                run_command(["sudo", "systemctl", "start", "avahi-daemon"], mutating=True)
                time.sleep(2)
        info(
            "Put the iPhone and this machine on the SAME Wi-Fi, open Screen Mirroring "
            "on the iPhone and pick 'UxPlay' (may take 10-15s). Ctrl+C to stop."
        )
        try:
            run_command(["uxplay", "-n", "UxPlay"], capture=False, timeout=None)
        except KeyboardInterrupt:
            info("Screen mirror stopped")

    def network_diagnostics(self) -> None:
        print("\n=== AirPlay network diagnostics ===")
        print("1. Interfaces:")
        for line in run_command(["ip", "-o", "-4", "addr", "show", "scope", "global"]).stdout.splitlines():
            print("   " + line.strip())
        print("2. Avahi:")
        if run_command(["systemctl", "is-active", "avahi-daemon"]).stdout.strip() == "active":
            ok("avahi-daemon running")
        else:
            fail("avahi-daemon NOT running")
        print("3. AirPlay services on network:")
        if which("avahi-browse"):
            out = run_command(["avahi-browse", "-a", "-t", "-r"], timeout=30).stdout.lower()
            if "_airplay" in out or "_raop" in out:
                ok("AirPlay services detected")
            else:
                warn("none detected")
        else:
            warn("avahi-browse missing")
        print("4. Firewall:")
        if which("ufw"):
            status = run_command(["sudo", "ufw", "status"]).stdout
            if "inactive" in status.lower():
                ok("ufw inactive")
            elif "7000" in status and "5353" in status:
                ok("AirPlay ports allowed")
            else:
                warn("AirPlay ports may be blocked")
                if confirm("Add LAN-only AirPlay rules?"):
                    system.configure_firewall()
        else:
            info("ufw not installed")
        print("5. UxPlay:", "installed" if system.check_uxplay() else "NOT installed")

    # -- filesystem, backup ------------------------------------------------
    def mount_device(self, mount_point: Optional[str] = None) -> Optional[str]:
        if not self._need("ifuse") or not self.select_device():
            return None
        mount_point = mount_point or tempfile.mkdtemp(prefix="bluephone-iphone-")
        os.makedirs(mount_point, mode=0o700, exist_ok=True)
        res = run_command(["ifuse"] + self._u() + [mount_point])
        if res.ok:
            ok(f"Mounted at {mount_point} (unmount from the menu or: fusermount -u {mount_point})")
            return mount_point
        report_failure(res, "Mount failed")
        return None

    def unmount_device(self, mount_point: str) -> bool:
        tool = "fusermount3" if which("fusermount3") else "fusermount"
        res = run_command([tool, "-u", mount_point])
        (ok if res.ok else fail)(f"{'Unmounted' if res.ok else 'Unmount failed'} {mount_point}")
        return res.ok

    def backup_device(self, backup_path: str = "./ios_backup", encrypt: bool = False) -> bool:
        if not self._need("idevicebackup2") or not self.select_device():
            return False
        os.makedirs(backup_path, exist_ok=True)
        warn("Backups contain personal data. Store them securely.")
        if encrypt:
            res = run_command(["idevicebackup2"] + self._u() + ["encryption", "on"], capture=False, timeout=None)
            if not res.ok:
                report_failure(res, "Could not enable backup encryption")
                return False
        res = run_command(["idevicebackup2"] + self._u() + ["backup", backup_path], capture=False, timeout=None)
        (ok if res.ok else fail)(f"Backup {'completed at ' + backup_path if res.ok else 'failed'}")
        return res.ok

    def restore_backup(self, backup_path: str) -> bool:
        if not os.path.isdir(backup_path):
            fail(f"{backup_path} is not a directory")
            return False
        if not self._need("idevicebackup2") or not self.select_device():
            return False
        if not confirm("Restoring OVERWRITES data on the device. Continue?"):
            return False
        res = run_command(["idevicebackup2"] + self._u() + ["restore", "--system", "--settings", backup_path],
                          capture=False, timeout=None)
        (ok if res.ok else fail)(f"Restore {'finished' if res.ok else 'failed'}")
        return res.ok

    # -- logs, apps --------------------------------------------------------
    def syslog(self) -> None:
        if not self._need("idevicesyslog") or not self.select_device():
            return
        info("Streaming device syslog, Ctrl+C to stop")
        try:
            run_command(["idevicesyslog"] + self._u(), capture=False, timeout=None)
        except KeyboardInterrupt:
            info("syslog stopped")

    def list_apps(self) -> None:
        if not self._need("ideviceinstaller") or not self.select_device():
            return
        res = run_command(["ideviceinstaller"] + self._u() + ["-l"], timeout=120)
        if res.ok:
            print(res.stdout)
        else:
            report_failure(res, "Could not list apps")


