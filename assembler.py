import argparse
import io
import os
import re

ASM = {
    "AND": ["addr", "00000111"],
    "OR": ["addr", "00000110"],
    "XOR": ["addr", "00000101"],
    "NOT": ["noarg", "00000011"],
    "NEG": ["noarg", "00000010"],
    "INC": ["noarg", "00000001"],
    "DEC": ["noarg", "00000000"],
    "ADD": ["addr", "00001111"],
    "SUB": ["addr", "00001110"],
    "MUL": ["addr", "00001101"],
    "DIV": ["addr", "00001100"],
    "ADC": ["addr", "00001011"],
    "CMP": ["addr", "00001010"],
    "SHL": ["noarg", "00010111"],
    "SHR": ["noarg", "00010110"],
    "ASL": ["noarg", "00010101"],
    "ASR": ["noarg", "00010100"],
    "CLO": ["noarg", "00010011"],
    "CLC": ["noarg", "00010010"],
    "JMP": ["label", "00011111"],
    "BEZ": ["label", "00011110"],
    "BLZ": ["label", "00011101"],
    "BGZ": ["label", "00011100"],
    "BCS": ["label", "00011011"],
    "BOS": ["label", "00011010"],
    "BCC": ["label", "00011001"],
    "BOC": ["label", "00011000"],
    "LD": ["addr", "00100111"],
    "ST": ["addr", "00100110"],
    "RD": ["byteaddr", "00100101"],
    "WR": ["byteaddr", "00100100"],
    "CALL": ["label", "00101111"],
    "RET": ["noarg", "00101110"],
    "SSP": ["noarg", "00101101"],
    "LDIM": ["value", "00110111"],
    "ADDIM": ["value", "00110110"],
    "HLT": ["noarg", "00111111"],
}

I_SIZE = {
    "noarg": 1,
    "addr": 5,
    "label": 5,
    "value": 4,
    "byteaddr": 4,
}

NUM_IO_PORTS = 8

STR_RE = re.compile(r'\.str\s+"((?:[^"\\]|\\.)*)"')
LABEL_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*")


def parse_value(s: str) -> int:
    """Parse dec or hex string to int."""
    s = s.strip()
    if s.startswith("0x") or s.startswith("0X"):
        return int(s, 16)
    return int(s, 10)


def strip_comment(line: str) -> str:
    """Remove inline comments."""
    in_string = False
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if in_string:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c == ";":
                return line[:i].strip()
        i += 1
    return line.strip()


def preprocess(lines: list[str]) -> list[str]:
    """Handle C-preprocessor-style directives."""
    defines: dict[str, str] = {}
    result: list[str] = []
    condition_stack: list[tuple[bool, bool]] = []

    def is_active() -> bool:
        return all(active for active, _ in condition_stack)

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("#define"):
            if is_active():
                parts = stripped.split(None, 2)
                name = parts[1]
                value = parts[2] if len(parts) > 2 else ""
                defines[name] = value
            continue

        if stripped.startswith("#ifdef"):
            parts = stripped.split(None, 1)
            name = parts[1].strip() if len(parts) > 1 else ""
            active = is_active() and name in defines
            condition_stack.append((active, active))
            continue

        if stripped.startswith("#ifndef"):
            parts = stripped.split(None, 1)
            name = parts[1].strip() if len(parts) > 1 else ""
            active = is_active() and name not in defines
            condition_stack.append((active, active))
            continue

        if stripped.startswith("#endif"):
            if condition_stack:
                condition_stack.pop()
            continue

        if stripped.startswith("#else"):
            if condition_stack:
                prev_active, prev_satisfied = condition_stack[-1]
                parent_active = all(a for a, _ in condition_stack[:-1])
                new_active = parent_active and not prev_satisfied
                condition_stack[-1] = (new_active, prev_satisfied or new_active)
            continue

        if not is_active():
            continue

        for name in sorted(defines.keys(), key=len, reverse=True):
            line = _subst_outside_strings(line, name, defines[name])

        result.append(line)

    return result


