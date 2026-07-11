import io
import logging
import logging.config
from unittest import TestCase

from python_example.logger import LOG_CONFIG

logging.config.dictConfig(LOG_CONFIG)


class MyLoggerTest(TestCase):
    def setUp(self) -> None:
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.log = logging.getLogger("base")
        self.log.setLevel(logging.INFO)
        self.log.addHandler(self.handler)

    def test_logger_sin_message(self) -> None:
        self.log.info("sin number: 123-456-789")
        self.handler.flush()
        self.assertEqual(
            self.stream.getvalue().replace("\n", ""),
            "sin number: <REDACTED>",
        )

    def test_credit_card_message(self) -> None:
        self.log.info("credit card number: 5415 9052 3492 1230")
        self.handler.flush()
        self.assertEqual(
            self.stream.getvalue().replace("\n", ""),
            "credit card number: <REDACTED>",
        )

    def test_ip_address_message(self) -> None:
        self.log.warning("ip address: 192.158.1.38")
        self.handler.flush()
        self.assertEqual(
            self.stream.getvalue().replace("\n", ""),
            "ip address: <REDACTED>",
        )

    def test_url_message(self) -> None:
        self.log.warning("url: https://test.website.com")
        self.handler.flush()
        self.assertEqual(
            self.stream.getvalue().replace("\n", ""),
            "url: https://test.website.com",
        )

    def tearDown(self) -> None:
        self.log.removeHandler(self.handler)
        self.handler.close()
