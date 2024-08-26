import logging
import random
import uuid
from datetime import datetime
from typing import List

from openg2p_g2p_bridge_example_bank_models.models import (
    Account,
    AccountingLog,
    DebitCreditTypes,
    FundBlock,
    InitiatePaymentBatchRequest,
    InitiatePaymentRequest,
    PaymentStatus,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings

_config = Settings.get_config()
_engine = get_engine()
_logger = logging.getLogger(_config.logging_default_logger_name)


@celery_app.task(name="process_payments_beat_producer")
def process_payments_beat_producer():
    _logger.info("Processing payments")
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    with session_maker() as session:
        initiate_payment_batch_requests = (
            session.execute(
                select(InitiatePaymentBatchRequest).where(
                    (InitiatePaymentBatchRequest.payment_status.in_(["PENDING"]))
                    & (
                        InitiatePaymentBatchRequest.payment_initiate_attempts
                        < _config.payment_initiate_attempts
                    )
                )
            )
            .scalars()
            .all()
        )

        for initiate_payment_batch_request in initiate_payment_batch_requests:
            _logger.info(
                f"Initiating payment processing for batch: {initiate_payment_batch_request.batch_id}"
            )
            celery_app.send_task(
                "process_payments_worker",
                args=[initiate_payment_batch_request.batch_id],
                queue="g2p_bridge_celery_worker_tasks",
            )
        _logger.info("Payments processing initiated")
        session.commit()


@celery_app.task(name="process_payments_worker")
def process_payments_worker(payment_request_batch_id: str):
    _logger.info(f"Processing payments for batch: {payment_request_batch_id}")
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    with session_maker() as session:
        initiate_payment_batch_request = (
            session.execute(
                select(InitiatePaymentBatchRequest).where(
                    InitiatePaymentBatchRequest.batch_id == payment_request_batch_id
                )
            )
            .scalars()
            .first()
        )
        try:
            initiate_payment_requests = (
                session.execute(
                    select(InitiatePaymentRequest).where(
                        InitiatePaymentRequest.batch_id == payment_request_batch_id
                    )
                )
                .scalars()
                .all()
            )

            failure_logs = []
            for initiate_payment_request in initiate_payment_requests:
                accounting_log: AccountingLog = construct_accounting_log(
                    initiate_payment_request
                )

                account = update_account(
                    initiate_payment_request.remitting_account,
                    initiate_payment_request.payment_amount,
                    session,
                )
                fund_block = update_fund_block(
                    accounting_log.corresponding_block_reference_no,
                    initiate_payment_request.payment_amount,
                    session,
                )

                failure_random_number = random.randint(1, 100)
                if failure_random_number <= 30:
                    failure_logs.append(accounting_log)

                session.add(accounting_log)
                session.add(fund_block)
                session.add(account)

            # End of loop

            generate_failures(failure_logs, session)
            initiate_payment_batch_request.payment_initiate_attempts += 1
            initiate_payment_batch_request.payment_status = PaymentStatus.PROCESSED
            _logger.info(f"Payments processed for batch: {payment_request_batch_id}")
            session.commit()
        except Exception as e:
            _logger.error(f"Error processing payment: {e}")
            initiate_payment_batch_request.payment_status = PaymentStatus.PENDING
            initiate_payment_batch_request.payment_initiate_attempts += 1
            session.commit()


def construct_accounting_log(initiate_payment_request: InitiatePaymentRequest):
    return AccountingLog(
        reference_no=str(uuid.uuid4()),
        corresponding_block_reference_no=initiate_payment_request.funds_blocked_reference_number,
        customer_reference_no=initiate_payment_request.payment_reference_number,
        debit_credit=DebitCreditTypes.DEBIT,
        account_number=initiate_payment_request.remitting_account,
        transaction_amount=initiate_payment_request.payment_amount,
        transaction_date=datetime.utcnow(),
        transaction_currency=initiate_payment_request.remitting_account_currency,
        transaction_code="DBT",
        narrative_1=initiate_payment_request.narrative_1,
        narrative_2=initiate_payment_request.narrative_2,
        narrative_3=initiate_payment_request.narrative_3,
        narrative_4=initiate_payment_request.narrative_4,
        narrative_5=initiate_payment_request.narrative_5,
        narrative_6=initiate_payment_request.narrative_6,
        active=True,
    )


def generate_failures(failure_logs: List[AccountingLog], session):
    _logger.info("Generating failures")
    failure_reasons = [
        "ACCOUNT_CLOSED",
        "ACCOUNT_NOT_FOUND",
        "ACCOUNT_DORMANT",
        "ACCOUNT_DECEASED",
    ]
    for failure_log in failure_logs:
        account_log: AccountingLog = AccountingLog(
            reference_no=str(uuid.uuid4()),
            customer_reference_no=failure_log.customer_reference_no,
            debit_credit=failure_log.debit_credit,
            account_number=failure_log.account_number,
            transaction_amount=-failure_log.transaction_amount,
            transaction_date=failure_log.transaction_date,
            transaction_currency=failure_log.transaction_currency,
            transaction_code=failure_log.transaction_code,
            narrative_1=failure_log.narrative_1,
            narrative_2=failure_log.narrative_2,
            narrative_3=failure_log.narrative_3,
            narrative_4=failure_log.narrative_4,
            narrative_5=failure_log.narrative_5,
            narrative_6=random.choice(failure_reasons),
            active=True,
        )

        account = update_account(
            account_log.account_number, account_log.transaction_amount, session
        )
        fund_block = update_fund_block(
            failure_log.corresponding_block_reference_no,
            account_log.transaction_amount,
            session,
        )

        session.add(account_log)
        session.add(account)
        session.add(fund_block)


def update_account(remitting_account_number, payment_amount, session) -> Account:
    account = (
        session.execute(
            select(Account).where(Account.account_number == remitting_account_number)
        )
        .scalars()
        .first()
    )
    account.book_balance -= payment_amount
    account.blocked_amount -= payment_amount
    account.available_balance = account.book_balance - account.blocked_amount
    return account


def update_fund_block(block_reference_no, payment_amount, session) -> FundBlock:
    fund_block = (
        session.execute(
            select(FundBlock).where(FundBlock.block_reference_no == block_reference_no)
        )
        .scalars()
        .first()
    )
    fund_block.amount_released += payment_amount
    return fund_block