def _subst_outside_strings(line: str, name: str, value: str) -> str:
    """Replace whole-word `name` with `value`, but never inside a string literal."""
    pattern = re.compile(r'"(?:\\.|[^"\\])*"|"(?:\\.|[^"\\])*$|\b' + re.escape(name) + r"\b")

    def repl(m: re.Match) -> str:
        text = m.group(0)
        if text.startswith('"'):
            if not (len(text) > 1 and text.endswith('"')):
                raise ValueError(f"wrong string: {line!r}")
            return text
        return value

    return pattern.sub(repl, line)


def tokenize(lines: list[str]) -> list[tuple[int, str]]:
    """Strip comments and blank lines."""
    result = []
    for i, line in enumerate(lines, 1):
        line = strip_comment(line)
        if line:
            result.append((i, line))
    return result


def str_size(text: str) -> int:
    """Size in bytes of pstr:."""
    return 4 * (1 + len(text))


def first_pass(tokens: list[tuple[int, str]]) -> tuple[dict[str, int], list[tuple[int, int, str]]]:
    """Single sequential pass: code and data are laid out in source order."""
    labels: dict[str, int] = {}
    instructions: list[tuple[int, int, str]] = []
    pc = 0

    for lineno, line in tokens:
        head = line.split(None, 1)[0]
        if head in (".text", ".data"):
            continue
        if head == ".org":
            parts = line.split(None, 1)
            if len(parts) < 2:
                raise SyntaxError(f"Line {lineno}: .org requires address")
            pc = parse_value(parts[1])
            continue

        rest = line
        while m := LABEL_RE.match(rest):
            labels[m.group(1)] = pc
            rest = rest[m.end() :]

        if not rest:
            continue

        instructions.append((lineno, pc, rest))
        if rest.startswith((".word", ".byte")):
            pc += 4
        elif rest.startswith(".str"):
            m = STR_RE.match(rest)
            if not m:
                raise SyntaxError(f"Line {lineno}: wrong .str directive")
            pc += str_size(decode_string(m.group(1)))
        else:
            mnemonic = rest.split()[0].upper()
            if mnemonic not in ASM:
                raise SyntaxError(f"Line {lineno}: unknown mnemonic '{mnemonic}'")
            pc += I_SIZE[ASM[mnemonic][0]]

    return labels, instructions


