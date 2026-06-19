from conftest import check

SOURCE = """\
; cat — посимвольно копирует порт 0 в порт 1, пока не встретит '\\n'
.text
loop:   RD 0
        WR 1
        CMP (nl)
        BEZ (done)
        JMP (loop)
done:   HLT
.data
nl:     .word 10
"""


def test_cat():
    check(
        SOURCE,
        inputs={0: "Meow\n"},
        cfg={},
        expected={1: [77, 101, 111, 119, 10]},
    )
