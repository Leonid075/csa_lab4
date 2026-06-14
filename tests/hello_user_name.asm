; hello_user_name — читает имя из порта 0 (до байта-терминатора 0),
; печатает "Hello, " + имя + "!" в порт 1.
.text
        LDIM 0x2000
        SSP                     ; стек для CALL
        ; --- читаем имя в pstr-буфер buf ---
        LDIM 0
        ST (ncnt)               ; счётчик символов
        LDIM buf
        ADDIM 4
        ST (nptr)               ; nptr -> buf+4 (первый символ)
rd:     RD 0                    ; RD ставит N/Z
        BEZ (rd_end)            ; 0 -> конец имени
        ST ([nptr])
        LD (nptr)
        ADDIM 4
        ST (nptr)
        LD (ncnt)
        INC
        ST (ncnt)
        JMP (rd)
rd_end: LD (ncnt)
        ST (buf)                ; длина -> buf становится pstr
        ; --- печать: префикс, имя, суффикс ---
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

; print_pstr: печатает pstr, адрес которой лежит в (sarg)
print_pstr:
        LD ([sarg])             ; ACC = длина = mem[mem[sarg]]
        ST (pcnt)
        LD (sarg)
        ADDIM 4
        ST (pp)                 ; pp -> первый символ
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
buf:    .word 0                 ; длина имени; далее символы (растёт в нулевую память)
