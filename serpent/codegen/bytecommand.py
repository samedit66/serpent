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

    def size(self) -> int:
        return len(self.to_bytes())


@dataclass(frozen=True)
class Nop(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0
    
    def to_bytes(self) -> bytes:
        return u1(self.tag)


# 1. Команды загрузки констант
@dataclass(frozen=True)
class Aconst_null(ByteCommand):
    
    @cached_property
    def tag(self) -> int:
        return 0x1
    
    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Iconst_i(ByteCommand):
    i: int

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
        # Здесь можно вернуть только код команды, так как она не имеет операндов
        return u1(self.tag)


@dataclass(frozen=True)
class Bipush(ByteCommand):
    value: int

    @cached_property
    def tag(self) -> int:
        return 0x10

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.value))


@dataclass(frozen=True)
class Sipush(ByteCommand):
    value: int

    @cached_property
    def tag(self) -> int:
        return 0x11

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.value))


@dataclass(frozen=True)
class Ldc(ByteCommand):
    index: int  # номер константы в таблице констант (однобайтный)

    @cached_property
    def tag(self) -> int:
        return 0x12

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.index))


@dataclass(frozen=True)
class Ldc_w(ByteCommand):
    index: int  # номер константы в таблице констант (двухбайтный)

    @cached_property
    def tag(self) -> int:
        return 0x13

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


# 2. Команды работы с локальными переменными (загрузка)
@dataclass(frozen=True)
class Iload(ByteCommand):
    var_index: int

    @cached_property
    def tag(self) -> int:
        return 0x15

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.var_index))


@dataclass(frozen=True)
class Fload(ByteCommand):
    var_index: int

    @cached_property
    def tag(self) -> int:
        return 0x17

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.var_index))


@dataclass(frozen=True)
class Aload(ByteCommand):
    var_index: int

    @cached_property
    def tag(self) -> int:
        return 0x19

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.var_index))


# 3. Команды работы с локальными переменными (сохранение)
@dataclass(frozen=True)
class Istore(ByteCommand):
    var_index: int

    @cached_property
    def tag(self) -> int:
        return 0x36

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.var_index))


@dataclass(frozen=True)
class Astore(ByteCommand):
    var_index: int

    @cached_property
    def tag(self) -> int:
        return 0x3A

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.var_index))


