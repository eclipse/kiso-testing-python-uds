#!/usr/bin/env python
from __future__ import annotations

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


from types import MethodType
from typing import List

from uds.uds_config_tool.odx.pos_response import PosResponse
from uds.uds_config_tool.SupportedServices.iContainer import iContainer


class ReadDataByIdentifierContainer(object):

    __metaclass__ = iContainer

    def __init__(self):

        # To cater for lists we may have to re-factor here - i.e. requestFunc can be split into
        # requestSIDFunc and requestDIDFunc to allow building on the fly from a DID list
        # Negative response function is ok as it it

        self.requestSIDFunctions = {}
        self.requestDIDFunctions = {}

        self.pos_response_objects = {}

        self.negativeResponseFunctions = {}

    ##
    # @brief this method is bound to an external Uds object so that it call be called
    # as one of the in-built methods. uds.readDataByIdentifier("something") It does not operate
    # on this instance of the container class.
    @staticmethod
    def __readDataByIdentifier(target, parameter):

        dids: str | list[str] = parameter
        if type(dids) is not list:
            dids = [dids]

        # Adding acceptance of lists at this point, as the spec allows for multiple rdbi request to be concatenated ...
        requestSIDFunction = target.readDataByIdentifierContainer.requestSIDFunctions[
            dids[0]
        ]  # ... the SID should be the same for all DIDs, so just use the first
        requestDIDFunctions = [
            target.readDataByIdentifierContainer.requestDIDFunctions[did]
            for did in dids
        ]
        expected_response_objects: List[PosResponse] = [
            target.readDataByIdentifierContainer.pos_response_objects[did]
            for did in dids
        ]

        # This is the same for all RDBI responses, irrespective of list or single input
        negativeResponseFunction = (
            target.readDataByIdentifierContainer.negativeResponseFunctions[dids[0]]
        )  # ... single code irrespective of list use, so just use the first

        # Call the sequence of functions to execute the RDBI request/response action ...
        # ==============================================================================

        # Create the request ...
        request = requestSIDFunction()
        for didFunc in requestDIDFunctions:
            request += didFunc()  # ... creates an array of integers

        # Send request and receive the response ...
        response = target.send(
            request
        )  # ... this returns a single response which may cover 1 or more DID response values

        negative_response = negativeResponseFunction(
            response
        )  # ... return nrc value if a negative response is received
        if negative_response:
            return negative_response

        # We have a positive response so check that it makes sense to us ...
        # SID is the same for all expected PosResponses, just take the first
        expected_response_objects[0].check_sid_in_response(response)
        sid_length = expected_response_objects[0].sid_length
        # remove SID from response for further parsing the response per DID/ PosResponse
        response_remaining = response[sid_length:]
        # parse each expected DID response of the response and store its part of the data
        for positive_response in expected_response_objects:
            response_length = positive_response.parse_did_response_length(
                response_remaining
            )
            response_remaining = response_remaining[response_length:]

        # after parsing each PARAM has its data and can decode it
        return_value = tuple(
            [response.decode() for response in expected_response_objects]
        )

        if len(return_value) == 1:
            return_value = return_value[
                0
            ]  # only send back a tuple if there were multiple DIDs
        return return_value

    def bind_function(self, bindObject):
        bindObject.readDataByIdentifier = MethodType(
            self.__readDataByIdentifier, bindObject
        )

    ##
    # @brief method to add function to container - requestSIDFunction handles the SID component of the request message
    # def add_requestFunction(self, aFunction, dictionaryEntry):
    def add_requestSIDFunction(self, aFunction, dictionaryEntry):
        self.requestSIDFunctions[dictionaryEntry] = aFunction

    ##
    # @brief method to add function to container - requestDIDFunction handles the 1 to N DID components
    # of the request message
    def add_requestDIDFunction(self, aFunction, dictionaryEntry):
        self.requestDIDFunctions[dictionaryEntry] = aFunction

    ##
    # @brief method to add object to container
    # handles return of the expected DID details length and the extraction of any
    # DID details in the response message fragment for the DID that require return
    def add_posResponseObject(self, aObject: PosResponse, dictionaryEntry: str):
        self.pos_response_objects[dictionaryEntry] = aObject

    ##
    # @brief method to add function to container - negativeResponseFunction handles the checking of all possible
    # negative response codes in the response message, raising the required exception
    def add_negativeResponseFunction(self, aFunction, dictionaryEntry):
        self.negativeResponseFunctions[dictionaryEntry] = aFunction


if __name__ == "__main__":

    pass
