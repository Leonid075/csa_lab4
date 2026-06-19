; org — проверка .org, последовательной раскладки и точки входа
.data
        .org 0x00
val1:   .word 65
        .org 0x10
val2:   .word 66
ptr:    .word val1

.text
        .org 0x100
        LD (val1)
        WR 1
        LD (val2)
        WR 1
        LD ([ptr])
        WR 1
        HLT
