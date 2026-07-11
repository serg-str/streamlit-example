# ruff: noqa: E402
import logging

from dotenv import load_dotenv

load_dotenv()
from python_example.db.init_db import init_db
from python_example.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    db = SessionLocal()
    init_db(db)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
