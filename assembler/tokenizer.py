
def tokenize(line, whitespace, op, comment):
    assert isinstance(line, str)

    op += comment

    tokens = []
    start, end = 0, 0
    while end < len(line):
        # skip whitespace
        while start < len(line) and line[start] in whitespace:
            start += 1

        # read up to whitespace or op
        end = start
        while end < len(line) and line[end] not in whitespace and line[end] not in op:
            end += 1

        # add non-op token if non-empty
        if start < end:
            tokens.append(line[start:end])

        # add ops
        while end < len(line) and line[end] in op:
            if line[end] in comment:
                return tokens
            tokens.append(line[end])
            end += 1

        # loop
        start = end

    return tokens
