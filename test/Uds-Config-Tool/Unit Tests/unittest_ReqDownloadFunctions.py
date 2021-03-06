#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import sys
import traceback
import unittest
from unittest import mock

from uds import Uds
from uds.uds_config_tool.UdsConfigTool import createUdsConnection


class RequestDownloadTestCase(unittest.TestCase):

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_reqDownloadRequest(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x74, 0x20, 0x05, 0x00]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __requestDownload to requestDownload in the uds object, so can now call below

        b = a.requestDownload(
            FormatIdentifier=[0x00],
            MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
            MemorySize=[0x00, 0x00, 0x0E, 0x56],
        )  # ... calls __requestDownload, which does the Uds.send

        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(
            {"LengthFormatIdentifier": [0x20], "MaxNumberOfBlockLength": [0x05, 0x00]},
            b,
        )  # ... (returns a dict)

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_reqDownloadRequest02(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x74, 0x40, 0x01, 0x00, 0x05, 0x08]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __requestDownload to requestDownload in the uds object, so can now call below

        b = a.requestDownload(
            FormatIdentifier=[0x00],
            MemoryAddress=[0x01, 0xFF, 0x0A, 0x80],
            MemorySize=[0x03, 0xFF],
        )  # ... calls __requestDownload, which does the Uds.send

        canTp_send.assert_called_with(
            [
                0x34,
                0x00,
                0x24,
                0x01,
                0xFF,
                0x0A,
                0x80,
                0x03,
                0xFF,
            ],
            False,
        )
        self.assertEqual(
            {
                "LengthFormatIdentifier": [0x40],
                "MaxNumberOfBlockLength": [0x01, 0x00, 0x05, 0x08],
            },
            b,
        )  # ... (returns a dict)

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_reqDownloadNegResponse_0x13(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x7F, 0x34, 0x13]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __requestDownload to requestDownload in the uds object, so can now call below

        try:
            b = a.requestDownload(
                FormatIdentifier=[0x00],
                MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
                MemorySize=[0x00, 0x00, 0x0E, 0x56],
            )  # ... calls __requestDownload, which does the Uds.send
        except:
            b = traceback.format_exc().split("\n")[-2:-1][
                0
            ]  # ... extract the exception text
        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(0x13, b["NRC"])

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_wdbiNegResponse_0x22(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x7F, 0x34, 0x22]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __readDataByIdentifier to readDataByIdentifier in the uds object, so can now call below

        try:
            b = a.requestDownload(
                FormatIdentifier=[0x00],
                MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
                MemorySize=[0x00, 0x00, 0x0E, 0x56],
            )  # ... calls __requestDownload, which does the Uds.send
        except:
            b = traceback.format_exc().split("\n")[-2:-1][
                0
            ]  # ... extract the exception text
        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(0x22, b["NRC"])

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_wdbiNegResponse_0x31(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x7F, 0x34, 0x31]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __readDataByIdentifier to readDataByIdentifier in the uds object, so can now call below

        try:
            b = a.requestDownload(
                FormatIdentifier=[0x00],
                MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
                MemorySize=[0x00, 0x00, 0x0E, 0x56],
            )  # ... calls __requestDownload, which does the Uds.send
        except:
            b = traceback.format_exc().split("\n")[-2:-1][
                0
            ]  # ... extract the exception text
        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(0x31, b["NRC"])

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_wdbiNegResponse_0x33(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x7F, 0x34, 0x33]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __readDataByIdentifier to readDataByIdentifier in the uds object, so can now call below

        try:
            b = a.requestDownload(
                FormatIdentifier=[0x00],
                MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
                MemorySize=[0x00, 0x00, 0x0E, 0x56],
            )  # ... calls __requestDownload, which does the Uds.send
        except:
            b = traceback.format_exc().split("\n")[-2:-1][
                0
            ]  # ... extract the exception text
        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(0x33, b["NRC"])

    # patches are inserted in reverse order
    @mock.patch("uds.TestTp.recv")
    @mock.patch("uds.TestTp.send")
    def test_wdbiNegResponse_0x72(self, canTp_send, canTp_recv):

        canTp_send.return_value = False
        canTp_recv.return_value = [0x7F, 0x34, 0x72]

        # Parameters: xml file (odx file), ecu name (not currently used) ...
        a = createUdsConnection(
            "../Functional Tests/Bootloader.odx", "bootloader", transportProtocol="TEST"
        )
        # ... creates the uds object and returns it; also parses out the rdbi info and attaches the __readDataByIdentifier to readDataByIdentifier in the uds object, so can now call below

        try:
            b = a.requestDownload(
                FormatIdentifier=[0x00],
                MemoryAddress=[0x40, 0x03, 0xE0, 0x00],
                MemorySize=[0x00, 0x00, 0x0E, 0x56],
            )  # ... calls __requestDownload, which does the Uds.send
        except:
            b = traceback.format_exc().split("\n")[-2:-1][
                0
            ]  # ... extract the exception text
        canTp_send.assert_called_with(
            [0x34, 0x00, 0x44, 0x40, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x0E, 0x56], False
        )
        self.assertEqual(0x72, b["NRC"])


if __name__ == "__main__":
    unittest.main()
