from .xml import Xml
from .method_holder import MethodHolder
from .ignore import Ignore
import xml.etree.ElementTree as ET
import os.path


class Class(MethodHolder):
    def __init__(self, et: ET, namespace, xml: Xml):
        MethodHolder.__init__(self, et, namespace, xml)

        self.name = et.attrib['name']
        self.interfaces = set()

        try:
            self.c_type = et.attrib[xml.ns("type", "c")]
        except KeyError:
            # Hack for the classes that don't have c:type
            self.c_type = et.attrib[xml.ns("type-name", "glib")]
        # Resolve clash with the namespace GObject
        if self.c_type == "GObject":
            self.c_type = "::GObject"
        self.get_type = et.attrib[xml.ns('get-type', 'glib')]

        self.parent = et.attrib.get('parent')
        if Ignore.skip_check(self.namespace.name, self.parent):
            self.parent = None

        ignore = frozenset(xml.ns(i) for i in (
            "property", "doc", "source-position",
            "field", "function", "prerequisite", "doc-deprecated",
        ))

        for x in et:
            if x.tag in ignore:
                continue
            elif x.tag == xml.ns('signal', 'glib'):
                continue
            name = x.attrib['name']
            if Ignore.skip_check(self.namespace.name, name):
                continue
            if x.tag in self.method_tags:
                continue
            if x.tag == xml.ns('implements'):
                self.interfaces.add(x.attrib['name'])
            else:
                print("Unhandled", x.tag)
                pass

    def get_header_includes(self):
        deps = set()
        if self.parent:
            deps.add(self._get_with_namespace(self.parent))
        for i in self.interfaces:
            deps.add(self._get_with_namespace(i))
        methods_includes = self.get_header_includes_for_methods()
        return set(d.replace('.', '/') for d in deps).union(methods_includes)

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
        for ext in ("hpp", "cpp"):
            template = self.get_repository().get_template(f"class.{ext}.in")
            fname = os.path.join(ns_dir, f"{self.name}.{ext}")
            with open(fname, 'w') as f:
                f.write(template.render(cls_=self))

    def cast_from_c(self, varname):
        # using GObject = ::GObject; return "G_OBJECT"
        return f"reinterpret_cast<::GObject*>({varname})"

    def cast_to_c(self, varname, refctype):
        return f"reinterpret_cast<{refctype}>({varname}.g_obj())"

    def cpp_type(self, decl):
        return f"{self.namespace.name}::{self.name}"


class Interface(Class):
    def __init__(self, et: ET, namespace, xml: Xml):
        Class.__init__(self, et, namespace, xml)
