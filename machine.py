import argparse
import sys

import yaml

MASK = 0xFFFFFFFF

MICROCODE = [
    # --- FETCH ---
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 000 FETCH: AR <- IP
    # 001 FETCH: CR <- mem[AR]  (opcode in CR[31:24])
    (0x08, 0x00, 0x08, 0x00, 0x02, 0x00),
    # --- DECODE ---
    (0x80, 0x08, 0x1D, 0x00, 0x02, 0x08),  # 002 DECODE: bit5 -> 1xx
    (0x80, 0x06, 0x1C, 0x00, 0x02, 0x08),  # 003 DECODE: bit4 -> 01x
    (0x80, 0x2B, 0x1B, 0x00, 0x02, 0x08),  # 004 DECODE: bit3 -> 001
    (0xA0, 0x0D, 0x00, 0x00, 0x02, 0x00),  # 005 -> 000
    # --- D01 ---
    (0x80, 0x57, 0x1B, 0x00, 0x02, 0x08),  # 006 -> 011
    (0xA0, 0x45, 0x00, 0x00, 0x02, 0x00),  # 007 -> 010
    # --- D1 ---
    (0x80, 0x0B, 0x1C, 0x00, 0x02, 0x08),  # 008 bit4 -> 11x
    (0x80, 0x93, 0x1B, 0x00, 0x02, 0x08),  # 009 -> 101
    (0xA0, 0x79, 0x00, 0x00, 0x02, 0x00),  # 010 -> 100
    # --- D11 ---
    (0x80, 0xAF, 0x1B, 0x00, 0x02, 0x08),  # 011 -> 111
    (0xA0, 0xA8, 0x00, 0x00, 0x02, 0x00),  # 012 -> 110
    # --- G000 ---
    (0x80, 0x1A, 0x1A, 0x00, 0x02, 0x08),  # 013 bit2 -> address ops
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 014 IP <- IP+1
    (0x80, 0x15, 0x19, 0x00, 0x02, 0x08),  # 015 bit1 -> NEG/NOT
    (0x80, 0x13, 0x18, 0x00, 0x02, 0x08),  # 016 bit0 -> INC
    (0x00, 0x00, 0x41, 0x10, 0x00, 0x01),  # 017 DEC: ACC <- ACC-1; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 018 -> COMMON
    # --- DO_INC ---
    (0x00, 0x00, 0x41, 0x08, 0x00, 0x01),  # 019 INC: ACC <- ACC+1; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 020 -> COMMON
    # --- G000_NEGNOT ---
    (0x80, 0x18, 0x18, 0x00, 0x02, 0x08),  # 021 bit0 -> NOT
    (0x00, 0x00, 0x41, 0x00, 0x10, 0x01),  # 022 NEG: ACC <- -ACC; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 023 -> COMMON
    # --- DO_NOT ---
    (0x00, 0x00, 0x41, 0x00, 0x04, 0x01),  # 024 NOT: ACC <- ~ACC; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 025 -> COMMON
    # --- G000_ADDR ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 026 AND/OR/XOR: IP <- IP+1
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 027 AND/OR/XOR: AR <- IP
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 028 AND/OR/XOR: DR <- mem[AR]
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 029 AND/OR/XOR: IP <- IP+4
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 030 AND/OR/XOR: AR <- DR
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 031 AND/OR/XOR: DR <- mem[AR]
    (0xA0, 0x23, 0x1F, 0x00, 0x02, 0x08),  # 032 AND/OR/XOR: direct? -> G000_DO
    # 033 AND/OR/XOR: AR <- DR (indirect)
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),
    # 034 AND/OR/XOR: DR <- mem[AR] (indirect)
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),
    # --- G000_DO ---
    (0x80, 0x26, 0x19, 0x00, 0x02, 0x08),  # 035 bit1 -> OR/AND
    (0x00, 0x00, 0x41, 0x00, 0x08, 0x05),  # 036 XOR: ACC <- ACC xor DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 037 -> COMMON
    # --- G000_OR_AND ---
    (0x80, 0x29, 0x18, 0x00, 0x02, 0x08),  # 038 bit0 -> AND
    (0x00, 0x00, 0x41, 0x00, 0x02, 0x05),  # 039 OR: ACC <- ACC or DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 040 -> COMMON
    # --- DO_AND ---
    (0x00, 0x00, 0x41, 0x00, 0x01, 0x05),  # 041 AND: ACC <- ACC and DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 042 -> COMMON
    # --- G001 ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 043 G1: IP <- IP+1
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 044 G1: AR <- IP
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 045 G1: DR <- mem[AR]
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 046 G1: IP <- IP+4
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 047 G1: AR <- DR
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 048 G1: DR <- mem[AR]
    (0xA0, 0x34, 0x1F, 0x00, 0x02, 0x08),  # 049 G1: direct? -> G001_DO
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 050 G1: AR <- DR (indirect)
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 051 G1: DR <- mem[AR] (indirect)
    # --- G001_DO ---
    (0x80, 0x3A, 0x1A, 0x00, 0x02, 0x08),  # 052 bit2 -> 4..7
    (0x80, 0x38, 0x18, 0x00, 0x02, 0x08),  # 053 bit0 -> ADC
    (0x00, 0x00, 0x40, 0x04, 0x00, 0x05),  # 054 CMP: ACC-DR -> SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 055 -> COMMON
    # --- DO_ADC ---
    (0x00, 0x00, 0x41, 0x02, 0x00, 0x05),  # 056 ADC: ACC <- ACC+DR+C; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 057 -> COMMON
    # --- G001_4 ---
    (0x80, 0x40, 0x19, 0x00, 0x02, 0x08),  # 058 bit1 -> 6/7
    (0x80, 0x3E, 0x18, 0x00, 0x02, 0x08),  # 059 bit0 -> MUL
    (0x00, 0x00, 0x41, 0x01, 0x00, 0x05),  # 060 DIV: ACC <- ACC/DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 061 -> COMMON
    # --- DO_MUL ---
    (0x00, 0x00, 0x41, 0x00, 0x80, 0x05),  # 062 MUL: ACC <- ACC*DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 063 -> COMMON
    # --- G001_6 ---
    (0x80, 0x43, 0x18, 0x00, 0x02, 0x08),  # 064 bit0 -> ADD
    (0x00, 0x00, 0x41, 0x00, 0x40, 0x05),  # 065 SUB: ACC <- ACC-DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 066 -> COMMON
    # --- DO_ADD ---
    (0x00, 0x00, 0x41, 0x00, 0x20, 0x05),  # 067 ADD: ACC <- ACC+DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 068 -> COMMON
    # --- G010 ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 069 IP <- IP+1
    (0x80, 0x4C, 0x1A, 0x00, 0x02, 0x08),  # 070 bit2 -> shifts
    (0x80, 0x4A, 0x18, 0x00, 0x02, 0x08),  # 071 bit0 -> CLO
    (0x00, 0x40, 0x40, 0x00, 0x02, 0x40),  # 072 CLC: C <- 0
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 073 -> COMMON
    # --- DO_CLO ---
    (0x00, 0x20, 0x40, 0x00, 0x02, 0x40),  # 074 CLO: O <- 0
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 075 -> COMMON
    # --- G010_4 ---
    (0x80, 0x52, 0x19, 0x00, 0x02, 0x08),  # 076 bit1 -> SHR/SHL
    (0x80, 0x50, 0x18, 0x00, 0x02, 0x08),  # 077 bit0 -> ASL
    (0x00, 0x10, 0x41, 0x00, 0x02, 0x01),  # 078 ASR: ACC <- ACC>>1 arith.; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 079 -> COMMON
    # --- DO_ASL ---
    (0x00, 0x08, 0x41, 0x00, 0x02, 0x01),  # 080 ASL: ACC <- ACC<<1 arith.; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 081 -> COMMON
    # --- G010_6 ---
    (0x80, 0x55, 0x18, 0x00, 0x02, 0x08),  # 082 bit0 -> SHL
    (0x00, 0x04, 0x41, 0x00, 0x02, 0x01),  # 083 SHR: ACC <- ACC>>1 logic.; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 084 -> COMMON
    # --- DO_SHL ---
    (0x00, 0x02, 0x41, 0x00, 0x02, 0x01),  # 085 SHL: ACC <- ACC<<1 logic.; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 086 -> COMMON
    # --- G011 ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 087 BR: IP <- IP+1
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 088 BR: AR <- IP
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 089 BR: DR <- mem[AR]
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 090 BR: IP <- IP+4
    (0x80, 0x67, 0x1A, 0x00, 0x02, 0x08),  # 091 bit2 -> 4..7
    (0x80, 0x62, 0x19, 0x00, 0x02, 0x08),  # 092 bit1 -> 2/3
    (0x80, 0x60, 0x18, 0x00, 0x02, 0x08),  # 093 bit0 -> BCC
    (0xA0, 0x77, 0x02, 0x00, 0x02, 0x40),  # 094 BOC: O==0 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 095 -> COMMON
    # --- DO_BCC ---
    (0xA0, 0x77, 0x03, 0x00, 0x02, 0x40),  # 096 BCC: C==0 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 097 -> COMMON
    # --- G011_2 ---
    (0x80, 0x65, 0x18, 0x00, 0x02, 0x08),  # 098 bit0 -> BCS
    (0x80, 0x77, 0x02, 0x00, 0x02, 0x40),  # 099 BOS: O==1 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 100 -> COMMON
    # --- DO_BCS ---
    (0x80, 0x77, 0x03, 0x00, 0x02, 0x40),  # 101 BCS: C==1 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 102 -> COMMON
    # --- G011_4 ---
    (0x80, 0x73, 0x19, 0x00, 0x02, 0x08),  # 103 bit1 -> 6/7
    (0x80, 0x6E, 0x18, 0x00, 0x02, 0x08),  # 104 bit0 -> BLZ
    (0x80, 0x6C, 0x00, 0x00, 0x02, 0x40),  # 105 BGZ: N==1?
    (0xA0, 0x77, 0x02, 0x00, 0x02, 0x40),  # 106 BGZ: N==0,O==0 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 107 -> COMMON
    # --- BGZ_N1 ---
    (0x80, 0x77, 0x02, 0x00, 0x02, 0x40),  # 108 BGZ: N==1,O==1 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 109 -> COMMON
    # --- DO_BLZ ---
    (0x80, 0x71, 0x00, 0x00, 0x02, 0x40),  # 110 BLZ: N==1?
    (0x80, 0x77, 0x02, 0x00, 0x02, 0x40),  # 111 BLZ: N==0,O==1 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 112 -> COMMON
    # --- BLZ_N1 ---
    (0xA0, 0x77, 0x02, 0x00, 0x02, 0x40),  # 113 BLZ: N==1,O==0 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 114 -> COMMON
    # --- G011_6 ---
    (0x80, 0x76, 0x18, 0x00, 0x02, 0x08),  # 115 bit0 -> JMP
    (0x80, 0x77, 0x01, 0x00, 0x02, 0x40),  # 116 BEZ: Z==1 -> branch taken
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 117 -> COMMON
    # --- DO_JMP ---
    (0xA0, 0x77, 0x00, 0x00, 0x02, 0x00),  # 118 JMP: unconditional
    # --- TAKE_BR ---
    (0x00, 0x00, 0x02, 0x00, 0x02, 0x04),  # 119 branch: IP <- DR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 120 -> COMMON
    # --- G100 ---
    (0x80, 0x81, 0x19, 0x00, 0x02, 0x08),  # 121 bit1 -> LD/ST
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 122 IP <- IP+4
    (0x00, 0x01, 0x20, 0x00, 0x02, 0x08),  # 123 AR <- VAL(CR)  (port one-hot)
    (0x80, 0x7F, 0x18, 0x00, 0x02, 0x08),  # 124 bit0 -> RD
    (0x04, 0x00, 0x00, 0x00, 0x02, 0x01),  # 125 WR: io[AR] <- ACC
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 126 -> COMMON
    # --- DO_RD ---
    (0x02, 0x00, 0x41, 0x00, 0x02, 0x00),  # 127 RD: ACC <- io[AR]; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 128 -> COMMON
    # --- G100_MEM ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 129 LD/ST: IP <- IP+1
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 130 LD/ST: AR <- IP
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 131 LD/ST: DR <- mem[AR]
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 132 LD/ST: IP <- IP+4
    (0x80, 0x8C, 0x18, 0x00, 0x02, 0x08),  # 133 bit0 -> LD
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 134 ST: AR <- DR
    (0xA0, 0x8A, 0x1F, 0x00, 0x02, 0x08),  # 135 ST: direct? -> store
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 136 ST: DR <- mem[AR] (indirect)
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 137 ST: AR <- DR (indirect)
    # --- ST_STORE ---
    (0x10, 0x00, 0x00, 0x00, 0x02, 0x01),  # 138 ST: mem[AR] <- ACC
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 139 -> COMMON
    # --- DO_LD ---
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 140 LD: AR <- DR
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 141 LD: DR <- mem[AR]
    (0xA0, 0x91, 0x1F, 0x00, 0x02, 0x08),  # 142 LD: direct? -> LD_DONE
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x04),  # 143 LD: AR <- DR (indirect)
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 144 LD: DR <- mem[AR] (indirect)
    # --- LD_DONE ---
    (0x00, 0x00, 0x41, 0x00, 0x02, 0x04),  # 145 LD: ACC <- DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 146 -> COMMON
    # --- G101 ---
    (0x80, 0x97, 0x19, 0x00, 0x02, 0x08),  # 147 bit1 -> RET/CALL
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 148 IP <- IP+1
    (0x00, 0x00, 0x10, 0x00, 0x02, 0x01),  # 149 SSP: SP <- ACC
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 150 -> COMMON
    # --- G101_RC ---
    (0x80, 0x9F, 0x18, 0x00, 0x02, 0x08),  # 151 bit0 -> CALL
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x10),  # 152 RET: AR <- SP
    (0x08, 0x00, 0x02, 0x00, 0x02, 0x00),  # 153 RET: IP <- mem[SP]
    (0x00, 0x00, 0x10, 0x10, 0x00, 0x10),  # 154 RET: SP <- SP-1
    (0x00, 0x00, 0x10, 0x10, 0x00, 0x10),  # 155 RET: SP <- SP-1
    (0x00, 0x00, 0x10, 0x10, 0x00, 0x10),  # 156 RET: SP <- SP-1
    (0x00, 0x00, 0x10, 0x10, 0x00, 0x10),  # 157 RET: SP <- SP-1
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 158 -> COMMON
    # --- DO_CALL ---
    (0x00, 0x00, 0x02, 0x08, 0x00, 0x02),  # 159 CALL: IP <- IP+1
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x02),  # 160 CALL: AR <- IP
    (0x08, 0x00, 0x04, 0x00, 0x02, 0x00),  # 161 CALL: DR <- mem[AR]
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 162 CALL: IP <- IP+4
    (0x00, 0x00, 0x10, 0x20, 0x00, 0x10),  # 163 CALL: SP <- SP+4
    (0x00, 0x00, 0x20, 0x00, 0x02, 0x10),  # 164 CALL: AR <- SP
    (0x10, 0x00, 0x00, 0x00, 0x02, 0x02),  # 165 CALL: mem[SP] <- IP
    (0x00, 0x00, 0x02, 0x00, 0x02, 0x04),  # 166 CALL: IP <- DR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 167 -> COMMON
    # --- G110 ---
    (0x00, 0x00, 0x02, 0x20, 0x00, 0x02),  # 168 IP <- IP+4
    (0x80, 0xAD, 0x18, 0x00, 0x02, 0x08),  # 169 bit0 -> LDIM
    (0x00, 0x01, 0x04, 0x00, 0x02, 0x08),  # 170 ADDIM: DR <- VAL(CR)
    (0x00, 0x00, 0x41, 0x00, 0x20, 0x05),  # 171 ADDIM: ACC <- ACC+DR; SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 172 -> COMMON
    # --- DO_LDIM ---
    (0x00, 0x01, 0x41, 0x00, 0x02, 0x08),  # 173 LDIM: ACC <- VAL(CR); SR
    (0xA0, 0x00, 0x00, 0x00, 0x02, 0x00),  # 174 -> COMMON
    # --- G111 ---
    (0x40, 0x00, 0x00, 0x00, 0x02, 0x00),  # 175 HLT: halt
]

