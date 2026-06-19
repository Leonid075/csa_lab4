; dpsum — 64-битная сумма двух чисел.
.text
        LDIM 0x2000
        SSP
        LD (a_lo)
        ADD (b_lo)
        ST (r_lo)
        LD (a_hi)
        ADC (b_hi)
        ST (r_hi)
        LD (r_hi)
        CALL (print_decimal)
        LDIM 32
        WR 1
        LD (r_lo)
        CALL (print_decimal)
        HLT

print_decimal:
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
        ADDIM 48
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
        LDIM 48
        WR 1
        RET

.data
a_hi:   .word 0x00000001
a_lo:   .word 0xFFFFFFFF
b_hi:   .word 0x00000002
b_lo:   .word 0x00000001
r_hi:   .word 0
r_lo:   .word 0
ten:    .word 10
four:   .word 4
pdn:    .word 0
pdq:    .word 0
pdt:    .word 0
dc:     .word 0
dp:     .word 0
dbuf:   .word 0
