#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"


import xml.etree.ElementTree as ET

# from uds.uds_communications.Uds.Uds import Uds
from uds.uds_config_tool.FunctionCreation.ClearDTCMethodFactory import (
    ClearDTCMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.DiagnosticSessionControlMethodFactory import (
    DiagnosticSessionControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ECUResetMethodFactory import (
    ECUResetMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.InputOutputControlMethodFactory import (
    InputOutputControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ReadDataByIdentifierMethodFactory import (
    ReadDataByIdentifierMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.ReadDTCMethodFactory import (
    ReadDTCMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RequestDownloadMethodFactory import (
    RequestDownloadMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RequestUploadMethodFactory import (
    RequestUploadMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.RoutineControlMethodFactory import (
    RoutineControlMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.SecurityAccessMethodFactory import (
    SecurityAccessMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TesterPresentMethodFactory import (
    TesterPresentMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TransferDataMethodFactory import (
    TransferDataMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.TransferExitMethodFactory import (
    TransferExitMethodFactory,
)
from uds.uds_config_tool.FunctionCreation.WriteDataByIdentifierMethodFactory import (
    WriteDataByIdentifierMethodFactory,
)
from uds.uds_config_tool.ISOStandard.ISOStandard import (
    IsoInputOutputControlOptionRecord,
)
from uds.uds_config_tool.ISOStandard.ISOStandard import IsoReadDTCStatusMask as Mask
from uds.uds_config_tool.ISOStandard.ISOStandard import (
    IsoReadDTCSubfunction,
    IsoRoutineControlType,
    IsoServices,
)
from uds.uds_config_tool.SupportedServices.ClearDTCContainer import ClearDTCContainer
from uds.uds_config_tool.SupportedServices.DiagnosticSessionControlContainer import (
    DiagnosticSessionControlContainer,
)
from uds.uds_config_tool.SupportedServices.ECUResetContainer import ECUResetContainer
from uds.uds_config_tool.SupportedServices.InputOutputControlContainer import (
    InputOutputControlContainer,
)
from uds.uds_config_tool.SupportedServices.ReadDataByIdentifierContainer import (
    ReadDataByIdentifierContainer,
)
from uds.uds_config_tool.SupportedServices.ReadDTCContainer import ReadDTCContainer
from uds.uds_config_tool.SupportedServices.RequestDownloadContainer import (
    RequestDownloadContainer,
)
from uds.uds_config_tool.SupportedServices.RequestUploadContainer import (
    RequestUploadContainer,
)
from uds.uds_config_tool.SupportedServices.RoutineControlContainer import (
    RoutineControlContainer,
)
from uds.uds_config_tool.SupportedServices.SecurityAccessContainer import (
    SecurityAccessContainer,
)
from uds.uds_config_tool.SupportedServices.TesterPresentContainer import (
    TesterPresentContainer,
)
from uds.uds_config_tool.SupportedServices.TransferDataContainer import (
    TransferDataContainer,
)
from uds.uds_config_tool.SupportedServices.TransferExitContainer import (
    TransferExitContainer,
)
from uds.uds_config_tool.SupportedServices.WriteDataByIdentifierContainer import (
    WriteDataByIdentifierContainer,
)
from uds.uds_config_tool.UtilityFunctions import isDiagServiceTransmissionOnly


class UdsContainerAccess:
    containers: list = []


def get_serviceIdFromXmlElement(diagServiceElement, xmlElements):

    requestKey = diagServiceElement.find("REQUEST-REF").attrib["ID-REF"]
    requestElement = xmlElements[requestKey]
    params = requestElement.find("PARAMS")
    for i in params:
        try:
            if i.attrib["SEMANTIC"] == "SERVICE-ID":
                return int(i.find("CODED-VALUE").text)
        except:
            pass

    return None


def fill_dictionary(xmlElement):
    temp_dictionary = {}
    for i in xmlElement:
        temp_dictionary[i.attrib["ID"]] = i

    return temp_dictionary


class UdsTool:

    diagnosticSessionControlContainer = DiagnosticSessionControlContainer()
    ecuResetContainer = ECUResetContainer()
    rdbiContainer = ReadDataByIdentifierContainer()
    wdbiContainer = WriteDataByIdentifierContainer()
    clearDTCContainer = ClearDTCContainer()
    readDTCContainer = ReadDTCContainer()
    inputOutputControlContainer = InputOutputControlContainer()
    routineControlContainer = RoutineControlContainer()
    requestDownloadContainer = RequestDownloadContainer()
    securityAccessContainer = SecurityAccessContainer()
    requestUploadContainer = RequestUploadContainer()
    transferDataContainer = TransferDataContainer()
    transferExitContainer = TransferExitContainer()
    testerPresentContainer = TesterPresentContainer()
    sessionService_flag = False
    ecuResetService_flag = False
    rdbiService_flag = False
    wdbiService_flag = False
    securityAccess_flag = False
    clearDTCService_flag = False
    readDTCService_flag = False
    ioCtrlService_flag = False
    routineCtrlService_flag = False
    reqDownloadService_flag = False
    reqUploadService_flag = False
    transDataService_flag = False
    transExitService_flag = False
    testerPresentService_flag = False

    @classmethod
    def create_service_containers(cls, xml_file):
        root = ET.parse(xml_file)

        xmlElements = {}

        for child in root.iter():
            currTag = child.tag
            try:
                xmlElements[child.attrib["ID"]] = child
            except KeyError:
                pass

        for key, value in xmlElements.items():
            if value.tag == "DIAG-SERVICE":
                serviceId = get_serviceIdFromXmlElement(value, xmlElements)
                sdg = value.find("SDGS").find("SDG")
                humanName = ""
                for sd in sdg:
                    try:
                        if sd.attrib["SI"] == "DiagInstanceName":
                            humanName = sd.text
                    except KeyError:
                        pass

                if serviceId == IsoServices.DiagnosticSessionControl:
                    cls.sessionService_flag = True

                    requestFunc = (
                        DiagnosticSessionControlMethodFactory.create_requestFunction(
                            value, xmlElements
                        )
                    )
                    cls.diagnosticSessionControlContainer.add_requestFunction(
                        requestFunc, humanName
                    )

                    negativeResponseFunction = DiagnosticSessionControlMethodFactory.create_checkNegativeResponseFunction(
                        value, xmlElements
                    )
                    cls.diagnosticSessionControlContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = DiagnosticSessionControlMethodFactory.create_checkPositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.diagnosticSessionControlContainer.add_checkFunction(
                        checkFunc, humanName
                    )

                    positiveResponseFunction = DiagnosticSessionControlMethodFactory.create_encodePositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.diagnosticSessionControlContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )
                    if (
                        cls.diagnosticSessionControlContainer
                        not in UdsContainerAccess.containers
                    ):
                        UdsContainerAccess.containers.append(
                            cls.diagnosticSessionControlContainer
                        )

                elif serviceId == IsoServices.EcuReset:
                    cls.ecuResetService_flag = True

                    requestFunc = ECUResetMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.ecuResetContainer.add_requestFunction(requestFunc, humanName)

                    negativeResponseFunction = (
                        ECUResetMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.ecuResetContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    try:
                        transmissionMode = value.attrib["TRANSMISSION-MODE"]
                        if transmissionMode == "SEND-ONLY":
                            sendOnly_flag = True
                    except:
                        sendOnly_flag = False

                    if sendOnly_flag:
                        checkFunc = None
                        positiveResponseFunction = None
                    else:
                        checkFunc = (
                            ECUResetMethodFactory.create_checkPositiveResponseFunction(
                                value, xmlElements
                            )
                        )
                        positiveResponseFunction = (
                            ECUResetMethodFactory.create_encodePositiveResponseFunction(
                                value, xmlElements
                            )
                        )

                    cls.ecuResetContainer.add_checkFunction(checkFunc, humanName)
                    cls.ecuResetContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )
                    if cls.ecuResetContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.ecuResetContainer)
                    pass

                elif serviceId == IsoServices.ReadDataByIdentifier:
                    cls.rdbiService_flag = True

                    # The new code extends the range of functions required, in order to handle RDBI working for concatenated lists of DIDs ...
                    requestFunctions = (
                        ReadDataByIdentifierMethodFactory.create_requestFunctions(
                            value, xmlElements
                        )
                    )
                    cls.rdbiContainer.add_requestSIDFunction(
                        requestFunctions[0], humanName
                    )  # ... note: this will now need to handle replication of this one!!!!
                    cls.rdbiContainer.add_requestDIDFunction(
                        requestFunctions[1], humanName
                    )

                    negativeResponseFunction = ReadDataByIdentifierMethodFactory.create_checkNegativeResponseFunction(
                        value, xmlElements
                    )
                    cls.rdbiContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )
                    posResponse = ReadDataByIdentifierMethodFactory.create_positive_response_objects(
                        value, xmlElements
                    )
                    cls.rdbiContainer.add_posResponseObject(posResponse, humanName)

                    if cls.rdbiContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.rdbiContainer)

                elif serviceId == IsoServices.SecurityAccess:
                    if isDiagServiceTransmissionOnly(value) == False:
                        requestFunction = (
                            SecurityAccessMethodFactory.create_requestFunction(
                                value, xmlElements
                            )
                        )
                        cls.securityAccessContainer.add_requestFunction(
                            requestFunction, humanName
                        )

                        negativeResponseFunction = SecurityAccessMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                        cls.securityAccessContainer.add_negativeResponseFunction(
                            negativeResponseFunction, humanName
                        )

                        checkFunction = SecurityAccessMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                        cls.securityAccessContainer.add_positiveResponseFunction(
                            checkFunction, humanName
                        )

                        cls.securityAccess_flag = True

                        if (
                            cls.securityAccessContainer
                            not in UdsContainerAccess.containers
                        ):
                            UdsContainerAccess.containers.append(
                                cls.securityAccessContainer
                            )

                elif serviceId == IsoServices.WriteDataByIdentifier:

                    cls.wdbiService_flag = True
                    requestFunc = (
                        WriteDataByIdentifierMethodFactory.create_requestFunction(
                            value, xmlElements
                        )
                    )
                    cls.wdbiContainer.add_requestFunction(requestFunc, humanName)

                    negativeResponseFunction = WriteDataByIdentifierMethodFactory.create_checkNegativeResponseFunction(
                        value, xmlElements
                    )
                    cls.wdbiContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = WriteDataByIdentifierMethodFactory.create_checkPositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.wdbiContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = WriteDataByIdentifierMethodFactory.create_encodePositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.wdbiContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if cls.wdbiContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.wdbiContainer)

                elif serviceId == IsoServices.ClearDiagnosticInformation:
                    cls.clearDTCService_flag = True
                    requestFunc = ClearDTCMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.clearDTCContainer.add_requestFunction(requestFunc, humanName)

                    negativeResponseFunction = (
                        ClearDTCMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.clearDTCContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = (
                        ClearDTCMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.clearDTCContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = (
                        ClearDTCMethodFactory.create_encodePositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.clearDTCContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if cls.clearDTCContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.clearDTCContainer)

                elif serviceId == IsoServices.ReadDTCInformation:
                    cls.readDTCService_flag = True
                    (
                        requestFunction,
                        qualifier,
                    ) = ReadDTCMethodFactory.create_requestFunction(value, xmlElements)
                    if qualifier != "":
                        cls.readDTCContainer.add_requestFunction(
                            requestFunction, "FaultMemoryRead" + qualifier
                        )

                        negativeResponseFunction = (
                            ReadDTCMethodFactory.create_checkNegativeResponseFunction(
                                value, xmlElements
                            )
                        )
                        cls.readDTCContainer.add_negativeResponseFunction(
                            negativeResponseFunction, "FaultMemoryRead" + qualifier
                        )

                        checkFunction = (
                            ReadDTCMethodFactory.create_checkPositiveResponseFunction(
                                value, xmlElements
                            )
                        )
                        cls.readDTCContainer.add_checkFunction(
                            checkFunction, "FaultMemoryRead" + qualifier
                        )

                        positiveResponseFunction = (
                            ReadDTCMethodFactory.create_encodePositiveResponseFunction(
                                value, xmlElements
                            )
                        )
                        cls.readDTCContainer.add_positiveResponseFunction(
                            positiveResponseFunction, "FaultMemoryRead" + qualifier
                        )

                        if cls.readDTCContainer not in UdsContainerAccess.containers:
                            UdsContainerAccess.containers.append(cls.readDTCContainer)

                elif serviceId == IsoServices.InputOutputControlByIdentifier:
                    cls.ioCtrlService_flag = True
                    (
                        requestFunc,
                        qualifier,
                    ) = InputOutputControlMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    if qualifier != "":
                        cls.inputOutputControlContainer.add_requestFunction(
                            requestFunc, humanName + qualifier
                        )

                        negativeResponseFunction = InputOutputControlMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                        cls.inputOutputControlContainer.add_negativeResponseFunction(
                            negativeResponseFunction, humanName + qualifier
                        )

                        checkFunc = InputOutputControlMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                        cls.inputOutputControlContainer.add_checkFunction(
                            checkFunc, humanName + qualifier
                        )

                        positiveResponseFunction = InputOutputControlMethodFactory.create_encodePositiveResponseFunction(
                            value, xmlElements
                        )
                        cls.inputOutputControlContainer.add_positiveResponseFunction(
                            positiveResponseFunction, humanName + qualifier
                        )

                        if (
                            cls.inputOutputControlContainer
                            not in UdsContainerAccess.containers
                        ):
                            UdsContainerAccess.containers.append(
                                cls.inputOutputControlContainer
                            )

                elif serviceId == IsoServices.RoutineControl:
                    cls.routineCtrlService_flag = True
                    # We need a qualifier, as the human name for the start stop, and results calls are all the same, so they otherwise overwrite each other
                    (
                        requestFunc,
                        qualifier,
                    ) = RoutineControlMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    if qualifier != "":
                        cls.routineControlContainer.add_requestFunction(
                            requestFunc, humanName + qualifier
                        )

                        negativeResponseFunction = RoutineControlMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                        cls.routineControlContainer.add_negativeResponseFunction(
                            negativeResponseFunction, humanName + qualifier
                        )

                        checkFunc = RoutineControlMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                        cls.routineControlContainer.add_checkFunction(
                            checkFunc, humanName + qualifier
                        )

                        positiveResponseFunction = RoutineControlMethodFactory.create_encodePositiveResponseFunction(
                            value, xmlElements
                        )
                        cls.routineControlContainer.add_positiveResponseFunction(
                            positiveResponseFunction, humanName + qualifier
                        )

                        if (
                            cls.routineControlContainer
                            not in UdsContainerAccess.containers
                        ):
                            UdsContainerAccess.containers.append(
                                cls.routineControlContainer
                            )

                elif serviceId == IsoServices.RequestDownload:
                    cls.reqDownloadService_flag = True
                    requestFunc = RequestDownloadMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.requestDownloadContainer.add_requestFunction(
                        requestFunc, humanName
                    )

                    negativeResponseFunction = RequestDownloadMethodFactory.create_checkNegativeResponseFunction(
                        value, xmlElements
                    )
                    cls.requestDownloadContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = RequestDownloadMethodFactory.create_checkPositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.requestDownloadContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = RequestDownloadMethodFactory.create_encodePositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.requestDownloadContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if (
                        cls.requestDownloadContainer
                        not in UdsContainerAccess.containers
                    ):
                        UdsContainerAccess.containers.append(
                            cls.requestDownloadContainer
                        )

                elif serviceId == IsoServices.RequestUpload:
                    cls.reqUploadService_flag = True
                    requestFunc = RequestUploadMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.requestUploadContainer.add_requestFunction(
                        requestFunc, humanName
                    )

                    negativeResponseFunction = (
                        RequestUploadMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.requestUploadContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = (
                        RequestUploadMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.requestUploadContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = RequestUploadMethodFactory.create_encodePositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.requestUploadContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if cls.requestUploadContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.requestUploadContainer)

                elif serviceId == IsoServices.TransferData:
                    cls.transDataService_flag = True
                    requestFunc = TransferDataMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.transferDataContainer.add_requestFunction(
                        requestFunc, humanName
                    )

                    negativeResponseFunction = (
                        TransferDataMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferDataContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = (
                        TransferDataMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferDataContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = (
                        TransferDataMethodFactory.create_encodePositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferDataContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if cls.transferDataContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.transferDataContainer)

                elif serviceId == IsoServices.RequestTransferExit:
                    cls.transExitService_flag = True
                    requestFunc = TransferExitMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.transferExitContainer.add_requestFunction(
                        requestFunc, humanName
                    )

                    negativeResponseFunction = (
                        TransferExitMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferExitContainer.add_negativeResponseFunction(
                        negativeResponseFunction, humanName
                    )

                    checkFunc = (
                        TransferExitMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferExitContainer.add_checkFunction(checkFunc, humanName)

                    positiveResponseFunction = (
                        TransferExitMethodFactory.create_encodePositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.transferExitContainer.add_positiveResponseFunction(
                        positiveResponseFunction, humanName
                    )

                    if cls.transferExitContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.transferExitContainer)

                elif serviceId == IsoServices.TesterPresent:
                    # Note: Tester Present is presented here as an exposed service, but it will typically not be called directly, as we'll hook it
                    # in to keep the session alive automatically if requested (details to come, but this is just getting the comms into place).
                    cls.testerPresentService_flag = True
                    requestFunc = TesterPresentMethodFactory.create_requestFunction(
                        value, xmlElements
                    )
                    cls.testerPresentContainer.add_requestFunction(
                        requestFunc, "TesterPresent"
                    )

                    negativeResponseFunction = (
                        TesterPresentMethodFactory.create_checkNegativeResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.testerPresentContainer.add_negativeResponseFunction(
                        negativeResponseFunction, "TesterPresent"
                    )

                    checkFunc = (
                        TesterPresentMethodFactory.create_checkPositiveResponseFunction(
                            value, xmlElements
                        )
                    )
                    cls.testerPresentContainer.add_checkFunction(
                        checkFunc, "TesterPresent"
                    )

                    positiveResponseFunction = TesterPresentMethodFactory.create_encodePositiveResponseFunction(
                        value, xmlElements
                    )
                    cls.testerPresentContainer.add_positiveResponseFunction(
                        positiveResponseFunction, "TesterPresent"
                    )

                    if cls.testerPresentContainer not in UdsContainerAccess.containers:
                        UdsContainerAccess.containers.append(cls.testerPresentContainer)

    @classmethod
    def bind_containers(cls, uds_instance) -> None:
        # Bind any ECU Reset services that have been found
        if cls.sessionService_flag:
            setattr(
                uds_instance,
                "diagnosticSessionControlContainer",
                cls.diagnosticSessionControlContainer,
            )
            cls.diagnosticSessionControlContainer.bind_function(uds_instance)

        # Bind any ECU Reset services that have been found
        if cls.ecuResetService_flag:
            setattr(uds_instance, "ecuResetContainer", cls.ecuResetContainer)
            cls.ecuResetContainer.bind_function(uds_instance)

        # Bind any rdbi services that have been found
        if cls.rdbiService_flag:
            setattr(uds_instance, "readDataByIdentifierContainer", cls.rdbiContainer)
            cls.rdbiContainer.bind_function(uds_instance)

        # Bind any security access services have been found
        if cls.securityAccess_flag:
            setattr(
                uds_instance, "securityAccessContainer", cls.securityAccessContainer
            )
            cls.securityAccessContainer.bind_function(uds_instance)

        # Bind any wdbi services have been found
        if cls.wdbiService_flag:
            setattr(uds_instance, "writeDataByIdentifierContainer", cls.wdbiContainer)
            cls.wdbiContainer.bind_function(uds_instance)

        # Bind any clear DTC services that have been found
        if cls.clearDTCService_flag:
            setattr(uds_instance, "clearDTCContainer", cls.clearDTCContainer)
            cls.clearDTCContainer.bind_function(uds_instance)

        # Bind any read DTC services that have been found
        if cls.readDTCService_flag:
            setattr(uds_instance, "readDTCContainer", cls.readDTCContainer)
            cls.readDTCContainer.bind_function(uds_instance)

        # Bind any input output control services that have been found
        if cls.ioCtrlService_flag:
            setattr(
                uds_instance,
                "inputOutputControlContainer",
                cls.inputOutputControlContainer,
            )
            cls.inputOutputControlContainer.bind_function(uds_instance)

        # Bind any routine control services that have been found
        if cls.routineCtrlService_flag:
            setattr(
                uds_instance, "routineControlContainer", cls.routineControlContainer
            )
            cls.routineControlContainer.bind_function(uds_instance)

        # Bind any request download services that have been found
        if cls.reqDownloadService_flag:
            setattr(
                uds_instance, "requestDownloadContainer", cls.requestDownloadContainer
            )
            cls.requestDownloadContainer.bind_function(uds_instance)

        # Bind any request upload services that have been found
        if cls.reqUploadService_flag:
            setattr(uds_instance, "requestUploadContainer", cls.requestUploadContainer)
            cls.requestUploadContainer.bind_function(uds_instance)

        # Bind any transfer data services that have been found
        if cls.transDataService_flag:
            setattr(uds_instance, "transferDataContainer", cls.transferDataContainer)
            cls.transferDataContainer.bind_function(uds_instance)

        # Bind any transfer exit data services that have been found
        if cls.transExitService_flag:
            setattr(uds_instance, "transferExitContainer", cls.transferExitContainer)
            cls.transferExitContainer.bind_function(uds_instance)

        # Bind any tester present services that have been found
        if cls.testerPresentService_flag:
            setattr(uds_instance, "testerPresentContainer", cls.testerPresentContainer)
            cls.testerPresentContainer.bind_function(uds_instance)
