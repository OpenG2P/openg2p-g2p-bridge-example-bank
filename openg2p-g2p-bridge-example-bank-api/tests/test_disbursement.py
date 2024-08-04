import datetime
from unittest.mock import AsyncMock, patch

import pytest
from openg2p_g2p_bridge_api.controllers import DisbursementController
from openg2p_g2p_bridge_models.errors.codes import G2PBridgeErrorCodes
from openg2p_g2p_bridge_models.errors.exceptions import DisbursementException
from openg2p_g2p_bridge_models.models import CancellationStatus
from openg2p_g2p_bridge_models.schemas import (
    DisbursementPayload,
    DisbursementRequest,
    DisbursementResponse,
    ResponseStatus,
)


def mock_create_disbursements(is_valid, disbursement_payloads):
    if not is_valid:
        raise DisbursementException(
            code=G2PBridgeErrorCodes.INVALID_DISBURSEMENT_PAYLOAD,
            disbursement_payloads=disbursement_payloads,
        )
    return disbursement_payloads


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementService.get_component")
async def test_create_disbursements_success(mock_service_get_component):
    mock_service_instance = AsyncMock()
    disbursement_payloads = [
        DisbursementPayload(
            disbursement_envelope_id="env123",
            beneficiary_id="123AB",
            disbursement_amount=1000,
        )
    ]
    mock_service_instance.create_disbursements = AsyncMock(
        return_value=mock_create_disbursements(True, disbursement_payloads)
    )
    mock_service_instance.construct_disbursement_success_response = AsyncMock(
        return_value=DisbursementResponse(
            response_status=ResponseStatus.SUCCESS,
            response_payload=disbursement_payloads,
        )
    )

    mock_service_get_component.return_value = mock_service_instance

    controller = DisbursementController()
    request_payload = DisbursementRequest(request_payload=disbursement_payloads)

    response = await controller.create_disbursements(request_payload)

    assert response.response_status == ResponseStatus.SUCCESS
    assert response.response_payload == disbursement_payloads


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementService.get_component")
async def test_create_disbursements_failure(mock_service_get_component):
    mock_service_instance = AsyncMock()
    disbursement_payloads = [
        DisbursementPayload(
            disbursement_envelope_id="env123",
            beneficiary_id="123AB",
            disbursement_amount=1000,
        )
    ]
    mock_service_instance.create_disbursements = AsyncMock(
        side_effect=lambda req: mock_create_disbursements(False, req.request_payload)
    )
    mock_service_instance.construct_disbursement_error_response = AsyncMock(
        return_value=DisbursementResponse(
            response_status=ResponseStatus.FAILURE,
            response_error_code=G2PBridgeErrorCodes.INVALID_DISBURSEMENT_PAYLOAD,
            response_payload=disbursement_payloads,
        )
    )

    mock_service_get_component.return_value = mock_service_instance

    controller = DisbursementController()
    request_payload = DisbursementRequest(request_payload=disbursement_payloads)

    response = await controller.create_disbursements(request_payload)

    assert response.response_status == ResponseStatus.FAILURE
    assert (
        response.response_error_code == G2PBridgeErrorCodes.INVALID_DISBURSEMENT_PAYLOAD
    )


def mock_cancel_disbursements(is_valid, disbursement_payloads):
    if not is_valid:
        raise DisbursementException(
            code=G2PBridgeErrorCodes.DISBURSEMENT_ALREADY_CANCELED,
            disbursement_payloads=disbursement_payloads,
        )
    for payload in disbursement_payloads:
        payload.cancellation_status = CancellationStatus.Cancelled
        payload.cancellation_time_stamp = datetime.datetime.utcnow()
    return disbursement_payloads


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementService.get_component")
async def test_cancel_disbursements_success(mock_service_get_component):
    mock_service_instance = AsyncMock()
    disbursement_payloads = [
        DisbursementPayload(
            disbursement_id="123",
            beneficiary_id="123AB",
            disbursement_amount=1000,
            cancellation_status=None,
        )
    ]
    mock_service_instance.cancel_disbursements = AsyncMock(
        return_value=mock_cancel_disbursements(True, disbursement_payloads)
    )
    mock_service_instance.construct_disbursement_success_response = AsyncMock(
        return_value=DisbursementResponse(
            response_status=ResponseStatus.SUCCESS,
            response_payload=disbursement_payloads,
        )
    )

    mock_service_get_component.return_value = mock_service_instance

    controller = DisbursementController()
    request_payload = DisbursementRequest(request_payload=disbursement_payloads)

    response = await controller.cancel_disbursements(request_payload)

    assert response.response_status == ResponseStatus.SUCCESS
    assert all(
        payload.cancellation_status == CancellationStatus.Cancelled
        for payload in response.response_payload
    )


@pytest.mark.asyncio
@patch("openg2p_g2p_bridge_api.services.DisbursementService.get_component")
async def test_cancel_disbursements_failure(mock_service_get_component):
    mock_service_instance = AsyncMock()
    disbursement_payloads = [
        DisbursementPayload(
            disbursement_id="123",
            beneficiary_id="123AB",
            disbursement_amount=1000,
            cancellation_status=None,
        )
    ]
    mock_service_instance.cancel_disbursements = AsyncMock(
        side_effect=lambda req: mock_cancel_disbursements(False, req.request_payload)
    )
    mock_service_instance.construct_disbursement_error_response = AsyncMock(
        return_value=DisbursementResponse(
            response_status=ResponseStatus.FAILURE,
            response_error_code=G2PBridgeErrorCodes.DISBURSEMENT_ALREADY_CANCELED,
            response_payload=disbursement_payloads,
        )
    )

    mock_service_get_component.return_value = mock_service_instance

    controller = DisbursementController()
    request_payload = DisbursementRequest(request_payload=disbursement_payloads)

    response = await controller.cancel_disbursements(request_payload)

    assert response.response_status == ResponseStatus.FAILURE
    assert (
        response.response_error_code
        == G2PBridgeErrorCodes.DISBURSEMENT_ALREADY_CANCELED
    )
