; cat — посимвольно копирует порт 0 в порт 1, пока не встретит '\n'
.text
loop:   RD 0
        WR 1
        CMP (nl)
        BEZ (done)
        JMP (loop)
done:   HLT
.data
nl:     .word 10
