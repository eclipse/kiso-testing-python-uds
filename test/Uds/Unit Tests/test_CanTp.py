

import pytest
from pytest_mock import MockerFixture

from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp
from uds.uds_communications.TransportProtocols.Can.CanTpTypes import CanTpAddressingTypes
from uds.config import Config, IsoTpConfig


@pytest.fixture
def can_tp_inst(mocker: MockerFixture):
    Config.isotp = IsoTpConfig(
        req_id=0x12, 
        res_id=0x21, 
        addressing_type="NORMAL",
        n_ae=0,
        n_sa=0,
        n_ta=0,
        m_type='DIAGNOSTICS',
        discard_neg_resp=False
    )
    CanTp.PADDING_PATTERN = 0xCC
    return CanTp(is_fd=False)


@pytest.fixture
def can_fd_tp_inst(mocker: MockerFixture):
    Config.isotp = IsoTpConfig(
        req_id=0x12, 
        res_id=0x21, 
        addressing_type="NORMAL",
        n_ae=0,
        n_sa=0,
        n_ta=0,
        m_type='DIAGNOSTICS',
        discard_neg_resp=False
    )
    CanTp.PADDING_PATTERN = 0xCC
    return CanTp(is_fd=True)


@pytest.mark.parametrize(
    "expected_stmin_value, expected_stmin_time",
    [
        (0x01, 1e-3), (0x7f, 127e-3), (0xF1, 1e-4), (0xF5, 5e-4), (0xF9, 9e-4),
    ]
)
def test_stmin_decode_encode(expected_stmin_value, expected_stmin_time):
    stmin_value = CanTp.encode_stMin(expected_stmin_time)
    assert stmin_value == expected_stmin_value

    stmin_time = CanTp.decode_stMin(expected_stmin_value)
    assert stmin_time == expected_stmin_time


