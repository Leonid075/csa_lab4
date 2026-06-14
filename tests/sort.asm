; sort — читает N (порт 0), затем N байт, сортирует по возрастанию (беззнаково),
; выводит N отсортированных байт в порт 1.
.text
        ; --- читаем количество ---
        RD 0
        ST (n)
        ; --- читаем N значений в arr ---
        LDIM arr
        ST (ptr)
        LD (n)
        ST (cnt)
rd_l:   LD (cnt)
        BEZ (rd_d)
        RD 0
        ST ([ptr])
        LD (ptr)
        ADDIM 4
        ST (ptr)
        LD (cnt)
        DEC
        ST (cnt)
        JMP (rd_l)
rd_d:
        ; --- пузырьковая сортировка ---
        LD (n)
        DEC
        ST (outer)              ; outer = n-1 проходов
out_l:  LD (outer)
        BEZ (sorted)
        LD (n)
        DEC
        ST (inner)              ; inner = n-1 сравнений
        LDIM arr
        ST (jp)
in_l:   LD (inner)
        BEZ (in_d)
        LD (jp)
        ADDIM 4
        ST (jn)                 ; jn -> следующий элемент
        LD ([jp])
        CMP ([jn])              ; arr[j] - arr[j+1]
        BCC (no_sw)             ; arr[j] < arr[j+1] -> не менять
        BEZ (no_sw)             ; равны -> не менять
        ; обмен
        LD ([jp])
        ST (tmp)
        LD ([jn])
        ST ([jp])
        LD (tmp)
        ST ([jn])
no_sw:  LD (jp)
        ADDIM 4
        ST (jp)
        LD (inner)
        DEC
        ST (inner)
        JMP (in_l)
in_d:   LD (outer)
        DEC
        ST (outer)
        JMP (out_l)
sorted:
        ; --- вывод ---
        LDIM arr
        ST (ptr)
        LD (n)
        ST (cnt)
wr_l:   LD (cnt)
        BEZ (fin)
        LD ([ptr])
        WR 1
        LD (ptr)
        ADDIM 4
        ST (ptr)
        LD (cnt)
        DEC
        ST (cnt)
        JMP (wr_l)
fin:    HLT
.data
n:      .word 0
cnt:    .word 0
ptr:    .word 0
outer:  .word 0
inner:  .word 0
jp:     .word 0
jn:     .word 0
tmp:    .word 0
arr:    .word 0                 ; начало массива (растёт в нулевую память)
