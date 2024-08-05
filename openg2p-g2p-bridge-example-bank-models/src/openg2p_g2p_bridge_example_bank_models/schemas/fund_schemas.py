from typing import Optional

from pydantic import BaseModel


class CheckFundRequest(BaseModel):
    account_number: str
    account_currency: str
    total_funds_needed: float


class CheckFundResponse(BaseModel):
    status: str
    account_number: str
    has_sufficient_funds: bool
    error_message: Optional[str] = None


class BlockFundsRequest(BaseModel):
    account_no: str
    currency: str
    amount: float


class BlockFundsResponse(BaseModel):
    status: str
    block_reference_no: str
    error_message: Optional[str] = None


class InitiatePaymentPayload(BaseModel):
    payment_reference_number: str
    remitting_account: str
    remitting_account_currency: str
    payment_amount: float
    funds_blocked_reference_number: str
    beneficiary_name: str

    beneficiary_account: str
    beneficiary_account_currency: str
    beneficiary_account_type: str
    beneficiary_bank_code: str
    beneficiary_branch_code: str

    beneficiary_mobile_wallet_provider: Optional[str] = None
    beneficiary_phone_no: Optional[str] = None

    beneficiary_email: Optional[str] = None
    beneficiary_email_wallet_provider: Optional[str] = None

    narrative_1: Optional[str] = None
    narrative_2: Optional[str] = None
    narrative_3: Optional[str] = None
    narrative_4: Optional[str] = None
    narrative_5: Optional[str] = None
    narrative_6: Optional[str] = None

    payment_date: str


class InitiatorPaymentResponse(BaseModel):
    status: str
    error_message: Optional[str] = None
