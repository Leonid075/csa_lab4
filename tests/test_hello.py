from conftest import check

SOURCE = """\
; hello — печать "Hello, world!" в порт 1
.text
        LD (msg)
        ST (cnt)
        LDIM msg
        ADDIM 4
        ST (ptr)
loop:   LD (cnt)
        BEZ (done)
        LD ([ptr])
        WR 1
        LD (ptr)
        ADDIM 4
        ST (ptr)
        LD (cnt)
        DEC
        ST (cnt)
        JMP (loop)
done:   HLT
.data
msg:    .str "Hello, world!"
cnt:    .word 0
ptr:    .word 0
"""


def test_hello():
    check(
        SOURCE,
        inputs={},
        cfg={},
        expected={1: [72, 101, 108, 108, 111, 44, 32, 119, 111, 114, 108, 100, 33]},
    )