ACC, IP, DR, CR, SP, AR, SR = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40

FN, FZ, FO, FC = 0, 1, 2, 3

(
    ALU_AND,
    ALU_OR,
    ALU_NOT,
    ALU_XOR,
    ALU_NEG,
    ALU_ADD,
    ALU_SUB,
    ALU_MUL,
    ALU_DIV,
    ALU_ADC,
    ALU_CMP,
    ALU_INC,
    ALU_DEC,
    ALU_ADD4,
) = range(14)

COM_VAL, COM_SHL, COM_SHR, COM_ASL, COM_ASR, COM_CLO, COM_CLC = (1 << i for i in range(7))

OPTAB = {
    0x00: ("DEC", "noarg"),
    0x01: ("INC", "noarg"),
    0x02: ("NEG", "noarg"),
    0x03: ("NOT", "noarg"),
    0x05: ("XOR", "addr"),
    0x06: ("OR", "addr"),
    0x07: ("AND", "addr"),
    0x0A: ("CMP", "addr"),
    0x0B: ("ADC", "addr"),
    0x0C: ("DIV", "addr"),
    0x0D: ("MUL", "addr"),
    0x0E: ("SUB", "addr"),
    0x0F: ("ADD", "addr"),
    0x12: ("CLC", "noarg"),
    0x13: ("CLO", "noarg"),
    0x14: ("ASR", "noarg"),
    0x15: ("ASL", "noarg"),
    0x16: ("SHR", "noarg"),
    0x17: ("SHL", "noarg"),
    0x18: ("BOC", "label"),
    0x19: ("BCC", "label"),
    0x1A: ("BOS", "label"),
    0x1B: ("BCS", "label"),
    0x1C: ("BGZ", "label"),
    0x1D: ("BLZ", "label"),
    0x1E: ("BEZ", "label"),
    0x1F: ("JMP", "label"),
    0x24: ("WR", "byteaddr"),
    0x25: ("RD", "byteaddr"),
    0x26: ("ST", "addr"),
    0x27: ("LD", "addr"),
    0x2D: ("SSP", "noarg"),
    0x2E: ("RET", "noarg"),
    0x2F: ("CALL", "label"),
    0x36: ("ADDIM", "value"),
    0x37: ("LDIM", "value"),
    0x3F: ("HLT", "noarg"),
}
INSTR_SIZE = {"noarg": 1, "value": 4, "byteaddr": 4, "addr": 5, "label": 5}


