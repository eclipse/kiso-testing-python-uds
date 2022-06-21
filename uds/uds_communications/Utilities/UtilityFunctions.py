#!/usr/bin/env python

__author__ = "Richard Clubb"
__copyrights__ = "Copyright 2018, the python-uds project"
__credits__ = ["Richard Clubb"]

__license__ = "MIT"
__maintainer__ = "Richard Clubb"
__email__ = "richard.clubb@embeduk.com"
__status__ = "Development"

from typing import List, Sequence

##
# @brief pads out an array with a fill value
def fillArray(data: Sequence[int], length: int, fillValue: int = 0) -> List[int]:
    padded_data = list(data) + ([fillValue] * (length - len(data)))
    return padded_data
