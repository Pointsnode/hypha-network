"""
HYPHA Three-Line Example
Autonomous agent coordination in 3 lines
"""

import asyncio
from hypha_sdk import Agent

async def main():
    # 1. Create agent
    agent = Agent()

    # 2. Hire another agent (use a valid Ethereum address)
    escrow_id = await agent.hire(
        peer="0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        amount=10.0,
        task="Analyze blockchain data"
    )

    # 3. Get paid automatically
    async def on_payment(payment):
        print(f"Received payment: {payment}")

    await agent.get_paid(on_payment)

if __name__ == "__main__":
    asyncio.run(main())
