"""
HYPHA Messaging Demo
Demonstrates P2P messaging between buyer and provider agents
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from hypha_sdk import Agent


async def provider_agent():
    """Provider agent that listens for and accepts tasks"""
    print("\n🤖 PROVIDER AGENT STARTING")
    print("=" * 60)

    # Create provider agent
    provider = Agent()
    print(f"✅ Provider ID: {provider.agent_id}")
    if provider.account:
        print(f"✅ Address: {provider.account.address}")

    # Define custom task handler
    async def handle_task_request(escrow_id, task_description, amount, deadline, requirements=None):
        """Handle incoming task requests"""
        print(f"\n📩 NEW TASK REQUEST:")
        print(f"  Escrow ID: {escrow_id}")
        print(f"  Task: {task_description}")
        print(f"  Payment: ${amount}")
        print(f"  Deadline: {deadline}")

        # Auto-accept tasks over $5
        if amount >= 5.0:
            print(f"✅ ACCEPTING task (amount >= $5)")
            return True
        else:
            print(f"❌ REJECTING task (amount < $5)")
            return False

    # Define payment handler
    async def handle_payment(escrow_id, amount, tx_hash, from_address, to_address):
        """Handle payment notifications"""
        print(f"\n💰 PAYMENT RECEIVED!")
        print(f"  Escrow ID: {escrow_id}")
        print(f"  Amount: ${amount}")
        print(f"  Tx: {tx_hash}")
        print(f"\n🎉 Task payment complete!")

    # Set handlers
    provider.set_task_handler(handle_task_request)
    provider.set_payment_handler(handle_payment)

    print(f"\n📡 Announcing availability on network...")

    # Announce on P2P network
    try:
        await provider.announce("hypha-agents")
        print(f"✅ Announced on hypha-agents topic")
    except Exception as e:
        print(f"⚠️  Announcement: {e}")

    print(f"\n⏳ Listening for task requests...")
    print(f"💡 Press Ctrl+C to stop\n")

    # Start listening for messages
    try:
        await provider.start_listening()
    except KeyboardInterrupt:
        print("\n\n👋 Provider agent stopped")


async def buyer_agent():
    """Buyer agent that hires providers"""
    print("\n👤 BUYER AGENT STARTING")
    print("=" * 60)

    # Create buyer agent
    buyer = Agent()
    print(f"✅ Buyer ID: {buyer.agent_id}")
    if buyer.account:
        print(f"✅ Address: {buyer.account.address}")
        print(f"💰 Balance: {buyer.check_balance()} ETH")

    # Define task response handler
    async def handle_task_response(escrow_id, accepted, estimated_completion, message):
        """Handle provider responses"""
        if accepted:
            print(f"\n✅ TASK ACCEPTED by provider")
            print(f"  Escrow ID: {escrow_id}")
            if estimated_completion:
                print(f"  ETA: {estimated_completion}")
            if message:
                print(f"  Message: {message}")
        else:
            print(f"\n❌ TASK REJECTED by provider")
            print(f"  Escrow ID: {escrow_id}")
            if message:
                print(f"  Reason: {message}")

    # Define completion handler
    async def handle_task_complete(escrow_id, result, proof):
        """Handle task completion"""
        print(f"\n🎯 TASK COMPLETED!")
        print(f"  Escrow ID: {escrow_id}")
        print(f"  Result: {result}")
        if proof:
            print(f"  Proof: {proof}")

        print(f"\n💳 Releasing payment...")

    # Set handlers
    buyer.message_handler.on_task_response(handle_task_response)
    buyer.message_handler.on_task_complete(handle_task_complete)

    print(f"\n🔍 Discovering providers...")

    # Discover providers
    try:
        peers = await buyer.discover_peers("hypha-agents")
        print(f"✅ Found {len(peers)} providers")
    except Exception as e:
        print(f"⚠️  Discovery: {e}")
        peers = []

    # Example: Send task request
    provider_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"  # Example

    print(f"\n💼 Sending task request to provider...")
    print(f"  Provider: {provider_address}")

    try:
        # Note: This would normally create an escrow
        # For demo purposes, we're just showing the messaging flow
        escrow_id = f"demo_escrow_{int(asyncio.get_event_loop().time())}"

        # Send task request via messaging
        await buyer.messaging.send_task_request(
            recipient=provider_address,
            escrow_id=escrow_id,
            task_description="Analyze blockchain transaction patterns",
            amount=10.0,
            deadline=int(asyncio.get_event_loop().time() + 86400)
        )

        print(f"✅ Task request sent")
        print(f"  Escrow ID: {escrow_id}")

        # Listen for response
        print(f"\n⏳ Waiting for provider response...")

        # Listen for a bit
        await asyncio.sleep(10)

    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n👋 Buyer agent finished")


async def main():
    """Run messaging demo"""
    import argparse

    parser = argparse.ArgumentParser(description="HYPHA Messaging Demo")
    parser.add_argument(
        '--mode',
        choices=['provider', 'buyer'],
        required=True,
        help='Run as provider or buyer'
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🌐 HYPHA P2P MESSAGING DEMO")
    print("=" * 60)

    if args.mode == 'provider':
        await provider_agent()
    else:
        await buyer_agent()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
