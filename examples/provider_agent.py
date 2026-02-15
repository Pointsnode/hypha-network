#!/usr/bin/env python3
"""
HYPHA Provider Agent - Accepts tasks and earns USDT
"""

import sys
import os
# Add parent directory to path so we can import hypha modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import hashlib
from hypha_nutrient import HyphaNutrient

async def run_provider():
    """Run a provider agent that accepts tasks"""

    # Create deterministic seed for this agent
    seed = hashlib.sha256(b"provider-agent-alpha").digest()

    # Initialize agent
    agent = HyphaNutrient(seed=seed)

    print("=" * 60)
    print("🤖 HYPHA Provider Agent Started")
    print("=" * 60)
    print(f"Node ID: {agent.node_id.hex()[:16]}...")
    print(f"Wallet:  {agent.get_wallet_address()}")
    print(f"Network: Base Sepolia")
    print("=" * 60)

    # Start P2P discovery
    await agent.start()

    print("\n✅ Provider ready - listening for tasks...")
    print("   Press Ctrl+C to stop\n")

    # Keep running and accepting tasks
    try:
        while True:
            # Check for fuel
            has_fuel = agent.verify_fuel(min_usdt=0.1)

            # Stream status every 30 seconds
            await asyncio.sleep(30)
            await agent.stream_context({
                "type": "provider",
                "status": "ready",
                "has_fuel": has_fuel,
                "wallet": agent.get_wallet_address()
            })

    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down provider...")
        await agent.stop()
        print("✅ Provider stopped")

if __name__ == "__main__":
    asyncio.run(run_provider())
