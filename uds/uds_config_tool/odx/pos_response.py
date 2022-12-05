from typing import Dict, List

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.param import Param


class PosResponse:
    """encapsulates PARAMs and DID + SID information for parsing and decoding a positive uds response"""

    def __init__(
        self, params: List[Param], did_length: int, did: int, sid_length: int, sid: int
    ) -> None:
        """initialize attributes

        :param params: List of Params that are defined in the POS-RESPONSE for a DID
        :param did_length: byte length of the PosResponse's DID
        :param did: the DID value
        :param sid_length: byte length of the PosResponse's SID
        :param sid: the SID value
        """
        self.params = params
        self.did_length = did_length
        self.did = did
        self.sid_length = sid_length
        self.sid = sid

    def decode(self) -> Dict[str, str]:
        """Decode the data stored in this PosResponses params

        :raises ValueError: if no data to decode in a param
        :return: dictionary with the params short name as key and the decoded data as value
        """
        result = {}
        for param in self.params:
            result[param.short_name] = param.decode()
        return result

    def parse_did_response_length(self, uds_response: List[int]) -> int:
        """parses the response component that contains this PosResponses (DID) data of the front of the
        passed uds_response

        stores the data parsed for each PARAM as that PARAM's data

        :param uds_response: the (remaining) uds response
        :return: byte length of this DIDs part of the response
        """
        self.check_DID_in_response(uds_response)
        start_position = self.did_length
        end_position = self.did_length
        for param in self.params:
            to_parse = uds_response[start_position:]
            param_length = param.calculate_length(to_parse)
            end_position += param_length
            data = uds_response[start_position:end_position]
            # store data in param for decoding
            param.data = data
            start_position = end_position
        return end_position  # this is the total length

    def check_DID_in_response(self, did_response: List[int]) -> None:
        """compare PosResponse's DID with the DID at beginning of a response

        :param did_response: uds response to take the DID from
        :raises AttributeError: if DID does not match the expected DID
        """
        actual_did = DecodeFunctions.buildIntFromList(did_response[: self.did_length])
        if self.did != actual_did:
            raise AttributeError(
                f"The expected DID {self.did} does not match the received DID {actual_did}"
            )

    def check_sid_in_response(self, response: List[int]) -> None:
        """compare PosResponse's SID with the SID at beginning of a response

        :param response: uds response to take the SID from
        :raises AttributeError: if SID does not match the expected SID
        """
        actual_sid = DecodeFunctions.buildIntFromList(response[: self.sid_length])
        if self.sid != actual_sid:
            raise AttributeError(
                f"The expected SID {self.sid} does not match the received SID {actual_sid}"
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: param={self.params}, did_length={self.did_length}, did={self.did}"
