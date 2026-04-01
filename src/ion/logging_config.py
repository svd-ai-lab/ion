"""Structured logging for the ion server → ~/.ion/server.log."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from ion.home import ION_HOME


def setup_server_logging() -> logging.Logger:
    """Configure and return the ``ion.server`` logger.

    Writes to ``~/.ion/server.log`` with rotation (5 MB, 3 backups).
    """
    ION_HOME.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("ion.server")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = RotatingFileHandler(
            ION_HOME / "server.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)

    return logger
