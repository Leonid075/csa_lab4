from conftest import assemble, check, run_source

SOURCE = """\
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
"""


def test_org():
    check(
        SOURCE,
        inputs={},
        cfg={"start": 0x100},
        expected={1: [65, 66, 65]},
    )


def test_org_layout_is_sequential():
    """`.org` размещает данные/код по абсолютным адресам в порядке записи."""
    image = assemble(SOURCE)
    assert image[0x00:0x04] == bytes([0, 0, 0, 65])
    assert image[0x10:0x14] == bytes([0, 0, 0, 66])
    assert image[0x14:0x18] == bytes([0, 0, 0, 0x00])
    assert image[0x100] == 0x27


def test_org_entry_point_separates_code_from_data():
    """Точка входа отделяет код от данных в начале образа."""
    from_entry = run_source(SOURCE, cfg={"start": 0x100})
    assert from_entry["instructions"] == 7

    from_zero = run_source(SOURCE)
    assert from_zero["instructions"] > from_entry["instructions"]
