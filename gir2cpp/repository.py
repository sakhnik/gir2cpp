from pathlib import Path
from typing import Dict
import os
import shutil
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
from . import namespace
from .xml import Xml
from .ignore import Ignore


Namespace = namespace.Namespace


class Repository:
    def __init__(self, gir_dir):
        self.gir_dir = gir_dir
        script_dir = Path(__file__).parent.absolute()
        templates_path = os.path.join(script_dir, '..', 'templates')
        self.env = Environment(
            loader=FileSystemLoader(templates_path),
        )

        self.namespaces: Dict[str, Namespace] = {}
        self.processed_modules = set()
        # GObject is referenced implicitly by everyone
        self.process('GObject', '2.0')

    def get_namespace(self, ns):
        return self.namespaces[ns]

    def get_template(self, name):
        return self.env.get_template(name)

    def process(self, module, version):
        if module in self.processed_modules:
            return
        self.processed_modules.add(module)

        fname = os.path.join(self.gir_dir, f'{module}-{version}.gir')
        xml = Xml(fname)

        tree = ET.parse(fname)
        root = tree.getroot()

        package = ''  # directory name
        c_includes = []

        for x in root:
            if x.tag == xml.ns('include'):
                self.process(x.attrib['name'], x.attrib['version'])
            elif x.tag == xml.ns('package'):
                package = x.attrib['name']
            elif x.tag == xml.ns('include', 'c'):
                c_includes.append(x.attrib['name'])
            elif x.tag == xml.ns('namespace'):
                name = x.attrib['name']
                if not Ignore.skip(name):
                    try:
                        ns = self.namespaces[name]
                    except KeyError:
                        ns = Namespace(name, c_includes, self)
                        self.namespaces[name] = ns
                    ns.parse(x, xml)
            else:
                print("Unhandled", x.tag, x.attrib)

    def output(self, out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
        os.makedirs(out_dir, exist_ok=True)
        for ns in self.namespaces.values():
            ns.output(out_dir)