def decode_string(s: str) -> str:
    """Decode escape sequences in a string literal."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            c = s[i + 1]
            if c == "n":
                result.append("\n")
            elif c == "t":
                result.append("\t")
            elif c == "\\":
                result.append("\\")
            elif c == '"':
                result.append('"')
            elif c == "0":
                result.append("\0")
            else:
                result.append(c)
            i += 2
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


def encode_u32_be(value: int) -> bytes:
    """Encode a 32-bit unsigned integer as 4 big-endian bytes."""
    value = value & 0xFFFFFFFF
    return value.to_bytes(4, byteorder="big")


def resolve(arg: str, labels: dict[str, int], lineno: int, what: str) -> int:
    """Resolve an operand that may be a label or a numeric literal."""
    if arg in labels:
        return labels[arg]
    try:
        return parse_value(arg)
    except ValueError as err:
        raise SyntaxError(f"Line {lineno}: undefined label or invalid {what} '{arg}'") from err


def second_pass(
    instructions: list[tuple[int, int, str]],
    labels: dict[str, int],
) -> list[tuple[int, bytes]]:
    """Second pass: generate binary for each instruction."""
    chunks: list[tuple[int, bytes]] = []

    def emit(addr: int, data: bytes):
        chunks.append((addr, data))

    for lineno, addr, line in instructions:
        # ---- Data directives ----
        if line.startswith((".word", ".byte")):
            parts = line.split(None, 1)
            name = parts[0]
            arg = parts[1] if len(parts) > 1 else "0"
            value = resolve(arg, labels, lineno, f"{name} value")
            if name == ".byte":
                value &= 0xFF
            emit(addr, encode_u32_be(value))
            continue

        if line.startswith(".str"):
            m = STR_RE.match(line)
            if not m:
                raise SyntaxError(f"Line {lineno}: wrong .str directive")
            text = decode_string(m.group(1))
            data = encode_u32_be(len(text))
            for ch in text:
                data += encode_u32_be(ord(ch) & 0xFF)
            emit(addr, data)
            continue

        # ---- Instructions ----
        parts = line.split(None, 1)
        mnemonic = parts[0].upper()
        arg = parts[1].strip() if len(parts) > 1 else ""

        indirect = False
        m_indirect = re.match(r"^\(\[(.+)\]\)$", arg)
        if m_indirect:
            indirect = True
            arg = m_indirect.group(1).strip()
        else:
            m_direct = re.match(r"^\((.+)\)$", arg)
            if m_direct:
                arg = m_direct.group(1).strip()
            elif arg.startswith("[") and arg.endswith("]"):
                indirect = True
                arg = arg[1:-1].strip()

        if mnemonic not in ASM:
            raise SyntaxError(f"Line {lineno}: unknown mnemonic '{mnemonic}'")

        kind, opcode_bits = ASM[mnemonic]
        opcode = int(opcode_bits, 2)

        if indirect and kind != "addr":
            raise SyntaxError(f"Line {lineno}: indirect addressing not allowed for '{mnemonic}' ")

        if kind == "noarg":
            emit(addr, bytes([opcode]))

        elif kind in ("addr", "label"):
            if kind == "addr" and indirect:
                opcode |= 0x80
            target = resolve(arg, labels, lineno, "address")
            emit(addr, bytes([opcode]) + encode_u32_be(target))

        elif kind == "value":
            value = resolve(arg, labels, lineno, "immediate value") & 0xFFFFFF
            emit(addr, bytes([opcode]) + encode_u32_be(value)[1:])

        elif kind == "byteaddr":
            try:
                port = parse_value(arg)
            except ValueError as err:
                raise SyntaxError(f"Line {lineno}: invalid port number '{arg}'") from err
            if not (0 <= port < NUM_IO_PORTS):
                raise SyntaxError(f"Line {lineno}: invalid port number '{arg}'")

            if mnemonic == "RD" and port % 2 != 0:
                raise SyntaxError(f"Line {lineno}: RD reads from an input port")
            if mnemonic == "WR" and port % 2 == 0:
                raise SyntaxError(f"Line {lineno}: WR writes to an output port")
            onehot = (1 << port) & 0xFF
            emit(addr, bytes([opcode, 0x00, 0x00, onehot]))

    return chunks


def build_listing(
    instructions: list[tuple[int, int, str]],
    chunks: list[tuple[int, bytes]],
) -> str:
    """Debug listing, one line per item:  <ADDR> - <HEXCODE> - <mnemonic>."""
    lines = [
        f"{addr:04X} - {data.hex().upper()} - {content}"
        for (_lineno, addr, content), (_addr, data) in zip(instructions, chunks, strict=True)
    ]
    return "\n".join(lines) + ("\n" if lines else "")


def translate(asm_file: io.TextIOWrapper, bin_file: io.RawIOBase, listing_file=None):
    raw_lines = asm_file.readlines()

    preprocessed = preprocess(raw_lines)
    tokens = tokenize(preprocessed)
    labels, instructions = first_pass(tokens)
    chunks = second_pass(instructions, labels)

    if listing_file is not None:
        listing_file.write(build_listing(instructions, chunks))

    if not chunks:
        return

    size = max(addr + len(data) for addr, data in chunks)
    binary = bytearray(size)
    for addr, data in chunks:
        binary[addr : addr + len(data)] = data

    bin_file.write(bytes(binary))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("asm_file", help="input assembler filename")
    parser.add_argument(
        "bin_file", nargs="?", help="output binary filename (default: ./tmp/<asm_file>.bin)"
    )
    parser.add_argument(
        "--listing", "-l", help="optional debug listing output (<addr> - <hexcode> - <mnemonic>)"
    )
    args = parser.parse_args()
    base = os.path.splitext(os.path.basename(args.asm_file))[0]
    if args.bin_file is None:
        args.bin_file = os.path.join("tmp", base + ".bin")
    if args.listing is None:
        args.listing = os.path.join("tmp", base + ".lst")
    return args


if __name__ == "__main__":
    args = parse_args()
    assert os.path.exists(args.asm_file), f"File not found: {args.asm_file}"
    os.makedirs(os.path.dirname(args.bin_file) or ".", exist_ok=True)
    with open(args.asm_file, encoding="utf-8") as asm, io.FileIO(args.bin_file, "wb") as bin_out:
        with open(args.listing, "w", encoding="utf-8") as lst:
            translate(asm, bin_out, lst)
