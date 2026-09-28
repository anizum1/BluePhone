from bluephone import system, utils


def test_firewall_rules_are_lan_scoped():
    cmds = system.firewall_commands("192.168.1.0/24")
    assert cmds and all("from" in c and "192.168.1.0/24" in c for c in cmds)
    assert not any("49152:65535" in " ".join(c) for c in cmds)


def test_lan_subnet_parses(fake_run):
    _, responses = fake_run
    responses["addr show"] = (0, "2: eth0    inet 192.168.1.42/24 brd 192.168.1.255 scope global eth0\n", "")
    assert system.lan_subnet() == "192.168.1.0/24"


def test_configure_and_remove_firewall(fake_run, monkeypatch, tmp_path):
    calls, responses = fake_run
    monkeypatch.setattr(system, "which", lambda t: "/usr/sbin/ufw")
    monkeypatch.setattr(system, "STATE_FILE", tmp_path / "fw.json")
    responses["ufw status"] = (0, "Status: active", "")
    responses["addr show"] = (0, "2: eth0    inet 10.1.2.3/24 scope global eth0\n", "")
    assert system.configure_firewall()
    assert system.STATE_FILE.exists()
    assert system.remove_firewall_rules()
    assert any(c[:3] == ["sudo", "ufw", "delete"] for c in calls)
    assert not system.STATE_FILE.exists()


def test_install_group_dry_run_executes_nothing(fake_run, monkeypatch):
    calls, _ = fake_run
    monkeypatch.setattr(utils.SETTINGS, "dry_run", True)
    monkeypatch.setattr(system, "which", lambda t: "/usr/bin/" + t if t == "apt-get" else None)
    assert system.install_group("android")
    assert calls == []


def test_install_declined_does_nothing(fake_run, monkeypatch):
    calls, _ = fake_run
    monkeypatch.setattr(utils.SETTINGS, "assume_yes", False)
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    monkeypatch.setattr(system, "which", lambda t: "/usr/bin/" + t if t == "apt-get" else None)
    assert system.install_group("ios") is False
    assert calls == []
