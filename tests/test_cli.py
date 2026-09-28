import pytest

from bluephone import VERSION, cli


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    assert VERSION in capsys.readouterr().out


def test_invalid_option_then_exit(fake_run, monkeypatch, capsys):
    answers = iter(["9", "0"])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    assert cli.main(["--no-check"]) == 0
    assert "Invalid option" in capsys.readouterr().out


def test_eof_exits_cleanly(fake_run, monkeypatch):
    def eof(*_):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert cli.main(["--no-check"]) == 0


def test_startup_runs_no_commands(fake_run, monkeypatch):
    calls, _ = fake_run
    monkeypatch.setattr("builtins.input", lambda *_: "0")
    cli.main(["--no-check"])
    assert calls == []


def test_bad_port_in_menu_does_not_crash(fake_run, monkeypatch, capsys):
    monkeypatch.setattr(cli, "which", lambda t: "/usr/bin/" + t)
    from bluephone import android as am
    monkeypatch.setattr(am, "which", lambda t: "/usr/bin/" + t)
    answers = iter(["1", "7", "10.0.0.2", "99999", "", "", "0", "0"])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    assert cli.main(["--no-check", "-y"]) == 0
    assert "port must be between" in capsys.readouterr().out
