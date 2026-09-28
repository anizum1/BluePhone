import pytest

from bluephone import android as android_mod
from bluephone.android import AndroidAccess


@pytest.fixture
def dev(fake_run, monkeypatch):
    monkeypatch.setattr(android_mod, "which", lambda t: "/usr/bin/" + t)
    a = AndroidAccess()
    a.serial = "SER1"
    return a


def test_battery_runs_adb_shell_dumpsys(dev, fake_run, capsys):
    calls, responses = fake_run
    responses["dumpsys battery"] = (0, "  AC powered: false\n  level: 87\n", "")
    dev.select_device = lambda: "SER1"
    dev.device_info()
    assert ["/usr/bin/adb", "-s", "SER1", "shell", "dumpsys", "battery"] in calls
    assert "level: 87" in capsys.readouterr().out


def test_device_ids_filters_unauthorized(dev, fake_run):
    _, responses = fake_run
    responses["devices"] = (0, "List of devices attached\nAAA\tdevice\nBBB\tunauthorized\n", "")
    assert dev.device_ids() == ["AAA"]


def test_screenshot_cleans_up_on_pull_failure(dev, fake_run):
    calls, responses = fake_run
    responses["devices"] = (0, "List of devices attached\nSER1\tdevice\n", "")
    responses["pull"] = (1, "", "boom")
    assert dev.screenshot("out.png") is False
    assert any(c[-3:-1] == ["rm", "-f"] for c in calls)


def test_wireless_rejects_bad_input(dev):
    with pytest.raises(ValueError):
        dev.connect_wireless("not-an-ip", 5555)
    with pytest.raises(ValueError):
        dev.connect_wireless("10.0.0.2", "abc")


def test_connect_wireless_success(dev, fake_run):
    _, responses = fake_run
    responses["connect"] = (0, "connected to 10.0.0.2:5555", "")
    assert dev.connect_wireless("10.0.0.2", 5555)


def test_recording_failure_not_reported_saved(dev, fake_run, capsys):
    _, responses = fake_run
    responses["scrcpy"] = (1, "", "")
    dev.select_device = lambda: "SER1"
    assert dev.screen_record("r.mp4") is False
    assert "saved" not in capsys.readouterr().out.lower()
