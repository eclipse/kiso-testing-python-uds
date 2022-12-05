from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class DiagCodedType(ABC):
    """Base Class for all DIAG-CODED-TYPEs"""

    def __init__(self, base_data_type: str) -> None:
        """initialize attributes

        :param base_data_type: BASE-DATA-TYPE attribute of DIAG-CODED-TYPE xml element
        """
        super().__init__()
        self.base_data_type = base_data_type

    @abstractmethod
    def calculate_length(self, response: List[int]) -> int:
        """ """


class StandardLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a PARAM with a static length"""

    def __init__(self, base_data_type: str, byte_length: int) -> None:
        """initialize attributes

        :param base_data_type: BASE-DATA-TYPE attribute of DIAG-CODED-TYPE xml element
        :param byte_length: length in number of bytes
        """
        super().__init__(base_data_type)
        self.byte_length = byte_length

    def calculate_length(self, response: List[int]) -> int:
        """Returns the static length of StandardLengthType (excluding DID)

        :param response: the response to parse the length from (not needed for standard length)
        :return: length in bytes as int
        """
        return self.byte_length

    def __repr__(self):
        return f"{self.__class__.__name__}: base_data_type={self.base_data_type} byte_length={self.byte_length}"


class MinMaxLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a PARAM with dynamic length

    max_length is None if it is not specified in the ODX file
    """

    class TerminationChar(Enum):
        """enum of all allowed termination types of a DIAG CODED TYPE"""

        ZERO = 0
        HEX_FF = 255
        END_OF_PDU = "END-OF-PDU"

    def __init__(
        self, base_data_type: str, min_length: int, max_length: int, termination: str
    ) -> None:
        """initialize attributes

        :param base_data_type: BASE-DATA-TYPE attribute of DIAG-CODED-TYPE xml element
        :param min_length: minimum length in number of bytes
        :param max_length: maximum length in number of bytes, can be None
        :param termination: the termination type from ODX as string
        """
        super().__init__(base_data_type)
        self.min_length = min_length
        self.max_length = max_length
        self.termination: MinMaxLengthType.TerminationChar = self._get_termination(
            termination
        )

    @staticmethod
    def _get_termination(termination: str) -> TerminationChar:
        """get the termination char from a ODX TERMINATION attribute string

        :param termination: termination type as string
        :return: termination char as enum member
        :raises ValueError: if param termination is not valid
        """
        if termination == "ZERO":
            return MinMaxLengthType.TerminationChar.ZERO
        if termination == "HEX-FF":
            return MinMaxLengthType.TerminationChar.HEX_FF
        if termination == "END-OF-PDU":
            return MinMaxLengthType.TerminationChar.END_OF_PDU
        raise ValueError(f"Termination {termination} found in .odx file is not valid")

    def get_termination_length(self) -> int:
        """get the byte length of the MinMaxLengthType's termination char

        :return: length of the termination char in byte if it has one (END OF PDU does not)
        """
        if self.termination == MinMaxLengthType.TerminationChar.ZERO:
            termination_length = 1
        elif self.termination == MinMaxLengthType.TerminationChar.HEX_FF:
            termination_length = 1
        return termination_length

    def calculate_length(self, response: List[int]) -> int:
        """Returns the dynamically calculated length of MinMaxLengthType from the response
        (excluding DID)

        :param response: the response to parse the length from
        :return: length in bytes as int
        :raises ValueError: if parsed response is shorter or longer than MinMaxLengthType's minimum or maximum
        """
        # ZERO, HEX-FF end after max length, at end of response or after termination char
        if self.termination.value != "END-OF-PDU":
            for dynamic_length, value in enumerate(response):
                if value == self.termination.value and dynamic_length < self.min_length:
                    raise ValueError("Response shorter than expected minimum")
                if value == self.termination.value or dynamic_length == self.max_length:
                    # does it ALWAYS have a termination char, even if max length used?
                    return dynamic_length + 1  # account for 0 indexing
                if self.max_length is not None and dynamic_length > self.max_length:
                    raise ValueError("Response longer than expected max length")
        # END-OF-PDU: response ends after max-length or at response end
        else:
            if self.max_length is None:
                return len(response)
            # go through response till end or max length (whichever comes first)
            return min(self.max_length, len(response))

    def __repr__(self):
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type}, min={self.min_length}, \
            max={self.max_length}, termination={self.termination}"
