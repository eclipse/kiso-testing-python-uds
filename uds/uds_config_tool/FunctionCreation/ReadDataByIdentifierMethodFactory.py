#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

import logging
from typing import List

from uds.uds_config_tool import DecodeFunctions
from uds.uds_config_tool.FunctionCreation.iServiceMethodFactory import \
    IServiceMethodFactory
from uds.uds_config_tool.odx.diag_coded_types import DiagCodedType
from uds.uds_config_tool.odx.param import Param
from uds.uds_config_tool.odx.pos_response import PosResponse
from uds.uds_config_tool.UtilityFunctions import (
    getDiagCodedTypeFromDop, getDiagCodedTypeFromStructure)

# Extended to cater for multiple DIDs in a request - typically rather than processing
# a whole response in one go, we break it down and process each part separately.
# We can cater for multiple DIDs by then combining whatever calls we need to.
log = logging.getLogger(__name__)

requestSIDFuncTemplate = str("def {0}():\n" "    return {1}")
requestDIDFuncTemplate = str("def {0}():\n" "    return {1}")

negativeResponseFuncTemplate = str(
    "def {0}(input):\n"
    "    result = {{}}\n"
    "    nrcList = {5}\n"
    "    if input[{1}:{2}] == [{3}]:\n"
    "        result['NRC'] = input[{4}]\n"
    "        result['NRC_Label'] = nrcList.get(result['NRC'])\n"
    "    return result"
)


##
# @brief this should be static
class ReadDataByIdentifierMethodFactory(IServiceMethodFactory):
    @staticmethod
    def create_requestFunctions(diagServiceElement, xmlElements):

        serviceId = 0
        diagnosticId = 0

        shortName = "request_{0}".format(diagServiceElement.find("SHORT-NAME").text)
        requestSIDFuncName = "requestSID_{0}".format(shortName)
        requestDIDFuncName = "requestDID_{0}".format(shortName)
        requestElement = xmlElements[
            diagServiceElement.find("REQUEST-REF").attrib["ID-REF"]
        ]
        paramsElement = requestElement.find("PARAMS")
        for param in paramsElement:
            semantic = None
            try:
                semantic = param.attrib["SEMANTIC"]
            except AttributeError:
                pass

            if semantic == "SERVICE-ID":
                serviceId = [int(param.find("CODED-VALUE").text)]
            elif semantic == "ID":
                diagnosticId = DecodeFunctions.intArrayToIntArray(
                    [int(param.find("CODED-VALUE").text)], "int16", "int8"
                )

        funcString = requestSIDFuncTemplate.format(
            requestSIDFuncName, serviceId  # 0
        )  # 1
        exec(funcString)

        funcString = requestDIDFuncTemplate.format(
            requestDIDFuncName, diagnosticId  # 0
        )  # 1
        exec(funcString)

        return (locals()[requestSIDFuncName], locals()[requestDIDFuncName])

    @staticmethod
    def create_positiveResponseObjects(diagServiceElement, xmlElements):

        positiveResponseElement = xmlElements[
            (diagServiceElement.find("POS-RESPONSE-REFS"))
            .find("POS-RESPONSE-REF")
            .attrib["ID-REF"]
        ]
        paramsElement = positiveResponseElement.find("PARAMS")
        # PosResponse attributes
        responseId = 0
        diagnosticId = 0
        SIDLength = 0
        DIDLength = 0
        params: List[Param] = []

        for paramElement in paramsElement:
            try:
                semantic = None
                try:
                    semantic = paramElement.attrib["SEMANTIC"]
                except AttributeError:
                    pass

                short_name = (paramElement.find("SHORT-NAME")).text
                byte_position = int((paramElement.find("BYTE-POSITION")).text)

                if semantic == "SERVICE-ID":
                    responseId = int(paramElement.find("CODED-VALUE").text)
                    bitLength = int(
                        (paramElement.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    SIDLength = int(bitLength / 8)
                elif semantic == "ID":
                    diagnosticId = int(paramElement.find("CODED-VALUE").text)
                    bitLength = int(
                        (paramElement.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    DIDLength = int(bitLength / 8)
                elif semantic == "DATA":
                    diagCodedType: DiagCodedType = None
                    # need to parse the param for the DIAG CODED TYPE
                    dataObjectElement = xmlElements[
                        (paramElement.find("DOP-REF")).attrib["ID-REF"]
                    ]
                    if dataObjectElement.tag == "DATA-OBJECT-PROP":
                        diagCodedType = getDiagCodedTypeFromDop(dataObjectElement)

                    elif dataObjectElement.tag == "STRUCTURE":
                        diagCodedType = getDiagCodedTypeFromStructure(dataObjectElement, xmlElements)
                    else:
                        # neither DOP nor STRUCTURE
                        pass
                    param: Param = Param(short_name, byte_position, diagCodedType)
                    params.append(param)
                else:
                    # not a PARAM with SID, ID (= DID), or DATA
                    pass
            except Exception as e:
                log.debug(e)

        posResponse = PosResponse(params, DIDLength, diagnosticId, SIDLength, responseId)
        return posResponse

    @staticmethod
    def create_checkNegativeResponseFunction(diagServiceElement, xmlElements):

        shortName = diagServiceElement.find("SHORT-NAME").text
        check_negativeResponseFunctionName = "check_negResponse_{0}".format(shortName)

        negativeResponsesElement = diagServiceElement.find("NEG-RESPONSE-REFS")

        negativeResponseChecks = []

        for negativeResponse in negativeResponsesElement:
            negativeResponseRef = xmlElements[negativeResponse.attrib["ID-REF"]]

            negativeResponseParams = negativeResponseRef.find("PARAMS")

            for param in negativeResponseParams:

                semantic = None
                try:
                    semantic = param.attrib["SEMANTIC"]
                except:
                    semantic = None

                bytePosition = int(param.find("BYTE-POSITION").text)

                if semantic == "SERVICE-ID":
                    serviceId = param.find("CODED-VALUE").text
                    start = int(param.find("BYTE-POSITION").text)
                    diagCodedType = param.find("DIAG-CODED-TYPE")
                    bitLength = int(
                        (param.find("DIAG-CODED-TYPE")).find("BIT-LENGTH").text
                    )
                    listLength = int(bitLength / 8)
                    end = start + listLength
                elif bytePosition == 2:
                    nrcPos = bytePosition
                    expectedNrcDict = {}
                    try:
                        dataObjectElement = xmlElements[
                            (param.find("DOP-REF")).attrib["ID-REF"]
                        ]
                        nrcList = (
                            dataObjectElement.find("COMPU-METHOD")
                            .find("COMPU-INTERNAL-TO-PHYS")
                            .find("COMPU-SCALES")
                        )
                        for nrcElem in nrcList:
                            expectedNrcDict[int(nrcElem.find("LOWER-LIMIT").text)] = (
                                nrcElem.find("COMPU-CONST").find("VT").text
                            )
                    except Exception as e:
                        log.debug(e)
                pass

        negativeResponseFunctionString = negativeResponseFuncTemplate.format(
            check_negativeResponseFunctionName,
            start,
            end,
            serviceId,
            nrcPos,
            expectedNrcDict,
        )

        exec(negativeResponseFunctionString)
        return locals()[check_negativeResponseFunctionName]
