from .xml import Xml
from .method import Method, Constructor
from .ignore import Ignore
import xml.etree.ElementTree as ET
import os.path


class Class:
    def __init__(self, et: ET, namespace, xml: Xml):
        self.namespace = namespace
        self.name = et.attrib['name']
        self.methods = {}
        self.interfaces = set()

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
            if x.tag == xml.ns('implements'):
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

    def get_repository(self):
        return self.namespace.get_repository()

    def _get_with_namespace(self, ident):
        if '.' not in ident:
            return f"{self.namespace.name}.{ident}"
        return ident

    def get_header_includes(self):
        deps = set()
        if self.parent:
            deps.add(self._get_with_namespace(self.parent))
        for i in self.interfaces:
            deps.add(self._get_with_namespace(i))
        for m in self.methods.values():
            if m.return_value and not m.return_value.is_built_in():
                deps.add(self._get_with_namespace(m.return_value.name))
            for p in m.params:
                if not p.is_built_in():
                    deps.add(self._get_with_namespace(p.name))

        def check_alias(d):
            ns, ident = d.split('.')
            try:
                namespace = self.get_repository().get_namespace(ns)
            except KeyError:
                print(f"Unknown symbol: {d}")
                raise
            if ident in namespace.aliases:
                return f"{ns}.aliases"
            return d

        return [check_alias(d).replace('.', '/') for d in deps]

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
        template = self.get_repository().get_template('class.hpp.in')
        fname = os.path.join(ns_dir, f"{self.name}.hpp")
        with open(fname, 'w') as f:
            f.write(template.render(cls_=self))


class Interface(Class):
    def __init__(self, et: ET, namespace, xml: Xml):
        Class.__init__(self, et, namespace, xml)
