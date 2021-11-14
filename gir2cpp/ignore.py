import re


class Ignore:
    include = re.compile(r"""^(
            GObject::.*
            |
            Gtk::.*
            )""", re.VERBOSE)
    ignore = re.compile(r"""^(
            Gtk::Print.*
            |
            Gio::SettingsBackend.*
            |
            GLib::StatBuf
            |
            Gsk::.*?Renderer.*
            |
            GLib::Unix.*
            |
            HarfBuzz::.*
            |
            GdkPixbuf::.*
            )$""", re.VERBOSE)

    @staticmethod
    def skip(ns, symbol=''):
        fqident = f"{ns}::{symbol}"
        if Ignore.include.match(fqident) is None:
            return True
        return not Ignore.ignore.match(fqident) is None

    @staticmethod
    def skip_dotted(symbol):
        try:
            ns, ident = symbol.split('.')
            return Ignore.skip(ns, ident)
        except ValueError:
            return False

    @staticmethod
    def skip_check(ns, symbol):
        if not symbol:
            return True
        if '.' in symbol:
            return Ignore.skip_dotted(symbol)
        return Ignore.skip(ns, symbol)
