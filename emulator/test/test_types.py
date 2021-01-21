from rpython.annotator.listdef import s_list_of_strings
from rpython.jit.metainterp.test.support import LLJitMixin
from rpython.rlib import rbigint
from rpython.rlib.jit import JitDriver
from rpython.translator.c.genc import CStandaloneBuilder
from rpython.translator.translator import TranslationContext

from emulator.test.conftest import option
from emulator.types import *


binop_d = {}
binop_l = []
def binop_f(op, a, b):
    return binop_l[op](a, b)
def def_binop(op):
    exec "def w(a, b):\n return a %s b" % op
    binop_d[op] = len(binop_l)
    binop_l.append(w)
def binop(f, op):
    i = binop_d[op]
    def impl(a, b):
        return f(i, a, b)
    return impl
def_binop('+')
def_binop('-')
def_binop('*')
# def_binop('/')
# def_binop('%')
def_binop('<<')
def_binop('>>')
def_binop('&')
def_binop('^')
def_binop('|')


cmpop_d = {}
cmpop_l = []
def cmpop_f(op, a, b):
    return cmpop_l[op](a, b)
def def_cmpop(op):
    exec """if 1:
    def w(a, b):
        if a %s b:
            return 1
        else:
            return 0""" % op
    cmpop_d[op] = len(cmpop_l)
    cmpop_l.append(w)
def cmpop(f, op):
    i = cmpop_d[op]
    def impl(a, b):
        r = f(i, a, b)
        if r == 1:
            return True
        elif r == 0:
            return False
        else:
            assert False, "unexpected return value: " + str(r)
    return impl
def_cmpop('<')
def_cmpop('<=')
def_cmpop('==')
def_cmpop('!=')
def_cmpop('>')
def_cmpop('>=')


unop_d = {}
unop_l = []
def unop_f(op, a):
    return unop_l[op](a)
def def_unop(op):
    exec "def w(a):\n return %sa" % op
    unop_d[op] = len(unop_l)
    unop_l.append(w)
def unop(f, op):
    i = unop_d[op]
    def impl(a):
        return f(i, a)
    return impl
def_unop('-')
def_unop('+')
# def_unop('abs(...)')
def_unop('~')


