; dpsum — 64-битная сумма двух чисел (hi:lo) через ADD (младшие) + ADC (старшие).
; Печатает "hi lo" в десятичном виде. Демонстрирует перенос между словами.
.text
        LDIM 0x2000
        SSP
        LD (a_lo)
        ADD (b_lo)              ; младшие слова, выставляет C
        ST (r_lo)
        LD (a_hi)
        ADC (b_hi)              ; старшие + перенос (LD/ST не трогают C)
        ST (r_hi)
        LD (r_hi)
        CALL (print_decimal)
        LDIM 32                 ; ' '
        WR 1
        LD (r_lo)
        CALL (print_decimal)
        HLT

; print_decimal: печатает ACC (>=0) в десятичном ASCII в порт 1.
; Делит на 10, собирает цифры в dbuf, печатает в обратном порядке.
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
        ST (pdt)                ; (n/10)*10
        LD (pdn)
        SUB (pdt)               ; цифра = n - (n/10)*10
        ADDIM 48                ; '0' + цифра
        ST ([dp])
        LD (dp)
        ADDIM 4
        ST (dp)
        LD (dc)
        INC
        ST (dc)
        LD (pdq)
        ST (pdn)                ; n = n/10
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
