"""
HYPHA Complete Workflow Example
Demonstrates end-to-end agent coordination with P2P discovery and payments
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hypha_sdk import Agent


async def buyer_workflow():
    """Example: Buyer hiring a provider agent"""
    print("\n=== BUYER AGENT ===")

    # 1. Create buyer agent
    buyer = Agent()
    print(f"✅ Created buyer agent: {buyer.agent_id}")
    print(f"💰 ETH Balance: {buyer.check_balance()} ETH")

    # 2. Discover available provider agents
    print("\n🔍 Discovering provider agents...")
    peers = await buyer.discover_peers(topic="hypha-agents")
    print(f"Found {len(peers)} peers")

    if not peers:
        print("⚠️  No providers found. Start a provider agent first.")
        return

    # 3. Hire a provider
    provider_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"  # Example address
    print(f"\n💼 Hiring provider: {provider_address}")

    try:
        escrow_id = await buyer.hire(
            peer=provider_address,
            amount=10.0,  # $10 USDT
            task="Analyze blockchain transaction patterns",
            deadline_hours=24
        )
        print(f"✅ Escrow created: {escrow_id}")

        # 4. Check escrow status
        status = buyer.get_escrow_status(escrow_id)
        print(f"\n📊 Escrow Status:")
        print(f"  Provider: {status['provider']}")
        print(f"  Amount: ${status['amount']}")
        print(f"  Task: {status['task']}")
        print(f"  Status: {status['status']}")
        print(f"  Deadline: {status['deadline']}")

        # 5. After work is done, complete the task
        print("\n✅ Completing task and releasing payment...")
        receipt = await buyer.complete_task(escrow_id)
        print(f"Transaction confirmed: {receipt['transactionHash'].hex()}")

    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("  1. Set PRIVATE_KEY in .env")
        print("  2. Deployed the escrow contract")
        print("  3. Set ESCROW_CONTRACT_ADDRESS in .env")


async def provider_workflow():
    """Example: Provider announcing availability"""
    print("\n=== PROVIDER AGENT ===")

    # 1. Create provider agent
    provider = Agent()
    print(f"✅ Created provider agent: {provider.agent_id}")
    print(f"📍 Address: {provider.account.address if provider.account else 'Not configured'}")

    # 2. Announce availability on P2P network
    print("\n📢 Announcing availability on P2P network...")
    try:
        result = await provider.announce(topic="hypha-agents")
        print(f"✅ Announced: {result}")
        print("\n⏳ Listening for task requests...")
        print("(In production, implement message handler to receive tasks)")

        # Keep running to accept connections
        await asyncio.sleep(30)

    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have Node.js and dependencies installed:")
        print("  npm install")


async def main():
    """Run example workflow"""
    import argparse

    parser = argparse.ArgumentParser(description="HYPHA Workflow Example")
    parser.add_argument(
        '--mode',
        choices=['buyer', 'provider'],
        required=True,
        help='Run as buyer or provider'
    )
    args = parser.parse_args()

    print("🌐 HYPHA - P2P Infrastructure for Autonomous AI Agents")

    if args.mode == 'buyer':
        await buyer_workflow()
    else:
        await provider_workflow()


if __name__ == "__main__":
    asyncio.run(main())
