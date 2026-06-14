; prob1 (Euler #4) — наибольший палиндром, равный произведению двух трёхзначных
; чисел. Ответ: 906609 = 913 * 993.
;
; Перебор с отсечениями: a от 999 вниз; b от 999 вниз до a (b >= a, без дублей).
; Произведения a*b убывают => как только a*b <= best, внутренний цикл прерывается.
; Если максимум для текущего a (a*999) уже <= best — внешний цикл завершается.
.text
        LDIM 0x3000
        SSP                     ; стек для CALL
        LDIM 0
        ST (best)
        LDIM 999
        ST (a)
o_loop: LD (a)
        CMP (hundred)
        BLZ (done)              ; a < 100 -> конец
        LD (a)
        MUL (n999)              ; a*999 — максимум для этого a
        CMP (best)
        BLZ (done)              ; a*999 < best  -> улучшить нельзя
        BEZ (done)              ; a*999 == best
        LDIM 999
        ST (b)
i_loop: LD (b)
        CMP (a)
        BLZ (next_a)            ; b < a -> к следующему a
        LD (a)
        MUL (b)                 ; p = a*b
        ST (p)
        CMP (best)
        BLZ (next_a)            ; p < best -> прервать внутренний (дальше только меньше)
        BEZ (next_a)            ; p == best
        ; палиндром?
        LD (p)
        ST (rvn)
        CALL (reverse)          ; ACC = развёрнутое(p)
        CMP (p)
        BEZ (is_pal)
        JMP (dec_b)
is_pal: LD (p)
        ST (best)               ; p > best (проверено) и палиндром
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

; reverse: (rvn) -> ACC = число с обратным порядком десятичных цифр
reverse:
        LDIM 0
        ST (rev)
        LD (rvn)
        ST (rvm)
rv_l:   LD (rvm)
        BEZ (rv_d)
        DIV (ten)
        ST (rvq)                ; q = m/10
        MUL (ten)
        ST (rvt)
        LD (rvm)
        SUB (rvt)               ; цифра = m - (m/10)*10
        ST (rvdig)
        LD (rev)
        MUL (ten)
        ADD (rvdig)
        ST (rev)                ; rev = rev*10 + цифра
        LD (rvq)
        ST (rvm)
        JMP (rv_l)
rv_d:   LD (rev)
        RET

; print_digits: печатает ACC (>=0) по одной десятичной цифре в порт 1.
; Цифры выводятся как числа 0..9 (без ASCII-смещения).
; Делит на 10, собирает цифры в dbuf, печатает в обратном порядке.
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
        ST (pdt)                ; (n/10)*10
        LD (pdn)
        SUB (pdt)               ; цифра = n - (n/10)*10
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
