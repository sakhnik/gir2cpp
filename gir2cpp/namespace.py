from .xml import Xml
from .alias import Alias
from .class_ import Class, Interface, Record
from .enumeration import Enumeration
from .config import Config
import xml.etree.ElementTree as ET
import os


class Namespace:
    def __init__(self, name, c_includes, repository, config: Config):
        self.name = name
        self.c_includes = c_includes
        self.repository = repository
        self.config = config
        self.typedefs = {}

    def get_repository(self):
        return self.repository

    def parse(self, et: ET, xml: Xml):
        ignore = frozenset(xml.ns(i) for i in (
            "function-macro", "constant", "function", "docsection",
            "union"
        ))

        type_mapping = {
            xml.ns("class"): Class,
            xml.ns("interface"): Interface,
            xml.ns("enumeration"): Enumeration,
            xml.ns("alias"): Alias,
            xml.ns("callback"): Alias,
            xml.ns("record"): Record,
            xml.ns("bitfield"): Enumeration,
        }

        for x in et:
            if x.tag in ignore:
                continue
            if x.tag == xml.ns("boxed", "glib"):
                continue
            if self.config.skip_deprecated(x):
                continue
            name = x.attrib['name']
            if self.config.skip(self.name, name):
                continue
            typedef_cl = type_mapping.get(x.tag, None)
            if not typedef_cl:
                print('Unhandled', x.tag)
                continue
            self.typedefs[name] = typedef_cl(x, self, xml, self.config)

    def fqname(self):
        return f"gir::{self.name}"

    def get_cpp_identifier(self, name: str):
        if '.' in name:
            return name.replace('.', '::')
        return f"{self.name}::{name}"

    def get_c_includes(self):
        for i in self.c_includes:
            yield i
        # Inject GObject into every namespace
        if self.name != "GObject":
            for i in self.get_repository().get_namespace("GObject").c_includes:
                yield i

    def get_aliases(self):
        for td in self.typedefs.values():
            if isinstance(td, Alias):
                yield td

    def get_typedef(self, name):
        return self.typedefs.get(name, None)

    def output(self, out_dir):
        ns_dir = os.path.join(out_dir, self.name)
        os.makedirs(ns_dir, exist_ok=True)
        self._output_aliases(ns_dir)
        self._output_typedefs(ns_dir)

    def _output_aliases(self, ns_dir):
        template = self.get_repository().get_template('aliases.hpp.in')
        fname = os.path.join(ns_dir, 'aliases.hpp')
        with open(fname, 'w') as f:
            f.write(template.render(ns=self))

    def _output_typedefs(self, ns_dir):
        for c in self.typedefs.values():
            c.output(ns_dir)
