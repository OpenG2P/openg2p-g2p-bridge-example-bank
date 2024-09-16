import logging

from typing import Optional
from fastapi import Form
from fastapi.responses import PlainTextResponse

from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.controller import BaseController
from openg2p_g2p_bridge_example_bank_models.models import Account

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class USSDController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["USSD Controller"]

        self.router.add_api_route(
            "/ussd",
            self.ussd,
            response_class=PlainTextResponse,
            response_model=str,
            methods=["POST"],
        )

    async def ussd(
            self,
            sessionId: str = Form(),
            serviceCode: str = Form(),
            phoneNumber: str = Form(),
            networkCode: str = Form(),
            text: Optional[str] = Form(""),
    ):
        response: str = ""
        _logger.info(f"Your input is {text}")
        if text == "":
            response = "CON What do you want to do \n"
            response += "1. Get account balance \n"
            response += "2. Initiate transfer"
        elif text == "1":
            response = await get_account_balance(phoneNumber)
        elif text == "2":
            response = "END Bye!"
        else:
            response = "END Invalid choice selected!"
        
        return response

    async def get_account_balance(
        self,
        phone_number: str
        
    ) -> str:
        _logger.info("Fetching account balance through USSD")
        _logger.info(f"Phone Number: {phone_number}")
        phone_number_parsed = phone_number[1:]
        _logger.info(f"Parsed Phone Number: {phone_number_parsed}")



        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            account_db_query = select(Account).where(
                Account.account_holder_phone
                == phone_number_parsed
            )
            result = await session.execute(account_db_query)
            account = result.scalars().first()

            if not account:
                _logger.error("Account not found")
                return f"Account not found for this phone number: {phone_number}"

            return f"Available balance is {account.available_balance}"
