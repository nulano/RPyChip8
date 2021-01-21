from rpython.rlib import rarithmetic
from rpython.rtyper import rint
from rpython.rtyper.error import TyperError
from rpython.rtyper.lltypesystem import rffi  # sets up predefined types
from rpython.rtyper.lltypesystem.lltype import Bool

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
_wrap_repr = rint.unsigned_repr


_rint_rtype_template = rint._rtype_template
def _rtype_template(hop, func):
    """Write a simple operation implementing the given 'func'.
    It must be an operation that cannot raise.
    """
    try:
        return _rint_rtype_template(hop, func)
    except TyperError:
        s_int1, s_int2 = hop.args_s
        if (not (s_int1.unsigned or s_int2.unsigned)
            or not s_int1.nonneg or not s_int2.nonneg):
            raise TyperError("binary ops for small signed ints not implemented")

        r_result = hop.r_result
        repr = _wrap_repr
        if func.startswith(('lshift', 'rshift')):
            repr2 = rint.signed_repr
        else:
            repr2 = repr
        vlist = hop.inputargs(repr, repr2)

        hop.exception_cannot_occur()

        v_res = hop.genop(repr.opprefix+func, vlist, resulttype=repr)
        v_res = hop.llops.convertvar(v_res, repr, r_result)
        return v_res
rint._rtype_template = _rtype_template


_rint_rtype_compare_template = rint._rtype_compare_template
def _rtype_compare_template(hop, func):
    try:
        return _rint_rtype_compare_template(hop, func)
    except TyperError:
        s_int1, s_int2 = hop.args_s
        if (not (s_int1.unsigned or s_int2.unsigned)
            or not s_int1.nonneg or not s_int2.nonneg):
            raise TyperError("comparing small signed ints not implemented")

        repr = _wrap_repr
        vlist = hop.inputargs(repr, repr)
        hop.exception_is_here()
        return hop.genop(repr.opprefix + func, vlist, resulttype=Bool)
rint._rtype_compare_template = _rtype_compare_template


_rint_IntegerRepr_rtype_neg = rint.IntegerRepr.rtype_neg
def _rtype_neg(self, hop):
    try:
        return _rint_IntegerRepr_rtype_neg(self, hop)
    except TyperError:
        if not hop.s_result.unsigned:
            raise TyperError("neg(...) for small signed ints not implemented")
        self = self.as_int
        vlist = hop.inputargs(_wrap_repr)
        zero = _wrap_repr.lowleveltype._defl()
        vlist.insert(0, hop.inputconst(_wrap_repr.lowleveltype, zero))
        v_res = hop.genop(_wrap_repr.opprefix + 'sub', vlist, resulttype=_wrap_repr)
        return hop.llops.convertvar(v_res, _wrap_repr, self)
rint.IntegerRepr.rtype_neg = _rtype_neg


_rint_IntegerRepr_rtype_invert = rint.IntegerRepr.rtype_invert
def _rtype_invert(self, hop):
    try:
        return _rint_IntegerRepr_rtype_invert(self, hop)
    except TyperError:
        if not hop.s_result.unsigned:
            raise TyperError("invert(...) for small signed ints not implemented")
        self = self.as_int
        vlist = hop.inputargs(_wrap_repr)
        v_res = hop.genop(_wrap_repr.opprefix + 'invert', vlist, resulttype=_wrap_repr)
        return hop.llops.convertvar(v_res, _wrap_repr, self)
rint.IntegerRepr.rtype_invert = _rtype_invert