def s32(v):
    v &= MASK
    return v - (1 << 32) if v & 0x80000000 else v


class HaltError(Exception):
    """Halt."""


class IOController:
    """8 byte ports: even — input, odd — output."""

    def __init__(self, buffers):
        self.inq = {p: list(buffers.get(p, [])) for p in (0, 2, 4, 6)}
        self.out = {p: [] for p in (1, 3, 5, 7)}

    @staticmethod
    def port_index(onehot):
        if onehot == 0 or (onehot & (onehot - 1)):
            raise ValueError(f"invalid port: {onehot:#x}")
        return onehot.bit_length() - 1

    def read(self, onehot):
        q = self.inq.get(self.port_index(onehot))
        if not q:
            raise HaltError("input stream empty")
        return q.pop(0) & 0xFF

    def write(self, onehot, byte):
        self.out[self.port_index(onehot)].append(byte & 0xFF)


class DataPath:
    """Registers, memory (byte-addressed, 32-bit port, big-endian), ALU, commutator."""

    def __init__(self, image: bytes, io: IOController, mem_size=1 << 16, start=0):
        self.mem = bytearray(max(mem_size, len(image)))
        self.mem[: len(image)] = image
        self.io = io
        # IP starts at the entry point (`start`); all other registers at 0.
        self.regs = {ACC: 0, IP: start & MASK, DR: 0, CR: 0, SP: 0, AR: 0, SR: 0}

    # --- memory ---
    def mem_read(self, a):
        a &= MASK
        return int.from_bytes(self.mem[a : a + 4].ljust(4, b"\0"), "big")

    def mem_write(self, a, v):
        a &= MASK
        self.mem[a : a + 4] = (v & MASK).to_bytes(4, "big")

    # --- bus ---
    def bus(self, mask):
        v = 0
        for bit, val in self.regs.items():
            if mask & bit:
                v |= val
        return v & MASK

    def latch(self, mask, v):
        for bit in self.regs:
            if mask & bit and bit != SR:
                self.regs[bit] = v & MASK

    def flag(self, n):
        return (self.regs[SR] >> n) & 1

    def set_flag(self, n, v):
        self.regs[SR] = (self.regs[SR] & ~(1 << n)) | ((v & 1) << n)

    # --- ALU ---
    def alu(self, op, in1, in2):
        if op == ALU_OR:
            return in1 | in2, None, None
        if op == ALU_AND:
            return in1 & in2, None, None
        if op == ALU_XOR:
            return in1 ^ in2, None, None
        if op == ALU_NOT:
            return (~in1) & MASK, None, None
        if op == ALU_ADD4:
            return (in2 + 4) & MASK, None, None
        if op in (ALU_ADD, ALU_ADC, ALU_INC):
            add = 1 if op == ALU_INC else (self.flag(FC) if op == ALU_ADC else 0)
            full = in1 + in2 + add
            r = full & MASK
            o = 1 if (~(in1 ^ in2) & (in1 ^ r) & 0x80000000) else 0
            return r, int(full > MASK), o
        if op in (ALU_SUB, ALU_CMP, ALU_DEC, ALU_NEG):
            a = 0 if op == ALU_NEG else in1
            b = in1 if op == ALU_NEG else (1 if op == ALU_DEC else in2)
            full = a + ((~b) & MASK) + 1
            r = full & MASK
            o = 1 if ((a ^ b) & (a ^ r) & 0x80000000) else 0
            return r, int(full > MASK), o
        if op == ALU_MUL:
            prod = s32(in1) * s32(in2)
            return prod & MASK, None, int(not -(1 << 31) <= prod < (1 << 31))
        if op == ALU_DIV:
            if s32(in2) == 0:
                return in1, None, 1
            return int(s32(in1) / s32(in2)) & MASK, None, 0
        raise ValueError(f"unknown ALU operation #{op}")

    # --- commutator ---
    def commutate(self, com, v):
        if com == 0:
            return v, None, None
        if com & COM_VAL:
            return v & 0x00FFFFFF, None, None
        if com & COM_SHL:
            return (v << 1) & MASK, None, None
        if com & COM_SHR:
            return v >> 1, None, None
        if com & COM_ASL:
            out = (v << 1) & MASK
            return out, (v >> 31) & 1, ((v >> 31) ^ (out >> 31)) & 1
        if com & COM_ASR:
            return (s32(v) >> 1) & MASK, v & 1, 0
        if com & COM_CLO:
            return v, None, "clr"
        if com & COM_CLC:
            return v, "clr", None
        raise ValueError(f"unknown commutator code {com:#x}")


