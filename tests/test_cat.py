from conftest import check

SOURCE = """\
; cat — посимвольно копирует порт 0 в порт 1, пока есть вход
.text
loop:   RD 0
        WR 1
        JMP (loop)
"""


def test_cat():
    check(
        SOURCE,
        inputs={0: "Meow"},
        cfg={},
        expected={1: [77, 101, 111, 119]},
    )
