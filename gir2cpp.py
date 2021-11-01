#!/usr/bin/env python

import xml.etree.ElementTree as ET
import os.path
from typing import Dict
import shutil
from jinja2 import Environment, FileSystemLoader

script_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(script_dir, 'templates')
env = Environment(
    loader=FileSystemLoader(templates_path),
)


gir_dir = '/usr/share/gir-1.0/'
out_dir = 'out'


class XmlContext:
    def __init__(self, fname):
        self.namespaces = dict([
            node for _, node in ET.iterparse(fname, events=['start-ns'])
        ])
        self.namespaces["ns0"] = self.namespaces[""]

    def ns(self, tag, ns=''):
        return f"{{{self.namespaces[ns]}}}{tag}"


class Type:
    def __init__(self, et: ET, xml: XmlContext):
        self.name = et.attrib['name']
        self.c_type = et.attrib[xml.ns('type', 'c')]
        #print(self.name, self.c_type)

    def cpp_name(self):
        if not self.name or self.name == "none":
            return "void"
        return self.name.replace(".", "::")


class Method:
    def __init__(self, et: ET, class_, xml: XmlContext):
        self.class_ = class_
        self.return_value = Type(et.find(xml.ns("return-value")).find(xml.ns("type")), xml)
        self.name = et.attrib['name']
        self.params = []


class Constructor(Method):
    def __init__(self, et: ET, class_, xml: XmlContext):
        Method.__init__(self, et, class_, xml)


class Class:
    def __init__(self, et: ET, namespace, xml: XmlContext):
        self.namespace = namespace
        self.name = et.attrib['name']
        self.parent = et.attrib.get('parent')
        self.methods = {}
        self.interfaces = set()

        ignore = frozenset(xml.ns(i) for i in (
            "property", "doc", "source-position",
            "field", "function", "prerequisite", "doc-deprecated",
        ))

        for x in et:
            if x.tag in ignore:
                pass
            elif x.tag == xml.ns('signal', 'glib'):
                pass
            elif x.tag == xml.ns('implements'):
                self.interfaces.add(x.attrib['name'])
            elif x.tag == xml.ns('method') or x.tag == xml.ns('virtual-method'):
                name = x.attrib['name']
                try:
                    self.methods[name] = Method(x, self, xml)
                except:
                    # TODO: skipped method
                    pass
            elif x.tag == xml.ns('constructor'):
                name = x.attrib['name']
                self.methods[name] = Constructor(x, self, xml)
            else:
                print("Unhandled", x.tag)
                pass

    def _header_includes(self):
        def _fix_sep(s):
            return s.replace('.', '/')
        deps = set()
        if self.parent:
            deps.add(_fix_sep(self.parent))
        for i in self.interfaces:
            deps.add(_fix_sep(i))
        # TODO: add types from the methods
        return deps

    def _parents(self):
        def _fix_sep(s):
            return s.replace('.', '::')
        ret = []
        if self.parent:
            ret.append(_fix_sep(self.parent))
        for i in self.interfaces:
            ret.append(f"virtual {_fix_sep(i)}")
        return ret

    def output(self, ns_dir):
        template = env.get_template('class.hpp.in')

        fname = os.path.join(ns_dir, f"{self.name}.hpp")
        with open(fname, 'w') as f:
            f.write(template.render(
                    cls_=self,
                    includes=self._header_includes(),
                    parents=self._parents()
                    ))


class Interface(Class):
    def __init__(self, et: ET, namespace, xml: XmlContext):
        Class.__init__(self, et, namespace, xml)


class Namespace:
    def __init__(self, name):
        self.name = name
        self.aliases = {}
        self.classes = {}

    def add_alias(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        type_et = et.find(xml.ns('type'))
        type_name = type_et.attrib['name']
        self.aliases[name] = type_name

    def add_class(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        self.classes[name] = Class(et, self, xml)

    def add_interface(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        self.classes[name] = Interface(et, self, xml)

    def output(self, out_dir):
        ns_dir = os.path.join(out_dir, self.name)
        os.makedirs(ns_dir, exist_ok=True)
        for c in self.classes.values():
            c.output(ns_dir)


namespaces: Dict[str, Namespace] = {}
processed_modules = set()


def process(module, version):
    if module in processed_modules:
        return
    processed_modules.add(module)

    fname = os.path.join(gir_dir, f'{module}-{version}.gir')
    xml = XmlContext(fname)

    tree = ET.parse(fname)
    root = tree.getroot()

    package = ''  # directory name
    c_include = ''

    def process_namespace(nstree):
        ns_name = nstree.attrib['name']
        try:
            namespace = namespaces[ns_name]
        except KeyError:
            namespace = Namespace(ns_name)
            namespaces[ns_name] = namespace

        ignore = frozenset(xml.ns(i) for i in (
            "function-macro", "constant", "function", "record", "docsection",
            "enumeration", "callback", "bitfield", "union"
        ))

        # c_id_pref = nstree.attrib[xml.ns('identifier-prefixes', 'c')]
        # c_sym_pref = nstree.attrib[xml.ns('symbol-prefixes', 'c')]
        for x in nstree:
            if x.tag in ignore:
                pass
            elif x.tag == xml.ns("boxed", "glib"):
                pass
            elif x.tag == xml.ns("alias"):
                namespace.add_alias(x, xml)
            elif x.tag == xml.ns("class"):
                namespace.add_class(x, xml)
            elif x.tag == xml.ns("interface"):
                namespace.add_interface(x, xml)
            else:
                print('Unhandled', x.tag)

    for x in root:
        if x.tag == xml.ns('include'):
            process(x.attrib['name'], x.attrib['version'])
        elif x.tag == xml.ns('package'):
            package = x.attrib['name']
        elif x.tag == xml.ns('include', 'c'):
            c_include = x.attrib['name']
        elif x.tag == xml.ns('namespace'):
            process_namespace(x)
        else:
            print("Unhandled", x.tag, x.attrib)


process('Gtk', '4.0')

shutil.rmtree(out_dir, ignore_errors=True)
os.makedirs(out_dir, exist_ok=True)

for ns, namespace in namespaces.items():
    namespace.output(out_dir)
