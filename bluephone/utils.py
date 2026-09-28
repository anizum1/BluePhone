"""Shared helpers: command execution, output, prompts, validation, logging."""

from __future__ import annotations

import ipaddress
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

DEFAULT_TIMEOUT = 60


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

    @classmethod
    def disable(cls) -> None:
        for name in ("HEADER", "OKBLUE", "OKCYAN", "OKGREEN", "WARNING", "FAIL", "ENDC", "BOLD"):
            setattr(cls, name, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    Colors.disable()


@dataclass
class Settings:
    """Process-wide switches set from the command line."""

    dry_run: bool = False
    assume_yes: bool = False


SETTINGS = Settings()
log = logging.getLogger("bluephone")


def setup_logging(log_file: Optional[str]) -> None:
    if not log_file:
        return
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


@dataclass
class CmdResult:
    args: List[str]
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    dry_run: bool = field(default=False)

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.error


def ok(msg: str) -> None:
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def warn(msg: str) -> None:
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")


def fail(msg: str) -> None:
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")


def info(msg: str) -> None:
    print(f"{Colors.OKCYAN}{msg}{Colors.ENDC}")


def run_command(
    cmd: Sequence[str],
    capture: bool = True,
    timeout: Optional[float] = DEFAULT_TIMEOUT,
    mutating: bool = False,
    cwd: Optional[str] = None,
) -> CmdResult:
    """Run a command without a shell and never raise.

    ``mutating`` commands (installs, service/firewall changes) are only printed
    when ``--dry-run`` is active. Interactive commands should pass
    ``capture=False, timeout=None``.
    """
    args = [str(c) for c in cmd]
    log.info("run: %s", " ".join(args))
    if mutating and SETTINGS.dry_run:
        print(f"{Colors.OKBLUE}[dry-run] {' '.join(args)}{Colors.ENDC}")
        return CmdResult(args, 0, dry_run=True)
    try:
        proc = subprocess.run(
            args, capture_output=capture, text=True, timeout=timeout, cwd=cwd
        )
    except FileNotFoundError:
        return CmdResult(args, 127, error=f"command not found: {args[0]}")
    except subprocess.TimeoutExpired:
        return CmdResult(args, 124, error=f"timed out after {timeout}s: {' '.join(args)}")
    except OSError as exc:
        return CmdResult(args, 126, error=str(exc))
    return CmdResult(args, proc.returncode, proc.stdout or "", proc.stderr or "")


def report_failure(res: CmdResult, what: str) -> None:
    fail(what)
    detail = res.error or res.stderr.strip()
    if detail:
        print(f"{Colors.FAIL}  {detail}{Colors.ENDC}")


def which(tool: str) -> Optional[str]:
    return shutil.which(tool)


def confirm(question: str, default: bool = False) -> bool:
    if SETTINGS.assume_yes:
        return True
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{Colors.OKCYAN}{question} {suffix}: {Colors.ENDC}").strip().lower()
    except EOFError:
        return False
    if not answer:
        return default
    return answer in ("y", "yes")


def prompt(text: str, default: str = "") -> str:
    hint = f" (default: {default})" if default else ""
    value = input(f"{Colors.OKCYAN}{text}{hint}: {Colors.ENDC}").strip()
    return value or default


def validate_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        raise ValueError(f"'{value}' is not a valid IP address") from None


def validate_port(value: object) -> int:
    try:
        port = int(str(value).strip())
    except ValueError:
        raise ValueError(f"'{value}' is not a valid port") from None
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    return port


def validate_filename(value: str) -> str:
    value = value.strip()
    if not value or "\x00" in value or value.startswith("-"):
        raise ValueError("invalid file name")
    return value


def clear_screen() -> None:
    if sys.stdout.isatty():
        print("\033[2J\033[H", end="")
