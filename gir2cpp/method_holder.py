from .xml import Xml
from .typedef import TypeDef
from .alias import Alias
from .config import Config
from .method import Method, Constructor, Signal
import xml.etree.ElementTree as ET
from itertools import chain


class MethodHolder(TypeDef):
    def __init__(self, et: ET, namespace, xml: Xml, config: Config):
        self.namespace = namespace
        self.methods = []
        self.signals = []
        self.name = et.attrib.get('name')
        self.method_names = set()  # For deduplication
        self.method_tags = frozenset((
            xml.ns("method"), xml.ns("virtual-method"),
            xml.ns("constructor"), xml.ns('signal', 'glib')
        ))

        for x in et:
            if config.skip_deprecated(x):
                continue
            name = x.attrib.get('name')
            if not name:
                continue
            if config.skip(f"{self.namespace.name}::{self.name}", name):
                continue
            try:
                if x.tag == xml.ns('method'):
                    self.append_method(Method(x, self, xml, config))
                elif x.tag == xml.ns('virtual-method'):
                    self.append_method(Method(x, self, xml, config))
                elif x.tag == xml.ns('constructor'):
                    self.append_method(Constructor(x, self, xml, config))
                elif x.tag == xml.ns('signal', 'glib'):
                    self.signals.append(Signal(x, self, xml, config))
            # except KeyError:
            #     pass
            except NotImplementedError:
                pass

    def append_method(self, method):
        # TODO: handle virtual methods without c_ident
        if not method.c_ident:
            return
        if method.name in self.method_names:
            return
        self.method_names.add(method.name)
        self.methods.append(method)

    def handled_in_method_holder(self, x: ET):
        return x.tag in self.method_tags

    def get_repository(self):
        return self.namespace.get_repository()

    def _get_extern_types(self):
        deps = set()
        for m in chain(self.methods, self.signals):
            if m.return_value and not m.return_value.is_built_in():
                fqname = self._get_with_namespace(m.return_value.name)
                if not self._is_alias(fqname):
                    deps.add(fqname)
            for _, ptype in m.params:
                if not ptype.is_built_in():
                    fqname = self._get_with_namespace(ptype.name)
                    if not self._is_alias(fqname):
                        deps.add(fqname)
        return deps

    def get_forward_decls(self):
        cur_class = self._get_with_namespace(self.name)
        deps = self._get_extern_types().difference({cur_class})
        return [d.split('.') for d in deps]

    def get_plain_methods(self):
        return filter(lambda m: not m.is_vararg, self.methods)

    def get_vararg_methods(self):
        return filter(lambda m: m.is_vararg, self.methods)

    def get_signals(self):
        # Skip through the signals that don't have all the C++ types defined
        def _is_defined(m: Method):
            if not m.return_value.cpp_type():
                return False
            for pn, pt in m.params:
                if not pt.cpp_type():
                    return False
            return True
        return filter(lambda m: _is_defined(m), self.signals)

    def _get_with_namespace(self, ident):
        if '.' not in ident:
            return f"{self.namespace.name}.{ident}"
        return ident

    def _is_alias(self, d):
        typedef = self.get_repository().get_typedef(d, self.namespace.name)
        if not typedef:
            return False
        return isinstance(typedef, Alias)

    def get_header_includes_for_methods(self):
        deps = set()

        def add_alias(t):
            fqname = self._get_with_namespace(t)
            if self._is_alias(fqname):
                ns, _ = fqname.split('.')
                deps.add(f'{ns}.aliases')

        for m in chain(self.methods, self.signals):
            if m.return_value and not m.return_value.is_built_in():
                add_alias(m.return_value.name)
            for _, ptype in m.params:
                if not ptype.is_built_in():
                    add_alias(ptype.name)

        return set(d.replace('.', '/') for d in deps)
