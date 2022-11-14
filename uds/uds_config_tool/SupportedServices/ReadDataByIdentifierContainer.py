#!/usr/bin/env python

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

        self.posResponseObjects = {}

        self.negativeResponseFunctions = {}

    ##
    # @brief this method is bound to an external Uds object so that it call be called
    # as one of the in-built methods. uds.readDataByIdentifier("something") It does not operate
    # on this instance of the container class.
    @staticmethod
    def __readDataByIdentifier(target, parameter):

        dids: str | List[str] = parameter
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
        expectedResponseObjects: List[PosResponse] = [
            target.readDataByIdentifierContainer.posResponseObjects[did]
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

        negativeResponse = negativeResponseFunction(
            response
        )  # ... return nrc value if a negative response is received
        if negativeResponse:
            return negativeResponse

        # We have a positive response so check that it makes sense to us ...
        # SID is the same for all expected PosResponses, just take the first
        expectedResponseObjects[0].checkSIDInResponse(response)
        SIDLength = expectedResponseObjects[0].sidLength
        # remove SID from response for further parsing the response per DID/ PosResponse
        responseRemaining = response[SIDLength:]
        # parse each expected DID response of the response and store its part of the data
        for positiveResponse in expectedResponseObjects:
            responseLength = positiveResponse.parseDIDResponseLength(responseRemaining)
            responseRemaining = responseRemaining[responseLength:]

        # after parsing each PARAM has its data and can decode it
        returnValue = tuple(
            [
                response.decode()
                for response in expectedResponseObjects
            ]
        )

        if len(returnValue) == 1:
            returnValue = returnValue[
                0
            ]  # only send back a tuple if there were multiple DIDs
        return returnValue

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
        self.posResponseObjects[dictionaryEntry] = aObject

    ##
    # @brief method to add function to container - negativeResponseFunction handles the checking of all possible
    # negative response codes in the response message, raising the required exception
    def add_negativeResponseFunction(self, aFunction, dictionaryEntry):
        self.negativeResponseFunctions[dictionaryEntry] = aFunction


if __name__ == "__main__":

    pass
