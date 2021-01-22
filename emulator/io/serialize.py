from rpython.rlib.objectmodel import always_inline, not_rpython

from emulator.types import uint2hex, hex2uint, uint8_t, uint16_t, uint32_t, uint64_t


@not_rpython
def serialized_field(name, func):
    func = always_inline(func)

    @not_rpython
    def impl(cls):
        prev_s = cls.serialize_impl
        prev_u = cls.unserialize_impl

        @always_inline
        def serialize_impl(slf, out):
            prev_s(slf, out)
            out.write(' ')
            func(out, getattr(slf, name))

        @always_inline
        def unserialize_impl(slf, t):
            i = prev_u(slf, t)
            setattr(slf, name, func.u(t[i]))
            return i + 1

        cls.serialize_impl = serialize_impl
        cls.unserialize_impl = unserialize_impl

        return cls
    return impl


@not_rpython
def serialized_field_list(name, func):
    func = always_inline(func)

    @not_rpython
    def impl(cls):
        prev_s = cls.serialize_impl
        prev_u = cls.unserialize_impl

        @always_inline
        def serialize_impl(slf, out):
            prev_s(slf, out)
            out.write(' ')
            lst = getattr(slf, name)
            s_uint32(out, uint32_t(len(lst)))
            for i in xrange(len(lst)):
                out.write(' ')
                func(out, lst[i])

        @always_inline
        def unserialize_impl(slf, t):
            i = prev_u(slf, t)
            ln = s_uint32.u(t[i])
            lst = []
            for j in xrange(ln):
                lst.append(func.u(t[i + j + 1]))
            setattr(slf, name, lst)
            return i + ln + 1

        cls.serialize_impl = serialize_impl
        cls.unserialize_impl = unserialize_impl

        return cls
    return impl


@not_rpython
def serialized_field_array(name, ln, func):
    func = always_inline(func)

    @not_rpython
    def impl(cls):
        prev_s = cls.serialize_impl
        prev_u = cls.unserialize_impl

        @always_inline
        def serialize_impl(slf, out):
            prev_s(slf, out)
            lst = getattr(slf, name)
            assert len(lst) == ln
            for i in xrange(len(lst)):
                out.write(' ')
                func(out, lst[i])

        @always_inline
        def unserialize_impl(slf, t):
            i = prev_u(slf, t)
            lst = []
            for j in xrange(ln):
                lst.append(func.u(t[i + j]))
            setattr(slf, name, lst)
            return i + ln

        cls.serialize_impl = serialize_impl
        cls.unserialize_impl = unserialize_impl

        return cls
    return impl


@not_rpython
def _unserialize_impl(tgt):
    @not_rpython
    def impl(func):
        tgt.u = always_inline(func)
    return impl


def s_str(out, val):
    # TODO quoted
    out.write(val)


@_unserialize_impl(s_str)
def u_str(t):
    return t


def _s_uint(cls):
    bits = cls.BITS

    def s_uint(out, val):
        assert isinstance(val, cls)
        out.write(uint2hex(bits, val))

    @_unserialize_impl(s_uint)
    def u_uint(t):
        return hex2uint(cls, t)

    return s_uint


s_uint8 = _s_uint(uint8_t)
s_uint16 = _s_uint(uint16_t)
s_uint32 = _s_uint(uint32_t)
s_uint64 = _s_uint(uint64_t)
