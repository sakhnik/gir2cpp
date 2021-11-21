import os
from .xml import Xml
from .typedef import TypeDef
from .method import Method
import xml.etree.ElementTree as ET


class Enumeration(TypeDef):
    def __init__(self, et: ET, namespace, xml: Xml):
        self.namespace = namespace
        self.name = et.attrib['name']
        self.c_type = et.attrib[xml.ns("type", "c")]
        self.members = []
        self.methods = {}

        ignore = frozenset(xml.ns(i) for i in (
            "doc", "source-position", "doc-deprecated"
        ))

        for x in et:
            if x.tag in ignore:
                pass
            elif x.tag == xml.ns('member'):
                mname = x.attrib['name']
                c_ident = x.attrib[xml.ns("identifier", "c")]
                self.members.append((mname, c_ident))
            elif x.tag == xml.ns('function'):
                self.methods[self.name] = Method(x, self, xml)
            else:
                print("Unhandled", x.tag)
                pass

    def get_repository(self):
        return self.namespace.get_repository()

    def output(self, ns_dir):
        template = self.get_repository().get_template('enum.hpp.in')
        fname = os.path.join(ns_dir, f"{self.name}.hpp")
        with open(fname, 'w') as f:
            f.write(template.render(enum_=self))

    def cast_from_c(self):
        return ""

    def cast_to_c(self, varname):
        return varname
