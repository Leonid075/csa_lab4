import io

import assembler
import machine


def assemble(source: str) -> bytes:
    out = io.BytesIO()
    assembler.translate(io.StringIO(source), out)
    return out.getvalue()


def run_source(source, inputs=None, cfg=None):
    image = assemble(source)
    bufs = machine.parse_inputs({"inputs": inputs or {}})
    return machine.simulate(image, bufs, cfg or {}, log=lambda *a, **k: None)


def check(source, inputs, cfg, expected):
    res = run_source(source, inputs, cfg)
    for port, exp in expected.items():
        got = res["io"].out.get(port, [])
        assert got == exp, f"порт {port} ожидалось {exp}, получено {got} (останов: {res['stop']})"
    return res
