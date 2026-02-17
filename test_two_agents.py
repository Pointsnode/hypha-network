#!/usr/bin/env python3
"""
Two-agent mesh test — proves P2P discovery + messaging end-to-end.
Agent A (Alice) announces, Agent B (Bob) discovers Alice, sends a message.
"""

import asyncio
import sys
import os
import json

# Ensure hypha_sdk is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hypha_sdk.discovery import Discovery
from hypha_sdk.transport import MessageTransport
from hypha_sdk.protocol import Message, MessageType, create_message
from hypha_sdk.seed_manager import SeedManager


async def run_test():
    print("=" * 60)
    print("HYPHA Two-Agent Mesh Test")
    print("=" * 60)

    # --- Create two agents from different seeds ---
    alice_seed = SeedManager.from_string("alice-test-agent-2026")
    bob_seed = SeedManager.from_string("bob-test-agent-2026")

    print(f"\n🅰️  Alice  node_id={alice_seed.node_id_hex}  wallet={alice_seed.wallet_address}")
    print(f"🅱️  Bob    node_id={bob_seed.node_id_hex}  wallet={bob_seed.wallet_address}")

    # --- Discovery layer (Kademlia DHT) ---
    alice_discovery = Discovery(port=8470, node_id=alice_seed.node_id[:20])
    bob_discovery = Discovery(port=8471, bootstrap_nodes=[("127.0.0.1", 8470)], node_id=bob_seed.node_id[:20])

    print("\n📡 Starting DHT nodes...")
    await alice_discovery.start()
    await bob_discovery.start()
    print("   ✅ Both DHT nodes up")

    # --- Alice announces ---
    topic = "hypha-test"
    alice_info = {
        "agent_id": alice_seed.node_id_hex,
        "wallet_address": alice_seed.wallet_address,
        "services": ["code-review", "translation"],
    }
    await alice_discovery.announce(topic, alice_info)
    print(f"\n📢 Alice announced on topic '{topic}'")

    # Small delay for DHT propagation
    await asyncio.sleep(1)

    # --- Bob discovers peers ---
    peers = await bob_discovery.discover_peers(topic)
    print(f"\n🔍 Bob discovered {len(peers)} peer(s):")
    for p in peers:
        print(f"   → {p.get('agent_id', '?')} @ {p.get('wallet_address', '?')}")
        print(f"     services: {p.get('services', [])}")

    if not peers:
        print("\n❌ FAIL: No peers discovered")
        await alice_discovery.stop()
        await bob_discovery.stop()
        return False

    # --- Messaging layer (TCP) ---
    received_messages = []

    alice_transport = MessageTransport(
        alice_seed.node_id_hex,
        bytes.fromhex(alice_seed.wallet_private_key.replace("0x", ""))
    )

    bob_transport = MessageTransport(
        bob_seed.node_id_hex,
        bytes.fromhex(bob_seed.wallet_private_key.replace("0x", ""))
    )

    # Alice listens for task requests
    async def alice_handler(msg: Message):
        print(f"\n📬 Alice received: type={msg.type} from={msg.sender}")
        print(f"   payload={json.dumps(msg.payload, indent=2)}")
        received_messages.append(msg)

    alice_transport.register_handler(MessageType.TASK_REQUEST, alice_handler)

    # Start Alice's TCP listener in background
    listen_task = asyncio.create_task(
        alice_transport.start_listening(host="127.0.0.1", port=8480)
    )
    await asyncio.sleep(0.5)  # let server start

    # Bob sends a task request to Alice
    print("\n✉️  Bob sending task request to Alice...")
    msg = create_message(
        MessageType.TASK_REQUEST,
        sender=bob_seed.node_id_hex,
        recipient=alice_seed.node_id_hex,
        escrow_id="test-escrow-001",
        task="Review my Python code for security issues",
        amount=5.0,
        deadline=1739900000,
    )
    sent = await bob_transport.send_message(msg, host="127.0.0.1", port=8480)
    print(f"   sent={sent}")

    # Wait for message to arrive
    await asyncio.sleep(1)

    # --- Results ---
    print("\n" + "=" * 60)
    if len(received_messages) > 0 and sent:
        print("✅ PASS: Full loop working!")
        print(f"   • DHT discovery: {len(peers)} peer(s) found")
        print(f"   • TCP messaging: {len(received_messages)} message(s) delivered")
    else:
        print("❌ FAIL")
        print(f"   • Peers found: {len(peers)}")
        print(f"   • Messages received: {len(received_messages)}")
    print("=" * 60)

    # Cleanup
    listen_task.cancel()
    await alice_discovery.stop()
    await bob_discovery.stop()

    return len(received_messages) > 0


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
