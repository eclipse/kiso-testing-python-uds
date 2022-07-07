#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

import configparser
from os import path

from uds import CanTp


##
# @brief class for creating Tp objects
class TpFactory:

    configType = ""
    configParameters = []

    config = None

    ##
    # @brief method to create the different connection types
    @staticmethod
    def __call__(tpType, configPath=None, **kwargs):

        if tpType == "CAN":
            return CanTp(configPath=configPath, **kwargs)
        else:
            raise Exception("Unknown transport type selected")
