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
        for x in et:
            if x.tag == xml.ns("type"):
                self.name = x.get('name')
                if self.name == "none":
                    self.name = None
                self.c_type = x.attrib.get(xml.ns('type', 'c'))
            elif x.tag == xml.ns("varargs"):
                self.name = None
                self.c_type = '...'
            elif x.tag == xml.ns("array"):
                self.c_type = x.attrib.get(xml.ns('type', 'c'))
                self.name = None
            elif x.tag == xml.ns("doc") or x.tag == xml.ns("attribute"):
                pass
            else:
                self.name = None
                print("Unknown type", x.tag)

    built_in_types = frozenset((
        "gchar", "guchar", "gshort", "gushort",
        "gint", "guint", "glong", "gulong", "gssize", "gsize", "gintptr",
        "guintptr", "gpointer", "gconstpointer", "gboolean", "gint8", "gint16",
        "guint8", "guint16", "gint32", "guint32", "gint64", "guint64",
        "gfloat", "gdouble", "GType", "utf8", "gunichar"
    ))

    def is_built_in(self):
        return not self.name or self.name in Type.built_in_types

    def cpp_name(self):
        if not self.name:
            return self.c_type
        if self.name == "none":
            return "void"
        return self.name.replace(".", "::")


class Method:
    def __init__(self, et: ET, class_, xml: XmlContext):
        self.class_ = class_
        self.name = et.attrib['name']
        self.params = []
        self.instance_parameter_idx = 0

        for x in et:
            if x.tag == xml.ns("return-value"):
                self.return_value = Type(x, xml)
            elif x.tag == xml.ns("parameters"):
                idx = 0
                for y in x:
                    if y.tag == xml.ns("parameter"):
                        self.params.append(Type(y, xml))
                        idx += 1
                    elif y.tag == xml.ns("instance-parameter"):
                        self.instance_parameter_idx = idx
                    else:
                        print("Unsupported", y.tag)
            elif x.tag == xml.ns("doc") or x.tag == xml.ns("source-position"):
                pass
            elif x.tag == xml.ns("doc-deprecated"):
                pass
            elif x.tag == xml.ns("attribute"):
                pass
            else:
                print("Unsupported", x.tag)


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

    def get_header_includes(self):
        deps = set()
        if self.parent:
            deps.add(self.parent)
        for i in self.interfaces:
            deps.add(i)
        for m in self.methods.values():
            if m.return_value and not m.return_value.is_built_in():
                deps.add(m.return_value.name)
            for p in m.params:
                if not p.is_built_in():
                    deps.add(p.name)
        return [d.replace('.', '/') for d in deps]

    def get_parents(self):
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
            f.write(template.render(cls_=self))


class Interface(Class):
    def __init__(self, et: ET, namespace, xml: XmlContext):
        Class.__init__(self, et, namespace, xml)


class Enumeration:
    def __init__(self, et: ET, namespace, xml: XmlContext):
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

    def output(self, ns_dir):
        template = env.get_template('enum.hpp.in')
        fname = os.path.join(ns_dir, f"{self.name}.hpp")
        with open(fname, 'w') as f:
            f.write(template.render(enum_=self))


class Namespace:
    def __init__(self, name, c_include):
        self.name = name
        self.c_include = c_include
        self.aliases = {}
        self.enumerations = {}
        self.classes = {}

    def parse(self, et: ET, xml: XmlContext):
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
            elif x.tag == xml.ns("alias") or x.tag == xml.ns("record") \
                    or x.tag == xml.ns("callback"):
                self.add_alias(x, xml)
            elif x.tag == xml.ns("class"):
                self.add_class(x, xml)
            elif x.tag == xml.ns("interface"):
                self.add_interface(x, xml)
            elif x.tag == xml.ns("enumeration"):
                self.add_enumeration(x, xml)
            else:
                print('Unhandled', x.tag)

    def add_alias(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        c_type = et.attrib.get(xml.ns('type', 'c'))
        self.aliases[name] = c_type

    def add_class(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        self.classes[name] = Class(et, self, xml)

    def add_interface(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        self.classes[name] = Interface(et, self, xml)

    def add_enumeration(self, et: ET, xml: XmlContext):
        name = et.attrib['name']
        self.enumerations[name] = Enumeration(et, self, xml)

    def output(self, out_dir):
        ns_dir = os.path.join(out_dir, self.name)
        os.makedirs(ns_dir, exist_ok=True)
        self._output_aliases(ns_dir)
        self._output_enumerations(ns_dir)
        self._output_classes(ns_dir)

    def _output_aliases(self, ns_dir):
        template = env.get_template('aliases.hpp.in')
        fname = os.path.join(ns_dir, 'aliases.hpp')
        with open(fname, 'w') as f:
            f.write(template.render(ns=self))

    def _output_enumerations(self, ns_dir):
        for e in self.enumerations.values():
            e.output(ns_dir)

    def _output_classes(self, ns_dir):
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

    for x in root:
        if x.tag == xml.ns('include'):
            process(x.attrib['name'], x.attrib['version'])
        elif x.tag == xml.ns('package'):
            package = x.attrib['name']
        elif x.tag == xml.ns('include', 'c'):
            c_include = x.attrib['name']
        elif x.tag == xml.ns('namespace'):
            name = x.attrib['name']
            try:
                ns = namespaces[name]
            except KeyError:
                ns = Namespace(name, c_include)
                namespaces[name] = ns
            ns.parse(x, xml)
        else:
            print("Unhandled", x.tag, x.attrib)


process('Gtk', '4.0')

shutil.rmtree(out_dir, ignore_errors=True)
os.makedirs(out_dir, exist_ok=True)

for ns, namespace in namespaces.items():
    namespace.output(out_dir)
