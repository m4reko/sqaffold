from __future__ import annotations

import struct

from sq.models import CHANNEL_TYPE_LIMITS, ChannelType

# Section 0x02 starts at this file offset
_SECTION_02_OFFSET = 0x370
# 4-byte section marker precedes block data
_SECTION_MARKER_SIZE = 4
# Each channel strip block is 336 bytes
_BLOCK_SIZE = 336
# Channel name is at the start of each block
_NAME_OFFSET_IN_BLOCK = 0x00
# Channel name field is 16 bytes (null-terminated ASCII)
_NAME_FIELD_SIZE = 16

# Block index where each channel type starts
_CHANNEL_TYPE_BLOCK_START: dict[ChannelType, int] = {
    "input": 0,
    "group": 72,
    "fx_send": 84,
    "mix": 88,
    "fx_return": 100,
    "lr": 104,
    "matrix": 115,
}

# CRC32 lookup table (polynomial 0xEDB88320)
_CRC_TABLE: list[int] = []
for _i in range(256):
    _crc = _i
    for _ in range(8):
        if _crc & 1:
            _crc = (_crc >> 1) ^ 0xEDB88320
        else:
            _crc >>= 1
    _CRC_TABLE.append(_crc)


def ah_crc32(data: bytes | bytearray) -> int:
    """Allen & Heath CRC32 variant."""
    crc = 0
    for byte in data:
        index = (~(crc ^ byte)) & 0xFF
        crc = _CRC_TABLE[index] ^ ((crc >> 8) | 0xFF000000)
    return crc & 0xFFFFFFFF


def channel_name_offset(channel_type: ChannelType, number: int) -> int:
    """Return the byte offset in NVDATA.DAT for a channel's name field.

    Args:
        channel_type: The channel type.
        number: 1-based channel number.

    Raises:
        ValueError: If number is out of range for the channel type.
    """
    limit = CHANNEL_TYPE_LIMITS[channel_type]
    if number < 1 or number > limit:
        raise ValueError(
            f"{channel_type} number must be 1–{limit}, got {number}"
        )
    block_index = _CHANNEL_TYPE_BLOCK_START[channel_type] + (number - 1)
    return (
        _SECTION_02_OFFSET
        + _SECTION_MARKER_SIZE
        + block_index * _BLOCK_SIZE
        + _NAME_OFFSET_IN_BLOCK
    )


def write_channel_name(
    data: bytearray,
    channel_type: ChannelType,
    number: int,
    name: str,
) -> None:
    """Write a channel name into the NVDATA.DAT bytearray."""
    offset = channel_name_offset(channel_type, number)
    encoded = name.encode("ascii")[:6]
    padded = encoded.ljust(_NAME_FIELD_SIZE, b"\x00")
    data[offset : offset + _NAME_FIELD_SIZE] = padded


def update_crc(data: bytearray) -> None:
    """Recalculate and write the CRC32 checksum in-place."""
    payload = data[0x14:0x1FFFC]
    crc = ah_crc32(payload)
    struct.pack_into("<I", data, 0x1FFFC, crc)


def write_show_name(show_dat: bytearray, name: str) -> None:
    """Write the show name into a 512-byte SHOW.DAT buffer."""
    encoded = name.encode("ascii")[:511]
    show_dat[:] = encoded.ljust(512, b"\x00")
