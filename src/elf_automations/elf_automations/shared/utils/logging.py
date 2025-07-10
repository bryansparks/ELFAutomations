"""
Logging utilities for teams
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_team_logging(team_name: str, log_dir: Path = None) -> logging.Logger:
    """
    Set up logging for a team

    Args:
        team_name: Name of the team
        log_dir: Directory for log files (default: ./logs)

    Returns:
        Configured logger for the team
    """
    if log_dir is None:
        log_dir = Path("logs")

    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(team_name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # File handler for team communications
    comm_handler = logging.FileHandler(log_dir / f"{team_name}_communications.log")
    comm_handler.setLevel(logging.INFO)
    comm_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    comm_handler.setFormatter(comm_formatter)

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)
    console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(comm_handler)
    logger.addHandler(console_handler)

    return logger


def get_team_logger(team_name: str) -> logging.Logger:
    """Get logger for a team"""
    return logging.getLogger(team_name)


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a basic logger for modules

    Args:
        name: Logger name (usually __name__)
        level: Logging level

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