@pytest.mark.parametrize(
    "payload_to_send, expected_single_frame",
    # less than 7 payload bytes -> 1st byte = 0x0 + MDL | payload | padding (reach 8 bytes)
    [
        (
            [0x22, 0x01, 0x00, 0x00, 0x00], 
            [0x05, 0x22, 0x01, 0x00, 0x00, 0x00, 0xCC, 0xCC]
        ),
        (
            [0x22, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00], 
            [0x07, 0x22, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
        ),
        # more than 7 payload bytes -> 1st byte = 0 | 2nd byte = MDL | payload | padding (reach 12 bytes)
        (
            [0x22, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 
            [0x00, 0x08, 0x22, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xCC]
        ),
    ],
    ids=["less than 8 bytes", "exactly 8 bytes", "more than 8 bytes"]
)
def test_make_single_frame_fd(can_fd_tp_inst: CanTp, payload_to_send, expected_single_frame):
    single_frame = can_fd_tp_inst.make_single_frame(payload_to_send)
    assert single_frame == expected_single_frame


@pytest.mark.parametrize(
    "payload_to_send, expected_transmit_calls, expected_recv_call_count",
    [
        pytest.param(
            [0x12] * 5, 
            [[0x05] + [0x12] * 5 + [0xCC] * 2],
            0,
            id="PDU smaller than 8 bytes -> send 8 bytes with padding"
        ),
        pytest.param(
            [0x12] * 7, 
            [[0x07] + [0x12] * 7],
            0,
            id="PDU exactly 8 bytes -> send 8 bytes without padding"
        ),
        pytest.param(
            [0x12] * 8, 
            [[0x00, 8] + [0x12] * 8 + [0xCC] * 2],
            0,
            id="PDU greater than 8 bytes -> send 12 bytes with padding"
        ),
        pytest.param(
            [0x12] * 11, 
            [([0x00, 11]) + ([0x12] * 11) + ([0xCC] * (16 - 11 - 2))],
            0,
            id="PDU greater than 12 bytes -> send 16 bytes with padding"
        ),
        pytest.param(
            [0x12] * 15, 
            [[0x00, 15] + [0x12] * 15 + [0xCC] * (20 - 15 - 2)],
            0,
            id="PDU greater than 16 bytes -> send 20 bytes with padding"
        ),
        pytest.param(
            [0x12] * 64, 
            [
                ([0x10, 64] + [0x12] * (64 - 2)),   # first frame
                ([0x21] + [0x12] * 2 + [0xCC] * 5)  # single consecutive frame
            ],
            1, # received 'flow control - continue to send'
            id="PDU greater than 64 bytes -> flow control"
        ),
    ]
)
def test_encode_isotp_canfd(can_fd_tp_inst: CanTp, mocker: MockerFixture, payload_to_send, expected_transmit_calls, expected_recv_call_count):
    # the only case where this is called is for flow control -> return a 'continue to send' frame
    mock_recv = mocker.patch.object(can_fd_tp_inst, "getNextBufferedMessage", return_value=[0x30, 0x10, 0x14])
    mock_send = mocker.patch.object(can_fd_tp_inst, "transmit")
    mocker.patch("time.sleep")

    can_fd_tp_inst.encode_isotp(payload_to_send)

    assert mock_recv.call_count == expected_recv_call_count
    assert mock_send.call_count == len(expected_transmit_calls)
    for call, expected_sent_data in zip(mock_send.call_args_list, expected_transmit_calls):
        assert call.args[0] == expected_sent_data


FIRST_FRAME_HEADER_LEN = 2
CAN_FRAME_LEN = 8

@pytest.mark.parametrize(
    "payload_to_send, expected_transmit_calls, expected_recv_call_count",
    [
        #    12 12 12 12 12
        # -> 05 12 12 12 12 CC CC CC
        pytest.param(
            [0x12] * 5, 
            [[0x05] + [0x12] * 5 + [0xCC] * 2],
            0,
            id="PDU smaller than 8 bytes -> send 8 bytes with padding"
        ),
        pytest.param(
            [0x12] * 7, 
            [[0x07] + [0x12] * 7],
            0,
            id="PDU exactly 8 bytes -> send 8 bytes without padding"
        ),
        #    12 12 12 12 12 12 12 12
        # -> 10 08 12 12 12 12 12 12    First frame
        # <- 30 10 14                   Continue to send frame
        # -> 21 12 12 CC CC CC CC CC    Consecutive frame
        pytest.param(
            [0x12] * 8, 
            [
                ([0x10, 8] + [0x12] * (CAN_FRAME_LEN - FIRST_FRAME_HEADER_LEN)),   # first frame
                ([0x21] + [0x12] * FIRST_FRAME_HEADER_LEN + [0xCC] * 5)  # single consecutive frame
            ],
            1,
            id="PDU greater than 8 bytes -> send 12 bytes with padding"
        ),
        pytest.param(
            [0x12] * 11, 
            [
                ([0x10, 11] + [0x12] * (CAN_FRAME_LEN - FIRST_FRAME_HEADER_LEN)),   # first frame
                ([0x21] + [0x12] * 5 + [0xCC] * 2)  # single consecutive frame
            ],
            1,
            id="PDU greater than 12 bytes -> send 16 bytes with padding"
        ),
        pytest.param(
            [0x12] * 64, 
            [
                ([0x10, 64] + [0x12] * 6),           # first frame          6 bytes
                ([0x21] + [0x12] * 7),               # consecutive frame   13 bytes
                ([0x22] + [0x12] * 7),               # consecutive frame   20 bytes
                ([0x23] + [0x12] * 7),               # consecutive frame   27 bytes
                ([0x24] + [0x12] * 7),               # consecutive frame   34 bytes
                ([0x25] + [0x12] * 7),               # consecutive frame   41 bytes
                ([0x26] + [0x12] * 7),               # consecutive frame   48 bytes
                ([0x27] + [0x12] * 7),               # consecutive frame   55 bytes
                ([0x28] + [0x12] * 7),               # consecutive frame   62 bytes
                ([0x29] + [0x12] * 2 + [0xCC] * 5),  # consecutive frame   64 bytes + padding
            ],
            1, # received 'flow control - continue to send'
            id="PDU greater than 64 bytes -> flow control"
        ),
    ]
)
def test_encode_isotp_can(can_tp_inst: CanTp, mocker: MockerFixture, payload_to_send, expected_transmit_calls, expected_recv_call_count):
    # the only case where this is called is for flow control -> return a 'continue to send' frame
    mock_recv = mocker.patch.object(can_tp_inst, "getNextBufferedMessage", return_value=[0x30, 0x10, 0x14])
    mock_send = mocker.patch.object(can_tp_inst, "transmit")
    mocker.patch("time.sleep")

    can_tp_inst.encode_isotp(payload_to_send)

    assert mock_recv.call_count == expected_recv_call_count
    assert mock_send.call_count == len(expected_transmit_calls)
    for call, expected_sent_data in zip(mock_send.call_args_list, expected_transmit_calls):
        assert call.args[0] == expected_sent_data