from conftest import check

SOURCE = """\
; cond — проверка условной трансляции: #ifdef / #ifndef / #else / #endif
#define FEATURE_B
.text
#ifdef FEATURE_B
        LDIM 66
        WR 1
#endif
#ifndef FEATURE_B
        LDIM 88
        WR 1
#endif
#ifdef FEATURE_A
        LDIM 65
#else
        LDIM 67
#endif
        WR 1
        HLT
"""


def test_cond():
    check(
        SOURCE,
        inputs={},
        cfg={},
        expected={1: [66, 67]},
    )
