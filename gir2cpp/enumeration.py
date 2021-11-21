import os
from .xml import Xml
from .typedef import TypeDef
from .method import Method
from .keywords import Keywords
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
                continue
            name = Keywords.fix_name(x.attrib['name'])
            if x.tag == xml.ns('member'):
                c_ident = x.attrib[xml.ns("identifier", "c")]
                self.members.append((name, c_ident))
            elif x.tag == xml.ns('function'):
                # TODO: handle enum methods
                # print(self.namespace.name, name)
                self.methods[self.name] = Method(x, self, xml)
            else:
                print("Unhandled", x.tag)
                pass

    def get_repository(self):
        return self.namespace.get_repository()

    def output(self, ns_dir):
        exts = ("hpp", "cpp") if self.methods else ('hpp',)
        for ext in exts:
            template = self.get_repository().get_template(f"enum.{ext}.in")
            fname = os.path.join(ns_dir, f"{self.name}.{ext}")
            with open(fname, 'w') as f:
                f.write(template.render(enum_=self))

    def cast_from_c(self, varname):
        return varname

    def cast_to_c(self, varname):
        return varname

    def cpp_type(self, decl):
        return f"{self.namespace.name}::{self.name}"