class TestEmulated:
    def compile(self, f, a, r):
        def wrap(*v):
            assert len(v) == len(a)
            for i, x in enumerate(v):
                assert type(x) is a[i]
            o = f(*v)
            assert type(o) is r
            return o
        return wrap

    def test_binop_uint8_uint8(self):
        f = self.compile(binop_f, [int, uint8_t, uint8_t], uint8_t)
        assert binop(f, '+')(uint8_t(255), uint8_t(255)) == uint8_t(254)
        assert binop(f, '-')(uint8_t(1), uint8_t(255)) == uint8_t(2)
        assert binop(f, '*')(uint8_t(255), uint8_t(255)) == uint8_t(1)
        # assert binop(f, '/')(uint8_t(255), uint8_t(2)) == uint8_t(127)
        # assert binop(f, '/')(uint8_t(255), uint8_t(255)) == uint8_t(1)
        # assert binop(f, '%')(uint8_t(255), uint8_t(4)) == uint8_t(3)
        # assert binop(f, '%')(uint8_t(255), uint8_t(254)) == uint8_t(1)
        assert binop(f, '<<')(uint8_t(255), uint8_t(0)) == uint8_t(255)
        assert binop(f, '<<')(uint8_t(255), uint8_t(2)) == uint8_t(252)
        assert binop(f, '<<')(uint8_t(255), uint8_t(8)) == uint8_t(0)
        assert binop(f, '>>')(uint8_t(255), uint8_t(0)) == uint8_t(255)
        assert binop(f, '>>')(uint8_t(255), uint8_t(2)) == uint8_t(63)
        assert binop(f, '>>')(uint8_t(255), uint8_t(8)) == uint8_t(0)
        assert binop(f, '&')(uint8_t(0xA5), uint8_t(0xAA)) == uint8_t(0xA0)
        assert binop(f, '^')(uint8_t(0xA5), uint8_t(0xAA)) == uint8_t(0x0F)
        assert binop(f, '|')(uint8_t(0xA5), uint8_t(0xAA)) == uint8_t(0xAF)

    def test_binop_uint16_uint16(self):
        f = self.compile(binop_f, [int, uint16_t, uint16_t], uint16_t)
        assert binop(f, '+')(uint16_t(2**16-1), uint16_t(2**16-1)) == uint16_t(2**16-2)
        assert binop(f, '-')(uint16_t(1), uint16_t(2**16-1)) == uint16_t(2)
        assert binop(f, '*')(uint16_t(2**16-1), uint16_t(2**16-1)) == uint16_t(1)
        # assert binop(f, '/')(uint16_t(2**16-1), uint16_t(2)) == uint16_t(2**15-1)
        # assert binop(f, '/')(uint16_t(2**16-1), uint16_t(2**16-1)) == uint16_t(1)
        # assert binop(f, '%')(uint16_t(2**16-1), uint16_t(4)) == uint16_t(3)
        # assert binop(f, '%')(uint16_t(2**16-1), uint16_t(2**16-2)) == uint16_t(1)
        assert binop(f, '<<')(uint16_t(2**16-1), uint16_t(0)) == uint16_t(2**16-1)
        assert binop(f, '<<')(uint16_t(2**16-1), uint16_t(2)) == uint16_t(2**16-4)
        assert binop(f, '<<')(uint16_t(2**16-1), uint16_t(15)) == uint16_t(2**15)
        assert binop(f, '>>')(uint16_t(2**16-1), uint16_t(0)) == uint16_t(2**16-1)
        assert binop(f, '>>')(uint16_t(2**16-1), uint16_t(2)) == uint16_t(2**14-1)
        assert binop(f, '>>')(uint16_t(2**16-1), uint16_t(15)) == uint16_t(1)
        assert binop(f, '&')(uint16_t(0xA5A5), uint16_t(0xAAAA)) == uint16_t(0xA0A0)
        assert binop(f, '^')(uint16_t(0xA5A5), uint16_t(0xAAAA)) == uint16_t(0x0F0F)
        assert binop(f, '|')(uint16_t(0xA5A5), uint16_t(0xAAAA)) == uint16_t(0xAFAF)

    def test_binop_uint32_uint32(self):
        f = self.compile(binop_f, [int, uint32_t, uint32_t], uint32_t)
        assert binop(f, '+')(uint32_t(2**32-1), uint32_t(2**32-1)) == uint32_t(2**32-2)
        assert binop(f, '-')(uint32_t(1), uint32_t(2**32-1)) == uint32_t(2)
        assert binop(f, '*')(uint32_t(2**32-1), uint32_t(2**32-1)) == uint32_t(1)
        # assert binop(f, '/')(uint32_t(2**32-1), uint32_t(2)) == uint32_t(2**31-1)
        # assert binop(f, '/')(uint32_t(2**32-1), uint32_t(2**32-1)) == uint32_t(1)
        # assert binop(f, '%')(uint32_t(2**32-1), uint32_t(4)) == uint32_t(3)
        # assert binop(f, '%')(uint32_t(2**32-1), uint32_t(2**32-2)) == uint32_t(1)
        assert binop(f, '<<')(uint32_t(2**32-1), uint32_t(0)) == uint32_t(2**32-1)
        assert binop(f, '<<')(uint32_t(2**32-1), uint32_t(2)) == uint32_t(2**32-4)
        assert binop(f, '<<')(uint32_t(2**32-1), uint32_t(31)) == uint32_t(2**31)
        assert binop(f, '>>')(uint32_t(2**32-1), uint32_t(0)) == uint32_t(2**32-1)
        assert binop(f, '>>')(uint32_t(2**32-1), uint32_t(2)) == uint32_t(2**30-1)
        assert binop(f, '>>')(uint32_t(2**32-1), uint32_t(31)) == uint32_t(1)
        assert binop(f, '&')(uint32_t(0xA5A5A5A5), uint32_t(0xAAAAAAAA)) == uint32_t(0xA0A0A0A0)
        assert binop(f, '^')(uint32_t(0xA5A5A5A5), uint32_t(0xAAAAAAAA)) == uint32_t(0x0F0F0F0F)
        assert binop(f, '|')(uint32_t(0xA5A5A5A5), uint32_t(0xAAAAAAAA)) == uint32_t(0xAFAFAFAF)

    def test_binop_uint64_uint64(self):
        f = self.compile(binop_f, [int, uint64_t, uint64_t], uint64_t)
        assert binop(f, '+')(uint64_t(2**64-1), uint64_t(2**64-1)) == uint64_t(2**64-2)
        assert binop(f, '-')(uint64_t(1), uint64_t(2**64-1)) == uint64_t(2)
        assert binop(f, '*')(uint64_t(2**64-1), uint64_t(2**64-1)) == uint64_t(1)
        # assert binop(f, '/')(uint64_t(2**64-1), uint64_t(2)) == uint64_t(2**63-1)
        # assert binop(f, '/')(uint64_t(2**64-1), uint64_t(2**64-1)) == uint64_t(1)
        # assert binop(f, '%')(uint64_t(2**64-1), uint64_t(4)) == uint64_t(3)
        # assert binop(f, '%')(uint64_t(2**64-1), uint64_t(2**64-2)) == uint64_t(1)
        assert binop(f, '<<')(uint64_t(2**64-1), uint64_t(0)) == uint64_t(2**64-1)
        assert binop(f, '<<')(uint64_t(2**64-1), uint64_t(2)) == uint64_t(2**64-4)
        assert binop(f, '<<')(uint64_t(2**64-1), uint64_t(63)) == uint64_t(2**63)
        assert binop(f, '>>')(uint64_t(2**64-1), uint64_t(0)) == uint64_t(2**64-1)
        assert binop(f, '>>')(uint64_t(2**64-1), uint64_t(2)) == uint64_t(2**62-1)
        assert binop(f, '>>')(uint64_t(2**64-1), uint64_t(63)) == uint64_t(1)
        assert binop(f, '&')(uint64_t(0xA5A5A5A5A5A5A5A5), uint64_t(0xAAAAAAAAAAAAAAAA))\
               == uint64_t(0xA0A0A0A0A0A0A0A0)
        assert binop(f, '^')(uint64_t(0xA5A5A5A5A5A5A5A5), uint64_t(0xAAAAAAAAAAAAAAAA))\
               == uint64_t(0x0F0F0F0F0F0F0F0F)
        assert binop(f, '|')(uint64_t(0xA5A5A5A5A5A5A5A5), uint64_t(0xAAAAAAAAAAAAAAAA))\
               == uint64_t(0xAFAFAFAFAFAFAFAF)

    def test_cmpop_uint8_uint8(self):
        f = self.compile(cmpop_f, [int, uint8_t, uint8_t], int)
        assert cmpop(f, '<')(uint8_t(254), uint8_t(253)) == False
        assert cmpop(f, '<')(uint8_t(254), uint8_t(254)) == False
        assert cmpop(f, '<')(uint8_t(254), uint8_t(255)) == True
        assert cmpop(f, '<=')(uint8_t(254), uint8_t(253)) == False
        assert cmpop(f, '<=')(uint8_t(254), uint8_t(254)) == True
        assert cmpop(f, '<=')(uint8_t(254), uint8_t(255)) == True
        assert cmpop(f, '==')(uint8_t(254), uint8_t(253)) == False
        assert cmpop(f, '==')(uint8_t(254), uint8_t(254)) == True
        assert cmpop(f, '==')(uint8_t(254), uint8_t(255)) == False
        assert cmpop(f, '!=')(uint8_t(254), uint8_t(253)) == True
        assert cmpop(f, '!=')(uint8_t(254), uint8_t(254)) == False
        assert cmpop(f, '!=')(uint8_t(254), uint8_t(255)) == True
        assert cmpop(f, '>')(uint8_t(254), uint8_t(253)) == True
        assert cmpop(f, '>')(uint8_t(254), uint8_t(254)) == False
        assert cmpop(f, '>')(uint8_t(254), uint8_t(255)) == False
        assert cmpop(f, '>=')(uint8_t(254), uint8_t(253)) == True
        assert cmpop(f, '>=')(uint8_t(254), uint8_t(254)) == True
        assert cmpop(f, '>=')(uint8_t(254), uint8_t(255)) == False

    def test_cmpop_uint16_uint16(self):
        f = self.compile(cmpop_f, [int, uint16_t, uint16_t], int)
        assert cmpop(f, '<')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == False
        assert cmpop(f, '<')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == False
        assert cmpop(f, '<')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == True
        assert cmpop(f, '<=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == False
        assert cmpop(f, '<=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == True
        assert cmpop(f, '<=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == True
        assert cmpop(f, '==')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == False
        assert cmpop(f, '==')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == True
        assert cmpop(f, '==')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == False
        assert cmpop(f, '!=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == True
        assert cmpop(f, '!=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == False
        assert cmpop(f, '!=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == True
        assert cmpop(f, '>')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == True
        assert cmpop(f, '>')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == False
        assert cmpop(f, '>')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == False
        assert cmpop(f, '>=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 3)) == True
        assert cmpop(f, '>=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 2)) == True
        assert cmpop(f, '>=')(uint16_t(2 ** 16 - 2), uint16_t(2 ** 16 - 1)) == False

    def test_cmpop_uint32_uint32(self):
        f = self.compile(cmpop_f, [int, uint32_t, uint32_t], int)
        assert cmpop(f, '<')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == False
        assert cmpop(f, '<')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == False
        assert cmpop(f, '<')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == True
        assert cmpop(f, '<=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == False
        assert cmpop(f, '<=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == True
        assert cmpop(f, '<=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == True
        assert cmpop(f, '==')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == False
        assert cmpop(f, '==')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == True
        assert cmpop(f, '==')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == False
        assert cmpop(f, '!=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == True
        assert cmpop(f, '!=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == False
        assert cmpop(f, '!=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == True
        assert cmpop(f, '>')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == True
        assert cmpop(f, '>')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == False
        assert cmpop(f, '>')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == False
        assert cmpop(f, '>=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 3)) == True
        assert cmpop(f, '>=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 2)) == True
        assert cmpop(f, '>=')(uint32_t(2 ** 32 - 2), uint32_t(2 ** 32 - 1)) == False

    def test_cmpop_uint64_uint64(self):
        f = self.compile(cmpop_f, [int, uint64_t, uint64_t], int)
        assert cmpop(f, '<')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == False
        assert cmpop(f, '<')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == False
        assert cmpop(f, '<')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == True
        assert cmpop(f, '<=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == False
        assert cmpop(f, '<=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == True
        assert cmpop(f, '<=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == True
        assert cmpop(f, '==')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == False
        assert cmpop(f, '==')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == True
        assert cmpop(f, '==')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == False
        assert cmpop(f, '!=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == True
        assert cmpop(f, '!=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == False
        assert cmpop(f, '!=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == True
        assert cmpop(f, '>')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == True
        assert cmpop(f, '>')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == False
        assert cmpop(f, '>')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == False
        assert cmpop(f, '>=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 3)) == True
        assert cmpop(f, '>=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 2)) == True
        assert cmpop(f, '>=')(uint64_t(2 ** 64 - 2), uint64_t(2 ** 64 - 1)) == False

    def test_unop_uint8(self):
        f = self.compile(unop_f, [int, uint8_t], uint8_t)
        assert unop(f, '+')(uint8_t(255)) == uint8_t(255)
        assert unop(f, '-')(uint8_t(255)) == uint8_t(1)
        assert unop(f, '-')(uint8_t(1)) == uint8_t(255)
        assert unop(f, '~')(uint8_t(0xAA)) == uint8_t(0x55)
        assert unop(f, '~')(uint8_t(0x55)) == uint8_t(0xAA)

    def test_unop_uint16(self):
        f = self.compile(unop_f, [int, uint16_t], uint16_t)
        assert unop(f, '+')(uint16_t(2**16-1)) == uint16_t(2**16-1)
        assert unop(f, '-')(uint16_t(2**16-1)) == uint16_t(1)
        assert unop(f, '-')(uint16_t(1)) == uint16_t(2**16-1)
        assert unop(f, '~')(uint16_t(0xAAAA)) == uint16_t(0x5555)
        assert unop(f, '~')(uint16_t(0x5555)) == uint16_t(0xAAAA)

    def test_unop_uint32(self):
        f = self.compile(unop_f, [int, uint32_t], uint32_t)
        assert unop(f, '+')(uint32_t(2**32-1)) == uint32_t(2**32-1)
        assert unop(f, '-')(uint32_t(2**32-1)) == uint32_t(1)
        assert unop(f, '-')(uint32_t(1)) == uint32_t(2**32-1)
        assert unop(f, '~')(uint32_t(0xAAAAAAAA)) == uint32_t(0x55555555)
        assert unop(f, '~')(uint32_t(0x55555555)) == uint32_t(0xAAAAAAAA)

    def test_unop_uint64(self):
        f = self.compile(unop_f, [int, uint64_t], uint64_t)
        assert unop(f, '+')(uint64_t(2**64-1)) == uint64_t(2**64-1)
        assert unop(f, '-')(uint64_t(2**64-1)) == uint64_t(1)
        assert unop(f, '-')(uint64_t(1)) == uint64_t(2**64-1)
        assert unop(f, '~')(uint64_t(0xAAAAAAAAAAAAAAAA)) == uint64_t(0x5555555555555555)
        assert unop(f, '~')(uint64_t(0x5555555555555555)) == uint64_t(0xAAAAAAAAAAAAAAAA)


class TestTranslated(TestEmulated):
    def compile(self, f, a, r):
        a = [rarithmetic.intmask if x is int else x for x in a]
        l = {'f': f, 'a': a, 'r': r,
             'rbigint': rbigint.rbigint,
             'unsigned': unsigned}
        exec("""def entrypoint(argv):
                    assert len(argv) == 1 + len(a)
                    o = f(%s)
                    assert isinstance(o, r)
                    print str(unsigned(o))
                    return 0""" % (",".join("a[%d](rbigint.fromstr(argv[%d]).ulonglongmask())" % (i,1+i) for i in xrange(len(a)))), l)
        def compile(entry_point):
            t = TranslationContext()
            ann = t.buildannotator()
            ann.build_types(entry_point, [s_list_of_strings])
            t.buildrtyper().specialize()
            cbuilder = CStandaloneBuilder(t, entry_point, t.config)
            cbuilder.generate_source()
            cbuilder.compile()
            if option is not None and option.view:
                t.view()
            return t, cbuilder
        t, cbuilder = compile(l['entrypoint'])
        def cmdexec(*v):
            o = cbuilder.cmdexec([str(x) for x in v])
            return r(unsigned(o))
        return cmdexec


class TestJitted(TestEmulated, LLJitMixin):
    def compile(self, f, a, r):
        l = {'f': f, 'a': a, 'r': r,
             'JitDriver': JitDriver}
        arg_list = ",".join("i%d" % i for i in xrange(len(a)))
        green_list = ",".join("'i%d'" % i for i in xrange(len(a)) if a[i] is int)
        red_list = ",".join("'i%d'" % i for i in xrange(len(a)) if a[i] is not int)
        kwarg_list = ",".join("i%d=i%d" % (i,i) for i in xrange(len(a)))
        exec("""if 1:
        driver = JitDriver(greens=[%s], reds=['it', %s])
        def entrypoint(%s, it):
            res = r(0)
            while it > 0:
                driver.can_enter_jit(it=it, %s)
                driver.jit_merge_point(it=it, %s)
                res = f(%s)
                it -= 1
            return res""" % (green_list, red_list, arg_list,
                             kwarg_list, kwarg_list, arg_list), l)
        def run(*v):
            arg = list(v)
            arg.append(7)
            res = self.meta_interp(l['entrypoint'], arg, backendopt=True, inline=True)
            self.check_trace_count(1)
            return res
        return run

