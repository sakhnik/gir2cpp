#!/usr/bin/env python

from gir2cpp.repository import Repository


gir_dir = '/usr/share/gir-1.0/'
out_dir = 'out'


repository = Repository(gir_dir)
repository.process('Gtk', '4.0')
repository.output(out_dir)
