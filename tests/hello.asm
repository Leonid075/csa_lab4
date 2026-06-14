; hello — печать статической строки "Hello, world!" в порт 1
.text
        LD (msg)            ; ACC = длина (слово длины pstr)
        ST (cnt)
        LDIM msg
        ADDIM 4
        ST (ptr)            ; ptr -> первый символ
loop:   LD (cnt)
        BEZ (done)
        LD ([ptr])          ; ACC = символ
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
