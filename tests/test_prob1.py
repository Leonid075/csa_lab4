from conftest import check

SOURCE = """\
; prob1 (Euler #4) — наибольший палиндром, равный произведению двух трёхзначных чисел.
.text
        LDIM 0x3000
        SSP
        LDIM 0
        ST (best)
        LDIM 999
        ST (a)
o_loop: LD (a)
        CMP (hundred)
        BLZ (done)
        LD (a)
        MUL (n999)
        CMP (best)
        BLZ (done)
        BEZ (done)
        LDIM 999
        ST (b)
i_loop: LD (b)
        CMP (a)
        BLZ (next_a)
        LD (a)
        MUL (b)
        ST (p)
        CMP (best)
        BLZ (next_a)
        BEZ (next_a)
        LD (p)
        ST (rvn)
        CALL (reverse)
        CMP (p)
        BEZ (is_pal)
        JMP (dec_b)
is_pal: LD (p)
        ST (best)
dec_b:  LD (b)
        DEC
        ST (b)
        JMP (i_loop)
next_a: LD (a)
        DEC
        ST (a)
        JMP (o_loop)
done:   LD (best)
        CALL (print_digits)
        HLT

reverse:
        LDIM 0
        ST (rev)
        LD (rvn)
        ST (rvm)
rv_l:   LD (rvm)
        BEZ (rv_d)
        DIV (ten)
        ST (rvq)
        MUL (ten)
        ST (rvt)
        LD (rvm)
        SUB (rvt)
        ST (rvdig)
        LD (rev)
        MUL (ten)
        ADD (rvdig)
        ST (rev)
        LD (rvq)
        ST (rvm)
        JMP (rv_l)
rv_d:   LD (rev)
        RET

print_digits:
        ST (pdn)
        LDIM dbuf
        ST (dp)
        LDIM 0
        ST (dc)
        LD (pdn)
        BEZ (pd_zero)
pd_div: LD (pdn)
        BEZ (pd_emit)
        DIV (ten)
        ST (pdq)
        MUL (ten)
        ST (pdt)
        LD (pdn)
        SUB (pdt)
        ST ([dp])
        LD (dp)
        ADDIM 4
        ST (dp)
        LD (dc)
        INC
        ST (dc)
        LD (pdq)
        ST (pdn)
        JMP (pd_div)
pd_emit:
        LD (dc)
        BEZ (pd_done)
        LD (dp)
        SUB (four)
        ST (dp)
        LD ([dp])
        WR 1
        LD (dc)
        DEC
        ST (dc)
        JMP (pd_emit)
pd_done:
        RET
pd_zero:
        LDIM 0
        WR 1
        RET

.data
best:   .word 0
a:      .word 0
b:      .word 0
p:      .word 0
n999:   .word 999
hundred:.word 100
ten:    .word 10
four:   .word 4
rev:    .word 0
rvm:    .word 0
rvq:    .word 0
rvt:    .word 0
rvdig:  .word 0
rvn:    .word 0
pdn:    .word 0
pdq:    .word 0
pdt:    .word 0
dc:     .word 0
dp:     .word 0
dbuf:   .word 0
"""


def test_prob1():
    check(
        SOURCE,
        inputs={},
        cfg={"limit_ticks": 50_000_000, "limit_instructions": 5_000_000},
        expected={1: [9, 0, 6, 6, 0, 9]},
    )
