import xml.etree.ElementTree as ET

class Xml:
    def __init__(self, fname):
        self.namespaces = dict([
            node for _, node in ET.iterparse(fname, events=['start-ns'])
        ])
        self.namespaces["ns0"] = self.namespaces[""]

    def ns(self, tag, ns=''):
        return f"{{{self.namespaces[ns]}}}{tag}"
