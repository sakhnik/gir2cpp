from .xml import Xml
from .ignore import Ignore
import xml.etree.ElementTree as ET


class Type:
    def __init__(self, et: ET, xml: Xml):
        for x in et:
            if x.tag == xml.ns("type"):
                self.name = x.get('name')
                self.c_type = x.attrib.get(xml.ns('type', 'c'))
                if Ignore.skip_dotted(self.name):
                    self.name = None
                elif self.name == "none" or self.name == "utf8" \
                        or self.name == "Value":
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
        return not self.name or self.name in Type.built_in_types

    def cpp_name(self):
        if not self.name:
            return self.c_type
        if self.name == "none":
            return "void"
        return self.name.replace(".", "::")
