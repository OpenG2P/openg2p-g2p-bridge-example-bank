from decimal import Decimal

from mt940_writer import (
    Account as MT940Account,
)
from mt940_writer import Balance, Statement, Transaction, TransactionType
from openg2p_g2p_bridge_example_bank_models.models import (
    Account,
    AccountingLog,
    AccountStatement,
    DebitCreditTypes,
)
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from ..app import celery_app, get_engine
from ..config import Settings
from ..utils import Mt940Writer, TransactionType

_config = Settings.get_config()
_engine = get_engine()


@celery_app.task(name="account_statement_generator")
def account_statement_generator(account_statement_id: int):
    session_maker = sessionmaker(bind=_engine, expire_on_commit=False)
    with session_maker() as session:
        account_statement = (
            session.execute(
                select(AccountStatement).where(
                    AccountStatement.id == account_statement_id
                )
            )
            .scalars()
            .first()
        )

        if not account_statement:
            return

        account = (
            session.execute(
                select(Account).where(
                    Account.account_number == account_statement.account_number
                )
            )
            .scalars()
            .first()
        )

        if not account:
            return

        account_logs = (
            session.execute(
                select(AccountingLog).where(
                    AccountingLog.account_number == account_statement.account_number
                )
            )
            .scalars()
            .all()
        )

        if not account_logs:
            return

        currency = account.account_currency
        statement_date = account_statement.account_statement_date
        mt940_account = MT940Account(account.account_number, "000001")
        mt940_opening_balance = Balance(Decimal("100000000"), statement_date, currency)
        mt940_closing_balance = Balance(
            Decimal(account.book_balance), statement_date, currency
        )


        mt940_writer = Mt940Writer.get_component()
        transactions = []
        for account_log in account_logs:
            transaction_debit_credit = account_log.debit_credit
            if account_log.debit_credit == DebitCreditTypes.DEBIT:
                transaction_debit_credit = "D"
            if account_log.debit_credit == DebitCreditTypes.CREDIT:
                transaction_debit_credit = "C"
            if (
                account_log.debit_credit == DebitCreditTypes.DEBIT
                and account_log.transaction_amount < 0
            ):
                transaction_debit_credit = "RD"
            if (
                account_log.debit_credit == DebitCreditTypes.CREDIT
                and account_log.transaction_amount < 0
            ):
                transaction_debit_credit = "RC"

            transactions.append(
                mt940_writer.create_transaction(
                    account_log.transaction_date,
                    account_log.transaction_date,
                    transaction_debit_credit,
                    Decimal(abs(account_log.transaction_amount)),
                    TransactionType.transfer,
                    account_log.customer_reference_no,
                    account_log.reference_no[:16],
                    "",
                    "",
                    f"{account_log.narrative_1}\n{account_log.narrative_2}"
                    f"\n{account_log.narrative_3}\n{account_log.narrative_4}"
                    f"\n{account_log.narrative_5}\n{account_log.narrative_6}",
                )
            )

        statement = mt940_writer.create_statement(
            account_statement_id,
            mt940_account,
            "1/1",
            mt940_opening_balance,
            mt940_closing_balance,
            transactions,
        )

        account_statement.account_statement_lob = str(statement)
        session.commit()
