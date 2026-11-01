import time


def wait_loaded(client, cx, cz, timeout=30.0, poll=0.5, sleep=time.sleep):
    x, z = cx * 16, cz * 16
    client.command(f"forceload add {x} {z}")
    waited = 0.0
    while True:
        if "Test passed" in client.command(f"execute if block {x} 0 {z} minecraft:bedrock"):
            return True
        if waited >= timeout:
            return False
        sleep(poll)
        waited += poll