# 4. Команды работы со стеком
@dataclass(frozen=True)
class Pop(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x57

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Dup(ByteCommand):
    
    @cached_property
    def tag(self) -> int:
        return 0x59
    
    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Dup2(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x5C

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Dupx1(ByteCommand):
    
    @cached_property
    def tag(self) -> int:
        return 0x5a
    
    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Swap(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x5f
    
    def to_bytes(self) -> bytes:
        return u1(self.tag)


# 5. Арифметические команды
@dataclass(frozen=True)
class Iadd(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x60

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Imul(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x68

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Isub(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x64

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Idiv(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x6C

    def to_bytes(self) -> bytes:
        return u1(self.tag)


# 6. Команды переходов (условные, безусловные и переключатели)
# 6.1 if_icmp<cond>
@dataclass(frozen=True)
class IfIcmpeq(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x9F

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfIcmpne(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA0

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfIcmplt(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA1

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfIcmpge(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA2

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfIcmpgt(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA3

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfIcmple(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA4

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


# 6.2 if<cond> (сравнение со значением 0)
@dataclass(frozen=True)
class Ifeq(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x99

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class Ifne(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x9A

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class Iflt(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x55  # согласно описанию
    
    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class Ifle(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x9E

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class Ifgt(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x9D

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class Ifge(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0x9C

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


# 6.3 if_acmp<cond> (сравнение ссылок)
@dataclass(frozen=True)
class IfAcmpeq(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA5

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


@dataclass(frozen=True)
class IfAcmpne(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xA6

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


# 6.4 Безусловный переход
@dataclass(frozen=True)
class Goto(ByteCommand):
    offset: int

    @cached_property
    def tag(self) -> int:
        return 0xa7

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), s2(self.offset))


# 6.5 Переключатели
@dataclass(frozen=True)
class TableSwitch(ByteCommand):
    default_offset: int
    low: int
    high: int
    offsets: list[int]
    padding: bytes = b''  # от 0 до 3 байт для выравнивания

    @cached_property
    def tag(self) -> int:
        return 0xAA

    def to_bytes(self) -> bytes:
        if len(self.offsets) != self.high - self.low + 1:
            raise ValueError("Количество сдвигов должно равняться high - low + 1")
        parts = [
            u1(self.tag),
            self.padding,
            s4(self.default_offset),
            s4(self.low),
            s4(self.high),
        ]
        for off in self.offsets:
            parts.append(s4(off))
        return merge_bytes(*parts)


@dataclass(frozen=True)
class LookupSwitch(ByteCommand):
    default_offset: int
    pairs: list[tuple[int, int]]  # список пар (ключ, сдвиг)
    padding: bytes = b''

    @cached_property
    def tag(self) -> int:
        return 0xAB

    def to_bytes(self) -> bytes:
        npairs = len(self.pairs)
        parts = [
            u1(self.tag),
            self.padding,
            s4(self.default_offset),
            s4(npairs),
        ]
        for key, offset in self.pairs:
            parts.append(s2(key))
            parts.append(s4(offset))
        return merge_bytes(*parts)


# 7. Команды работы с массивами
@dataclass(frozen=True)
class NewArray(ByteCommand):
    element_type: int  # тип элементов (например, T_INT = 10)

    @cached_property
    def tag(self) -> int:
        return 0xBC

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u1(self.element_type))


@dataclass(frozen=True)
class AnewArray(ByteCommand):
    index: int  # индекс в таблице констант, описывающий тип элементов массива

    @cached_property
    def tag(self) -> int:
        return 0xBD

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class ArrayLength(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0xBE

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Iaload(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x2E

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Aaload(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x32

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Iastore(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x4F

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Aastore(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0x53

    def to_bytes(self) -> bytes:
        return u1(self.tag)


# 8. Команды работы с объектами
@dataclass(frozen=True)
class New(ByteCommand):
    index: int  # индекс в таблице констант для типа объекта

    @cached_property
    def tag(self) -> int:
        return 0xBB

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class GetField(ByteCommand):
    index: int  # индекс в таблице констант для ссылки на поле

    @cached_property
    def tag(self) -> int:
        return 0xB4

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class PutField(ByteCommand):
    index: int  # индекс в таблице констант для ссылки на поле

    @cached_property
    def tag(self) -> int:
        return 0xB5

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class Instanceof(ByteCommand):
    index: int  # индекс в таблице констант для класса

    @cached_property
    def tag(self) -> int:
        return 0xC1

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class CheckCast(ByteCommand):
    index: int  # индекс в таблице констант для класса

    @cached_property
    def tag(self) -> int:
        return 0xC0

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


# 9. Команды работы с методами
@dataclass(frozen=True)
class InvokeVirtual(ByteCommand):
    index: int  # индекс в таблице констант для метода

    @cached_property
    def tag(self) -> int:
        return 0xB6

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class InvokeSpecial(ByteCommand):
    index: int  # индекс в таблице констант для метода

    @cached_property
    def tag(self) -> int:
        return 0xB7

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


@dataclass(frozen=True)
class InvokeStatic(ByteCommand):
    index: int  # индекс в таблице констант для метода

    @cached_property
    def tag(self) -> int:
        return 0xB8

    def to_bytes(self) -> bytes:
        return merge_bytes(u1(self.tag), u2(self.index))


# 10. Команды возврата из метода
@dataclass(frozen=True)
class Ireturn(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0xAC

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Areturn(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0xB0

    def to_bytes(self) -> bytes:
        return u1(self.tag)


@dataclass(frozen=True)
class Return(ByteCommand):

    @cached_property
    def tag(self) -> int:
        return 0xB1

    def to_bytes(self) -> bytes:
        return u1(self.tag)
