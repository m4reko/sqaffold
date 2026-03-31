# Allen & Heath SQ — Show File Format Documentation

Reverse-engineered documentation of the Allen & Heath SQ series mixer show file format as stored on USB.

> **Note:** Allen & Heath has not published an official specification for this format. This documentation is based on binary analysis of show files and disassembly of the SQ MixPad 1.6.0 macOS application (`cScene`, `cLibrary`, `CRC32` classes). Modifying files directly is unsupported and may cause corruption.

## Directory Structure

```
AHSQ/
├── SHOWS/
│   └── SHOW0000/
│       ├── SHOW.DAT          (512 bytes)
│       ├── NVDATA.DAT        (131072 bytes)
│       ├── SCENE000.DAT      (131072 bytes)
│       ├── SCENE001.DAT      ...
│       ├── LIB000.DAT        (512 bytes)
│       ├── LIB001.DAT        ...
│       └── ...
├── SCENES/                   (standalone exported scenes)
│   └── SCENE000.DAT
└── LIBRARY/                  (standalone exported libraries)
```

Show directories are named `SHOW0000` through `SHOW0010` (or higher). Scene and library files use zero-padded sequential numbering.

## SHOW.DAT (512 bytes)

The simplest file — contains only the show name.

| Offset | Size | Field |
|--------|------|-------|
| 0x000 | ~511 | Null-terminated ASCII show name |

The rest of the file is zero-padded.

Examples: `"NC Default 1.5"`, `"Backup 24-10-06"`, `"ChapterJam2Mon"`

## SCENE Files (131,072 bytes / 128 KB each)

Each scene file contains a complete mixer state snapshot.

### Header (0x00–0x37)

| Offset | Size | Field | Notes |
|--------|------|-------|-------|
| 0x00 | 2 | Magic/Type | `0xA1 0x00` for scenes, `0xB5 0x00` for NVDATA |
| 0x02 | 2 | Constant | `0xFE 0xFF` |
| 0x04 | 2 | Scene index | LE uint16: 0 = Scene 1, 1 = Scene 2, etc. `0xFFFF` in NVDATA |
| 0x06 | 2 | Reserved | `0xFF 0xFF` |
| 0x08 | 2 | Sub-version/variant | Varies: 0, 1, 2 |
| 0x0A | 2 | Field | `0x00 0x00` in scenes, `0xFF 0xFF` in NVDATA |
| 0x0C | 2 | Format version | `0x01 0x05` consistently (possibly firmware family) |
| 0x0E | 2 | Firmware version | `0x07 0x00` = v1.x, `0x0A 0x00` = later, `0x0B 0x00` = v1.5+ |
| 0x10 | 4 | Constant | `0x04 0x00 0x00 0x00` |
| 0x14 | 16 | Scene name | Null-terminated ASCII, max ~15 chars |
| 0x24 | 20 | Scene filter/safe flags | `0xFF` bytes in unused scenes |

### Section Layout

The file body is divided into sections separated by **sentinel markers**. Each sentinel is a 4-byte little-endian value with the pattern `0xA5A5A5NN`, where `NN` is the section ID (stored on disk as bytes `NN A5 A5 A5`).

These offsets are confirmed from disassembly of `cScene::TestSentinels()` in the MixPad binary:

| Section | Offset | Size | Content |
|---------|--------|------|---------|
| 0x01 | 0x00038 | 824 bytes | Routing/patching configuration |
| 0x02 | 0x00370 | 41,988 bytes | **Channel strip data** — 122 blocks x 336 bytes |
| 0x03 | 0x0A394 | 772 bytes | Output bus configuration |
| 0x04 | 0x0A698 | 772 bytes | Additional bus configuration |
| 0x05 | 0x0A99C | 36,604 bytes | **Send/crosspoint matrix** — 2 bytes per crosspoint, `0x0080` = default |
| 0x06 | 0x13898 | 1,264 bytes | Dynamics/processing parameters |
| 0x07 | 0x13D88 | 1,748 bytes | GEQ/PEQ data |
| 0x08 | 0x1445C | 24 bytes | Small config block |
| 0x09 | 0x14474 | 36 bytes | Small config block (possibly talkback/oscillator) |
| 0x0A | 0x14498 | 1,476 bytes | Additional processing/routing |
| 0x0B | 0x14A5C | 28 bytes | Small config block |
| 0x0C | 0x14A78 | 2,800 bytes | Processing data |
| 0x0D | 0x15568 | 2,500 bytes | **FX engines** (contains type names: "EMT 250", "Hall 480", etc.) |
| 0x0E | 0x15F2C | 41,168 bytes | Large data section (possibly recall filter masks or routing) |

