from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property

from serpent.codegen.byte_utils import *


class ByteCommand(ABC):
    
    @property
    @abstractmethod
    def tag(self) -> int: ...

    @abstractmethod
    def to_bytes(self) -> bytes: ...


@dataclass(frozen=True)
class Iconst_i(ByteCommand):
    i: int

    def __post_init__(self):
        assert -1 <= self.i <= 5, "i_const_<i> argument must be in range -1..5"

    @cached_property
    def tag(self) -> int:
        i_mapping = {
            -1: 0x2,
            0: 0x3,
            1: 0x4,
            2: 0x5,
            3: 0x6,
            4: 0x7,
            5: 0x8,
        }
        return i_mapping[self.i]
    
    def to_bytes(self) -> bytes:
        return self.i
    

@dataclass(frozen=True)
class Bipush(ByteCommand):
    ...
