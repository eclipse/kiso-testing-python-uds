from pathlib import Path

from uds.uds_config_tool.UtilityFunctions import (
    getLongName,
    getParamWithSemantic,
    getPositiveResponse,
    getSdgsData,
    getSdgsDataItem,
    getServiceIdFromDiagService,
    getShortName,
)

if __name__ == "__main__":
    import xml.etree.ElementTree as ET

    here = Path(__file__).parent
    filename = "Bootloader.odx"
    filepath = here.joinpath(filename)

    root = ET.parse(filepath)

    xmlElements = {}

    for child in root.iter():
        currTag = child.tag
        try:
            xmlElements[child.attrib["ID"]] = child
        except KeyError:
            pass

    for key, value in xmlElements.items():
        if value.tag == "DIAG-SERVICE":
            print(value)
            shortName = getShortName(value)
            longName = getLongName(value)
            sdgsParams = getSdgsData(value)
            print("Short Name: {0}".format(shortName))
            print("Long Name: {0}".format(longName))
            for i, j in sdgsParams.items():
                print("{0}: {1}".format(i, j))
            print(
                "Service Id: {0:#x}".format(
                    getServiceIdFromDiagService(value, xmlElements)
                )
            )
            print(
                "DiagInstanceName: {0}".format(
                    getSdgsDataItem(value, "DiagInstanceName")
                )
            )
            requestElement = xmlElements[value.find("REQUEST-REF").attrib["ID-REF"]]
            positiveResponses = getPositiveResponse(value, xmlElements)
            print(positiveResponses)
            print("")

    pass
