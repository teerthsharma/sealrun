import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import orderrun


class FakeClient:
    def __init__(self, replies):
        self.replies = list(replies)
        self.sent = []

    def command(self, text):
        self.sent.append(text)
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


class Lab(unittest.TestCase):
    def wait_loaded_polls_bedrock_probe_until_loaded(self):
        client = FakeClient(["Forced chunks", "Test failed", "Test failed", "Test passed"])
        sleeps = []
        result = orderrun.wait_loaded(client, -3, 5, sleep=sleeps.append)
        self.assertIs(result, True)
        self.assertEqual(client.sent[0], "forceload add -48 80")
        self.assertEqual(len(client.sent), 4)
        self.assertEqual(set(client.sent[1:]), {"execute if block -48 0 80 minecraft:bedrock"})

        client = FakeClient(["Forced chunks", "Test failed"])
        sleeps = []
        result = orderrun.wait_loaded(client, -3, 5, timeout=2.0, poll=0.5, sleep=sleeps.append)
        self.assertIs(result, False)
        self.assertEqual(client.sent[0], "forceload add -48 80")
        self.assertEqual(sum(sleeps), 2.0)


if __name__ == "__main__":
    unittest.main()
