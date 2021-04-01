import btype


class Range(btype.Struct):
    begin = btype.uint64_t()
    end   = btype.uint64_t()
    elems = btype.Array(btype.uint8_t(), 4)


class Foo(btype.Struct):
    checksum  = btype.uint64_t()
    signature = btype.uint64_t(0x12345678)
    date      = btype.CString(20)
    count     = btype.uint64_t(1)
    r         = Range(begin=1, end=2)
    r2        = Range(begin=3, end=4)
    ranges    = btype.Array(Range(), 3)
    a         = btype.Array(btype.uint64_t(), 10)
    hz        = btype.float64_t()
    freq      = btype.float32_t()
