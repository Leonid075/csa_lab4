from conftest import check

SOURCE = """\
; hello_user_name — читает имя из порта 0 (до байта-терминатора 0),
; печатает "Hello, " + имя + "!" в порт 1.
.text
        LDIM 0x2000
        SSP
        LDIM 0
        ST (ncnt)
        LDIM buf
        ADDIM 4
        ST (nptr)
rd:     RD 0
        BEZ (rd_end)
        ST ([nptr])
        LD (nptr)
        ADDIM 4
        ST (nptr)
        LD (ncnt)
        INC
        ST (ncnt)
        JMP (rd)
rd_end: LD (ncnt)
        ST (buf)
        LDIM pre
        ST (sarg)
        CALL (print_pstr)
        LDIM buf
        ST (sarg)
        CALL (print_pstr)
        LDIM suf
        ST (sarg)
        CALL (print_pstr)
        HLT

print_pstr:
        LD ([sarg])
        ST (pcnt)
        LD (sarg)
        ADDIM 4
        ST (pp)
pp_l:   LD (pcnt)
        BEZ (pp_d)
        LD ([pp])
        WR 1
        LD (pp)
        ADDIM 4
        ST (pp)
        LD (pcnt)
        DEC
        ST (pcnt)
        JMP (pp_l)
pp_d:   RET

.data
pre:    .str "Hello, "
suf:    .str "!"
sarg:   .word 0
pcnt:   .word 0
pp:     .word 0
ncnt:   .word 0
nptr:   .word 0
buf:    .word 0
"""


def test_hello_user_name():
    check(
        SOURCE,
        inputs={0: [73, 109, 101, 111, 110, 0]},
        cfg={},
        expected={1: [72, 101, 108, 108, 111, 44, 32, 73, 109, 101, 111, 110, 33]},
    )
