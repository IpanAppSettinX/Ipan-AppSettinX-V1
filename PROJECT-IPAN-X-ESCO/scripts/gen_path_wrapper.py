"""Generate api-ms-win-core-path-l1-1-0.dll forwarder for Python 3.12 on stripped Windows.

Creates a minimal PE32+ DLL that forwards the required path functions to
shlwapi.dll and kernel32.dll where the real implementations live.
"""

from __future__ import annotations

import struct
from pathlib import Path


def build_forwarder_dll(output_path: str) -> None:
    exports = [
        ("PathIsRelativeW", "shlwapi.PathIsRelativeW"),
        ("PathCombineW", "shlwapi.PathCombineW"),
        ("PathSkipRootW", "shlwapi.PathSkipRootW"),
        ("PathCchCombineEx", "kernel32.PathCchCombineEx"),
        ("PathCchAppendEx", "kernel32.PathCchAppendEx"),
        ("PathCchSkipRoot", "kernel32.PathCchSkipRoot"),
        ("PathCchIsRoot", "kernel32.PathCchIsRoot"),
        ("PathCchCanonicalizeEx", "kernel32.PathCchCanonicalizeEx"),
        ("PathCchRemoveFileSpec", "kernel32.PathCchRemoveFileSpec"),
        ("PathCchFindExtension", "kernel32.PathCchFindExtension"),
        ("PathCchAddExtension", "kernel32.PathCchAddExtension"),
        ("PathCchRemoveExtension", "kernel32.PathCchRemoveExtension"),
        ("PathCchRenameExtension", "kernel32.PathCchRenameExtension"),
        ("PathCchRemoveBackslash", "kernel32.PathCchRemoveBackslash"),
        ("PathCchRemoveBackslashEx", "kernel32.PathCchRemoveBackslashEx"),
        ("PathCchAddBackslash", "kernel32.PathCchAddBackslash"),
        ("PathCchAddBackslashEx", "kernel32.PathCchAddBackslashEx"),
        ("PathCchAppend", "kernel32.PathCchAppend"),
        ("PathCchStripToRoot", "kernel32.PathCchStripToRoot"),
        ("PathCchStripPrefix", "kernel32.PathCchStripPrefix"),
    ]
    num_exports = len(exports)

    forwarder_strings = b""
    fwd_offsets: list[int] = []
    for _name, target in exports:
        fwd_offsets.append(len(forwarder_strings))
        forwarder_strings += target.encode("ascii") + b"\0"

    name_strings = b""
    name_offsets: list[int] = []
    for name, _target in exports:
        name_offsets.append(len(name_strings))
        name_strings += name.encode("ascii") + b"\0"

    dll_name = b"api-ms-win-core-path-l1-1-0.dll\0"

    # --- Layout (all file offsets) ---
    # 0x000: DOS header (64 bytes)
    # 0x040: PE sig + COFF (24 bytes)
    # 0x058: Optional header PE32+ (240 bytes = 112 + 16*8)
    # 0x148: Section header .edata (40 bytes)
    # 0x170: Export directory (40 bytes)
    # 0x198: EAT (num*4)
    # EPT: Name pointer table (num*4)
    # OT:  Ordinal table (num*2)
    # FS:  Forwarder strings
    # NS:  Name strings
    # DN:  DLL name

    export_dir_off = 0x200
    eat_off = export_dir_off + 40
    npt_off = eat_off + num_exports * 4
    ord_off = npt_off + num_exports * 4
    fs_off = ord_off + num_exports * 2
    ns_off = fs_off + len(forwarder_strings)
    dn_off = ns_off + len(name_strings)
    raw_end = dn_off + len(dll_name)

    section_align = 0x1000
    file_align = 0x200
    raw_size = (raw_end + file_align - 1) & ~(file_align - 1)
    image_size = (raw_end + section_align - 1) & ~(section_align - 1)

    total = raw_size
    buf = bytearray(total)

    # --- DOS header ---
    buf[0:2] = b"MZ"
    struct.pack_into("<I", buf, 0x3C, 0x40)

    # --- PE signature ---
    pe = 0x40
    buf[pe : pe + 4] = b"PE\0\0"

    # --- COFF header (20 bytes) ---
    c = pe + 4
    struct.pack_into("<H", buf, c + 0, 0x8664)  # Machine AMD64
    struct.pack_into("<H", buf, c + 2, 1)  # NumberOfSections
    struct.pack_into("<I", buf, c + 4, 0)  # TimeDateStamp
    struct.pack_into("<I", buf, c + 8, 0)  # PointerToSymbolTable
    struct.pack_into("<I", buf, c + 12, 0)  # NumberOfSymbols
    struct.pack_into("<H", buf, c + 16, 240)  # SizeOfOptionalHeader
    struct.pack_into("<H", buf, c + 18, 0x2026)  # Characteristics

    # --- Optional header PE32+ (112 bytes) ---
    o = c + 20
    struct.pack_into("<H", buf, o + 0, 0x20B)  # Magic
    buf[o + 2] = 14  # MajorLinkerVersion
    buf[o + 3] = 0  # MinorLinkerVersion
    struct.pack_into("<I", buf, o + 4, 0)  # SizeOfCode
    struct.pack_into("<I", buf, o + 8, raw_size)  # SizeOfInitializedData
    struct.pack_into("<I", buf, o + 12, 0)  # SizeOfUninitializedData
    struct.pack_into("<I", buf, o + 16, 0)  # AddressOfEntryPoint
    struct.pack_into("<I", buf, o + 20, 0)  # BaseOfCode
    struct.pack_into("<Q", buf, o + 24, 0x10000000)  # ImageBase
    struct.pack_into("<I", buf, o + 32, section_align)  # SectionAlignment
    struct.pack_into("<I", buf, o + 36, file_align)  # FileAlignment
    struct.pack_into("<H", buf, o + 40, 6)  # MajorOSVersion
    struct.pack_into("<H", buf, o + 42, 0)  # MinorOSVersion
    struct.pack_into("<H", buf, o + 44, 0)  # MajorImageVersion
    struct.pack_into("<H", buf, o + 46, 0)  # MinorImageVersion
    struct.pack_into("<H", buf, o + 48, 6)  # MajorSubsysVersion
    struct.pack_into("<H", buf, o + 50, 0)  # MinorSubsysVersion
    struct.pack_into("<I", buf, o + 52, 0)  # Win32VersionValue
    struct.pack_into("<I", buf, o + 56, image_size)  # SizeOfImage
    struct.pack_into("<I", buf, o + 60, file_align)  # SizeOfHeaders
    struct.pack_into("<I", buf, o + 64, 0)  # CheckSum
    struct.pack_into("<H", buf, o + 68, 3)  # Subsystem (CONSOLE)
    struct.pack_into("<H", buf, o + 70, 0x8160)  # DllCharacteristics
    struct.pack_into("<Q", buf, o + 72, 0x100000)  # SizeOfStackReserve
    struct.pack_into("<Q", buf, o + 80, 0x1000)  # SizeOfStackCommit
    struct.pack_into("<Q", buf, o + 88, 0x100000)  # SizeOfHeapReserve
    struct.pack_into("<Q", buf, o + 96, 0x1000)  # SizeOfHeapCommit
    struct.pack_into("<I", buf, o + 104, 0)  # LoaderFlags
    struct.pack_into("<I", buf, o + 108, 16)  # NumberOfRvaAndSizes

    # --- Data directories (16 entries) ---
    d = o + 112
    # Export table: RVA = 0x1000 + (export_dir_off - file_align), since section starts at RVA 0x1000
    # but our raw data starts at file_align (0x200). So RVA = 0x1000 + offset - 0x200
    export_rva = 0x1000 + (export_dir_off - 0x200)
    export_size = raw_end - export_dir_off
    struct.pack_into("<I", buf, d + 0, export_rva)  # Export VirtualAddress
    struct.pack_into("<I", buf, d + 4, export_size)  # Export Size

    # --- Section header .edata (40 bytes) ---
    s = d + 16 * 8
    buf[s : s + 8] = b".edata\0\0"
    struct.pack_into("<I", buf, s + 8, raw_end)  # VirtualSize
    struct.pack_into("<I", buf, s + 12, 0x1000)  # VirtualAddress
    struct.pack_into("<I", buf, s + 16, raw_size)  # SizeOfRawData
    struct.pack_into("<I", buf, s + 20, 0x200)  # PointerToRawData
    struct.pack_into("<I", buf, s + 24, 0)  # PointerToRelocations
    struct.pack_into("<I", buf, s + 28, 0)  # PointerToLinenumbers
    struct.pack_into("<H", buf, s + 32, 0)  # NumberOfRelocations
    struct.pack_into("<H", buf, s + 34, 0)  # NumberOfLinenumbers
    struct.pack_into("<I", buf, s + 36, 0x40000040)  # Characteristics

    # --- Export directory (40 bytes) at export_dir_off ---
    # File offset = export_dir_off, RVA = 0x1000 + (export_dir_off - 0x200)
    base_rva = 0x1000 - 0x200  # file offset 0x200 = RVA 0x1000
    ed = export_dir_off
    struct.pack_into("<I", buf, ed + 0, 0)  # Characteristics
    struct.pack_into("<I", buf, ed + 4, 0)  # TimeDateStamp
    struct.pack_into("<H", buf, ed + 8, 0)  # MajorVersion
    struct.pack_into("<H", buf, ed + 10, 0)  # MinorVersion
    struct.pack_into("<I", buf, ed + 12, base_rva + dn_off)  # Name RVA
    struct.pack_into("<I", buf, ed + 16, 1)  # OrdinalBase
    struct.pack_into("<I", buf, ed + 20, num_exports)  # NumberOfFunctions
    struct.pack_into("<I", buf, ed + 24, num_exports)  # NumberOfNames
    struct.pack_into("<I", buf, ed + 28, base_rva + eat_off)  # AddressOfFunctions
    struct.pack_into("<I", buf, ed + 32, base_rva + npt_off)  # AddressOfNames
    struct.pack_into("<I", buf, ed + 36, base_rva + ord_off)  # AddressOfNameOrdinals

    # --- EAT: RVAs to forwarder strings ---
    for i in range(num_exports):
        fwd_rva = base_rva + fs_off + fwd_offsets[i]
        struct.pack_into("<I", buf, eat_off + i * 4, fwd_rva)

    # --- Name pointer table: RVAs to name strings ---
    for i in range(num_exports):
        name_rva = base_rva + ns_off + name_offsets[i]
        struct.pack_into("<I", buf, npt_off + i * 4, name_rva)

    # --- Ordinal table ---
    for i in range(num_exports):
        struct.pack_into("<H", buf, ord_off + i * 2, i)

    # --- Forwarder strings ---
    buf[fs_off : fs_off + len(forwarder_strings)] = forwarder_strings

    # --- Name strings ---
    buf[ns_off : ns_off + len(name_strings)] = name_strings

    # --- DLL name ---
    buf[dn_off : dn_off + len(dll_name)] = dll_name

    Path(output_path).write_bytes(buf)
    print(f"Written {output_path} ({len(buf)} bytes, {num_exports} exports)")


if __name__ == "__main__":
    import sys

    output = sys.argv[1] if len(sys.argv) > 1 else "api-ms-win-core-path-l1-1-0.dll"
    build_forwarder_dll(output)
