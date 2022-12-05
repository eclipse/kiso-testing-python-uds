import logging
from typing import Dict
from xml.etree.ElementTree import Element as XMLElement

from uds.uds_config_tool.odx.diag_coded_types import (
    DiagCodedType,
    MinMaxLengthType,
    StandardLengthType,
)
from uds.uds_config_tool.odx.globals import xsi


##
# param: a diag service element
# return: a dictionary with the sdgs data elements
def getSdgsData(diagServiceElement):

    output = {}

    sdgs = diagServiceElement.find("SDGS")
    sdg = sdgs.find("SDG")
    for i in sdg:
        try:
            output[i.attrib["SI"]] = i.text
        except:
            pass
    return output


##
# param: a diagServiceElement, an string representing the si attribute
# return: a specific entry from the sdgs params, or none if it does not exist
def getSdgsDataItem(diagServiceElement, itemName):

    outputDict = getSdgsData(diagServiceElement)

    try:
        output = outputDict[itemName]
    except:
        output = None

    return output


##
# param: an xml element
# return: a string with the short name, or None if no short name exists
def getShortName(xmlElement):

    try:
        output = xmlElement.find("SHORT-NAME").text
    except:
        output = None

    return output


##
# param: an xml element
# return: a string with the long name, or None if no long name exists
def getLongName(xmlElement):
    try:
        output = xmlElement.find("LONG-NAME").text
    except:
        output = None

    return output


##
# param: a diag service element, a list of other xmlElements
# return: an integer
def getServiceIdFromDiagService(diagServiceElement, xmlElements):

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


##
# param: a diag service element, a list of other xmlElements
# return: an integer
def getResponseIdFromDiagService(diagServiceElement, xmlElements):

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


##
# params: an xmlElement, the name of a semantic to match
# return: a single parameter matching the semantic, or a list of parameters which match the semantic
def getParamWithSemantic(xmlElement, semanticName):

    output = None

    try:
        params = xmlElement.find("PARAMS")
    except AttributeError:
        return output

    paramsList = []

    for i in params:
        paramSemantic = i.attrib["SEMANTIC"]
        if paramSemantic == semanticName:
            paramsList.append(i)

    if len(paramsList) == 0:
        output = None
    elif len(paramsList) == 1:
        output = paramsList[0]
    else:
        output = paramsList
    return output


##
# params: a diagnostic service element xml entry, and the dictionary of all possible xml elements
# return: if only 1 element, then a single xml element, else a list of xml elements, or none if no positive responses
def getPositiveResponse(diagServiceElement, xmlElements):

    positiveResponseList = []
    try:
        positiveResponseReferences = diagServiceElement.find("POS-RESPONSE-REFS")
    except:
        return None

    if positiveResponseReferences is None:
        return None
    else:
        for i in positiveResponseReferences:
            try:
                positiveResponseList.append(xmlElements[i.attrib["ID-REF"]])
            except:
                pass

    positiveResponseList_length = len(positiveResponseList)
    if positiveResponseList_length == 0:
        return None
    if positiveResponseList_length:
        return positiveResponseList[0]
    else:
        return positiveResponseList


def getDiagObjectProp(paramElement, xmlElements):

    try:
        dopElement = xmlElements[paramElement.find("DOP-REF").attrib["ID-REF"]]
    except:
        dopElement = None

    return dopElement


def getBitLengthFromDop(diagObjectPropElement: XMLElement):

    try:
        bitLength = int(
            diagObjectPropElement.find("DIAG-CODED-TYPE").find("BIT-LENGTH").text
        )
    except:
        bitLength = None

    return bitLength


def isDiagServiceTransmissionOnly(diagServiceElement):

    output = getSdgsDataItem(diagServiceElement, "PositiveResponseSuppressed")

    if output is not None:
        if output == "yes":
            return True

    return False


