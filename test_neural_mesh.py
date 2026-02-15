#!/usr/bin/env python3
"""
Test HYPHA Neural Mesh - Dual Node Connection
Demonstrates AGI-to-AGI state sharing
"""

import asyncio
import hashlib
from hypha_node import NeuralNode


async def run_node_a():
    """Run Neural Node A"""
    seed = hashlib.sha256(b"neural-node-A").digest()
    node = NeuralNode(seed=seed)

    print(f"[A] NODE_START ID={node.node_id.hex()[:16]}")

    await node.start()

    try:
        for i in range(10):
            await asyncio.sleep(3)

            # Simulate AGI state: embeddings, loss, checkpoint
            state = {
                "node": "A",
                "iteration": i,
                "embeddings_dim": 768,
                "model_params": 1_000_000 + i * 10000,
                "training_loss": round(1.0 / (i + 1), 4),
                "checkpoint_hash": hashlib.sha256(f"A-{i}".encode()).hexdigest()[:16]
            }

            await node.stream_context(state)

    except KeyboardInterrupt:
        pass
    finally:
        await node.stop()


async def run_node_b():
    """Run Neural Node B"""
    seed = hashlib.sha256(b"neural-node-B").digest()
    node = NeuralNode(seed=seed)

    print(f"[B] NODE_START ID={node.node_id.hex()[:16]}")

    await node.start()

    try:
        for i in range(10):
            await asyncio.sleep(4)

            # Different AGI state
            state = {
                "node": "B",
                "iteration": i,
                "embeddings_dim": 1024,
                "model_params": 2_000_000 + i * 20000,
                "validation_accuracy": round(0.8 + (i * 0.01), 4),
                "checkpoint_hash": hashlib.sha256(f"B-{i}".encode()).hexdigest()[:16]
            }

            await node.stream_context(state)

    except KeyboardInterrupt:
        pass
    finally:
        await node.stop()


async def main():
    """Run both nodes in parallel"""
    print("=" * 60)
    print("HYPHA Neural Mesh Test - Dual Node P2P")
    print("=" * 60)
    print()

    # Run both nodes concurrently
    await asyncio.gather(
        run_node_a(),
        run_node_b()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nMesh terminated.")
