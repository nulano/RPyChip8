from assembler.tokenizer import tokenize as _tokenize

whitespace = " \t\n\r"
op = ",:"
comment = "#;"


def tokenize(line):
    return _tokenize(line, whitespace=whitespace, op=op, comment=comment)


class const:
    def __init__(self, target):
        self.target = target

    def accept(self, token):
        return token == self.target

    def parse(self, token, line, labels):
        assert self.accept(token)
        return 0


class label:
    def accept(self, token):
        for c in token:
            if c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
                return False
        return True

    def parse(self, token, line, labels):
        return labels[token]
label = label()


class num:
    def __init__(self, nibbles):
        self.nibbles = nibbles

    def accept(self, token):
        try:
            self.parse(token)
            return True
        except ValueError:
            return False

    def parse(self, token, line=0, labels={}):
        if token[0:2] != "0x" and token[-1] in "bB":
            val = int(token[:-1], base=2)
        elif token[-1] in "oO":
            val = int(token[:-1], base=8)
        elif token[-1] in "hH":
            val = int(token[:-1], base=16)
        else:
            val = int(token, base=0)
        if val < 0:
            raise ValueError, "number constant negative"
        if val >= (1 << (4 * self.nibbles)):
            raise ValueError, "number constant too large"
        return val
num1 = num(1)
num2 = num(2)
num3 = num(3)
num4 = num(4)


class group:
    def __init__(self, *options):
        self.options = options

    def accept(self, token):
        for x in self.options:
            if x.accept(token):
                return True
        return False

    def parse(self, token, line, labels):
        for x in self.options:
            if x.accept(token):
                return x.parse(token, line, labels)
        raise ValueError(token)
addr_exact = group(num3, label)


class offset:
    def accept(self, token):
        if token[0:2] == "$+" or token[0:2] == "$-":
            return addr_exact.accept(token[2:])
        return token == "$"

    def parse(self, token, line, labels):
        off = 0
        if token[0:2] == "$+":
            off = addr_exact.parse(token[2:], line, labels)
        elif token[0:2] == "$-":
            off = -addr_exact.parse(token[2:], line, labels)
        val = off + line
        if val < 0:
            raise ValueError, "computed position negative"
        if val > 0xFFF:
            raise ValueError, "computed position overflow"
        return val
offset = offset()
addr = group(offset, addr_exact)


class reg:
    def __init__(self, mask):
        self.mask = mask

    def accept(self, token):
        return token[0] == "V" and token[1] in "0123456789ABCDEF" and len(token) == 2

    def parse(self, token, line, labels):
        val = int(token[1], 16)
        return val * self.mask
reg1 = reg(0x0100)
reg2 = reg(0x0010)
reg3 = reg(0x0001)
reg12 = reg(0x0110)


class special:
    def __init__(self, name, synonymous, synonym):
        self.name = name
        self.synonymous = synonymous
        self.synonym = synonym
        assert synonymous.accept(synonym)

    def accept(self, token):
        return token == self.name

    def parse(self, token, line, labels):
        return self.synonymous.parse(self.synonym, line, labels)


matchers = {
    'word': num4,
    'addr': addr,
    'byte': num2,
    'nib': num1,
    'Vx': reg1,
    'Vy': reg2,
    'Vxy': reg12,
    'HLT': special('HLT', offset, '$'),
}

_specification = {
    'CLS':                  0x00E0,
    'RET':                  0x00EE,
    'SYS addr':             0x0000,
    'HLT':                  0x1000,  # alternative for 'JP $'
    'JP addr':              0x1000,
    # 'J addr':               0x1000,  # alternative spelling
    'CALL addr':            0x2000,
    'SE Vx, byte':          0x3000,
    'IFNE Vx, byte':        0x3000,  # alternative spelling
    'SNE Vx, byte':         0x4000,
    'IFEQ Vx, byte':        0x4000,  # alternative spelling
    'SE Vx, Vy':            0x5000,
    'IFNE Vx, Vy':          0x5000,  # alternative spelling
    'LD Vx, byte':          0x6000,
    'ADD Vx, byte':         0x7000,
    'LD Vx, Vy':            0x8000,
    # 'L Vx, Vy':             0x8000,  # alternative spelling
    'OR Vx, Vy':            0x8001,
    'AND Vx, Vy':           0x8002,
    'XOR Vx, Vy':           0x8003,
    'ADD Vx, Vy':           0x8004,
    'SUB Vx, Vy':           0x8005,
    'SHR Vx, Vy':           0x8006,
    'SHR Vxy':              0x8006,  # alternative, source == dest
    'SUBN Vx, Vy':          0x8007,
    'SHL Vx, Vy':           0x800E,
    'SHL Vxy':              0x800E,  # alternative, source == dest
    'SNE Vx, Vy':           0x9000,
    'IFEQ Vx, Vy':          0x9000,  # alternative spelling
    'LD I, addr':           0xA000,
    # 'L I, addr':            0xA000,  # alternative spelling
    'JP V0, addr':          0xB000,
    # 'J V0, addr':           0xB000,  # alternative spelling
    'RND Vx, byte':         0xC000,
    'DRW Vx, Vy, nib':      0xD000,
    'SKP Vx':               0xE09E,
    'IFUP Vx':              0xE09E,  # alternative spelling
    'SKNP Vx':              0xE0A1,
    'IFDN Vx':              0xE0A1,  # alternative spelling
    'LD Vx, DT':            0xF007,
    'LD Vx, K':             0xF00A,
    'LD DT, Vx':            0xF015,
    'LD ST, Vx':            0xF018,
    'ADD I, Vx':            0xF01E,
    'LD F, Vx':             0xF029,
    'LD B, Vx':             0xF033,
    'LD [I], Vx':           0xF055,
    'LD Vx, [I]':           0xF065,
    # constant must be last
    'DW word':              0,
}

specification = []
for _k, _v in _specification.iteritems():
    _matchers = []
    _toks = tokenize(_k)
    for _t in _toks:
        try:
            _m = matchers[_t]
        except KeyError:
            _m = const(_t)
        _matchers.append(_m)
    specification.append((_matchers, _v))
del _specification


def assemble(lines, base=0x200):
    labels = {}
    ops = []
    for line in lines:
        tokens = tokenize(line)
        if len(tokens) == 0:
            continue
        for spec_tokens, spec_id in specification:
            if len(tokens) != len(spec_tokens):
                continue
            i = 0
            while i < len(tokens):
                if not spec_tokens[i].accept(tokens[i]):
                    break
                i += 1
            else:
                ops.append((tokens, spec_tokens, spec_id))
                break
        else:
            if len(tokens) == 2 and label.accept(tokens[0]) and tokens[1] == ":":
                labels[tokens[0]] = len(ops) * 2 + base
            elif len(tokens) == 2 and tokens[0] == ".org" and num3.accept(tokens[1]):
                org = (num3.parse(tokens[1]) - base) // 2
                if org < len(ops):
                    raise ValueError, ".org too small"
                while len(ops) < org:
                    ops.append(([], [], 0))
            else:
                raise ValueError, "unrecognized: " + line
    out = ""
    for tokens, spec_tokens, spec_id in ops:
        assert len(tokens) == len(spec_tokens)
        val = spec_id
        i = 0
        while i < len(tokens):
            val |= spec_tokens[i].parse(tokens[i], len(out) + base, labels)
            i += 1
        out += chr(val >> 8)
        out += chr(val & 0xFF)
    return out
