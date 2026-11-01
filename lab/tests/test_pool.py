import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pool

DELAY = {0: 0.2, 1: 0.05, 2: 0.15, 3: 0.1}


def counting_fn(state):
    lock = threading.Lock()
    state.update(now=0, peak=0, calls=0)

    def fn(job):
        with lock:
            state["now"] += 1
            state["calls"] += 1
            state["peak"] = max(state["peak"], state["now"])
        time.sleep(DELAY[job])
        with lock:
            state["now"] -= 1
        return f"r{job}"

    return fn


class Lab(unittest.TestCase):
    def pool_returns_results_in_job_order_and_refuses_four_servers(self):
        jobs = [0, 1, 2, 3]
        expected = ["r0", "r1", "r2", "r3"]

        state = {}
        self.assertEqual(pool.run(jobs, counting_fn(state), 2), expected)
        self.assertEqual(state["peak"], 2, state)

        state = {}
        self.assertEqual(pool.run(jobs, counting_fn(state), 1), expected)
        self.assertEqual(state["peak"], 1, state)

        for workers in (3, 4):
            state = {}
            with self.assertRaises(ValueError):
                pool.run(jobs, counting_fn(state), workers)
            self.assertEqual(state["calls"], 0, state)

        def boom(job):
            if job == 2:
                raise RuntimeError("job 2 failed")
            return job

        with self.assertRaises(RuntimeError):
            pool.run(jobs, boom, 2)


if __name__ == "__main__":
    unittest.main()
