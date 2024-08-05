from datetime import datetime
from enum import Enum

from openg2p_fastapi_common.models import BaseORMModelWithTimes
from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column


class PaymentStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DebitCreditTypes(Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class Account(BaseORMModelWithTimes):
    __tablename__ = "accounts"
    account_holder_name: Mapped[str] = mapped_column(String)
    account_number: Mapped[str] = mapped_column(String)
    account_currency: Mapped[str] = mapped_column(String)
    book_balance: Mapped[float] = mapped_column(Float)
    available_balance: Mapped[float] = mapped_column(Float)
    blocked_amount: Mapped[float] = mapped_column(Float, default=0)


class FundBlock(BaseORMModelWithTimes):
    __tablename__ = "fund_blocks"
    block_reference_no: Mapped[str] = mapped_column(String, index=True, unique=True)
    account_no: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    amount_released: Mapped[float] = mapped_column(Float, default=0)


class InitiatePaymentRequest(BaseORMModelWithTimes):
    __tablename__ = "initiate_payment_requests"
    payment_reference_number = mapped_column(
        String, index=True, unique=True
    )  # disbursement id

    remitting_account: Mapped[str] = mapped_column(String, nullable=False)
    remitting_account_currency: Mapped[str] = mapped_column(String, nullable=False)
    payment_amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[str] = mapped_column(String, nullable=False)
    funds_blocked_reference_number: Mapped[str] = mapped_column(String, nullable=False)

    beneficiary_name: Mapped[str] = mapped_column(String)
    beneficiary_account: Mapped[str] = mapped_column(String)
    beneficiary_account_currency: Mapped[str] = mapped_column(String)
    beneficiary_account_type: Mapped[str] = mapped_column(String)
    beneficiary_bank_code: Mapped[str] = mapped_column(String)
    beneficiary_branch_code: Mapped[str] = mapped_column(String)

    beneficiary_mobile_wallet_provider: Mapped[str] = mapped_column(
        String, nullable=True
    )
    beneficiary_phone_no: Mapped[str] = mapped_column(String, nullable=True)

    beneficiary_email: Mapped[str] = mapped_column(String, nullable=True)
    beneficiary_email_wallet_provider: Mapped[str] = mapped_column(
        String, nullable=True
    )

    narrative_1: Mapped[str] = mapped_column(
        String, nullable=True
    )  # disbursement narrative
    narrative_2: Mapped[str] = mapped_column(String, nullable=True)  # program pneumonic
    narrative_3: Mapped[str] = mapped_column(
        String, nullable=True
    )  # cycle code pneumonic
    narrative_4: Mapped[str] = mapped_column(String, nullable=True)  # beneficiary id
    narrative_5: Mapped[str] = mapped_column(String, nullable=True)
    narrative_6: Mapped[str] = mapped_column(String, nullable=True)

    payment_initiate_attempts: Mapped[int] = mapped_column(Integer, default=0)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SqlEnum(PaymentStatus), default=PaymentStatus.PENDING
    )


class AccountingLog(BaseORMModelWithTimes):
    __tablename__ = "accounting_logs"
    reference_no: Mapped[str] = mapped_column(String, index=True, unique=True)
    customer_reference_no: Mapped[str] = mapped_column(String, index=True)
    debit_credit: Mapped[DebitCreditTypes] = mapped_column(SqlEnum(DebitCreditTypes))
    account_number: Mapped[str] = mapped_column(String, index=True)
    transaction_amount: Mapped[float] = mapped_column(Float)
    transaction_date: Mapped[datetime] = mapped_column(DateTime)
    transaction_currency: Mapped[str] = mapped_column(String)
    transaction_code: Mapped[str] = mapped_column(String, nullable=True)

    narrative_1: Mapped[str] = mapped_column(String, nullable=True)  # disbursement id
    narrative_2: Mapped[str] = mapped_column(String, nullable=True)  # beneficiary id
    narrative_3: Mapped[str] = mapped_column(String, nullable=True)  # program pneumonic
    narrative_4: Mapped[str] = mapped_column(
        String, nullable=True
    )  # cycle code pneumonic
    narrative_5: Mapped[str] = mapped_column(String, nullable=True)  # beneficiary email
    narrative_6: Mapped[str] = mapped_column(
        String, nullable=True
    )  # beneficiary phone number
