from .xml import Xml
from .typeref import TypeRef
from .keywords import Keywords
from .config import Config
import xml.etree.ElementTree as ET


class Method:
    def __init__(self, et: ET, class_, xml: Xml, config: Config):
        self.class_ = class_
        self.name = et.attrib['name']
        self.c_ident = et.attrib.get(xml.ns('identifier', 'c'))
        self.params = []
        self.c_params = []
        self.is_vararg = False
        self.return_value = None
        self.throws = et.attrib.get('throws') == "1"

        for x in et:
            if x.tag == xml.ns("return-value"):
                self.return_value = TypeRef(x, class_.namespace, xml, config)
            elif x.tag == xml.ns("parameters"):
                idx = 0
                for y in x:
                    if y.tag == xml.ns("parameter"):
                        name = y.attrib['name']
                        if name == '...':
                            self.is_vararg = True
                            name = ''
                        type = TypeRef(y, class_.namespace, xml, config)
                        self.params.append((name, type))
                        self.c_params.append((name, type))
                        idx += 1
                    elif y.tag == xml.ns("instance-parameter"):
                        type = TypeRef(y, class_.namespace, xml, config)
                        self.c_params.append(("(*this)", type))
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

    def is_static(self):
        return False

    def get_name(self):
        return Keywords.fix_name(self.name).replace('-', '_')

    def has_return(self):
        return self.return_value is not None \
            and self.return_value.c_type != 'void'


class Constructor(Method):
    def __init__(self, et: ET, class_, xml: Xml, config: Config):
        Method.__init__(self, et, class_, xml, config)

    def is_static(self):
        return True


class StaticFunc(Method):
    def __init__(self, et: ET, class_, xml: Xml, config: Config):
        Method.__init__(self, et, class_, xml, config)

    def is_static(self):
        return True


class Signal(Method):
    def __init__(self, et: ET, class_, xml: Xml, config: Config):
        Method.__init__(self, et, class_, xml, config)

    def is_static(self):
        return True
