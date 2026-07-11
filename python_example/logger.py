import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import LogRecord


SENSITIVE_PATTERNS = [
    r"\d{3}-\d{3}-\d{3}",  # Social Security Number (SSN) pattern
    r"\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}",  # Credit card number pattern
    r"\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4}",  # Phone number
    r"(0[1-9]|1[0-2])[-/.](0[1-9]|[12][0-9]|3[01])[-/.](19|20)\d\d",  # date of birth
    r"((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",  # IP address
    r"\b(SECRET)\b",  # secret keyword
    # remove this api key since it can filter out the correct value for example UUID and signal name
    # r"(?=(?:.{32}|.{36}))[a-zA-Z0-9_-]*",  # API key with 32 or 36 length
]

DATE_FORMAT = "TZ:%Z %Y-%m-%d %H:%M:%S"


class SensitiveDataFilter(logging.Filter):
    def __init__(self, patterns=None):
        super().__init__()
        self.patterns = patterns or []

    def filter(self, record: logging.LogRecord) -> bool:
        for pattern in self.patterns:
            record.msg = re.sub(pattern, "<REDACTED>", record.msg)
        return True


class RequestIdFilter(logging.Filter):
    def __init__(self, name: str = "") -> None:
        super().__init__(name)

    def filter(self, record: "LogRecord") -> bool:
        rid = os.environ.get("request_id", "Not-provided")
        record.request_id = rid
        return True


# https://docs.python.org/3/library/logging.config.html#dictionary-schema-details
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sensitive_info": {
            "()": SensitiveDataFilter,
            "patterns": SENSITIVE_PATTERNS,
        },
        "request_id": {
            "()": RequestIdFilter,
        },
    },
    "formatters": {
        "info": {
            "class": "logging.Formatter",
            "datefmt": DATE_FORMAT,
             "format": (
                "%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(filename)s |"
                "L%(lineno)s | %(funcName)s() | %(message)s"
            ),
        },
        "debug": {
            "class": "logging.Formatter",
            "datefmt": DATE_FORMAT,
            "format": (
                "%(asctime)s.%(msecs)03d | %(levelname)s | %(request_id)s | %(name)s | "
                "%(filename)s | L%(lineno)s | %(funcName)s() | %(message)s"
            ),
        },
    },
    "handlers": {
        "base": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["sensitive_info"],
            "formatter": "info",
        },
        "debug": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["sensitive_info", "request_id"],
            "formatter": "debug",
        },
    },
    "loggers": {
        "base": {"handlers": ["base"], "level": "INFO", "propagate": True},
        "debug": {"handlers": ["debug"], "level": "DEBUG", "propagate": True},
        "uvicorn": {"handlers": ["base"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["base"], "level": "INFO", "propagate": False},
    },
}
