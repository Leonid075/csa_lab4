import pathlib

import machine
from conftest import assemble

HERE = pathlib.Path(__file__).parent

# (name, inputs, cfg, assert)
CASES = [
    (
        "cat",
        {0: "Meow"},
        {},
        {1: [77, 101, 111, 119]},
    ),
    (
        "hello",
        {},
        {},
        {1: [72, 101, 108, 108, 111, 44, 32, 119, 111, 114, 108, 100, 33]},
    ),
    (
        "hello_user_name",
        {0: [73, 109, 101, 111, 110, 0]},
        {},
        {1: [72, 101, 108, 108, 111, 44, 32, 73, 109, 101, 111, 110, 33]},
    ),
    (
        "sort",
        {0: [5, 42, 7, 99, 13, 5]},
        {},
        {1: [5, 7, 13, 42, 99]},
    ),
    (
        "dpsum",
        {},
        {},
        {1: [52, 32, 48]},
    ),
    (
        "prob1",
        {},
        {"limit_ticks": 50_000_000, "limit_instructions": 5_000_000},
        {1: [9, 0, 6, 6, 0, 9]},
    ),
    (
        "macros",
        {},
        {},
        {1: [65, 66]},
    ),
    (
        "cond",
        {},
        {},
        {1: [66, 67]},
    ),
    (
        "org",
        {},
        {"start": 0x100},
        {1: [65, 66, 65]},
    ),
]


def run_case(name, inputs, cfg):
    image = assemble((HERE / f"{name}.asm").read_text(encoding="utf-8"))
    bufs = machine.parse_inputs({"inputs": inputs})
    return machine.simulate(image, bufs, cfg, log=lambda *a, **k: None)


def check(name, inputs, cfg, expected):
    res = run_case(name, inputs, cfg)
    for port, exp in expected.items():
        got = res["io"].out.get(port, [])
        assert got == exp, (
            f"{name}: порт {port} ожидалось {exp}, получено {got} (останов: {res['stop']})"
        )


def test_cat():
    check(*CASES[0])


def test_hello():
    check(*CASES[1])


def test_hello_user_name():
    check(*CASES[2])


def test_sort():
    check(*CASES[3])


def test_dpsum():
    check(*CASES[4])


def test_prob1():
    check(*CASES[5])


def test_macros():
    check(*CASES[6])


def test_cond():
    check(*CASES[7])


def test_org():
    check(*CASES[8])


def test_org_layout_is_sequential():
    """`.org` размещает данные/код по абсолютным адресам в порядке записи."""
    image = assemble((HERE / "org.asm").read_text(encoding="utf-8"))
    assert image[0x00:0x04] == bytes([0, 0, 0, 65])
    assert image[0x10:0x14] == bytes([0, 0, 0, 66])
    assert image[0x14:0x18] == bytes([0, 0, 0, 0x00])
    assert image[0x100] == 0x27


def test_org_entry_point_separates_code_from_data():
    """Точка входа отделяет код от данных в начале образа."""
    image = assemble((HERE / "org.asm").read_text(encoding="utf-8"))
    bufs = machine.parse_inputs({"inputs": {}})

    from_entry = machine.simulate(image, bufs, {"start": 0x100}, log=lambda *a, **k: None)
    assert from_entry["instructions"] == 7

    from_zero = machine.simulate(image, bufs, {}, log=lambda *a, **k: None)
    assert from_zero["instructions"] > from_entry["instructions"]
