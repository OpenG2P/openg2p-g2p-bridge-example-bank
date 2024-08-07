import logging
import uuid
from typing import List

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.controller import BaseController
from openg2p_g2p_bridge_example_bank_models.models import (
    FundBlock,
    InitiatePaymentBatchRequest,
    InitiatePaymentRequest,
)
from openg2p_g2p_bridge_example_bank_models.schemas import (
    InitiatePaymentPayload,
    InitiatorPaymentResponse,
)
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class PaymentController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Payments Management"]

        self.router.add_api_route(
            "/initiate_payment",
            self.initiate_payment,
            response_model=InitiatorPaymentResponse,
            methods=["POST"],
        )

    async def initiate_payment(
        self, initiate_payment_payloads: List[InitiatePaymentPayload]
    ) -> InitiatorPaymentResponse:
        _logger.info("Initiating payment")
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            batch_id = str(uuid.uuid4())
            initiate_payment_batch_request = InitiatePaymentBatchRequest(
                batch_id=batch_id,
                active=True,
            )
            session.add(initiate_payment_batch_request)
            initiate_payment_requests = []
            for initiate_payment_payload in initiate_payment_payloads:
                fund_block_stmt = select(FundBlock).where(
                    FundBlock.block_reference_no
                    == initiate_payment_payload.funds_blocked_reference_number
                )
                fund_block_result = await session.execute(fund_block_stmt)
                fund_block = fund_block_result.scalars().first()

                if (
                    not fund_block
                    or initiate_payment_payload.payment_amount > fund_block.amount
                    or fund_block.currency
                    != initiate_payment_payload.remitting_account_currency
                ):
                    _logger.error(
                        "Invalid funds block reference or mismatch in details"
                    )
                    return InitiatorPaymentResponse(
                        status="failed",
                        error_message="Invalid funds block reference or mismatch in details",
                    )

                initiate_payment_request = InitiatePaymentRequest(
                    batch_id=batch_id,
                    payment_reference_number=initiate_payment_payload.payment_reference_number,
                    remitting_account=initiate_payment_payload.remitting_account,
                    remitting_account_currency=initiate_payment_payload.remitting_account_currency,
                    payment_amount=initiate_payment_payload.payment_amount,
                    funds_blocked_reference_number=initiate_payment_payload.funds_blocked_reference_number,
                    beneficiary_name=initiate_payment_payload.beneficiary_name,
                    beneficiary_account=initiate_payment_payload.beneficiary_account,
                    beneficiary_account_currency=initiate_payment_payload.beneficiary_account_currency,
                    beneficiary_account_type=initiate_payment_payload.beneficiary_account_type,
                    beneficiary_bank_code=initiate_payment_payload.beneficiary_bank_code,
                    beneficiary_branch_code=initiate_payment_payload.beneficiary_branch_code,
                    beneficiary_mobile_wallet_provider=initiate_payment_payload.beneficiary_mobile_wallet_provider,
                    beneficiary_phone_no=initiate_payment_payload.beneficiary_phone_no,
                    beneficiary_email=initiate_payment_payload.beneficiary_email,
                    beneficiary_email_wallet_provider=initiate_payment_payload.beneficiary_email_wallet_provider,
                    payment_date=initiate_payment_payload.payment_date,
                    narrative_1=initiate_payment_payload.narrative_1,
                    narrative_2=initiate_payment_payload.narrative_2,
                    narrative_3=initiate_payment_payload.narrative_3,
                    narrative_4=initiate_payment_payload.narrative_4,
                    narrative_5=initiate_payment_payload.narrative_5,
                    narrative_6=initiate_payment_payload.narrative_6,
                    active=True,
                )
                initiate_payment_requests.append(initiate_payment_request)

            session.add_all(initiate_payment_requests)
            await session.commit()
            _logger.info("Payment initiated successfully")
            return InitiatorPaymentResponse(status="success", error_message="")
