import struct

LOGIN = 3
COMMAND = 2
RESPONSE = 0


def encode(req_id: int, ptype: int, body: str) -> bytes:
    data = body.encode("utf-8")
    return struct.pack("<iii", 10 + len(data), req_id, ptype) + data + b"\x00\x00"


def decode(buf: bytes) -> tuple[int, int, str, bytes]:
    if len(buf) < 4:
        raise ValueError("short packet")
    (length,) = struct.unpack_from("<i", buf)
    if length < 10 or len(buf) < 4 + length:
        raise ValueError("short packet")
    req_id, ptype = struct.unpack_from("<ii", buf, 4)
    if buf[4 + length - 2 : 4 + length] != b"\x00\x00":
        raise ValueError("missing terminator")
    body = buf[12 : 4 + length - 2].decode("utf-8")
    return req_id, ptype, body, buf[4 + length :]
