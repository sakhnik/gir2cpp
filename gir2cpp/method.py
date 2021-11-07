from .xml import Xml
from .type import Type
import xml.etree.ElementTree as ET


class Method:
    def __init__(self, et: ET, class_, xml: Xml):
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
    def __init__(self, et: ET, class_, xml: Xml):
        Method.__init__(self, et, class_, xml)
