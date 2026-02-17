#!/usr/bin/env python3
"""
HYPHA Bootstrap Node + Groot Agent
First agent on the Hypha P2P mesh.

Runs a persistent Kademlia DHT node and announces Groot as available for hire.
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime

# Add parent to path for local dev
sys.path.insert(0, '.')

from hypha_sdk import SeedManager
from hypha_sdk.discovery import Discovery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HYPHA] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

# Groot's permanent identity
GROOT_SEED = "groot-hypha-agent-v1"
BOOTSTRAP_PORT = 8468
ANNOUNCE_TOPIC = "hypha-agents"

# Groot's service listing
GROOT_SERVICE = {
    "agent_id": None,  # set at runtime
    "name": "Groot 🌱",
    "wallet": None,  # set at runtime
    "services": [
        {
            "name": "web-research",
            "description": "Search the web and summarize findings on any topic",
            "price_usdt": 0.50,
        },
        {
            "name": "code-review",
            "description": "Review Python/JS code for bugs, security issues, and improvements",
            "price_usdt": 1.00,
        },
        {
            "name": "text-writing",
            "description": "Write documentation, blog posts, or technical content",
            "price_usdt": 0.75,
        },
    ],
    "status": "online",
    "announced_at": None,
}


async def main():
    sm = SeedManager.from_string(GROOT_SEED)

    log.info("=" * 60)
    log.info("  HYPHA NETWORK — Bootstrap Node")
    log.info("=" * 60)
    log.info(f"  Agent:    Groot 🌱")
    log.info(f"  Node ID:  {sm.node_id_hex}")
    log.info(f"  Wallet:   {sm.wallet_address}")
    log.info(f"  Port:     {BOOTSTRAP_PORT}")
    log.info(f"  Topic:    {ANNOUNCE_TOPIC}")
    log.info("=" * 60)

    # Initialize discovery with our seed-derived node ID
    discovery = Discovery(port=BOOTSTRAP_PORT, node_id=sm.node_id[:20])
    await discovery.start()

    # Populate service listing
    GROOT_SERVICE["agent_id"] = sm.node_id_hex
    GROOT_SERVICE["wallet"] = sm.wallet_address
    GROOT_SERVICE["announced_at"] = datetime.utcnow().isoformat() + "Z"

    # Announce on the mesh
    await discovery.announce(ANNOUNCE_TOPIC, GROOT_SERVICE)
    log.info("Announced on mesh — Groot is live! 🌱")

    # Re-announce periodically to stay fresh in DHT
    async def reannounce_loop():
        while True:
            await asyncio.sleep(300)  # every 5 minutes
            GROOT_SERVICE["announced_at"] = datetime.utcnow().isoformat() + "Z"
            await discovery.announce(ANNOUNCE_TOPIC, GROOT_SERVICE)
            peers = await discovery.discover_peers(ANNOUNCE_TOPIC)
            log.info(f"Re-announced. {len(peers)} peer(s) on mesh.")

    # Handle shutdown
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def shutdown():
        log.info("Shutting down...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    # Run
    reannounce_task = asyncio.create_task(reannounce_loop())

    log.info("Bootstrap node running. Press Ctrl+C to stop.")
    await stop_event.wait()

    reannounce_task.cancel()
    await discovery.stop()
    log.info("Groot offline. See you next time. 🌱")


if __name__ == "__main__":
    asyncio.run(main())
