from typing import List

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.odx.diag_coded_types import DiagCodedType, MinMaxLengthType


class Param:
    """represents a PARAM with its DIAG CODED TYPE, name, byte position and (optionally) data

    data is set when parsing a uds response and can then be decoded
    """

    def __init__(
        self,
        short_name: str,
        byte_position: int,
        diag_coded_type: DiagCodedType,
        data=None,
    ) -> None:
        """initialize attributes

        :param short_name: name defined in ODX as str
        :param byte_position: byte position in the response of the param
        :param diag_coded_type: the Param's DiagCodedType containing length and decode info
        :param data: the part of the uds response that belongs to this Param
        """
        self.short_name = short_name
        self.byte_position = byte_position
        self.diag_coded_type = diag_coded_type
        self.data = data

    def calculate_length(self, response: List[int]) -> int:
        """calculate the params byte length in the response based on its DIAG CODED TYPE

        :param response: uds response to parse the param from
        :return: the calculated byte length
        """
        return self.diag_coded_type.calculate_length(response)

    def decode(self) -> str:
        """decode Param's internal data that is set after parsing a uds response

        :return: the PARAM's decoded data as string
        :raises ValueError: if there is no data set to decode
        """
        if self.data is None:
            raise ValueError(
                "Data in param is None, check if data DID response was parsed correctly"
            )
        # there is data to decode
        to_decode = self.data
        # remove termination char, END-OF-PDU type has no termination char
        if (
            isinstance(self.diag_coded_type, MinMaxLengthType)
            and self.diag_coded_type.termination.value != "END-OF-PDU"
        ):
            termination_char_length = self.diag_coded_type.get_termination_length()
            to_decode = self.data[:-termination_char_length]
        encoding_type = self.diag_coded_type.base_data_type
        if encoding_type == "A_ASCIISTRING":
            decoded_response = DecodeFunctions.intListToString(to_decode, None)
        elif encoding_type == "A_UINT32":
            # no decoding needed?
            decoded_response = to_decode
        else:
            # no decoding needed?
            decoded_response = to_decode
        return decoded_response

    def __repr__(self):
        return f"{self.__class__.__name__}: short_name={self.short_name}, byte_position={self.byte_position}, \
            diag_coded_type={self.diag_coded_type}, data={self.data}"
