from concurrent.futures import ThreadPoolExecutor


def run(jobs, fn, workers):
    if workers not in (1, 2):
        raise ValueError(f"workers must be 1 or 2, got {workers}")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(fn, job) for job in jobs]
        return [f.result() for f in futures]