class ControlUnit:
    """Executes microcode from microprogram memory; one microinstruction per tick."""

    def __init__(self, dp: DataPath):
        self.dp = dp
        self.upc = 0
        self.tick_count = 0

    def at_fetch(self):
        return self.upc == 0

    def tick(self):
        b0, b1, b2, b3, b4, b5 = MICROCODE[self.upc]
        self.tick_count += 1
        if b0 & 0x80:  # control microinstruction
            val = self.dp.bus(b5)
            bit = (val >> b2) & 1
            self.upc = b1 if bit ^ ((b0 >> 5) & 1) else self.upc + 1
            return
        if b0 & 0x40:  # HLT
            raise HaltError("HLT")
        dp = self.dp
        com, dst, src = b1, b2, b5
        alu_op = ((b3 << 8) | b4).bit_length() - 1
        in1 = dp.bus(src & ACC)
        in2 = dp.bus(src & ~ACC)
        res, c, o = dp.alu(alu_op, in1, in2)
        out, c_ov, o_ov = dp.commutate(com, res)
        if b0 & 0x08:  # mem_rd
            out = dp.mem_read(dp.regs[AR])
        if b0 & 0x02:  # io_rd
            out = dp.io.read(dp.regs[AR] & 0xFF)
        dp.latch(dst, out)
        if dst & SR:
            self._update_flags(com, alu_op, out, c, o, c_ov, o_ov)
        if b0 & 0x10:  # mem_wr
            dp.mem_write(dp.regs[AR], out)
        if b0 & 0x04:  # io_wr
            dp.io.write(dp.regs[AR] & 0xFF, out)
        self.upc += 1

    def _update_flags(self, com, alu_op, out, c, o, c_ov, o_ov):
        dp = self.dp
        if c_ov == "clr":
            dp.set_flag(FC, 0)
            return
        if o_ov == "clr":
            dp.set_flag(FO, 0)
            return
        dp.set_flag(FN, (out >> 31) & 1)
        dp.set_flag(FZ, int(out == 0))
        if com & (COM_ASL | COM_ASR):
            dp.set_flag(FC, c_ov)
            dp.set_flag(FO, o_ov)
        elif com & (COM_SHL | COM_SHR):
            pass  # logical shifts
        else:
            if c is not None:
                dp.set_flag(FC, c)
            if o is not None:
                dp.set_flag(FO, o)


