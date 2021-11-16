#pragma once

#include <glib-object.h>

namespace gir {

namespace GObject { class Object; }

class Base
{
protected:
    ::GObject *_g_obj = nullptr;
};

} //namespace gir;
