import socket
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


class Client:
    def __init__(self, host, port, password, timeout=10.0):
        self._sock = socket.create_connection((host, port), timeout=timeout)
        self._buf = b""
        self._next_id = 2
        try:
            self._sock.sendall(encode(1, LOGIN, password))
            if self._recv()[0] == -1:
                raise PermissionError("rcon login rejected")
        except BaseException:
            self._sock.close()
            raise

    def command(self, text: str) -> str:
        n = self._next_id
        self._next_id += 2
        self._sock.sendall(encode(n, COMMAND, text))
        parts = []
        while not parts:
            rid, _, body = self._recv()
            if rid == n:
                parts.append(body)
        self._sock.sendall(encode(n + 1, RESPONSE, ""))
        while True:
            rid, _, body = self._recv()
            if rid == n + 1:
                return "".join(parts)
            if rid == n:
                parts.append(body)

    def close(self) -> None:
        self._sock.close()

    def _recv(self) -> tuple[int, int, str]:
        while True:
            if len(self._buf) >= 4:
                (length,) = struct.unpack_from("<i", self._buf)
                if len(self._buf) >= 4 + length:
                    req_id, ptype, body, self._buf = decode(self._buf)
                    return req_id, ptype, body
            data = self._sock.recv(65536)
            if not data:
                raise ConnectionError("rcon connection closed")
            self._buf += data
