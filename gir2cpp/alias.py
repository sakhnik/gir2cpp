from .typedef import TypeDef
from .xml import Xml
import xml.etree.ElementTree as ET


class Alias(TypeDef):
    def __init__(self, et: ET, xml: Xml):
        self.name = et.attrib['name']
        self.c_type = et.attrib.get(xml.ns('type', 'c'))
