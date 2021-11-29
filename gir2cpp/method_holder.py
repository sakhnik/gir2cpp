from .xml import Xml
from .typedef import TypeDef
from .alias import Alias
from .ignore import Ignore
from .method import Method, Constructor
import xml.etree.ElementTree as ET


class MethodHolder(TypeDef):
    def __init__(self, et: ET, namespace, xml: Xml):
        self.namespace = namespace
        self.methods = []
        self.method_tags = frozenset((
            xml.ns("method"), xml.ns("virtual-method"),
            xml.ns("constructor")
        ))

        for x in et:
            name = x.attrib.get('name')
            if not name:
                continue
            if Ignore.skip_check(self.namespace.name, name):
                continue
            try:
                if x.tag == xml.ns('method'):
                    self.methods.append(Method(x, self, xml))
                elif x.tag == xml.ns('virtual-method'):
                    self.methods.append(Method(x, self, xml))
                elif x.tag == xml.ns('constructor'):
                    self.methods.append(Constructor(x, self, xml))
            except KeyError:
                pass
            except NotImplementedError:
                pass

    def get_repository(self):
        return self.namespace.get_repository()

    def _get_extern_types(self):
        deps = set()
        for m in self.methods:
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
        deps = self._get_extern_types()
        return [d.split('.') for d in deps]

    def get_plain_methods(self):
        return filter(lambda m: not m.is_vararg, self.methods)

    def get_vararg_methods(self):
        return filter(lambda m: m.is_vararg, self.methods)

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

        for m in self.methods:
            if m.return_value and not m.return_value.is_built_in():
                add_alias(m.return_value.name)
            for _, ptype in m.params:
                if not ptype.is_built_in():
                    add_alias(ptype.name)

        return set(d.replace('.', '/') for d in deps)
