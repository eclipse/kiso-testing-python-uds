#!/usr/bin/env python

from __future__ import annotations

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

import logging
import queue

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

logger = logging.getLogger(__name__)

CAN_FD_DATA_LENGTHS = (8, 12, 16, 20, 24, 32, 48, 64)

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
    def __init__(self, connector=None, **kwargs):

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
        if self.__addressingType in (CanTpAddressingTypes.NORMAL, CanTpAddressingTypes.NORMAL_FIXED):
            self.__minPduLength = 7
            self.__maxPduLength = 63
            self.__pduStartIndex = 0
        elif self.__addressingType in (CanTpAddressingTypes.EXTENDED, CanTpAddressingTypes.MIXED):
            self.__minPduLength = 6
            self.__maxPduLength = 62
            self.__pduStartIndex = 1

        self.__connection = connector
        self.__recvBuffer = queue.Queue()
        self.__discardNegResp = Config.isotp.discard_neg_resp

        # default STmin for flow control when receiving consecutive frames 
        self.st_min = 0.030

    ##
    # @brief send method
    # @param [in] payload the payload to be sent
    # @param [in] tpWaitTime time to wait inside loop
    def send(self, payload, functionalReq=False, tpWaitTime=0.01) -> None:
        result = self.encode_isotp(payload, functionalReq)
        return result
    
    def make_single_frame(self, payload: list[int]) -> list[int]:
        single_frame = [0x00] * 8
        if len(payload) <= self.__minPduLength:   
            single_frame[N_PCI_INDEX] += CanTpMessageType.SINGLE_FRAME << 4
            single_frame[SINGLE_FRAME_DL_INDEX] += len(payload)
            single_frame[SINGLE_FRAME_DATA_START_INDEX:] = fillArray(
                payload, self.__minPduLength
            )
        else:
            single_frame[N_PCI_INDEX] = 0
            single_frame[FIRST_FRAME_DL_INDEX_LOW] = len(payload)
            single_frame[FIRST_FRAME_DATA_START_INDEX:] = payload
        return single_frame
    
    def make_first_frame(self, payload: list[int]) -> list[int]:
        first_frame = [0x00] * 8
        payload_len = len(payload)
        payloadLength_highNibble = (payload_len & 0xF00) >> 8
        payloadLength_lowNibble = payload_len & 0x0FF
        first_frame[N_PCI_INDEX] += CanTpMessageType.FIRST_FRAME << 4
        first_frame[FIRST_FRAME_DL_INDEX_HIGH] += payloadLength_highNibble
        first_frame[FIRST_FRAME_DL_INDEX_LOW] = payloadLength_lowNibble
        first_frame[FIRST_FRAME_DATA_START_INDEX:] = payload[0 : self.__maxPduLength - 1]
        return first_frame
    
    def make_consecutive_frame(self, payload: list[int], sequence_number: int = 1) -> list[int]:
        consecutive_frame = [0x00] * 8
        consecutive_frame[N_PCI_INDEX] += CanTpMessageType.CONSECUTIVE_FRAME << 4
        consecutive_frame[CONSECUTIVE_FRAME_SEQUENCE_NUMBER_INDEX] += sequence_number
        consecutive_frame[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:] = payload
        return consecutive_frame
    
    def make_flow_control_frame(self, blocksize: int = 0, st_min: float = 0) -> list[int]:
        flow_control = [0x00] * 8
        flow_control[N_PCI_INDEX] = 0x30
        flow_control[FLOW_CONTROL_BS_INDEX] = blocksize
        flow_control[FLOW_CONTROL_STMIN_INDEX] = self.encode_stMin(st_min)
        return flow_control

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
    ) -> list[int] | None:

        payloadLength = len(payload)
        payloadPtr = 0

        state = CanTpState.IDLE

        if payloadLength > CANTP_MAX_PAYLOAD_LENGTH:
            raise ValueError("Payload too large for CAN Transport Protocol")

        if payloadLength < self.__maxPduLength:
            state = CanTpState.SEND_SINGLE_FRAME
        else:
            # we might need a check for functional request as we may not be able to service functional requests for
            # multi frame requests
            state = CanTpState.SEND_FIRST_FRAME

        sequenceNumber = 1
        endOfMessage_flag = False

        blockList = []
        currBlock = []

        # TODO this needs fixing to get the timing from the config
        # general timeout when waiting for a flow control frame from the ECU
        timeoutTimer = ResettableTimer(1)
        stMinTimer = ResettableTimer()

        data = None

        while endOfMessage_flag is False:

            if state == CanTpState.WAIT_FLOW_CONTROL:
                rxPdu = self.getNextBufferedMessage(timeoutTimer.remainingTime)
                if rxPdu is None:
                    raise TimeoutError("Timed out while waiting for flow control message")

                N_PCI = (rxPdu[0] & 0xF0) >> 4
                if N_PCI == CanTpMessageType.FLOW_CONTROL:
                    fs = rxPdu[0] & 0x0F
                    if fs == CanTpFsTypes.CONTINUE_TO_SEND:
                        if state != CanTpState.WAIT_FLOW_CONTROL:
                            raise ValueError(
                                "Received unexpected Flow Control Continue to Send request"
                            )

                        block_size = rxPdu[FC_BS_INDEX]
                        if block_size == 0:
                            block_size = 585
                        blockList = self.create_blockList(payload[payloadPtr:], block_size)
                        currBlock = blockList.pop(0)
                        stMin = self.decode_stMin(rxPdu[FC_STMIN_INDEX])
                        stMinTimer.timeoutTime = stMin
                        stMinTimer.start()
                        timeoutTimer.stop()
                        state = CanTpState.SEND_CONSECUTIVE_FRAME
                    elif fs == CanTpFsTypes.WAIT:
                        raise NotImplementedError("Wait not currently supported")
                    elif fs == CanTpFsTypes.OVERFLOW:
                        raise Exception("Overflow received from ECU")
                    else:
                        raise ValueError(f"Unexpected fs response from ECU. {rxPdu}")
                else:
                    logger.warning(f"Unexpected response from ECU while waiting for flow control: 0x{bytes(rxPdu).hex()}")

            if state == CanTpState.SEND_SINGLE_FRAME:
                txPdu = self.make_single_frame(payload)
                data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                endOfMessage_flag = True
            elif state == CanTpState.SEND_FIRST_FRAME:
                txPdu = self.make_first_frame(payload)
                payloadPtr += self.__maxPduLength - 1
                data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                timeoutTimer.start()
                state = CanTpState.WAIT_FLOW_CONTROL
            elif state == CanTpState.SEND_CONSECUTIVE_FRAME and stMinTimer.isExpired():
                txPdu = self.make_consecutive_frame(currBlock.pop(0), sequenceNumber)
                payloadPtr += self.__maxPduLength
                data = self.transmit(txPdu, functionalReq, use_external_snd_rcv_functions)
                sequenceNumber = (sequenceNumber + 1) % 16
                stMinTimer.restart()
                if len(currBlock) == 0:
                    if len(blockList) == 0:
                        endOfMessage_flag = True
                    else:
                        timeoutTimer.start()
                        state = CanTpState.WAIT_FLOW_CONTROL

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
    ) -> list:

        payload = []
        payloadPtr = 0
        payloadLength = None

        sequenceNumberExpected = 1

        endOfMessage_flag = False

        state = CanTpState.IDLE

        timeoutTimer = ResettableTimer(timeout_s)
        timeoutTimer.start()

        while endOfMessage_flag is False:

            if use_external_snd_rcv_functions and state != CanTpState.RECEIVING_CONSECUTIVE_FRAME:
                rxPdu = received_data
            else:
                rxPdu = self.getNextBufferedMessage(timeout=timeoutTimer.remainingTime)
                if rxPdu is None:
                    raise TimeoutError(f"Timed out while waiting for message in state {state.name}")

            if rxPdu[N_PCI_INDEX] == 0x00:
                rxPdu = rxPdu[1:]
                N_PCI = CanTpMessageType.SINGLE_FRAME
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
                        raise ValueError(
                            f"Consecutive frame sequence out of order, expected {sequenceNumberExpected} got {sequenceNumber}"
                        )
                    
                    sequenceNumberExpected = (sequenceNumberExpected + 1) % 16
                    payload += rxPdu[CONSECUTIVE_FRAME_SEQUENCE_DATA_START_INDEX:]
                    payloadPtr += self.__maxPduLength
                    timeoutTimer.restart()
                else:
                    logger.warning(
                        f"Unexpected PDU received while waiting for consecutive frame: 0x{bytes(rxPdu).hex()}"
                    )

            if state == CanTpState.SEND_FLOW_CONTROL:
                txPdu = self.make_flow_control_frame(blocksize=0, st_min=self.st_min)
                self.transmit(txPdu)
                state = CanTpState.RECEIVING_CONSECUTIVE_FRAME

            if payloadLength is not None and payloadPtr >= payloadLength:
                endOfMessage_flag = True

        return list(payload[:payloadLength])

    ##
    # @brief clear out the receive list
    def clearBufferedMessages(self):
        with self.__recvBuffer.mutex:
            self.__recvBuffer.queue.clear()

    ##
    # @brief retrieves the next message from the received message buffers
    # @return list, or None if nothing is on the receive list
    def getNextBufferedMessage(self, timeout: float = 0) -> list[int] | None:
        try:
            return self.__recvBuffer.get(timeout=timeout)
        except queue.Empty:
            return None

    ##
    # @brief the listener callback used when a message is received
    def callback_onReceive(self, msg):
        if self.__addressingType == CanTpAddressingTypes.NORMAL:
            if msg.arbitration_id == self.__resId:
                self.__recvBuffer.put(list(msg.data[self.__pduStartIndex :]))
        elif self.__addressingType == CanTpAddressingTypes.NORMAL_FIXED:
            raise NotImplementedError("I do not know how to receive this addressing type yet")
        elif self.__addressingType == CanTpAddressingTypes.MIXED:
            raise NotImplementedError("I do not know how to receive this addressing type yet")
        else:
            raise NotImplementedError("I do not know how to receive this addressing type")

    ##
    # @brief function to decode the StMin parameter
    @staticmethod
    def decode_stMin(val: int) -> float:
        if val <= 0x7F:
            return val / 1000
        elif 0xF1 <= val <= 0xF9:
            return (val & 0x0F) / 10000
        else:
            raise ValueError(
                f"Invalid STMin value {hex(val)}, should be between 0x00 and 0x7F or between 0xF1 and 0xF9"
            )
        
    @staticmethod
    def encode_stMin(val: float) -> int:
        if (0x01 * 1e-3) <= val <= (0x7F * 1e-3):
            # 1ms - 127ms -> 0x01 - 0x7F
            return int(val * 1000)
        elif 1e-4 <= val <= 9e-4:
            # 100us - 900us -> 0xF1 - 0xF9
            return 0xF0 + int(val * 1e4)
        else:
            raise ValueError(
                f"Invalid STMin time {val}, should be between 0.1 and 0.9 ms or between 1 and 127 ms"
            )

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
                curr_payload = payload[payloadPtr:]
                currPdu = fillArray(
                    curr_payload,
                    self.get_padded_length(len(curr_payload) + 1) - 1,
                    fillValue=self.PADDING_PATTERN,
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

    @staticmethod
    def get_padded_length(msg_length: int) -> int:
        """Get the size of the CAN FD message needed to send a message.

        :param msg_length: length of the message to send
        :return: size of the CAN FD message
        """
        return next(size for size in CAN_FD_DATA_LENGTHS if size >= msg_length)

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
