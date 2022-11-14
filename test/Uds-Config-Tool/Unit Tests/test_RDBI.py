import traceback
from pathlib import Path

import pytest

from uds.config import Config
from uds.uds_communications.TransportProtocols.Can.CanTp import CanTp
from uds.uds_communications.Uds.Uds import Uds


@pytest.fixture
def default_tp_config():
    DEFAULT_TP_CONFIG = {
        "addressing_type": "NORMAL",
        "n_sa": 0xFF,
        "n_ta": 0xFF,
        "n_ae": 0xFF,
        "m_type": "DIAGNOSTICS",
        "discard_neg_resp": False,
    }
    DEFAULT_TP_CONFIG["req_id"] = 0xb0
    DEFAULT_TP_CONFIG["res_id"] = 0xb1
    return DEFAULT_TP_CONFIG


@pytest.fixture
def default_uds_config():
    DEFAULT_UDS_CONFIG = {
        "transport_protocol": "CAN",
        "p2_can_client": 5,
        "p2_can_server": 1,
    }
    return DEFAULT_UDS_CONFIG


def test_RDBI_staticLength(monkeypatch, default_tp_config, default_uds_config):

    here = Path(__file__).parent
    filename = "Bootloader.odx"
    odxFile = here.joinpath(filename)

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        return [
            0x62,
            0xF1,
            0x8C,
            0x41,
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x35,
            0x35,
            0x36,
        ]

    expected = {"ECU_Serial_Number": "ABC0011223344556"}

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("ECU Serial Number")

    assert expected == actual


def test_RDBI_minMaxLength(monkeypatch, default_tp_config, default_uds_config):
    here = Path(__file__).parent
    odxFile = here.joinpath("minmaxlength.odx")

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0x02, 0x94]
        assert functionalReq == False
        assert tpWaitTime == 0.01
        return False

    def mock_return(self, timeout_s):
        # DID: 660 => 0x2 0x94 Termination: "Zero" Min: 1 Max: 15 Data: ABC0011223344
        return [
            0x62, # SID
            0x02, # DID
            0x94, # DID
            0x41, # DATA ...
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x00 # Termination Char
        ]
    expected = {"PartNumber": "ABC0011223344"}

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)


    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("Dynamic_PartNumber")

    assert expected == actual


def test_RDBI_minLengthOnly(monkeypatch, default_tp_config, default_uds_config):

    here = Path(__file__).parent
    odxFile = here.joinpath("minlengthonly.odx")

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0x02, 0x94]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        # DID: 660 => 0x2 0x94 Termination: "end-of-pdu" Min: 1 Data: ABC0011223344
        return [
            0x62, # SID
            0x02, # DID
            0x94, # DID
            0x41, # DATA ...
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
        ] # no Termination Char for end-of-pdu
    expected = {"PartNumber": "ABC0011223344"}

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)


    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("Dynamic_PartNumber")

    assert expected == actual


def test_RDBI_singleDIDmixedResponse(monkeypatch, default_tp_config, default_uds_config):
    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x80]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        # numberOfModules = 0x01   (1 bytes as specified in "_Bootloader_1")
        # Boot Software Identification = "SwId12345678901234567890"   (24 bytes as specified in "_Bootloader_71")
        return [
            0x62, # SID
            0xF1, # DID
            0x80, # DID
            0x01, # Data 1
            0x53, # Data 2 ...
            0x77,
            0x49,
            0x64,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x30,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x30,
        ]
    expected = ({
        "numberOfModules": [0x01],
        "Boot_Software_Identification": "SwId12345678901234567890",
    })

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier("Boot Software Identification")

    assert expected == actual


def test_RDBI_multipleDIDs(monkeypatch, default_tp_config, default_uds_config):
    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    def mock_send(self, payload, functionalReq, tpWaitTime):
        # Boot Software Version Number DID: 0xF1 0x09 = 61705
        # ECU Serial Number DID: 0xF1 0x8C = 61836
        assert payload == [0x22, 0xF1, 0x8C, 0xF1, 0x09]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        # Boot Software Version Number = "111"   (3 bytes/ 24 bits as specified in "_Bootloader_40")
        # ECU Serial Number = "ABC0011223344556"   (16 bytes/ 128 bits as specified in "_Bootloader_87")
        return [
            0x62, # SID
            0xF1, # DID 1
            0x8C, # DID 1
            0x41, # Data
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x35,
            0x35,
            0x36,
            0xF1, # DID 2
            0x09, # DID 2
            0x01, # Data
            0x01,
            0x01,
        ] # len = 24 (1 SID, 2 DID, 16 DATA, 2 DID, 3 DATA)

    expected = (
        {"ECU_Serial_Number": "ABC0011223344556"},
        {"Boot_Software_Version_Number": [1, 1, 1]}
    )

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier(["ECU Serial Number", "Boot Software Version Number"])

    assert expected == actual