### Channel Strip Block (Section 0x02)

Each of the 122 blocks is 336 (0x150) bytes. The first block is preceded by the `02 a5 a5 a5` section marker.

The 122 blocks map to the following channel types (verified against real show files):

| Block Range | Count | Channel Type | Notes |
|-------------|-------|-------------|-------|
| 0–47 | 48 | Input channels | 1–40 mono, 41–48 stereo (ST1–ST3, USB) |
| 48–71 | 24 | *(unknown)* | Empty in all observed shows |
| 72–83 | 12 | Groups | |
| 84–87 | 4 | FX sends | *(unverified)* |
| 88–99 | 12 | Mixes | |
| 100–107 | 8 | FX returns | *(unverified)* |
| 104 | 1 | LR | Verified via SHOW0003 diff |
| 105–113 | 9 | *(unknown)* | |
| 115–117 | 3 | Matrix | Verified: "Main", "FrFill", "BaFill" in SHOW0000 |
| 118–121 | 4 | *(unknown)* | |

| Offset (within block) | Field |
|------------------------|-------|
| +0x00 to +0x0F | Channel name (16 bytes, null-terminated ASCII) |
| +0x14 to +0x17 | Channel flags (mute, phantom, pad, etc.) |
| +0x18 to +0x1F | Source/routing assignment |
| +0x20 to +0x3F | EQ/dynamics enable flags and basic parameters |
| +0x40 to +0x41 | HPF frequency value (e.g. `0x007A` = 122, possibly Hz) |
| +0x58 to +0x5F | Fixed parameter block ID (`0x9653 0100` observed) |
| +0x60 to +0x6F | EQ band parameters (frequency/gain/Q) |
| +0x78 to +0x9F | Dynamics parameters (compressor/gate) |
| +0xB0 to +0xEF | **Send levels to mixes** — 32 x 2-byte values |
| +0xF0 to +0x10F | Pan/balance and additional routing |
| +0x128 to +0x12F | Additional dynamics parameters |
| +0x140 to +0x14F | Tail data with level values |

### Checksum (CRC32 variant — CRACKED)

The **last 4 bytes** (offset `0x1FFFC`-`0x1FFFF`) contain a CRC32 checksum computed over bytes `0x14` through `0x1FFFB`.

The algorithm uses the **standard CRC32 polynomial** (`0xEDB88320`) but with a non-standard update step. Disassembled from `_CRC32` and `cScene::CalcSceneCRC()` in the MixPad binary:

```python
# Standard CRC32 lookup table (polynomial 0xEDB88320)
table = [0] * 256
for i in range(256):
    crc = i
    for _ in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ 0xEDB88320
        else:
            crc >>= 1
    table[i] = crc

def ah_crc32(data):
    """Allen & Heath CRC32 variant."""
    crc = 0
    for byte in data:
        index = (~(crc ^ byte)) & 0xFF    # XOR with low byte of CRC, then NOT
        crc = table[index] ^ ((crc >> 8) | 0xFF000000)  # OR 0xFF into top byte
    return crc & 0xFFFFFFFF

# For scene/NVDATA files (131072 bytes):
#   payload = file_data[0x14 : 0x1FFFC]
#   stored_crc = uint32_le(file_data[0x1FFFC : 0x20000])
#   assert ah_crc32(payload) == stored_crc
```

**Verified against all 109 .DAT files across 10 shows — 100% match.**

Key differences from standard CRC32:
1. The index byte is **inverted** (`~(crc ^ byte)` instead of `crc ^ byte`)
2. The shifted CRC has the **top byte forced to 0xFF** (`| 0xFF000000` instead of masking)
3. Initial CRC value is **0** (standard CRC32 uses `0xFFFFFFFF`)
4. No final inversion (standard CRC32 XORs result with `0xFFFFFFFF`)

