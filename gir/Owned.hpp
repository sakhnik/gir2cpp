#pragma once

#include "Base.hpp"
#include <utility>

namespace gir {

template <typename T>
struct Owned : T
{
    explicit Owned(T &&t)
        : T{t}
    {
        this->_g_obj = t.g_obj();
    }

    ~Owned()
    {
        if (this->g_obj())
            this->unref();
    }

    explicit Owned(const Owned<T> &o)
        : T{o}
    {
        this->_g_obj = o.g_obj();
        if (this->g_obj())
            this->ref();
    }

    explicit Owned(Owned<T> &&o)
        : T{o}
    {
        this->_g_obj = o.g_obj();
        o._g_obj = nullptr;
    }

    Owned<T>& operator=(const Owned<T> &o)
    {
        if (this == &o)
            return *this;
        static_cast<T&>(*this) = o;
        this->_g_obj = o.g_obj();
        if (this->g_obj())
            this->ref();
        return *this;
    }

    Owned<T>& operator=(Owned<T> &&o)
    {
        static_cast<T&>(*this) = o;
        this->_g_obj = o.g_obj();
        if (o.g_obj())
            o._g_obj = nullptr;
        return *this;
    }
};

template <typename T>
Owned<T> MakeOwned(T &&t)
{
    return Owned<T>(std::move(t));
}

} //namespace;
