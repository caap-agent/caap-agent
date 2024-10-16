
import importlib

from src.utils import elements_util
from breakdown_modules import breakdown__scrollbar_v


def Breakdown(element, png_fullpath):

    importlib.reload(elements_util)
    importlib.reload(breakdown__scrollbar_v)

    element_type = elements_util.TYPE_DICT[element['type']]

    if element_type == 'scrollbar_v':
        sub_element_list = breakdown__scrollbar_v.Breakdown__ScrollbarV(element, png_fullpath)

    else:
        raise NotImplementedError

    return sub_element_list
