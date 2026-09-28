import subprocess

import pytest

from bluephone import utils
from bluephone.utils import run_command, validate_filename, validate_ip, validate_port


def test_run_command_ok(fake_run):
    calls, _ = fake_run
    assert run_command(["echo", "x"]).ok
    assert calls == [["echo", "x"]]


def test_run_command_missing_binary(fake_run):
    _, responses = fake_run
    responses["nope"] = FileNotFoundError()
    res = run_command(["nope"])
    assert not res.ok and "not found" in res.error


def test_run_command_timeout(fake_run):
    _, responses = fake_run
    responses["slow"] = subprocess.TimeoutExpired("slow", 1)
    assert "timed out" in run_command(["slow"], timeout=1).error


def test_dry_run_skips_mutating(fake_run, monkeypatch):
    calls, _ = fake_run
    monkeypatch.setattr(utils.SETTINGS, "dry_run", True)
    res = run_command(["sudo", "apt-get", "install", "x"], mutating=True)
    assert res.dry_run and res.ok and calls == []
    run_command(["ls"])  # read-only commands still run
    assert calls == [["ls"]]


@pytest.mark.parametrize("bad", ["abc", "1.2.3", "999.1.1.1", ""])
def test_validate_ip_rejects(bad):
    with pytest.raises(ValueError):
        validate_ip(bad)


def test_validate_ip_ok():
    assert validate_ip(" 192.168.1.5 ") == "192.168.1.5"


@pytest.mark.parametrize("bad", ["x", "0", "70000", ""])
def test_validate_port_rejects(bad):
    with pytest.raises(ValueError):
        validate_port(bad)


def test_validate_port_ok():
    assert validate_port("5555") == 5555


def test_validate_filename():
    assert validate_filename("a.png") == "a.png"
    with pytest.raises(ValueError):
        validate_filename("-rf")
    with pytest.raises(ValueError):
        validate_filename("")