# Disassembler
def disasm_at(mem, addr):
    """-> (text, hex code, size)."""
    op = mem[addr]
    indirect = bool(op & 0x80)
    mn, kind = OPTAB.get(op & 0x7F, (None, None))
    if mn is None or (indirect and kind != "addr"):
        return f"?? {op:02X}", f"{op:02X}", 1
    size = INSTR_SIZE[kind]
    raw = bytes(mem[addr : addr + size])
    hexcode = raw.hex().upper()
    if kind == "noarg":
        return mn, hexcode, size
    if kind == "value":
        return f"{mn} {int.from_bytes(raw[1:4], 'big')}", hexcode, size
    if kind == "byteaddr":
        return f"{mn} {raw[3].bit_length() - 1}", hexcode, size
    operand = int.from_bytes(raw[1:5], "big")
    arg = f"[0x{operand:X}]" if indirect else f"0x{operand:X}"
    return f"{mn} ({arg})", hexcode, size


# Simulation and logging
DEFAULT_FORMAT = (
    "{tick:6} | {iaddr:04X} | {hex:<10} | {mnemonic:<16} | "
    "ACC={acc:08X} IP={ip:08X} DR={dr:08X} CR={cr:08X} "
    "SP={sp:08X} AR={ar:08X} NZOC={n}{z}{o}{c}"
)
TICK_FORMAT = (
    "{tick:6} | upc={upc:3} | ACC={acc:08X} IP={ip:08X} DR={dr:08X} "
    "CR={cr:08X} SP={sp:08X} AR={ar:08X} SR={sr:08X}"
)


