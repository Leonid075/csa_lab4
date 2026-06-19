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
