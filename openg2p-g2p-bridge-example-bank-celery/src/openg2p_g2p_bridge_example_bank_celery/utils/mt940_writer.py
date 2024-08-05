from enum import Enum

from openg2p_fastapi_common.service import BaseService


class TransactionType(Enum):
    transfer = "NTRF"


class Mt940Writer(BaseService):
    def create_transaction(
        self,
        value_date,
        entry_date,
        dr_cr,
        transaction_amount,
        transaction_type,
        customer_reference,
        bank_reference,
        funds_code="0",
        supplementary_details=None,
        additional_info=None,
    ):
        transaction = {
            "value_date": value_date,
            "entry_date": entry_date,
            "dr_cr": dr_cr,
            "funds_code": funds_code,
            "transaction_amount": transaction_amount,
            "transaction_type": transaction_type,
            "customer_reference": customer_reference,
            "bank_reference": f"//{bank_reference}",
            "supplementary_details": supplementary_details,
            "additional_info": additional_info,
        }
        return transaction

    def format_transaction(self, transaction):
        return "{value_date}{entry_date}{dr_cr}{funds_code}{transaction_amount}{transaction_type}{customer_reference}{bank_reference}{supplementary_details}".format(
            value_date=transaction["value_date"].strftime("%y%m%d"),
            entry_date=transaction["entry_date"].strftime("%m%d"),
            dr_cr=transaction["dr_cr"],
            funds_code=transaction["funds_code"],
            transaction_amount="{:015.2f}".format(
                transaction["transaction_amount"]
            ).replace(".", ","),
            transaction_type=transaction["transaction_type"].value,
            customer_reference="{:<17}".format(transaction["customer_reference"]),
            bank_reference="{:<17}".format(transaction["bank_reference"]),
            supplementary_details="{:<34}".format(transaction["supplementary_details"]),
        )

    def create_statement(
        self,
        reference_number,
        account,
        statement_number,
        opening_balance,
        closing_balance,
        transactions,
    ):
        statement = {
            "reference_number": reference_number,
            "account": account,
            "statement_number": statement_number,
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "transactions": transactions,
        }
        return statement

    def format_statement(self, statement):
        result = []
        result.append(f':20:{statement["reference_number"]}')
        result.append(f':25:{statement["account"]}')
        result.append(f':28C:{statement["statement_number"]}')
        result.append(f':60F:{statement["opening_balance"]}')
        for transaction in statement["transactions"]:
            result.append(f":61:{self.format_transaction(transaction)}")
            if transaction["additional_info"]:
                result.append(f':86:{transaction["additional_info"]}')
        result.append(f':62F:{statement["closing_balance"]}')
        return "\n".join(result)
