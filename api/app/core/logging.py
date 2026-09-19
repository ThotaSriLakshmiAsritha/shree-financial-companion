import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure one predictable stdout logger for local and hosted runs."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )

