"""Celery application. Task modules are added per phase (notifications,
expiry sweeps, reservation timeouts, report exports)."""

from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "pharmacy",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    timezone="Asia/Kolkata",
    enable_utc=True,
)
