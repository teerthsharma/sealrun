import queue
import socket
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rcon

PASSWORD = "secret"
LIST_TEXT = "There are 0 of a max of 4 players online: "
BIG_BODIES = ["a" * 4096, "b" * 4096, "c" * 100]


class FakeServer:
    def __init__(self):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(4)
        self.listener.settimeout(0.2)
        self.port = self.listener.getsockname()[1]
        self.eofs = queue.Queue()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        self.thread.join(5)
        self.listener.close()

    def _serve(self):
        while not self.stop.is_set():
            try:
                conn, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                return
            self._handle(conn)

    def _handle(self, conn):
        with conn:
            conn.settimeout(5)
            buf = b""
            try:
                while True:
                    data = conn.recv(65536)
                    if not data:
                        self.eofs.put(True)
                        return
                    buf += data
                    while True:
                        try:
                            rid, ptype, body, buf = rcon.decode(buf)
                        except ValueError:
                            break
                        reply = self._reply(rid, ptype, body)
                        for i in range(0, len(reply), 1000):
                            conn.sendall(reply[i : i + 1000])
                            time.sleep(0.001)
            except OSError:
                return

    @staticmethod
    def _reply(rid, ptype, body):
        if ptype == rcon.LOGIN:
            return rcon.encode(rid if body == PASSWORD else -1, 2, "")
        if ptype == rcon.COMMAND and body == "list":
            return rcon.encode(rid, rcon.RESPONSE, LIST_TEXT)
        if ptype == rcon.COMMAND and body == "big":
            return b"".join(rcon.encode(rid, rcon.RESPONSE, text) for text in BIG_BODIES)
        return rcon.encode(rid, rcon.RESPONSE, "Unknown request 0")


class Lab(unittest.TestCase):
    def rcon_wrong_password_and_long_reply_against_fake(self):
        server = FakeServer()
        self.addCleanup(server.close)
        before = threading.active_count()

        with self.assertRaises(PermissionError):
            rcon.Client("127.0.0.1", server.port, "wrong")
        self.assertTrue(server.eofs.get(timeout=5))

        client = rcon.Client("127.0.0.1", server.port, PASSWORD)
        self.assertEqual(client.command("list"), LIST_TEXT)
        big = client.command("big")
        self.assertEqual(big, "a" * 4096 + "b" * 4096 + "c" * 100)
        self.assertEqual(len(big), 8292)
        self.assertEqual(client.command("list"), LIST_TEXT)

        client.close()
        self.assertTrue(server.eofs.get(timeout=5))
        self.assertEqual(threading.active_count(), before)


if __name__ == "__main__":
    unittest.main()
