from .xml import Xml
from .ignore import Ignore
from .alias import Alias
import xml.etree.ElementTree as ET


class TypeRef:
    def __init__(self, et: ET, namespace, xml: Xml):
        self.namespace = namespace
        for x in et:
            if x.tag == xml.ns("type"):
                self.name = x.get('name')
                self.c_type = x.attrib.get(xml.ns('type', 'c'))
                if Ignore.skip_check(namespace.name, self.name):
                    self.name = None
                elif self.name == "none" or self.name == "utf8" \
                        or self.name == "Value":
                    self.name = None
                elif self.is_built_in():
                    self.name = None
                elif self.name == "va_list":
                    self.name = None
                    self.c_type == '...'
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
        return not self.name or self.name in TypeRef.built_in_types

    def cpp_name(self):
        if not self.name:
            return self.c_type
        repository = self.namespace.get_repository()
        typedef = repository.get_typedef(self.name, self.namespace.name)
        # TODO: a virtual call to typedef
        if isinstance(typedef, Alias):
            return self.c_type.replace(typedef.c_type, self.name)
        return self.name.replace(".", "::")

    def cast_from_c(self):
        if not self.name:
            return ""
        repository = self.namespace.get_repository()
        typedef = repository.get_typedef(self.name, self.namespace.name)
        if not typedef:
            return ""
        return typedef.cast_from_c()

    def cast_to_c(self, varname):
        if not self.name:
            return varname
        repository = self.namespace.get_repository()
        typedef = repository.get_typedef(self.name, self.namespace.name)
        if not typedef:
            return varname
        return typedef.cast_to_c(varname)
