#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import unittest
from unittest.mock import patch
from parameterized import parameterized

from uds import CanTp
from uds.config import Config

PADDING_PATTERN = [CanTp.PADDING_PATTERN]


class CanTpMocker(CanTp):
    @patch("uds.config.IsoTpConfig")
    def __init__(
        self,
        iso_mocker,
        Mtype="DIAGNOSTICS",
        adressing_type="NORMAL",
        connector=None,
        **kwargs
    ):
        iso_mocker.m_type = Mtype
        iso_mocker.addressing_type = adressing_type
        Config.isotp = iso_mocker

        super().__init__(connector=connector, **kwargs)


class CanTpTestCase(unittest.TestCase):
    @parameterized.expand(
        [
            (3, 4),
            (7, 0),
            (8, 3),
            (11, 0),
            (13, 2),
            (15, 0),
            (16, 3),
            (19, 0),
            (22, 1),
            (23, 0),
            (28, 3),
            (31, 0),
            (39, 8),
            (47, 0),
            (56, 7),
            (63, 0),
        ]
    )
    def test_create_blocklist_payload_inferior_than_63_bytes(
        self, len_payload, len_padding_expected
    ):
        test_val = []
        for i in range(0, len_payload):
            test_val.append(0xFF)

        tp_connection = CanTpMocker()

        a = tp_connection.create_blockList(test_val, 1)

        self.assertEqual(a, [[test_val + len_padding_expected * PADDING_PATTERN]])

    def test_create_blocklist_longer_than_63_bytes_blocksize_1(self):
        test_val = []
        for i in range(0, 66):
            test_val.append(0xFF)

        tp_connection = CanTpMocker()

        a = tp_connection.create_blockList(test_val, 1)

        self.assertEqual(
            a,
            [
                [test_val[:63]],
                [test_val[63:] + (7 - len(test_val[63:])) * PADDING_PATTERN],
            ],
        )

    def test_create_blocklist_longer_than_63_bytes_blocksize_2(self):
        test_val = []
        for i in range(0, 66):
            test_val.append(0xFF)

        tp_connection = CanTpMocker()

        a = tp_connection.create_blockList(test_val, 2)

        self.assertEqual(
            a,
            [
                [
                    test_val[:63],
                    test_val[63:] + (7 - len(test_val[63:])) * PADDING_PATTERN,
                ],
            ],
        )

    def test_create_blocklist_no_block_size_pdu(self):
        testVal = []
        for i in range(0, 4089):
            testVal.append(0xFF)

        result = []

        for i in range(64):
            result.append([0xFF] * 63)

        result.append([0xFF] * 57 + [0x0] * 6)

        tpConnection = CanTpMocker()

        a = tpConnection.create_blockList(testVal, 585)
        self.assertEqual(a, [result])

    @parameterized.expand(
        [
            (4, 8),
            (8, 8),
            (11, 12),
            (14, 16),
            (16, 16),
            (18, 20),
            (21, 24),
            (24, 24),
            (28, 32),
            (46, 48),
            (55, 64),
        ]
    )
    def test_get_padded_length(self, len_payload, expected_padded_length):
        tpConnection = CanTpMocker()

        self.assertEqual(
            expected_padded_length, tpConnection.get_padded_length(len_payload)
        )

    def test_canTpRaiseExceptionOnTooLargePayload(self):
        payload = []
        for i in range(0, 4096):
            payload.append(0)
        tpConnection = CanTpMocker()
        with self.assertRaises(Exception):
            tpConnection.send(payload)

    @patch("can.interfaces.virtual.VirtualBus.send")
    def test_canTpSendSingleFrame(self, sendMock):

        result = []

        def msgData(msg):
            nonlocal result
            result = msg.data

        sendMock.side_effect = msgData

        tpConnection = CanTp(reqId=0x600, resId=0x650)

        payload = [0x01, 0x02, 0x03]
        tpConnection.send(payload)

        self.assertEqual(result, [0x03, 0x01, 0x02, 0x03, 0x00, 0x00, 0x00, 0x00])

    @patch("can.interfaces.virtual.VirtualBus.send")
    @patch("uds.CanTp.getNextBufferedMessage")
    def test_smallMultiFrameSend(self, getNextMessageMock, canSendMock):

        result = []
        count = 1

        fcSent = False

        def msgData(msg):

            nonlocal getNextMessageMock
            nonlocal result

            getNextMessageMock.side_effect = getNextMessageFunc
            result += msg.data

        def getNextMessageFunc():

            nonlocal fcSent

            if fcSent is True:
                return None

            if fcSent is False:
                fcSent = True
                return [0x30, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

        getNextMessageMock.return_value = None
        canSendMock.side_effect = msgData

        tpConnection = CanTp(reqId=0x600, resId=0x650)

        tpConnection.send([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])

        self.assertEqual(
            [
                0x10,
                0x08,
                0x01,
                0x02,
                0x03,
                0x04,
                0x05,
                0x06,
                0x21,
                0x07,
                0x08,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ],
            result,
        )

    @patch("can.interfaces.virtual.VirtualBus.send")
    @patch("uds.CanTp.getNextBufferedMessage")
    def test_largerMultiFrameSend(self, getNextMessageMock, canSendMock):

        result = []
        count = 1

        fcSent = False

        def msgData(msg):

            nonlocal getNextMessageMock
            nonlocal result

            getNextMessageMock.side_effect = getNextMessageFunc
            result += msg.data

        def getNextMessageFunc():

            nonlocal fcSent

            if fcSent is True:
                return None

            if fcSent is False:
                fcSent = True
                return [0x30, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

        getNextMessageMock.return_value = None
        canSendMock.side_effect = msgData

        tpConnection = CanTp(reqId=0x600, resId=0x650)

        payload = []
        for i in range(1, 41):
            payload.append(i)

        tpConnection.send(payload)

        self.assertEqual(
            [
                0x10,
                0x28,
                0x01,
                0x02,
                0x03,
                0x04,
                0x05,
                0x06,
                0x21,
                0x07,
                0x08,
                0x09,
                0x0A,
                0x0B,
                0x0C,
                0x0D,
                0x22,
                0x0E,
                0x0F,
                0x10,
                0x11,
                0x12,
                0x13,
                0x14,
                0x23,
                0x15,
                0x16,
                0x17,
                0x18,
                0x19,
                0x1A,
                0x1B,
                0x24,
                0x1C,
                0x1D,
                0x1E,
                0x1F,
                0x20,
                0x21,
                0x22,
                0x25,
                0x23,
                0x24,
                0x25,
                0x26,
                0x27,
                0x28,
                0x00,
            ],
            result,
        )

    @patch("can.interfaces.virtual.VirtualBus.send")
    @patch("uds.CanTp.getNextBufferedMessage")
    def test_canTpLargeMultiFrameWithMultipleBlocks(
        self, getNextMessageMock, canSendMock
    ):

        result = []
        blockSize = 20
        cfCounter = 0
        fcSent = False

        ffSent_flag = False

        def msgData(msg):
            nonlocal getNextMessageMock
            nonlocal result
            nonlocal ffSent_flag
            nonlocal cfCounter

            if ffSent_flag is True:
                cfCounter += 1

            if ffSent_flag is False:
                ffSent_flag = True
                getNextMessageMock.side_effect = getNextMessageFunc

            result += msg.data

        def getNextMessageFunc():

            nonlocal result
            nonlocal fcSent
            nonlocal cfCounter
            nonlocal blockSize

            if fcSent is False:
                fcSent = True
                return [0x30, blockSize, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

            if cfCounter == blockSize:
                fcSent = False
                cfCounter = 0

            if fcSent is True:
                return None

        getNextMessageMock.return_value = None
        canSendMock.side_effect = msgData

        payload = []
        for i in range(0, 500):
            payload.append(i % 256)

        tpConnection = CanTp(reqId=0x600, resId=0x650)

        tpConnection.send(payload)

        expectedResult = [
            0x11,
            0xF4,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x21,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x22,
            0x0D,
            0x0E,
            0x0F,
            0x10,
            0x11,
            0x12,
            0x13,
            0x23,
            0x14,
            0x15,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x24,
            0x1B,
            0x1C,
            0x1D,
            0x1E,
            0x1F,
            0x20,
            0x21,
            0x25,
            0x22,
            0x23,
            0x24,
            0x25,
            0x26,
            0x27,
            0x28,
            0x26,
            0x29,
            0x2A,
            0x2B,
            0x2C,
            0x2D,
            0x2E,
            0x2F,
            0x27,
            0x30,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x28,
            0x37,
            0x38,
            0x39,
            0x3A,
            0x3B,
            0x3C,
            0x3D,
            0x29,
            0x3E,
            0x3F,
            0x40,
            0x41,
            0x42,
            0x43,
            0x44,
            0x2A,
            0x45,
            0x46,
            0x47,
            0x48,
            0x49,
            0x4A,
            0x4B,
            0x2B,
            0x4C,
            0x4D,
            0x4E,
            0x4F,
            0x50,
            0x51,
            0x52,
            0x2C,
            0x53,
            0x54,
            0x55,
            0x56,
            0x57,
            0x58,
            0x59,
            0x2D,
            0x5A,
            0x5B,
            0x5C,
            0x5D,
            0x5E,
            0x5F,
            0x60,
            0x2E,
            0x61,
            0x62,
            0x63,
            0x64,
            0x65,
            0x66,
            0x67,
            0x2F,
            0x68,
            0x69,
            0x6A,
            0x6B,
            0x6C,
            0x6D,
            0x6E,
            0x20,
            0x6F,
            0x70,
            0x71,
            0x72,
            0x73,
            0x74,
            0x75,
            0x21,
            0x76,
            0x77,
            0x78,
            0x79,
            0x7A,
            0x7B,
            0x7C,
            0x22,
            0x7D,
            0x7E,
            0x7F,
            0x80,
            0x81,
            0x82,
            0x83,
            0x23,
            0x84,
            0x85,
            0x86,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x24,
            0x8B,
            0x8C,
            0x8D,
            0x8E,
            0x8F,
            0x90,
            0x91,
            0x25,
            0x92,
            0x93,
            0x94,
            0x95,
            0x96,
            0x97,
            0x98,
            0x26,
            0x99,
            0x9A,
            0x9B,
            0x9C,
            0x9D,
            0x9E,
            0x9F,
            0x27,
            0xA0,
            0xA1,
            0xA2,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0x28,
            0xA7,
            0xA8,
            0xA9,
            0xAA,
            0xAB,
            0xAC,
            0xAD,
            0x29,
            0xAE,
            0xAF,
            0xB0,
            0xB1,
            0xB2,
            0xB3,
            0xB4,
            0x2A,
            0xB5,
            0xB6,
            0xB7,
            0xB8,
            0xB9,
            0xBA,
            0xBB,
            0x2B,
            0xBC,
            0xBD,
            0xBE,
            0xBF,
            0xC0,
            0xC1,
            0xC2,
            0x2C,
            0xC3,
            0xC4,
            0xC5,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0x2D,
            0xCA,
            0xCB,
            0xCC,
            0xCD,
            0xCE,
            0xCF,
            0xD0,
            0x2E,
            0xD1,
            0xD2,
            0xD3,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0x2F,
            0xD8,
            0xD9,
            0xDA,
            0xDB,
            0xDC,
            0xDD,
            0xDE,
            0x20,
            0xDF,
            0xE0,
            0xE1,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0x21,
            0xE6,
            0xE7,
            0xE8,
            0xE9,
            0xEA,
            0xEB,
            0xEC,
            0x22,
            0xED,
            0xEE,
            0xEF,
            0xF0,
            0xF1,
            0xF2,
            0xF3,
            0x23,
            0xF4,
            0xF5,
            0xF6,
            0xF7,
            0xF8,
            0xF9,
            0xFA,
            0x24,
            0xFB,
            0xFC,
            0xFD,
            0xFE,
            0xFF,
            0x00,
            0x01,
            0x25,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x26,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x0D,
            0x0E,
            0x0F,
            0x27,
            0x10,
            0x11,
            0x12,
            0x13,
            0x14,
            0x15,
            0x16,
            0x28,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x1B,
            0x1C,
            0x1D,
            0x29,
            0x1E,
            0x1F,
            0x20,
            0x21,
            0x22,
            0x23,
            0x24,
            0x2A,
            0x25,
            0x26,
            0x27,
            0x28,
            0x29,
            0x2A,
            0x2B,
            0x2B,
            0x2C,
            0x2D,
            0x2E,
            0x2F,
            0x30,
            0x31,
            0x32,
            0x2C,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x2D,
            0x3A,
            0x3B,
            0x3C,
            0x3D,
            0x3E,
            0x3F,
            0x40,
            0x2E,
            0x41,
            0x42,
            0x43,
            0x44,
            0x45,
            0x46,
            0x47,
            0x2F,
            0x48,
            0x49,
            0x4A,
            0x4B,
            0x4C,
            0x4D,
            0x4E,
            0x20,
            0x4F,
            0x50,
            0x51,
            0x52,
            0x53,
            0x54,
            0x55,
            0x21,
            0x56,
            0x57,
            0x58,
            0x59,
            0x5A,
            0x5B,
            0x5C,
            0x22,
            0x5D,
            0x5E,
            0x5F,
            0x60,
            0x61,
            0x62,
            0x63,
            0x23,
            0x64,
            0x65,
            0x66,
            0x67,
            0x68,
            0x69,
            0x6A,
            0x24,
            0x6B,
            0x6C,
            0x6D,
            0x6E,
            0x6F,
            0x70,
            0x71,
            0x25,
            0x72,
            0x73,
            0x74,
            0x75,
            0x76,
            0x77,
            0x78,
            0x26,
            0x79,
            0x7A,
            0x7B,
            0x7C,
            0x7D,
            0x7E,
            0x7F,
            0x27,
            0x80,
            0x81,
            0x82,
            0x83,
            0x84,
            0x85,
            0x86,
            0x28,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x8B,
            0x8C,
            0x8D,
            0x29,
            0x8E,
            0x8F,
            0x90,
            0x91,
            0x92,
            0x93,
            0x94,
            0x2A,
            0x95,
            0x96,
            0x97,
            0x98,
            0x99,
            0x9A,
            0x9B,
            0x2B,
            0x9C,
            0x9D,
            0x9E,
            0x9F,
            0xA0,
            0xA1,
            0xA2,
            0x2C,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0xA7,
            0xA8,
            0xA9,
            0x2D,
            0xAA,
            0xAB,
            0xAC,
            0xAD,
            0xAE,
            0xAF,
            0xB0,
            0x2E,
            0xB1,
            0xB2,
            0xB3,
            0xB4,
            0xB5,
            0xB6,
            0xB7,
            0x2F,
            0xB8,
            0xB9,
            0xBA,
            0xBB,
            0xBC,
            0xBD,
            0xBE,
            0x20,
            0xBF,
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC4,
            0xC5,
            0x21,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0xCA,
            0xCB,
            0xCC,
            0x22,
            0xCD,
            0xCE,
            0xCF,
            0xD0,
            0xD1,
            0xD2,
            0xD3,
            0x23,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0xD8,
            0xD9,
            0xDA,
            0x24,
            0xDB,
            0xDC,
            0xDD,
            0xDE,
            0xDF,
            0xE0,
            0xE1,
            0x25,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0xE6,
            0xE7,
            0xE8,
            0x26,
            0xE9,
            0xEA,
            0xEB,
            0xEC,
            0xED,
            0xEE,
            0xEF,
            0x27,
            0xF0,
            0xF1,
            0xF2,
            0xF3,
            0x00,
            0x00,
            0x00,
        ]

        self.assertEqual(expectedResult, result)

    @patch("can.interfaces.virtual.VirtualBus.send")
    @patch("uds.CanTp.getNextBufferedMessage")
    def test_canTpLargeMultiFrameWithMultipleBlockChangingBlockSizeDuringTransmission(
        self, getNextMessageMock, canSendMock
    ):

        result = []
        blockSize = 20
        cfCounter = 0
        fcSent = False

        ffSent_flag = False

        def msgData(msg):
            nonlocal getNextMessageMock
            nonlocal result
            nonlocal ffSent_flag
            nonlocal cfCounter

            if ffSent_flag is True:
                cfCounter += 1

            if ffSent_flag is False:
                ffSent_flag = True
                getNextMessageMock.side_effect = getNextMessageFunc

            result += msg.data

        def getNextMessageFunc():

            nonlocal result
            nonlocal fcSent
            nonlocal cfCounter
            nonlocal blockSize

            if fcSent is False:
                fcSent = True
                return [0x30, blockSize, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]

            if cfCounter == blockSize:
                fcSent = False
                cfCounter = 0
                blockSize = 10

            if fcSent is True:
                return None

        getNextMessageMock.return_value = None
        canSendMock.side_effect = msgData

        payload = []
        for i in range(0, 500):
            payload.append(i % 256)

        tpConnection = CanTp(reqId=0x600, resId=0x650)
        tpConnection.send(payload)

        expectedResult = [
            0x11,
            0xF4,
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x21,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x22,
            0x0D,
            0x0E,
            0x0F,
            0x10,
            0x11,
            0x12,
            0x13,
            0x23,
            0x14,
            0x15,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x24,
            0x1B,
            0x1C,
            0x1D,
            0x1E,
            0x1F,
            0x20,
            0x21,
            0x25,
            0x22,
            0x23,
            0x24,
            0x25,
            0x26,
            0x27,
            0x28,
            0x26,
            0x29,
            0x2A,
            0x2B,
            0x2C,
            0x2D,
            0x2E,
            0x2F,
            0x27,
            0x30,
            0x31,
            0x32,
            0x33,
            0x34,
            0x35,
            0x36,
            0x28,
            0x37,
            0x38,
            0x39,
            0x3A,
            0x3B,
            0x3C,
            0x3D,
            0x29,
            0x3E,
            0x3F,
            0x40,
            0x41,
            0x42,
            0x43,
            0x44,
            0x2A,
            0x45,
            0x46,
            0x47,
            0x48,
            0x49,
            0x4A,
            0x4B,
            0x2B,
            0x4C,
            0x4D,
            0x4E,
            0x4F,
            0x50,
            0x51,
            0x52,
            0x2C,
            0x53,
            0x54,
            0x55,
            0x56,
            0x57,
            0x58,
            0x59,
            0x2D,
            0x5A,
            0x5B,
            0x5C,
            0x5D,
            0x5E,
            0x5F,
            0x60,
            0x2E,
            0x61,
            0x62,
            0x63,
            0x64,
            0x65,
            0x66,
            0x67,
            0x2F,
            0x68,
            0x69,
            0x6A,
            0x6B,
            0x6C,
            0x6D,
            0x6E,
            0x20,
            0x6F,
            0x70,
            0x71,
            0x72,
            0x73,
            0x74,
            0x75,
            0x21,
            0x76,
            0x77,
            0x78,
            0x79,
            0x7A,
            0x7B,
            0x7C,
            0x22,
            0x7D,
            0x7E,
            0x7F,
            0x80,
            0x81,
            0x82,
            0x83,
            0x23,
            0x84,
            0x85,
            0x86,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x24,
            0x8B,
            0x8C,
            0x8D,
            0x8E,
            0x8F,
            0x90,
            0x91,
            0x25,
            0x92,
            0x93,
            0x94,
            0x95,
            0x96,
            0x97,
            0x98,
            0x26,
            0x99,
            0x9A,
            0x9B,
            0x9C,
            0x9D,
            0x9E,
            0x9F,
            0x27,
            0xA0,
            0xA1,
            0xA2,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0x28,
            0xA7,
            0xA8,
            0xA9,
            0xAA,
            0xAB,
            0xAC,
            0xAD,
            0x29,
            0xAE,
            0xAF,
            0xB0,
            0xB1,
            0xB2,
            0xB3,
            0xB4,
            0x2A,
            0xB5,
            0xB6,
            0xB7,
            0xB8,
            0xB9,
            0xBA,
            0xBB,
            0x2B,
            0xBC,
            0xBD,
            0xBE,
            0xBF,
            0xC0,
            0xC1,
            0xC2,
            0x2C,
            0xC3,
            0xC4,
            0xC5,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0x2D,
            0xCA,
            0xCB,
            0xCC,
            0xCD,
            0xCE,
            0xCF,
            0xD0,
            0x2E,
            0xD1,
            0xD2,
            0xD3,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0x2F,
            0xD8,
            0xD9,
            0xDA,
            0xDB,
            0xDC,
            0xDD,
            0xDE,
            0x20,
            0xDF,
            0xE0,
            0xE1,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0x21,
            0xE6,
            0xE7,
            0xE8,
            0xE9,
            0xEA,
            0xEB,
            0xEC,
            0x22,
            0xED,
            0xEE,
            0xEF,
            0xF0,
            0xF1,
            0xF2,
            0xF3,
            0x23,
            0xF4,
            0xF5,
            0xF6,
            0xF7,
            0xF8,
            0xF9,
            0xFA,
            0x24,
            0xFB,
            0xFC,
            0xFD,
            0xFE,
            0xFF,
            0x00,
            0x01,
            0x25,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x26,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x0D,
            0x0E,
            0x0F,
            0x27,
            0x10,
            0x11,
            0x12,
            0x13,
            0x14,
            0x15,
            0x16,
            0x28,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x1B,
            0x1C,
            0x1D,
            0x29,
            0x1E,
            0x1F,
            0x20,
            0x21,
            0x22,
            0x23,
            0x24,
            0x2A,
            0x25,
            0x26,
            0x27,
            0x28,
            0x29,
            0x2A,
            0x2B,
            0x2B,
            0x2C,
            0x2D,
            0x2E,
            0x2F,
            0x30,
            0x31,
            0x32,
            0x2C,
            0x33,
            0x34,
            0x35,
            0x36,
            0x37,
            0x38,
            0x39,
            0x2D,
            0x3A,
            0x3B,
            0x3C,
            0x3D,
            0x3E,
            0x3F,
            0x40,
            0x2E,
            0x41,
            0x42,
            0x43,
            0x44,
            0x45,
            0x46,
            0x47,
            0x2F,
            0x48,
            0x49,
            0x4A,
            0x4B,
            0x4C,
            0x4D,
            0x4E,
            0x20,
            0x4F,
            0x50,
            0x51,
            0x52,
            0x53,
            0x54,
            0x55,
            0x21,
            0x56,
            0x57,
            0x58,
            0x59,
            0x5A,
            0x5B,
            0x5C,
            0x22,
            0x5D,
            0x5E,
            0x5F,
            0x60,
            0x61,
            0x62,
            0x63,
            0x23,
            0x64,
            0x65,
            0x66,
            0x67,
            0x68,
            0x69,
            0x6A,
            0x24,
            0x6B,
            0x6C,
            0x6D,
            0x6E,
            0x6F,
            0x70,
            0x71,
            0x25,
            0x72,
            0x73,
            0x74,
            0x75,
            0x76,
            0x77,
            0x78,
            0x26,
            0x79,
            0x7A,
            0x7B,
            0x7C,
            0x7D,
            0x7E,
            0x7F,
            0x27,
            0x80,
            0x81,
            0x82,
            0x83,
            0x84,
            0x85,
            0x86,
            0x28,
            0x87,
            0x88,
            0x89,
            0x8A,
            0x8B,
            0x8C,
            0x8D,
            0x29,
            0x8E,
            0x8F,
            0x90,
            0x91,
            0x92,
            0x93,
            0x94,
            0x2A,
            0x95,
            0x96,
            0x97,
            0x98,
            0x99,
            0x9A,
            0x9B,
            0x2B,
            0x9C,
            0x9D,
            0x9E,
            0x9F,
            0xA0,
            0xA1,
            0xA2,
            0x2C,
            0xA3,
            0xA4,
            0xA5,
            0xA6,
            0xA7,
            0xA8,
            0xA9,
            0x2D,
            0xAA,
            0xAB,
            0xAC,
            0xAD,
            0xAE,
            0xAF,
            0xB0,
            0x2E,
            0xB1,
            0xB2,
            0xB3,
            0xB4,
            0xB5,
            0xB6,
            0xB7,
            0x2F,
            0xB8,
            0xB9,
            0xBA,
            0xBB,
            0xBC,
            0xBD,
            0xBE,
            0x20,
            0xBF,
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC4,
            0xC5,
            0x21,
            0xC6,
            0xC7,
            0xC8,
            0xC9,
            0xCA,
            0xCB,
            0xCC,
            0x22,
            0xCD,
            0xCE,
            0xCF,
            0xD0,
            0xD1,
            0xD2,
            0xD3,
            0x23,
            0xD4,
            0xD5,
            0xD6,
            0xD7,
            0xD8,
            0xD9,
            0xDA,
            0x24,
            0xDB,
            0xDC,
            0xDD,
            0xDE,
            0xDF,
            0xE0,
            0xE1,
            0x25,
            0xE2,
            0xE3,
            0xE4,
            0xE5,
            0xE6,
            0xE7,
            0xE8,
            0x26,
            0xE9,
            0xEA,
            0xEB,
            0xEC,
            0xED,
            0xEE,
            0xEF,
            0x27,
            0xF0,
            0xF1,
            0xF2,
            0xF3,
            0x00,
            0x00,
            0x00,
        ]

        self.assertEqual(expectedResult, result)


if __name__ == "__main__":
    unittest.main()
