from .xml import Xml
from .class_ import Class, Interface
from .enumeration import Enumeration
import xml.etree.ElementTree as ET
import os


class Namespace:
    def __init__(self, name, c_includes, repository):
        self.name = name
        self.c_includes = c_includes
        self.repository = repository
        self.aliases = {}
        self.enumerations = {}
        self.classes = {}

    def get_repository(self):
        return self.repository

    def parse(self, et: ET, xml: Xml):
        ignore = frozenset(xml.ns(i) for i in (
            "function-macro", "constant", "function", "docsection",
            "bitfield", "union"
        ))

        # c_id_pref = nstree.attrib[xml.ns('identifier-prefixes', 'c')]
        # c_sym_pref = nstree.attrib[xml.ns('symbol-prefixes', 'c')]
        for x in et:
            if x.tag in ignore:
                pass
            elif x.tag == xml.ns("boxed", "glib"):
                pass
            elif x.tag == xml.ns("alias") \
                    or x.tag == xml.ns("record") \
                    or x.tag == xml.ns("callback") \
                    or x.tag == xml.ns("bitfield"):
                # TODO: handle records, bitfields like enumerations
                self.add_alias(x, xml)
            elif x.tag == xml.ns("class"):
                self.add_class(x, xml)
            elif x.tag == xml.ns("interface"):
                self.add_interface(x, xml)
            elif x.tag == xml.ns("enumeration"):
                self.add_enumeration(x, xml)
            else:
                print('Unhandled', x.tag)

    def add_alias(self, et: ET, xml: Xml):
        name = et.attrib['name']
        if self.get_repository().should_ignore(self.name, name):
            return
        c_type = et.attrib.get(xml.ns('type', 'c'))
        self.aliases[name] = c_type

    def add_class(self, et: ET, xml: Xml):
        name = et.attrib['name']
        if self.get_repository().should_ignore(self.name, name):
            return
        self.classes[name] = Class(et, self, xml)

    def add_interface(self, et: ET, xml: Xml):
        name = et.attrib['name']
        if self.get_repository().should_ignore(self.name, name):
            return
        self.classes[name] = Interface(et, self, xml)

    def add_enumeration(self, et: ET, xml: Xml):
        name = et.attrib['name']
        if self.get_repository().should_ignore(self.name, name):
            return
        self.enumerations[name] = Enumeration(et, self, xml)

    def get_c_includes(self):
        for i in self.c_includes:
            yield i
        # Inject GObject into every namespace
        if self.name != "GObject":
            for i in self.get_repository().get_namespace("GObject").c_includes:
                yield i

    def output(self, out_dir):
        ns_dir = os.path.join(out_dir, self.name)
        os.makedirs(ns_dir, exist_ok=True)
        self._output_aliases(ns_dir)
        self._output_enumerations(ns_dir)
        self._output_classes(ns_dir)

    def _output_aliases(self, ns_dir):
        template = self.get_repository().get_template('aliases.hpp.in')
        fname = os.path.join(ns_dir, 'aliases.hpp')
        with open(fname, 'w') as f:
            f.write(template.render(ns=self))

    def _output_enumerations(self, ns_dir):
        for e in self.enumerations.values():
            e.output(ns_dir)

    def _output_classes(self, ns_dir):
        for c in self.classes.values():
            c.output(ns_dir)
