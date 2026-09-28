import subprocess

import pytest

from bluephone import utils


@pytest.fixture
def fake_run(monkeypatch):
    """Record subprocess.run calls; responses keyed by first matching substring."""
    calls, responses = [], {}

    def _run(args, **kw):
        calls.append(list(args))
        joined = " ".join(args)
        for key, val in responses.items():
            if key in joined:
                if isinstance(val, Exception):
                    raise val
                return subprocess.CompletedProcess(args, val[0], val[1], val[2])
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(utils.SETTINGS, "assume_yes", True)
    monkeypatch.setattr(utils.SETTINGS, "dry_run", False)
    return calls, responses
