#!/usr/bin/env python3
"""Backward-compatible entry point: run `python BluePhone.py` or `python -m bluephone`."""

import sys

from bluephone.cli import main

if __name__ == "__main__":
    sys.exit(main())
