"""
Resolve the current DATARUN value.

Priority:
  1. ``DATARUN`` environment variable (allows one-off overrides)
  2. ``Data/.datarun`` file written automatically by ``scrape.py``

``scrape.py`` writes the date string to ``Data/.datarun`` at the end of each
successful run so that subsequent pipeline steps can pick it up without
requiring the user to manually export an environment variable.
"""

import os
import sys

DATARUN_FILE = os.path.join("Data", ".datarun")


def get_datarun():
    """Return the current datarun string, or exit with an error message."""
    datarun = os.getenv("DATARUN")
    if datarun:
        return datarun.strip()

    if os.path.isfile(DATARUN_FILE):
        with open(DATARUN_FILE, "r") as f:
            datarun = f.read().strip()
        if datarun:
            return datarun

    print(
        "Could not determine DATARUN.\n"
        "Either set the DATARUN environment variable or run scrape.py first\n"
        f"(which writes the value to {DATARUN_FILE})."
    )
    sys.exit(1)


def save_datarun(value):
    """Persist *value* to the datarun file so later steps can find it."""
    os.makedirs(os.path.dirname(DATARUN_FILE), exist_ok=True)
    with open(DATARUN_FILE, "w") as f:
        f.write(value + "\n")
