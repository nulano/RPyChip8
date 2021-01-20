from rpython.rlib import rarithmetic
from rpython.rtyper import rint
from rpython.rtyper.error import TyperError
from rpython.rtyper.lltypesystem import rffi  # sets up predefined types


unsigned = rarithmetic.r_uint64
signed = rarithmetic.r_int64


def make_uint(bits):
    # mask = (2 ** bits) - 1
    storage = rarithmetic.build_int(None, False, bits)
    # tp = type("uint%d_t" % bits, (base_uint,), {"MASK": unsigned(mask),
    #                                             "BITS": bits,
    #                                             "STORE": storage})
    # return tp
    return storage


uint8_t = make_uint(8)
uint16_t = make_uint(16)
uint32_t = make_uint(32)
uint64_t = make_uint(64)


# _wrap_repr = rint.unsignedlonglong_repr
# _wrap_prefix = 'ullong_'
_wrap_repr = rint.unsigned_repr
_wrap_prefix = 'uint_'


_rint_rtype_template = rint._rtype_template
def _rtype_template(hop, func):
    """Write a simple operation implementing the given 'func'.
    It must be an operation that cannot raise.
    """
    try:
        return _rint_rtype_template(hop, func)
    except TyperError:
        r_result = hop.r_result
        repr = _wrap_repr
        if func.startswith(('lshift', 'rshift')):
            repr2 = rint.signed_repr
        else:
            repr2 = repr
        vlist = hop.inputargs(repr, repr2)

        hop.exception_cannot_occur()

        v_res = hop.genop(_wrap_prefix+func, vlist, resulttype=repr)
        v_res = hop.llops.convertvar(v_res, repr, r_result)
        return v_res
rint._rtype_template = _rtype_template
