from .typedef import TypeDef
from .xml import Xml
from .config import Config
import xml.etree.ElementTree as ET


class Alias(TypeDef):
    def __init__(self, et: ET, namespace, xml: Xml, config: Config):
        self.namespace = namespace
        self.name = et.attrib['name']
        self.c_type = et.attrib.get(xml.ns('type', 'c'))

    def output(self, ns_dir):
        # Aliases are output into one file aliases.hpp
        return

    def cast_from_c(self, varname):
        return varname

    def cast_to_c(self, varname, refctype):
        return varname

    def cpp_type(self, decl):
        return decl.replace(self.c_type, f"{self.namespace.name}::{self.name}")
