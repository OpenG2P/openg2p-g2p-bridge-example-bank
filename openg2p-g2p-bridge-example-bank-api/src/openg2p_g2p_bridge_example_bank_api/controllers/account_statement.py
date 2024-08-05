from openg2p_fastapi_common.context import dbengine
from openg2p_fastapi_common.controller import BaseController
from openg2p_g2p_bridge_example_bank_models.models import Account, AccountStatement
from openg2p_g2p_bridge_example_bank_models.schemas import (
    AccountStatementRequest,
    AccountStatementResponse,
)
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select

from ..celery_app import celery_app


class AccountStatementController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["Account Statement"]

        self.router.add_api_route(
            "/generate_account_statement",
            self.generate_account_statement,
            response_model=AccountStatementResponse,
            methods=["POST"],
        )

    async def generate_account_statement(
        self, account_statement_request: AccountStatementRequest
    ) -> AccountStatementResponse:
        session_maker = async_sessionmaker(dbengine.get(), expire_on_commit=False)
        async with session_maker() as session:
            stmt = select(Account).where(
                Account.account_number
                == account_statement_request.program_account_number
            )
            result = await session.execute(stmt)
            account = result.scalars().first()

            if not account:
                return AccountStatementResponse(
                    status="failed",
                    error_message="Account not found",
                )

            account_statement = AccountStatement(
                account_number=account_statement_request.program_account_number,
                active=True,
            )
            session.add(account_statement)
            await session.commit()

            # Create a new task to generate the account statement
            celery_app.send_task(
                "account_statement_generator",
                args=(account_statement.id,),
            )

            return AccountStatementResponse(
                status="success", account_statement_id=str(account_statement.id)
            )