## NVDATA.DAT (131,072 bytes)

Same structure as scene files with these differences:

- Magic byte at 0x00 is `0xB5` (instead of `0xA1`)
- Scene index fields are `0xFFFF`
- Name field at 0x14 is all `0xFF`
- Represents the **current/global mixer state** and filter/safe settings

Typically only ~135 bytes differ from SCENE000.DAT in the same show.

## LIB Files (512 bytes each)

Library files are **single channel strip presets**.

| Offset | Size | Field |
|--------|------|-------|
| 0x00-0x03 | 4 | Header (`0xA1 0x00 0xFE 0xFF`) |
| 0x04-0x05 | 2 | Library index (LE uint16) |
| 0x0C-0x0F | 4 | Version fields (matches scene header format) |
| 0x10-0x1F | 16 | Short name / source reference (e.g. `"WL7"`) |
| 0x20-0x16F | 336 | Channel strip parameters (same format as a single channel block) |
| 0x170-0x17F | 16 | Library preset full name (e.g. `"EV N/D 308"`, `"WL KSM9"`) |
| 0x1FC-0x1FF | 4 | Checksum (same A&H CRC32 variant, computed over bytes `0x14`-`0x1FB`) |

## Fader Level Encoding

From reverse-engineering of the MIDI NRPN protocol (via the Bitfocus companion module):

- 14-bit value: `(coarse << 7) | fine`
- **LinearTaper formula:** `dB = (value - 15196) / 118.775`
- **AudioTaper:** Piecewise linear, 255 possible values

## MIDI NRPN Parameter Addressing

The NRPN addresses used in the MIDI protocol likely mirror the internal data organization. Key base addresses:

### Mute

| Channel Type | MSB | LSB |
|-------------|-----|-----|
| Input Channel | 0x00 | 0x00 |
| LR Mix | 0x00 | 0x44 |
| Mix | 0x00 | 0x45 |
| Group | 0x00 | 0x30 |
| Matrix | 0x00 | 0x55 |
| FX Send | 0x00 | 0x51 |
| FX Return | 0x00 | 0x3C |
| DCA | 0x02 | 0x00 |
| Mute Group | 0x04 | 0x00 |

### Source -> Sink Routing

| Source -> Sink | Assign MSB/LSB | Level MSB/LSB | Pan MSB/LSB |
|--------------|----------------|---------------|-------------|
| Input -> LR | 0x60/0x00 | 0x40/0x00 | 0x50/0x00 |
| Input -> Mix | 0x60/0x44 | 0x40/0x44 | 0x50/0x44 |
| Input -> FX Send | 0x6C/0x14 | 0x4C/0x14 | -- |
| Input -> Group | 0x66/0x74 | -- | -- |
| FX Return -> LR | 0x60/0x3C | 0x40/0x3C | 0x50/0x3C |
| Group -> LR | 0x60/0x30 | 0x40/0x30 | 0x50/0x30 |
| Group -> Matrix | 0x6E/0x4B | 0x4E/0x4B | 0x5E/0x4B |

## MixPad Application Structure

The SQ MixPad macOS app (`/Applications/SQ MixPad 1.6.0.app`) is a Qt 6 application (x86_64 Mach-O, ~19 MB binary). Key internal classes discovered via symbol analysis:

| Class | Source Path | Purpose |
|-------|------------|---------|
| `cScene` | `SQu/SQApps/Common/CMNet2/Core/Scene.cpp` | Scene serialization, CRC, sentinel validation |
| `cLibrary` | `SQu/SQApps/Common/CMNet2/Core/Library.cpp` | Library preset serialization and CRC |
| `cNVData` | `SQu/SQApps/Common/CMNet2/Core/NVDataStore.cpp` | Current mixer state management |
| `cShowManager` | `SQu/SQApps/Common/Qt/Shows/QtShowManager.cpp` | Show file I/O |
| `cRecipientBase` | `CMNet2/Core/Recipients/RecipientBase.cpp` | Parameter recipient base class |
| `FileIO` | `SQu/Common/Qt/IO/FileIO.cpp` | File read/write operations |
| `ScenePullSyncDriver` | `SQu/Common/Qt/Drivers/EditorSync/ScenePullSyncDriver.cpp` | Scene download from mixer |
| `ScenePushSyncDriver` | `SQu/Common/Qt/Drivers/EditorSync/ScenePushSyncDriver.cpp` | Scene upload to mixer |

