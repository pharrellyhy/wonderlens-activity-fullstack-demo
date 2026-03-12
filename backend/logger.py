"""Centralized logging configuration for the WonderLens backend."""

import logging


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Configure and return the application logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("wonderlens")


logger = setup_logger()