def log_fields(cu, dp, iaddr=0, mnemonic="", hexcode="", icount=0):
    return {
        "tick": cu.tick_count,
        "instr": icount,
        "iaddr": iaddr,
        "mnemonic": mnemonic,
        "hex": hexcode,
        "upc": cu.upc,
        "acc": dp.regs[ACC],
        "ip": dp.regs[IP],
        "dr": dp.regs[DR],
        "cr": dp.regs[CR],
        "sp": dp.regs[SP],
        "ar": dp.regs[AR],
        "sr": dp.regs[SR],
        "n": dp.flag(FN),
        "z": dp.flag(FZ),
        "o": dp.flag(FO),
        "c": dp.flag(FC),
    }


def fmt_buf(buf, mode):
    if mode == "char":
        return "".join(chr(b) if 32 <= b < 127 else f"\\x{b:02x}" for b in buf)
    if mode == "hex":
        return " ".join(f"{b:02X}" for b in buf)
    return str(list(buf))


def simulate(image, io_bufs, cfg, log=print):
    io = IOController(io_bufs)
    dp = DataPath(image, io, start=cfg.get("start", 0))
    cu = ControlUnit(dp)
    limit_t = cfg.get("limit_ticks", 1_000_000)
    limit_i = cfg.get("limit_instructions", 100_000)
    trace = cfg.get("trace", "instr")
    fmt = cfg.get("log_format", DEFAULT_FORMAT if trace == "instr" else TICK_FORMAT)
    icount = 0
    stop = "limit"
    try:
        while cu.tick_count < limit_t and icount < limit_i:
            if cu.at_fetch():
                icount += 1
                if trace == "instr":
                    ia = dp.regs[IP]
                    mn, hx, _ = disasm_at(dp.mem, ia)
                    log(fmt.format(**log_fields(cu, dp, ia, mn, hx, icount)))
            cu.tick()
            if trace == "tick":
                log(fmt.format(**log_fields(cu, dp, icount=icount)))
    except HaltError as e:
        stop = str(e)
    return {"io": io, "dp": dp, "cu": cu, "instructions": icount, "stop": stop}


