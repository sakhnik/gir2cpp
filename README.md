# C++ wrappers generator from GObject introspection

This project was inspired by the brilliant idea in [cppgir](https://gitlab.com/mnauw/cppgir).
And because I wasn't able to figure out how to get text from a Gtk entry.
It wasn't obvious indeed that instead of the conventional

```cpp
auto t = entry.get_text();
```

one should know in beforehand that `GtkEntry` implements `Editable`:

```cpp
auto t = gtk_editable_get_text(GTK_EDITABLE(entry));
```

The wrappers are mainly generated for the other sandbox project
[sakhnik/nvim-ui](https://github.com/sakhnik/nvim-ui).
