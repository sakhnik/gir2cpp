#!/usr/bin/env python

from gir2cpp.repository import Repository
from gir2cpp.config import Config


config = Config()

repository = Repository(config)
repository.process('Gtk', '4.0')
repository.output()
