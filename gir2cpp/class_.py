from .xml import Xml
from .method_holder import MethodHolder
from .config import Config
import xml.etree.ElementTree as ET
import os.path


class Class(MethodHolder):
    def __init__(self, et: ET, namespace, xml: Xml, config: Config):
        MethodHolder.__init__(self, et, namespace, xml, config)

        self.name = et.attrib['name']
        # Interface names in C++ format like "Gtk::Editable"
        # TODO: Unify namespace-aware name management
        self.interfaces = set()

        try:
            self.c_type = et.attrib[xml.ns("type", "c")]
        except KeyError:
            # Hack for the classes that don't have c:type
            self.c_type = et.attrib[xml.ns("type-name", "glib")]
        # Resolve clash with the namespace GObject
        if self.c_type == "GObject":
            self.c_type = "::GObject"
        self.get_type = et.attrib.get(xml.ns('get-type', 'glib'))

        self.parent = et.attrib.get('parent')
        if config.skip_check(self.namespace.name, self.parent):
            self.parent = None

        ignore = frozenset(xml.ns(i) for i in (
            "property", "doc", "source-position",
            "field", "prerequisite", "doc-deprecated",
        ))

        for x in et:
            if x.tag in ignore:
                continue
            if config.skip_deprecated(x):
                continue
            name = x.attrib['name']
            if config.skip_check(self.namespace.name, name):
                continue
            if self.handled_in_method_holder(x):
                continue
            if x.tag == xml.ns('implements'):
                cpp_id = self.namespace.get_cpp_identifier(x.attrib['name'])
                self.interfaces.add(cpp_id)
            else:
                print("Unhandled", x.tag)
                pass

    def get_header_includes(self):
        deps = set()
        if self.parent:
            deps.add(self._get_with_namespace(self.parent))
        for i in self.interfaces:
            # No need to inherit from an interface another time
            # if it's already done in one of parent classes.
            if not self.parent_implements_interface(i):
                deps.add(i.replace('::', '.'))
        methods_includes = self.get_header_includes_for_methods()
        return set(d.replace('.', '/') for d in deps).union(methods_includes)

    def get_impl_includes(self):
        return set(d for d in self.get_header_includes()
                   if not d.endswith('aliases'))

    def get_parents(self):
        def _fix_sep(s):
            return s.replace('.', '::')
        ret = []
        if self.parent:
            ret.append(_fix_sep(self.parent))
        for i in self.interfaces:
            # No need to inherit from an interface another time
            # if it's already done in one of parent classes.
            if not self.parent_implements_interface(i):
                ret.append(i)
        return ret

    def parent_implements_interface(self, cpp_type):
        """Check whether the interface is already implemented
           in one of parent classes."""
        if not self.parent:
            return False
        parent = self.get_repository().get_typedef(self.parent,
                                                   self.namespace.name)
        for i in parent.interfaces:
            if i == cpp_type:
                return True
        return parent.parent_implements_interface(cpp_type)

    def output(self, ns_dir):
        for ext in ("hpp", "ipp", "cpp"):
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
        return f"{self.namespace.fqname()}::{self.name}"

    def c_type_decl(self):
        return f"{self.c_type} *"

    def can_assert_type(self):
        return self.namespace.name != "GObject" and self.get_type is not None


class Interface(Class):
    def __init__(self, et: ET, namespace, xml: Xml, config: Config):
        Class.__init__(self, et, namespace, xml, config)


class Record(Class):
    def __init__(self, et: ET, namespace, xml: Xml, config: Config):
        Class.__init__(self, et, namespace, xml, config)

    def can_assert_type(self):
        return False
