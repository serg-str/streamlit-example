from typing import Dict

import kombu
import pytest
from fastapi.testclient import TestClient
import logging
from python_example.core.config import settings


def test_celery_worker_test(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
) -> None:
    data = {"msg": "test"}
    with pytest.raises(Exception) as info:
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-celery/",
            json=data,
            headers=superuser_token_headers,
        )
        response = r.json()
        logging.info(response)
    assert isinstance(info.value, kombu.exceptions.OperationalError)
