"""Command line entry point: ``python -m gbif_harvestor``."""

from __future__ import annotations

import logging
import os

from .config import Config
from .services.harvest import HarvestService


def main() -> None:
    """Run one harvest from the environment configuration."""
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    HarvestService(Config.from_env()).run()