def parse_inputs(cfg):
    """Input buffers from config."""
    bufs = {}
    for port, buf in (cfg.get("inputs") or {}).items():
        if isinstance(buf, str):
            buf = [ord(ch) for ch in buf]
        bufs[int(port)] = list(buf)
    return bufs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("binary", help="binary code")
    p.add_argument("--config", "-c", help="yaml config")
    args = p.parse_args()

    with open(args.binary, "rb") as f:
        image = f.read()

    cfg = {}
    if args.config:
        with open(args.config) as f:
            cfg = yaml.safe_load(f) or {}

    io_bufs = parse_inputs(cfg)
    io_fmt = cfg.get("io_format", "int")
    print(f"entry point: 0x{cfg.get('start', 0):X}")
    for port in sorted(io_bufs):
        print(f"input port {port}: {fmt_buf(io_bufs[port], io_fmt)}")

    res = simulate(image, io_bufs, cfg)

    print(
        f"\n halt: {res['stop']}; instructions: {res['instructions']}, "
        f" ticks: {res['cu'].tick_count}"
    )
    for port in sorted(res["io"].out):
        buf = res["io"].out[port]
        if buf:
            print(f"output port {port}: {fmt_buf(buf, io_fmt)}")

    failed = False
    for port, expected in (cfg.get("assert_output") or {}).items():
        got = res["io"].out.get(int(port), [])
        status = "OK" if got == list(expected) else "FAIL"
        failed |= status == "FAIL"
        print(
            f"assert port {port}: {status}"
            + ("" if status == "OK" else f" (expected {expected}, got {got})")
        )
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
