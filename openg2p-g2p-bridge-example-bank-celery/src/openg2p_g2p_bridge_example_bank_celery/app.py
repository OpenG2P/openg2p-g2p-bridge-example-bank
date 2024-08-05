# ruff: noqa: E402
import logging

from .config import Settings
_config = Settings.get_config()


from celery import Celery
from openg2p_fastapi_common.app import Initializer as BaseInitializer
from openg2p_g2p_bridge_example_bank_api.controllers import (
    BlockFundsController,
    FundAvailabilityController,
    PaymentController,
)
from sqlalchemy import create_engine

_logger = logging.getLogger(_config.logging_default_logger_name)


class Initializer(BaseInitializer):
    def initialize(self, **kwargs):
        super().initialize()

        BlockFundsController().post_init()
        FundAvailabilityController().post_init()
        PaymentController().post_init()


def get_engine():
    if _config.db_datasource:
        db_engine = create_engine(_config.db_datasource)
        return db_engine


celery_app = Celery(
    "example_bank_celery_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["openg2p_g2p_bridge_example_bank_celery.tasks.process_payment"],
)

celery_app.conf.beat_schedule = {
    "process_payments": {
        "task": "process_payments",
        "schedule": _config.process_payment_frequency,
    }
}

celery_app.conf.timezone = "UTC"
