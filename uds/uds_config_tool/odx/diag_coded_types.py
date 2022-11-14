from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class DiagCodedType(ABC):
    """Base Class for all DIAG-CODED-TYPEs
    """

    def __init__(self, base_data_type: str) -> None:
        """initialize attributes

        :param base_data_type: BASE-DATA-TYPE attribute of DIAG-CODED-TYPE xml element
        """
        super().__init__()
        self.base_data_type = base_data_type

    @abstractmethod
    def calculateLength(self, response: List[int]) -> int:
        pass


class StandardLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a PARAM with a static length
    """

    def __init__(self, base_data_type: str, bitLength: int) -> None:
        """initialize attributes

        :param base_data_type: BASE-DATA-TYPE attribute of DIAG-CODED-TYPE xml element
        :param bitLength: length in number of bits
        """
        super().__init__(base_data_type)
        self.bitLength = bitLength

    def calculateLength(self, response: List[int]) -> int:
        """Returns the static length of StandardLengthType (excluding DID)

        :param response: the response to parse the length from (not needed for standard length)
        :return: length in bits as int
        """
        return self.bitLength

    def __repr__(self):
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type} length={self.bitLength}"


class MinMaxLengthType(DiagCodedType):
    """Represents the DIAG-CODED-TYPE of a PARAM with dynamic length

    maxLength is None if it is not specified in the ODX file
    """

    class TerminationChar(Enum):
        ZERO = 0
        HEX_FF = 255
        END_OF_PDU = "END-OF-PDU"

    def __init__(self, base_data_type: str, minLength: int, maxLength: int, termination: str) -> None:
        """
        """
        super().__init__(base_data_type)
        self.minLength = minLength
        self.maxLength = maxLength
        self.termination: MinMaxLengthType.TerminationChar = self._getTermination(termination)

    @staticmethod
    def _getTermination(termination):
        if termination == "ZERO":
            return MinMaxLengthType.TerminationChar.ZERO
        elif termination == "HEX-FF":
            return MinMaxLengthType.TerminationChar.HEX_FF
        elif termination == "END-OF-PDU":
            return MinMaxLengthType.TerminationChar.END_OF_PDU
        else:
            raise ValueError(f"Termination {termination} found in .odx file is not valid")

    def getTerminationLength(self):
        if self.termination == MinMaxLengthType.TerminationChar.ZERO:
            terminationLength = 1
        elif self.termination == MinMaxLengthType.TerminationChar.HEX_FF:
            terminationLength = 1
        return terminationLength

    def calculateLength(self, response: List[int]) -> int:
        """Returns the dynamically calculated length of MinMaxLengthType from the response
        (excluding DID)

        :param response: the response to parse the length from
        :return: length in bytes as int
        """
        # ZERO, HEX-FF end after max length, at end of response or after termination char
        if self.termination.value != "END-OF-PDU":
            for dynamicLength, value in enumerate(response):
                if value == self.termination.value and dynamicLength < self.minLength:
                    raise ValueError("Response shorter than expected minimum")
                elif value == self.termination.value or dynamicLength == self.maxLength:
                    # does it ALWAYS have a termination char, even if max length used?
                    return dynamicLength + 1  # account for 0 indexing
                elif self.maxLength is not None and dynamicLength > self.maxLength:
                    raise ValueError("Response longer than expected max length")
        # END-OF-PDU: response ends after max-length or at response end
        else:
            if self.maxLength is None:
                return len(response)
            else:
                # go through response till end or max length (whichever comes first)
                return min(self.maxLength, len(response))

    def __repr__(self):
        return f"{self.__class__.__name__}: base-data-type={self.base_data_type}, min={self.minLength}, \
            max={self.maxLength}, termination={self.termination}"
