import raftos
import asyncio
import sys
import logging

PORTS = {1:8001, 2:8002, 3:8003, 4:8004, 5:8005}

HOSTS = {
    1: "172.28.0.2",
    2: "172.28.0.3",
    3: "172.28.0.4",
    4: "172.28.0.5",
    5: "172.28.0.6"
}

async def main(node_id):
    port = PORTS[node_id]
    host = HOSTS[node_id]

    node_address = f"{host}:{port}"

    cluster = [
        "172.28.0.2:8001",
        "172.28.0.3:8002",
        "172.28.0.4:8003",
	"172.28.0.5:8004",
    	"172.28.0.6:8005"
    ]

    print(f"Starting Node {node_id} at {node_address}", flush=True)

    await raftos.register(node_address, cluster=cluster)

    last_leader = None

    while True:
        leader = raftos.get_leader()

        if leader != last_leader:
            print(f"[Node {node_id}] Leader changed: {leader}", flush=True)
            last_leader = leader

        if leader == node_address:
            print(f"[LEADER Node {node_id}] I am the leader", flush=True)

        elif leader is None:
            print(f"[Node {node_id}] Waiting for leader election...", flush=True)

        else:
            print(f"[FOLLOWER Node {node_id}] Current leader: {leader}", flush=True)

        await asyncio.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python node.py <node_id>")
        sys.exit(1)

    node_id = int(sys.argv[1])

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main(node_id))
