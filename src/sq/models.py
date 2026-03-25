from __future__ import annotations

from typing import Literal

from pydantic import field_validator
from pydantic.dataclasses import dataclass

ChannelType = Literal[
    "input", "mix", "group", "fx_return", "fx_send", "matrix", "lr"
]

CHANNEL_TYPE_LIMITS: dict[ChannelType, int] = {
    "input": 48,
    "mix": 12,
    "group": 12,
    "fx_return": 8,
    "fx_send": 4,
    "matrix": 3,
    "lr": 1,
}


@dataclass
class Channel:
    type: ChannelType
    number: int
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        encoded = v.encode("ascii", errors="strict")
        if len(encoded) > 15:
            raise ValueError("Channel name must be max 15 ASCII characters")
        return v

    @field_validator("number")
    @classmethod
    def validate_number(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Channel number must be >= 1")
        return v


@dataclass
class ShowConfig:
    show_name: str
    channels: list[Channel]

    @field_validator("show_name")
    @classmethod
    def validate_show_name(cls, v: str) -> str:
        encoded = v.encode("ascii", errors="strict")
        if len(encoded) > 511:
            raise ValueError("Show name must be max 511 ASCII characters")
        return v
