from __future__ import annotations

from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "dataharvester.log"

    logger.remove()
    logger.add(
        log_file,
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        enqueue=False,
        backtrace=True,
        diagnose=False,
    )
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level="INFO",
    )
    return logger