def find_descendant(name: str, root: XMLElement) -> XMLElement:
    """Search for an element in all descendants of an element by tag name

    :param name: the xml element tag as str
    :param root: the xml element to search in
    :return: first instance found otherwise None
    """
    for child in root.iter():
        if child.tag == name.upper():
            return child
    return None


def get_diag_coded_type_from_dop(data_object_prop: XMLElement) -> DiagCodedType:
    """Parse ODX to get the DIAG CODED TYPE from a DATA OBJECT PROP and create
    DiagCodedType object

    :param data_object_prop: xml element representing a DATA-OBJECT-PROP
    :return: the DiagCodedType containing necessary info to calculate the length of the response and decode it
    """
    diag_coded_type_element = data_object_prop.find("DIAG-CODED-TYPE")
    length_type = diag_coded_type_element.get(f"{xsi}type")
    base_data_type = diag_coded_type_element.attrib["BASE-DATA-TYPE"]
    if length_type == "STANDARD-LENGTH-TYPE":
        bit_length_element = diag_coded_type_element.find("BIT-LENGTH")
        bit_length = int(bit_length_element.text)
        byte_length = int(bit_length / 8)
        diag_coded_type = StandardLengthType(base_data_type, byte_length)
    elif length_type == "MIN-MAX-LENGTH-TYPE":
        min_length_element = diag_coded_type_element.find("MIN-LENGTH")
        max_length_element = diag_coded_type_element.find("MAX-LENGTH")
        min_length = None
        max_length = None
        if min_length_element is not None:
            min_length = int(min_length_element.text)
        if max_length_element is not None:
            max_length = int(max_length_element.text)
        termination = diag_coded_type_element.attrib["TERMINATION"]
        diag_coded_type = MinMaxLengthType(
            base_data_type, min_length, max_length, termination
        )
    else:
        raise NotImplementedError(f"Handling of {length_type} is not implemented")
    return diag_coded_type


def get_diag_coded_type_from_structure(
    structure: XMLElement, xml_elements: Dict[str, XMLElement]
) -> DiagCodedType:
    """Parse ODX to get the DIAG CODED TYPE from a STRUCTURE and create
    DiagCodedType object

    :param structure: xml element representing a STRUCTURE
    :param xml_elements: dict containing all xml elements by ID
    :return: the DiagCodedType containing necessary info to calculate the length of the response and decode it
    """
    diag_coded_type = None
    byte_size_element = structure.find("BYTE-SIZE")
    # STRUCTURE with BYTE-SIZE
    if structure.find("BYTE-SIZE") is not None:
        byte_length = int(byte_size_element.text)
        # get decoding info from first DOP, assume same decoding for each param
        dop = xml_elements[find_descendant("DOP-REF", structure).attrib["ID-REF"]]
        # if DOP is another structure, need to go deeper into the xml tree until we find a diag coded type
        if dop.tag == "STRUCTURE":
            return get_diag_coded_type_from_structure(dop, xml_elements)
        else:
            base_data_type = dop.find("DIAG-CODED-TYPE").attrib["BASE-DATA-TYPE"]
            diag_coded_type = StandardLengthType(base_data_type, byte_length)
    # STRUCTURE with DOP-REF
    else:
        dop_ref = find_descendant("DOP-REF", structure)
        if dop_ref is None:
            raise AttributeError(
                "Could not find DOP from Structure, and no BYTE-SIZE: ODX probably invalid"
            )
        nested_dop = xml_elements[dop_ref.attrib["ID-REF"]]
        if nested_dop.tag == "DATA-OBJECT-PROP":
            diag_coded_type = get_diag_coded_type_from_dop(nested_dop)
        elif nested_dop.tag == "END-OF-PDU-FIELD":
            # handle END-OF-PDU-FIELD?
            pass
        else:
            # nested structure (if possible in ODX spec):
            # recursively check structure: return get_diag_coded_type_from_structure(nestedDop, xmlElements)
            raise NotImplementedError(f"parsing of {nested_dop.tag} is not implemented")
    return diag_coded_type


if __name__ == "__main__":

    pass
