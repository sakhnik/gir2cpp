#pragma once

#include <glib-object.h>

namespace gir {

namespace GObject { class Object; }

template <typename T>
class Base
{
};

template <>
class Base<GObject::Object>
{
protected:
    ::GObject *_g_obj = nullptr;
};

} //namespace gir;
