#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

import configparser
from os import path
from time import sleep

from uds.config import Config
from uds.interfaces import TpInterface
from uds import ResettableTimer, fillArray
from uds.uds_communications.TransportProtocols.Can.CanTpTypes import (
    CANTP_MAX_PAYLOAD_LENGTH,
    CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX,
    CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX,
    FC_BS_INDEX,
    FC_STMIN_INDEX,
    FIRST_FRAME_DATA_START_INDEX,
    FIRST_FRAME_DL_INDEX_HIGH,
    FIRST_FRAME_DL_INDEX_LOW,
    FLOW_CONTROL_BS_INDEX,
    FLOW_CONTROL_STMIN_INDEX,
    N_PCI_INDEX,
    SINGLE_FRAME_DATA_START_INDEX,
    SINGLE_FRAME_DL_INDEX,
    CanTpAddressingTypes,
    CanTpFsTypes,
    CanTpMessageType,
    CanTpMTypes,
    CanTpState,
)


##
# @class CanTp
# @brief This is the main class to support CAN transport protocol
#
# Will spawn a CanTpListener class for incoming messages
# depends on a bus object for communication on CAN
class CanTp(TpInterface):

    configParams = ["reqId", "resId", "addressingType"]
    PADDING_PATTERN = 0x00

    ##
    # @brief constructor for the CanTp object
    def __init__(self, connector = None, **kwargs):


        self.__N_AE = Config.isotp.n_ae
        self.__N_TA = Config.isotp.n_ta
        self.__N_SA = Config.isotp.n_sa

        Mtype = Config.isotp.m_type
        if Mtype == "DIAGNOSTICS":
            self.__Mtype = CanTpMTypes.DIAGNOSTICS
        elif Mtype == "REMOTE_DIAGNOSTICS":
            self.__Mtype = CanTpMTypes.REMOTE_DIAGNOSTICS
        else:
            raise Exception("Do not understand the Mtype config")

        addressingType = Config.isotp.addressing_type
        if addressingType == "NORMAL":
            self.__addressingType = CanTpAddressingTypes.NORMAL
        elif addressingType == "NORMAL_FIXED":
            self.__addressingType = CanTpAddressingTypes.NORMAL_FIXED
        elif self.__addressingType == "EXTENDED":
            self.__addressingType = CanTpAddressingTypes.EXTENDED
        elif addressingType == "MIXED":
            self.__addressingType = CanTpAddressingTypes.MIXED
        else:
            raise Exception("Do not understand the addressing config")

        self.__reqId = Config.isotp.req_id
        self.__resId = Config.isotp.res_id

        # sets up the relevant parameters in the instance
        if (self.__addressingType == CanTpAddressingTypes.NORMAL) | (
            self.__addressingType == CanTpAddressingTypes.NORMAL_FIXED
        ):
            self.__minPduLength = 7
            self.__maxPduLength = 63
            self.__pduStartIndex = 0
        elif (self.__addressingType == CanTpAddressingTypes.EXTENDED) | (
            self.__addressingType == CanTpAddressingTypes.MIXED
        ):
            self.__minPduLength = 6
            self.__maxPduLength = 62
            self.__pduStartIndex = 1
        self.__connection = connector
        self.__recvBuffer = []
        self.__discardNegResp = Config.isotp.discard_neg_resp

    ##
    # @brief send method
    # @param [in] payload the payload to be sent
    # @param [in] tpWaitTime time to wait inside loop
    def send(self, payload, functionalReq=False, tpWaitTime=0.01):
        self.clearBufferedMessages()
        result = self.encode_isotp(payload, functionalReq, tpWaitTime=tpWaitTime)
        return result

    ##
    # @brief encoding method
    # @param payload the payload to be sent
    # @param use_external_snd_rcv_functions boolean to state if external sending and receiving functions shall be used
    # @param [in] tpWaitTime time to wait inside loop
    def encode_isotp(
        self,
        payload,
        functionalReq: bool = False,
        use_external_snd_rcv_functions: bool = False,
        tpWaitTime=0.01,
    ):

        payloadLength = len(payload)
        payloadPtr = 0

        state = CanTpState.IDLE

        if payloadLength > CANTP_MAX_PAYLOAD_LENGTH:
            raise Exception("Payload too large for CAN Transport Protocol")

        if payloadLength < self.__maxPduLength:
            state = CanTpState.SEND_SINGLE_FRAME
        else:
            # we might need a check for functional request as we may not be able to service functional requests for
            # multi frame requests
            state = CanTpState.SEND_FIRST_FRAME

        txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        sequenceNumber = 1
        endOfMessage_flag = False

        blockList = []
        currBlock = []

        # this needs fixing to get the timing from the config
        timeoutTimer = ResettableTimer(1)
        stMinTimer = ResettableTimer()

        data = None

        while endOfMessage_flag is False:

            rxPdu = None

            if state == CanTpState.WAIT_FLOW_CONTROL:
                rxPdu = self.getNextBufferedMessage()

            if rxPdu is not None:
                N_PCI = (rxPdu[0] & 0xF0) >> 4
                if N_PCI == CanTpMessageType.FLOW_CONTROL:
                    fs = rxPdu[0] & 0x0F
                    if fs == CanTpFsTypes.WAIT:
                        raise Exception("Wait not currently supported")
                    elif fs == CanTpFsTypes.OVERFLOW:
                        raise Exception("Overflow received from ECU")
                    elif fs == CanTpFsTypes.CONTINUE_TO_SEND:
                        if state == CanTpState.WAIT_FLOW_CONTROL:
                            bs = rxPdu[FC_BS_INDEX]
                            if bs == 0:
                                bs = 585
                            blockList = self.create_blockList(payload[payloadPtr:], bs)
                            stMin = self.decode_stMin(rxPdu[FC_STMIN_INDEX])
                            currBlock = blockList.pop(0)
                            state = CanTpState.SEND_CONSECUTIVE_FRAME
                            stMinTimer.timeoutTime = stMin
                            stMinTimer.start()
                            timeoutTimer.stop()
                        else:
                            raise Exception(
                                "Unexpected Flow Control Continue to Send request"
                            )
                    else:
                        raise Exception("Unexpected fs response from ECU")
                else:
                    raise Exception("Unexpected response from device")

            if state == CanTpState.SEND_SINGLE_FRAME:
                if len(payload) <= self.__minPduLength:
                    txPdu[N_PCI_INDEX] += CanTpMessageType.SINGLE_FRAME << 4
                    txPdu[SINGLE_FRAME_DL_INDEX] += payloadLength
                    txPdu[SINGLE_FRAME_DATA_START_INDEX:] = fillArray(
                        payload, self.__minPduLength
                    )
                else:
                    txPdu[N_PCI_INDEX] = 0
                    txPdu[FIRST_FRAME_DL_INDEX_LOW] = payloadLength
                    txPdu[FIRST_FRAME_DATA_START_INDEX:] = payload
                data = self.transmit(
                    txPdu, functionalReq, use_external_snd_rcv_functions
                )
                endOfMessage_flag = True
            elif state == CanTpState.SEND_FIRST_FRAME:
                payloadLength_highNibble = (payloadLength & 0xF00) >> 8
                payloadLength_lowNibble = payloadLength & 0x0FF
                txPdu[N_PCI_INDEX] += CanTpMessageType.FIRST_FRAME << 4
                txPdu[FIRST_FRAME_DL_INDEX_HIGH] += payloadLength_highNibble
                txPdu[FIRST_FRAME_DL_INDEX_LOW] += payloadLength_lowNibble
                txPdu[FIRST_FRAME_DATA_START_INDEX:] = payload[
                    0 : self.__maxPduLength - 1
                ]
                payloadPtr += self.__maxPduLength - 1
                data = self.transmit(
                    txPdu, functionalReq, use_external_snd_rcv_functions
                )
                timeoutTimer.start()
                state = CanTpState.WAIT_FLOW_CONTROL
            elif state == CanTpState.SEND_CONSECUTIVE_FRAME:
                if stMinTimer.isExpired():
                    txPdu[N_PCI_INDEX] += CanTpMessageType.CONSECUTIVE_FRAME << 4
                    txPdu[CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX] += sequenceNumber
                    txPdu[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:] = currBlock.pop(
                        0
                    )
                    payloadPtr += self.__maxPduLength
                    data = self.transmit(
                        txPdu, functionalReq, use_external_snd_rcv_functions
                    )
                    sequenceNumber = (sequenceNumber + 1) % 16
                    stMinTimer.restart()
                    if len(currBlock) == 0:
                        if len(blockList) == 0:
                            endOfMessage_flag = True
                        else:
                            timeoutTimer.start()
                            state = CanTpState.WAIT_FLOW_CONTROL
            else:
                sleep(tpWaitTime)
            txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            # timer / exit condition checks
            if timeoutTimer.isExpired():
                raise Exception("Timeout waiting for message")
        if use_external_snd_rcv_functions:
            return data

    ##
    # @brief recv method
    # @param [in] timeout_ms The timeout to wait before exiting
    # @return a list
    def recv(self, timeout_s=1):
        return self.decode_isotp(timeout_s)

    ##
    # @brief decoding method
    # @param timeout_ms the timeout to wait before exiting
    # @param received_data the data that should be decoded in case of ITF Automation
    # @param use_external_snd_rcv_functions boolean to state if external sending and receiving functions shall be used
    # @return a list
    def decode_isotp(
        self,
        timeout_s=1,
        received_data=None,
        use_external_snd_rcv_functions: bool = False,
    ):
        timeoutTimer = ResettableTimer(timeout_s)

        payload = []
        payloadPtr = 0
        payloadLength = None

        sequenceNumberExpected = 1

        txPdu = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        endOfMessage_flag = False

        state = CanTpState.IDLE

        timeoutTimer.start()
        while endOfMessage_flag is False:

            if (
                use_external_snd_rcv_functions
                and state != CanTpState.RECEIVING_CONSECUTIVE_FRAME
            ):
                rxPdu = received_data
            else:
                rxPdu = self.getNextBufferedMessage()

            if rxPdu is not None:
                if rxPdu[N_PCI_INDEX] == 0x00:
                    rxPdu = rxPdu[1:]
                    N_PCI = 0
                else:
                    N_PCI = (rxPdu[N_PCI_INDEX] & 0xF0) >> 4
                if state == CanTpState.IDLE:
                    if N_PCI == CanTpMessageType.SINGLE_FRAME:
                        payloadLength = rxPdu[N_PCI_INDEX & 0x0F]
                        payload = rxPdu[
                            SINGLE_FRAME_DATA_START_INDEX : SINGLE_FRAME_DATA_START_INDEX
                            + payloadLength
                        ]
                        endOfMessage_flag = True
                    elif N_PCI == CanTpMessageType.FIRST_FRAME:
                        payload = rxPdu[FIRST_FRAME_DATA_START_INDEX:]
                        payloadLength = (
                            (rxPdu[FIRST_FRAME_DL_INDEX_HIGH] & 0x0F) << 8
                        ) + rxPdu[FIRST_FRAME_DL_INDEX_LOW]
                        payloadPtr = self.__maxPduLength - 1
                        state = CanTpState.SEND_FLOW_CONTROL
                elif state == CanTpState.RECEIVING_CONSECUTIVE_FRAME:
                    if N_PCI == CanTpMessageType.CONSECUTIVE_FRAME:
                        sequenceNumber = (
                            rxPdu[CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX] & 0x0F
                        )
                        if sequenceNumber != sequenceNumberExpected:
                            raise Exception("Consecutive frame sequence out of order")
                        else:
                            sequenceNumberExpected = (sequenceNumberExpected + 1) % 16
                        payload += rxPdu[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:]
                        payloadPtr += self.__maxPduLength
                        timeoutTimer.restart()
                    else:
                        raise Exception("Unexpected PDU received")
            else:
                sleep(0.01)

            if state == CanTpState.SEND_FLOW_CONTROL:
                txPdu[N_PCI_INDEX] = 0x30
                txPdu[FLOW_CONTROL_BS_INDEX] = 0
                txPdu[FLOW_CONTROL_STMIN_INDEX] = 0x1E
                self.transmit(txPdu)
                state = CanTpState.RECEIVING_CONSECUTIVE_FRAME

            if payloadLength is not None:
                if payloadPtr >= payloadLength:
                    endOfMessage_flag = True

            if timeoutTimer.isExpired():
                raise Exception("Timeout in waiting for message")

        return list(payload[:payloadLength])


    ##
    # @brief clear out the receive list
    def clearBufferedMessages(self):
        self.__recvBuffer = []

    ##
    # @brief retrieves the next message from the received message buffers
    # @return list, or None if nothing is on the receive list
    def getNextBufferedMessage(self):
        length = len(self.__recvBuffer)
        if length != 0:
            return self.__recvBuffer.pop(0)
        else:
            return None

    ##
    # @brief the listener callback used when a message is received
    def callback_onReceive(self, msg):
        if self.__addressingType == CanTpAddressingTypes.NORMAL:
            if msg.arbitration_id == self.__resId:
                self.__recvBuffer.append(msg.data[self.__pduStartIndex :])
        elif self.__addressingType == CanTpAddressingTypes.NORMAL_FIXED:
            raise Exception("I do not know how to receive this addressing type yet")
        elif self.__addressingType == CanTpAddressingTypes.MIXED:
            raise Exception("I do not know how to receive this addressing type yet")
        else:
            raise Exception("I do not know how to receive this addressing type")

    ##
    # @brief function to decode the StMin parameter
    @staticmethod
    def decode_stMin(val):
        if val <= 0x7F:
            time = val / 1000
            return time
        elif (val >= 0xF1) & (val <= 0xF9):
            time = (val & 0x0F) / 10000
            return time
        else:
            raise Exception("Unknown STMin time")

    ##
    # @brief creates the blocklist from the blocksize and payload
    def create_blockList(self, payload, blockSize):

        blockList = []
        currBlock = []
        currPdu = []

        payloadPtr = 0
        blockPtr = 0

        payloadLength = len(payload)
        pduLength = self.__maxPduLength
        blockLength = blockSize * pduLength

        working = True
        while working:
            if (payloadPtr + pduLength) >= payloadLength:
                working = False
                currPdu = fillArray(
                    payload[payloadPtr:], pduLength, fillValue=self.PADDING_PATTERN
                )
                currBlock.append(currPdu)
                blockList.append(currBlock)

            if working:
                currPdu = payload[payloadPtr : payloadPtr + pduLength]
                currBlock.append(currPdu)
                payloadPtr += pduLength
                blockPtr += pduLength

                if blockPtr == blockLength:
                    blockList.append(currBlock)
                    currBlock = []
                    blockPtr = 0

        return blockList

    ##
    # @brief transmits the data over can using can connection
    def transmit(
        self, data, functionalReq=False, use_external_snd_rcv_functions: bool = False
    ):
        # check functional request
        if functionalReq:
            raise Exception("Functional requests are currently not supported")

        transmitData = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        if (self.__addressingType == CanTpAddressingTypes.NORMAL) | (
            self.__addressingType == CanTpAddressingTypes.NORMAL_FIXED
        ):
            transmitData = data
        elif self.__addressingType == CanTpAddressingTypes.MIXED:
            transmitData[0] = self.__N_AE
            transmitData[1:] = data
        else:
            raise Exception("I do not know how to send this addressing type")
        self.__connection.transmit(transmitData, self.__reqId)

    @property
    def reqIdAddress(self):
        return self.__reqId

    @reqIdAddress.setter
    def reqIdAddress(self, value):
        self.__reqId = value

    @property
    def resIdAddress(self):
        return self.__resId

    @resIdAddress.setter
    def resIdAddress(self, value):
        self.__resId = value

    @property
    def connection(self):
        return self.__connection

    @connection.setter
    def connection(self, value):
        self.__connection = value