from rpython.rlib.objectmodel import always_inline, not_rpython


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


# @specialize.argtype(0)
# def s_hex(out, val):
#     out.write(hex(val))
