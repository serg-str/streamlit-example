from raven import Client

from python_example.core.celery_app import celery_app
from python_example.core.config import settings

client_sentry = Client(settings.LINEPULSE_SVC_SENTRY_DSN)


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"