Key exported functions for file format work:
- `cScene::CalcSceneCRC(const UBYTE *)` — CRC over bytes 0x14-0x1FFFB
- `cScene::CheckBufferCRC(const UBYTE *)` — Calculate CRC and compare with stored value at 0x1FFFC
- `cScene::CRCFromBuffer(const UBYTE *)` — Read stored CRC from offset 0x1FFFC
- `cScene::TestSentinel(UBYTE, const UBYTE *, ULONG)` — Validate sentinel at offset
- `cScene::TestSentinels(const UBYTE *)` — Validate all 14 sentinels
- `cScene::TestCheckSum(const UBYTE *)` — Validate CRC
- `cLibrary::CalcLibraryCRC(const UBYTE *)` — CRC over bytes 0x14-0x1FB
- `CRC32(u32 crc, u8 byte)` — Single-byte CRC update
- `BufferCRC32(u32 crc, const u8 *buf, int len)` — Multi-byte CRC update

The app communicates with the mixer over:
- **TCP port 51325** — MIDI service (documented protocol)
- **TCP port 51326** — App control protocol (proprietary, used by MixPad)

## Reverse Engineering Approach

To further decode the file format, the most productive approaches are:

1. **Disassemble `cScene` methods** — The MixPad binary contains full symbol names (C++ mangled). Use `nm` to find symbols and `otool -tV` to disassemble. Key methods: `Serialise`, `Deserialise`, `GetParam`, `SetParam`.
2. **Use Ghidra or Hopper for deeper analysis** — The binary is not stripped; class hierarchies and vtables are recoverable. Load the Mach-O binary and search for `cScene::` or `cLibrary::` symbols.
3. **Correlate MIDI NRPN addresses with binary offsets** — Change a single parameter via MIDI, save the scene, and diff the binary to map addresses.
4. **Monitor TCP traffic** — Capture MixPad <-> mixer communication to understand the parameter protocol.

## Related Resources

- [SQ Transferring Show Files](https://support.allen-heath.com/hc/en-gb/articles/4402941948561-SQ-Transferring-Show-Files-to-a-computer) — Official A&H support article
- [SQ MIDI Protocol Issue 5 (PDF)](https://www.allen-heath.com/content/uploads/2023/11/SQ-MIDI-Protocol-Issue5.pdf) — Official MIDI/NRPN documentation
- [SQ Reference Guide V1.6.0 (PDF)](https://www.allen-heath.com/content/uploads/2025/02/SQ_ReferenceGuide_V1_6_0_iss1.pdf) — Official user reference
- [Bitfocus companion-module-allenheath-sq](https://github.com/bitfocus/companion-module-allenheath-sq) — Open source MIDI/TCP control module with NRPN parameter tables
- [A&H Forum: File structure/names](https://forums.allen-heath.com/t/file-structure-names-of-shows-and-scenes/15371) — Community discussion confirming scene name at offset 0x14
- [A&H Forum: File name for USB storage](https://forums.allen-heath.com/t/file-name-for-show-scene-library-when-storing-on-usb/10489) — Directory naming conventions
- [Include Security: Production Security](https://blog.includesecurity.com/2025/10/production-security-not-that-kind/) — Security research documenting TCP ports and app communication

## Known Unknowns

1. **Exact channel block mapping** — Which of the 122 blocks maps to which channel type and index.
2. **Section 0x0E contents** — The largest unnamed section (~41 KB), possibly recall filter masks.
3. **NVDATA vs scene relationship** — How the mixer resolves differences between NVDATA and the active scene.
4. **Firmware version compatibility** — How the format version fields affect file compatibility across firmware versions.
5. **Detailed parameter encoding** — Exact byte-level mapping of EQ bands, dynamics thresholds, FX parameters, etc.
