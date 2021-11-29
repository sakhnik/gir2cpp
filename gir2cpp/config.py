import re


class Config:
    def __init__(self):
        self.include = re.compile(r"""^(
                GObject::.*
                |
                Gtk::.*
                )""", re.VERBOSE)
        self.ignore = re.compile(r"""^(
                Gtk::Print.*
                |
                GdkPixbuf::.*
                |
                Gtk::PageSetupUnixDialog
                )$""", re.VERBOSE)
        self.gir_dir = '/usr/share/gir-1.0/'
        self.out_dir = 'out'

    def skip(self, ns, symbol=''):
        fqident = f"{ns}::{symbol}"
        if self.include.match(fqident) is None:
            return True
        return not self.ignore.match(fqident) is None

    def skip_dotted(self, symbol):
        try:
            ns, ident = symbol.split('.')
            return self.skip(ns, ident)
        except ValueError:
            return False

    def skip_check(self, ns, symbol):
        if not symbol:
            return True
        if '.' in symbol:
            return self.skip_dotted(symbol)
        return self.skip(ns, symbol)
