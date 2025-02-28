def u1(x: int) -> bytes:
    # Кодирует число в 1 байт (big-endian)
    return x.to_bytes(1, byteorder='big', signed=False)


def u2(x: int) -> bytes:
    # Кодирует число в 2 байта (big-endian)
    return x.to_bytes(2, byteorder='big', signed=False)


def u4(x: int) -> bytes:
    # Кодирует число в 4 байта (big-endian)
    return x.to_bytes(4, byteorder='big', signed=False)


def s2(x: int) -> bytes:
    # Кодирует число в 2 байта (big-endian) со знаком
    return x.to_bytes(2, byteorder='big', signed=True)


def s4(x: int) -> bytes:
    # Кодирует число в 4 байта (big-endian) со знаком
    return x.to_bytes(4, byteorder='big', signed=True)


def u1_seq(s: str) -> bytes:
    # Кодирует строку в последовательность байтов в формате UTF-8
    return s.encode('utf-8')


def merge_bytes(*bs: bytes) -> bytes:
    # Объединяет все переданные байтовые последовательности в одну
    return b"".join(bs)
