from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from openg2p_g2p_bridge_api.controllers import DisbursementEnvelopeController
from openg2p_g2p_bridge_models.errors.codes import G2PBridgeErrorCodes
from openg2p_g2p_bridge_models.errors.exceptions import DisbursementEnvelopeException
from openg2p_g2p_bridge_models.schemas import (
    DisbursementEnvelopePayload,
    DisbursementEnvelopeRequest,
    DisbursementEnvelopeResponse,
    ResponseStatus,
)


def mock_create_disbursement_envelope(is_valid, error_code=None):
    if not is_valid:
        raise DisbursementEnvelopeException(
            code=error_code, message=f"{error_code} error."
        )
    return DisbursementEnvelopePayload(
        disbursement_envelope_id="env123",
        benefit_program_mnemonic="TEST123",
        disbursement_frequency="Monthly",
        cycle_code_mnemonic="CYCLE42",
        number_of_beneficiaries=100,
        number_of_disbursements=100,
        total_disbursement_amount=5000.00,
        disbursement_schedule_date=datetime.date(datetime.utcnow()),
    )


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementEnvelopeService.get_component")
async def test_create_disbursement_envelope_success(mock_service_get_component):
    mock_service_instance = AsyncMock()
    mock_service_instance.create_disbursement_envelope = AsyncMock(
        return_value=mock_create_disbursement_envelope(True)
    )
    mock_service_instance.construct_disbursement_envelope_success_response = AsyncMock()

    mock_service_get_component.return_value = mock_service_instance

    expected_payload = mock_create_disbursement_envelope(True)
    expected_response = DisbursementEnvelopeResponse(
        response_status=ResponseStatus.SUCCESS, response_payload=expected_payload
    )
    mock_service_instance.construct_disbursement_envelope_success_response.return_value = (
        expected_response
    )
    controller = DisbursementEnvelopeController()
    request_payload = DisbursementEnvelopeRequest(
        request_payload=DisbursementEnvelopePayload(
            benefit_program_mnemonic="TEST123",
            disbursement_frequency="Monthly",
            cycle_code_mnemonic="CYCLE42",
            number_of_beneficiaries=100,
            number_of_disbursements=100,
            total_disbursement_amount=5000.00,
            disbursement_schedule_date=datetime.date(datetime.utcnow()),
        )
    )

    actual_response = await controller.create_disbursement_envelope(request_payload)

    assert actual_response == expected_response


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementEnvelopeService.get_component")
@pytest.mark.parametrize("error_code", list(G2PBridgeErrorCodes))
async def test_create_disbursement_envelope_errors(
    mock_service_get_component, error_code
):
    mock_service_instance = AsyncMock()
    mock_service_instance.create_disbursement_envelope.side_effect = (
        lambda request: mock_create_disbursement_envelope(False, error_code)
    )
    mock_service_instance.construct_disbursement_envelope_error_response = AsyncMock()

    mock_service_get_component.return_value = mock_service_instance

    error_response = DisbursementEnvelopeResponse(
        response_status=ResponseStatus.FAILURE,
        response_error_code=error_code,
    )

    mock_service_instance.construct_disbursement_envelope_error_response.return_value = (
        error_response
    )

    controller = DisbursementEnvelopeController()

    request_payload = DisbursementEnvelopeRequest(
        request_payload=DisbursementEnvelopePayload(
            benefit_program_mnemonic="",  # Trigger the error
            disbursement_frequency="Monthly",
            cycle_code_mnemonic="CYCLE42",
            number_of_beneficiaries=100,
            number_of_disbursements=100,
            total_disbursement_amount=5000.00,
            disbursement_schedule_date=datetime.date(datetime.utcnow()),
        )
    )

    actual_response = await controller.create_disbursement_envelope(request_payload)

    assert (
        actual_response == error_response
    ), f"The response did not match the expected error response for {error_code}."


def mock_cancel_disbursement_envelope(is_valid, error_code=None):
    if not is_valid:
        raise DisbursementEnvelopeException(
            code=error_code, message=f"{error_code} error."
        )

    return DisbursementEnvelopePayload(
        disbursement_envelope_id="env123",
        benefit_program_mnemonic="TEST123",
        disbursement_frequency="Monthly",
        cycle_code_mnemonic="CYCLE42",
        number_of_beneficiaries=100,
        number_of_disbursements=100,
        total_disbursement_amount=5000.00,
        disbursement_schedule_date=datetime.date(datetime.utcnow()),
    )


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementEnvelopeService.get_component")
async def test_cancel_disbursement_envelope_success(mock_service_get_component):
    mock_service_instance = AsyncMock()
    mock_service_instance.cancel_disbursement_envelope = AsyncMock(
        return_value=mock_cancel_disbursement_envelope(True)
    )
    mock_service_instance.construct_disbursement_envelope_success_response = AsyncMock()

    mock_service_get_component.return_value = mock_service_instance

    successful_payload = mock_cancel_disbursement_envelope(True)
    expected_response = DisbursementEnvelopeResponse(
        response_status=ResponseStatus.SUCCESS, response_payload=successful_payload
    )
    mock_service_instance.construct_disbursement_envelope_success_response.return_value = (
        expected_response
    )

    controller = DisbursementEnvelopeController()
    request_payload = DisbursementEnvelopeRequest(
        request_payload=DisbursementEnvelopePayload(disbursement_envelope_id="env123")
    )

    actual_response = await controller.cancel_disbursement_envelope(request_payload)
    assert actual_response == expected_response


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementEnvelopeService.get_component")
@pytest.mark.parametrize(
    "error_code",
    [
        G2PBridgeErrorCodes.DISBURSEMENT_ENVELOPE_NOT_FOUND,
        G2PBridgeErrorCodes.DISBURSEMENT_ENVELOPE_ALREADY_CANCELED,
    ],
)
async def test_cancel_disbursement_envelope_failure(
    mock_service_get_component, error_code
):
    mock_service_instance = AsyncMock()
    mock_service_instance.cancel_disbursement_envelope.side_effect = (
        lambda request: mock_cancel_disbursement_envelope(False, error_code)
    )
    mock_service_instance.construct_disbursement_envelope_error_response = AsyncMock()

    mock_service_get_component.return_value = mock_service_instance

    error_response = DisbursementEnvelopeResponse(
        response_status=ResponseStatus.FAILURE,
        response_error_code=error_code.value,
    )
    mock_service_instance.construct_disbursement_envelope_error_response.return_value = (
        error_response
    )

    controller = DisbursementEnvelopeController()
    request_payload = DisbursementEnvelopeRequest(
        request_payload=DisbursementEnvelopePayload(
            disbursement_envelope_id="env123"  # Assuming this ID triggers the error
        )
    )

    actual_response = await controller.cancel_disbursement_envelope(request_payload)
    assert (
        actual_response == error_response
    ), f"The response for {error_code} did not match the expected error response."
