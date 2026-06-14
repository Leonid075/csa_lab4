"""Golden-тесты: каждая программа из tests/<name>.asm ассемблируется,
исполняется на модели и сверяется с захардкоженным эталоном вывода.

Кейсы (входные буферы, лимиты и ожидаемый вывод по портам) заданы явно
в CASES — без чтения .yaml.
"""
import pathlib

import machine
from conftest import assemble

HERE = pathlib.Path(__file__).parent

# (имя, inputs, cfg, {порт: ожидаемый вывод})
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
        {1: [52, 32, 48]},  # "4 0"
    ),
    (
        "prob1",
        {},
        {"limit_ticks": 50_000_000, "limit_instructions": 5_000_000},
        {1: [9, 0, 6, 6, 0, 9]},  # цифры как числа, не ASCII
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
            f"{name}: порт {port} ожидалось {exp}, получено {got} "
            f"(останов: {res['stop']})"
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
