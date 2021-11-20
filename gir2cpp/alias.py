from .typedef import TypeDef
from .xml import Xml
import xml.etree.ElementTree as ET


class Alias(TypeDef):
    def __init__(self, et: ET, namespace, xml: Xml):
        self.name = et.attrib['name']
        self.c_type = et.attrib.get(xml.ns('type', 'c'))

    def output(self, ns_dir):
        # Aliases are output into one file aliases.hpp
        return

    def cast_from_c(self):
        return ""

    def cast_to_c(self, varname):
        return varname