def test_RDBI_multipleDIDMixedResponse(monkeypatch, default_tp_config, default_uds_config):

    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C, 0xF1, 0x80]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
    # ECU Serial Number = "ABC0011223344556"   (16 bytes as specified in "_Bootloader_87")
    # numberOfModules = 0x01   (1 bytes as specified in "_Bootloader_1")
    # Boot Software Identification = "SwId12345678901234567890"   (24 bytes as specified in "_Bootloader_71")
        return [
            0x62, # SID
            0xF1, # DID 1
            0x8C, # DID 1
            0x41, # Data ...
            0x42,
            0x43,
            0x30,
            0x30,
            0x31,
            0x31,
            0x32,
            0x32,
            0x33,
            0x33,
            0x34,
            0x34,
            0x35,
            0x35,
            0x36,
            0xF1, # DID 2
            0x80, # DID 2
            0x01, # Data 1
            0x53, # Data 2 ...
            0x77,
            0x49,
            0x64,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x30,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x30,
        ] # size 46 (1 SID, 2 DID, 16  Data, 2 DID, 1 Data, 24 Data)

    expected = (
        {"ECU_Serial_Number": "ABC0011223344556"},
        {
            "numberOfModules": [0x01],
            "Boot_Software_Identification": "SwId12345678901234567890"
        },
    )

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    actual = uds.readDataByIdentifier(["ECU Serial Number", "Boot Software Identification"])

    assert expected == actual


def test_RDBI_negResponse0x13(monkeypatch, default_tp_config, default_uds_config):

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        return [0x7F, 0x22, 0x13]

    expected = {'NRC': 19, 'NRC_Label': None}

    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    try:
        actual = uds.readDataByIdentifier(
            "ECU Serial Number"
        )
    except:
        actual = traceback.format_exc().split("\n")[-2:-1][0]  # extract the exception text
    assert expected == actual


def test_RDBI_negResponse0x22(monkeypatch, default_tp_config, default_uds_config):

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        return [0x7F, 0x22, 0x22]

    expected = {'NRC': 34, 'NRC_Label': None}

    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    try:
        actual = uds.readDataByIdentifier(
            "ECU Serial Number"
        )
    except:
        actual = traceback.format_exc().split("\n")[-2:-1][0]  # extract the exception text
    assert expected == actual


def test_RDBI_negResponse0x31(monkeypatch, default_tp_config, default_uds_config):

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        return [0x7F, 0x22, 0x31]

    expected = {'NRC': 49, 'NRC_Label': None}

    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    try:
        actual = uds.readDataByIdentifier(
            "ECU Serial Number"
        )
    except:
        actual = traceback.format_exc().split("\n")[-2:-1][0]  # extract the exception text
    assert expected == actual


def test_RDBI_negResponse0x33(monkeypatch, default_tp_config, default_uds_config):

    def mock_send(self, payload, functionalReq, tpWaitTime):
        assert payload == [0x22, 0xF1, 0x8C]
        assert functionalReq == False
        assert tpWaitTime == 0.01

        return False

    def mock_return(self, timeout_s):
        return [0x7F, 0x22, 0x33]

    expected = {'NRC': 51, 'NRC_Label': None}

    here = Path(__file__).parent
    odxFile = here.joinpath("Bootloader.odx")

    monkeypatch.setattr(CanTp, "send", mock_send)
    monkeypatch.setattr(CanTp, "recv", mock_return)

    Config.load_com_layer_config(default_tp_config, default_uds_config)
    uds = Uds(odxFile)

    try:
        actual = uds.readDataByIdentifier(
            "ECU Serial Number"
        )
    except:
        actual = traceback.format_exc().split("\n")[-2:-1][0]  # extract the exception text
    assert expected == actual