"""Common device interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .utils import prompt, warn


class BaseDevice(ABC):
    """Shared behaviour for Android and iOS backends."""

    label = "device"

    def __init__(self) -> None:
        self.serial: Optional[str] = None

    @abstractmethod
    def device_ids(self) -> List[str]:
        """Return identifiers (serial/UDID) of connected devices."""

    @abstractmethod
    def list_devices(self) -> Optional[str]: ...

    @abstractmethod
    def device_info(self) -> None: ...

    @abstractmethod
    def screenshot(self, output_file: str) -> bool: ...

    def select_device(self) -> Optional[str]:
        """Pick the target device; asks only when several are connected."""
        ids = self.device_ids()
        if not ids:
            self.serial = None
            warn(f"No {self.label} devices found")
            return None
        if len(ids) == 1:
            self.serial = ids[0]
            return self.serial
        for i, dev in enumerate(ids, 1):
            print(f"  [{i}] {dev}")
        choice = prompt("Select device number", "1")
        try:
            self.serial = ids[int(choice) - 1]
        except (ValueError, IndexError):
            warn("Invalid selection, using the first device")
            self.serial = ids[0]
        return self.serial
