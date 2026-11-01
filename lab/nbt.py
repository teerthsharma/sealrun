import struct

_SCALARS = {1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}


class _Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def take(self, n: int) -> bytes:
        end = self.pos + n
        if n < 0 or end > len(self.data):
            raise ValueError("truncated NBT data")
        chunk = self.data[self.pos:end]
        self.pos = end
        return chunk

    def unpack(self, fmt: str):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self) -> str:
        return self.take(self.unpack(">H")).decode("utf-8")

    def count(self) -> int:
        n = self.unpack(">i")
        if n < 0:
            raise ValueError("negative NBT count")
        return n

    def payload(self, tag: int):
        if tag in _SCALARS:
            return self.unpack(_SCALARS[tag])
        if tag == 7:
            return [self.unpack(">b") for _ in range(self.count())]
        if tag == 8:
            return self.string()
        if tag == 9:
            element = self.unpack(">B")
            n = self.count()
            if element == 0 and n:
                raise ValueError("non-empty list of End tags")
            return [self.payload(element) for _ in range(n)]
        if tag == 10:
            value = {}
            while True:
                child = self.unpack(">B")
                if child == 0:
                    return value
                name = self.string()
                value[name] = self.payload(child)
        if tag == 11:
            return [self.unpack(">i") for _ in range(self.count())]
        if tag == 12:
            return [self.unpack(">q") for _ in range(self.count())]
        raise ValueError(f"unknown NBT tag id {tag}")


def read(data: bytes) -> tuple[str, object]:
    reader = _Reader(data)
    tag = reader.unpack(">B")
    name = reader.string()
    return name, reader.payload(tag)
