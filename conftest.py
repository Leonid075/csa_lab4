import io

import assembler


def assemble(source: str) -> bytes:
    out = io.BytesIO()
    assembler.translate(io.StringIO(source), out)
    return out.getvalue()
