"""Android access via adb and scrcpy."""

from __future__ import annotations

import os
import re
from typing import List, Optional

from .base import BaseDevice
from .utils import (
    CmdResult,
    fail,
    info,
    ok,
    report_failure,
    run_command,
    validate_filename,
    validate_ip,
    validate_port,
    warn,
    which,
)


class AndroidAccess(BaseDevice):
    label = "Android"

    def __init__(self) -> None:
        super().__init__()
        self.adb = which("adb")

    # -- helpers -----------------------------------------------------------
    def has_adb(self) -> bool:
        if not self.adb:
            self.adb = which("adb")
        if not self.adb:
            fail("adb not found. Install it from the Setup menu (or your package manager).")
            return False
        return True

    def _adb(self, *args: str, **kw) -> CmdResult:
        cmd = [self.adb or "adb"]
        if self.serial:
            cmd += ["-s", self.serial]
        return run_command(cmd + list(args), **kw)

    def _need_scrcpy(self) -> bool:
        if which("scrcpy"):
            return True
        fail("scrcpy not found. Install it from the Setup menu (or your package manager).")
        return False

    # -- devices -----------------------------------------------------------
    def device_ids(self) -> List[str]:
        if not self.has_adb():
            return []
        res = run_command([self.adb, "devices"])
        ids = []
        for line in res.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                ids.append(parts[0])
        return ids

    def list_devices(self) -> Optional[str]:
        if not self.has_adb():
            return None
        res = run_command([self.adb, "devices", "-l"])
        if not res.ok:
            report_failure(res, "Could not list devices")
            return None
        print(f"\nConnected Android devices:\n{res.stdout}")
        return res.stdout

    def device_info(self) -> None:
        if not self.has_adb() or not self.select_device():
            return
        print("\nAndroid device information:")
        for label, args in (
            ("Model", ["shell", "getprop", "ro.product.model"]),
            ("Android version", ["shell", "getprop", "ro.build.version.release"]),
            ("Screen", ["shell", "wm", "size"]),
        ):
            res = self._adb(*args)
            if res.ok:
                print(f"{label}: {res.stdout.strip()}")
        battery = self._adb("shell", "dumpsys", "battery")
        if battery.ok:
            for line in battery.stdout.splitlines():
                if line.strip().startswith("level"):
                    print(f"Battery: {line.strip()}")
                    break

    # -- connectivity ------------------------------------------------------
    def pair_wireless(self, ip: str, port: object, code: str) -> bool:
        """Android 11+ wireless debugging pairing (`adb pair`)."""
        if not self.has_adb():
            return False
        target = f"{validate_ip(ip)}:{validate_port(port)}"
        res = run_command([self.adb, "pair", target, code])
        if res.ok and "successfully" in res.stdout.lower():
            ok("Paired. Now use 'connect' with the port shown on the Wireless debugging screen.")
            return True
        report_failure(res, "Pairing failed")
        return False

    def connect_wireless(self, ip: str, port: object = 5555, use_tcpip: bool = False) -> bool:
        """Connect over Wi-Fi. ``use_tcpip`` switches a USB device to legacy TCP mode first."""
        if not self.has_adb():
            return False
        ip, port_n = validate_ip(ip), validate_port(port)
        if use_tcpip:
            warn("Legacy tcpip mode exposes an unauthenticated-by-network ADB port; disconnect when done.")
            if not self.serial and not self.select_device():
                return False
            self._adb("tcpip", str(port_n))
        res = run_command([self.adb, "connect", f"{ip}:{port_n}"], timeout=20)
        if res.ok and "connected" in res.stdout.lower() and "cannot" not in res.stdout.lower():
            ok(f"Connected to {ip}:{port_n}")
            return True
        report_failure(res, res.stdout.strip() or "Connection failed")
        return False

    def disconnect_wireless(self) -> bool:
        """Drop network connections and return adb to USB mode."""
        if not self.has_adb():
            return False
        run_command([self.adb, "disconnect"])
        res = run_command([self.adb, "usb"])
        if res.ok:
            ok("Disconnected wireless devices; adb back in USB mode")
        return res.ok

    # -- capture -----------------------------------------------------------
    def screen_mirror(self) -> None:
        if not self._need_scrcpy() or not self.select_device():
            return
        info("Starting screen mirror (close the window or Ctrl+C to stop)")
        cmd = ["scrcpy"] + (["-s", self.serial] if self.serial else [])
        try:
            run_command(cmd, capture=False, timeout=None)
        except KeyboardInterrupt:
            info("Screen mirror stopped")

    def screen_record(self, output_file: str = "android_record.mp4") -> bool:
        output_file = validate_filename(output_file)
        if not self._need_scrcpy() or not self.select_device():
            return False
        info("Recording... close the window or Ctrl+C to stop")
        cmd = ["scrcpy", "--record", output_file] + (["-s", self.serial] if self.serial else [])
        try:
            res = run_command(cmd, capture=False, timeout=None)
        except KeyboardInterrupt:
            info("Recording stopped")
            return os.path.exists(output_file)
        if res.ok:
            ok(f"Recording saved to {output_file}")
            return True
        report_failure(res, "Recording failed")
        return False

    def screenshot(self, output_file: str = "android_screenshot.png") -> bool:
        output_file = validate_filename(output_file)
        if not self.has_adb() or not self.select_device():
            return False
        remote = f"/sdcard/bluephone_{os.getpid()}.png"
        try:
            res = self._adb("shell", "screencap", "-p", remote)
            if not res.ok:
                report_failure(res, "Screenshot failed")
                return False
            res = self._adb("pull", remote, output_file)
            if not res.ok:
                report_failure(res, "Could not pull screenshot")
                return False
            ok(f"Screenshot saved to {output_file}")
            return True
        finally:
            self._adb("shell", "rm", "-f", remote)

    # -- files, apps, logs -------------------------------------------------
    def push_file(self, local: str, remote: str) -> bool:
        if not os.path.exists(local):
            fail(f"{local} does not exist")
            return False
        if not self.has_adb() or not self.select_device():
            return False
        res = self._adb("push", local, remote, timeout=None)
        (ok if res.ok else fail)(f"push {'done' if res.ok else 'failed'}: {res.stderr.strip() or res.stdout.strip()}")
        return res.ok

    def pull_file(self, remote: str, local: str) -> bool:
        if not self.has_adb() or not self.select_device():
            return False
        res = self._adb("pull", remote, validate_filename(local), timeout=None)
        (ok if res.ok else fail)(f"pull {'done' if res.ok else 'failed'}: {res.stderr.strip() or res.stdout.strip()}")
        return res.ok

    def install_apk(self, apk: str) -> bool:
        if not apk.lower().endswith(".apk") or not os.path.isfile(apk):
            fail("Provide the path of an existing .apk file")
            return False
        if not self.has_adb() or not self.select_device():
            return False
        res = self._adb("install", "-r", apk, timeout=300)
        if res.ok:
            ok("APK installed")
        else:
            report_failure(res, "Install failed")
        return res.ok

    def list_apps(self, third_party: bool = True) -> List[str]:
        if not self.has_adb() or not self.select_device():
            return []
        args = ["shell", "pm", "list", "packages"] + (["-3"] if third_party else [])
        res = self._adb(*args)
        if not res.ok:
            report_failure(res, "Could not list apps")
            return []
        pkgs = sorted(re.sub(r"^package:", "", l.strip()) for l in res.stdout.splitlines() if l.strip())
        print("\n".join(pkgs))
        return pkgs

    def logcat(self) -> None:
        if not self.has_adb() or not self.select_device():
            return
        info("Streaming logcat, Ctrl+C to stop")
        try:
            self._adb("logcat", capture=False, timeout=None)
        except KeyboardInterrupt:
            info("logcat stopped")


