#pragma once

#include <exception>
#include <cstdint>
#include <string>
#include <functional>
#include <cassert>
#include <glib-object.h>

namespace gir {

namespace GObject { class Object; }

#ifdef GIR_INLINE
#  define GIR_INLINE_DECL inline
#else
#  define GIR_INLINE_DECL
#endif

class Base
{
protected:
    ::GObject *_g_obj = nullptr;

public:
    ::GObject* g_obj() const { return _g_obj; }
};

struct Error : std::exception
{
    uint32_t domain{};
    int code{};
    std::string message;

    Error(GError *err)
        : domain{err->domain}
        , code{err->code}
        , message{err->message}
    {
    }
};

} //namespace gir;
