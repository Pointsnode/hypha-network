#!/usr/bin/env python3
"""
HYPHA Nutrient - AGI Node with Tether WDK Wallet
One seed controls identity AND money
"""

import time
import asyncio
from typing import Optional, Dict, Any
from hypha_node import NeuralNode
from hypha_sdk.wallet_wdk import WDKWallet
from hypha_sdk.seed_manager import SeedManager

# Import validation if available
try:
    from hypha_sdk.validation import validate_ethereum_address, ValidationError
except ImportError:
    # Fallback validation
    class ValidationError(Exception):
        pass

    def validate_ethereum_address(address: str, param_name: str = "address") -> str:
        if not isinstance(address, str):
            raise ValidationError(f"{param_name} must be string")
        if not address.startswith('0x'):
            raise ValidationError(f"{param_name} must start with '0x'")
        if len(address) != 42:
            raise ValidationError(f"{param_name} must be 42 characters")
        return address


class HyphaNutrient(NeuralNode):
    """
    AGI Neural Node with Tether WDK Wallet Integration

    Features:
    - P2P discovery (Hyperswarm)
    - Binary state streaming (neural handshake)
    - Self-custodial USDT wallet (Tether WDK)
    - Atomic micro-payments
    """

    def __init__(self, seed: Optional[bytes] = None):
        """
        Initialize nutrient node

        Args:
            seed: 32-byte master seed (controls P2P + wallet)
        """
        # Initialize parent NeuralNode (handles P2P)
        super().__init__(seed)

        # Initialize WDK wallet from same seed
        self.wallet = WDKWallet(self.seed_manager.wallet_seed_hex)

        print(f"{int(time.time())} NUTRIENT_INIT NODE_ID={self.node_id.hex()[:16]} WALLET={self.wallet.address}")

    def verify_fuel(self, min_usdt: float = 1.0) -> bool:
        """
        Verify node has enough USDT to pay for tasks

        Args:
            min_usdt: Minimum USDT balance required

        Returns:
            True if balance sufficient
        """
        has_fuel = self.wallet.verify_fuel(min_usdt)

        balance = self.wallet.get_balance()
        print(f"{int(time.time())} FUEL_CHECK BAL={balance:.2f} MIN={min_usdt:.2f} OK={has_fuel}")

        return has_fuel

    async def atomic_pay(self, peer_address: str, amount_usdt: float) -> str:
        """
        Send atomic USDT payment to peer

        Args:
            peer_address: Peer's WDK wallet address (EVM)
            amount_usdt: Amount to send (e.g., 0.5 for $0.50)

        Returns:
            Transaction hash

        Raises:
            ValidationError: Invalid address
            RuntimeError: Payment failed
        """
        # Validate peer address
        try:
            peer_address = validate_ethereum_address(peer_address, "peer_address")
        except ValidationError as e:
            print(f"{int(time.time())} PAY_FAIL INVALID_ADDR")
            raise

        # Check balance
        balance = self.wallet.get_balance()
        if balance < amount_usdt:
            raise RuntimeError(f"Insufficient fuel: {balance} < {amount_usdt}")

        # Execute payment
        print(f"{int(time.time())} PAY_START TO={peer_address[:10]}... AMT={amount_usdt:.2f}")

        tx_hash = self.wallet.send_payment(peer_address, amount_usdt)

        print(f"{int(time.time())} PAY_COMPLETE TX={tx_hash[:16]}...")

        return tx_hash

    async def stream_with_payment(
        self,
        state_dict: Dict[str, Any],
        payment_to: Optional[str] = None,
        amount: Optional[float] = None
    ):
        """
        Stream AGI context and optionally pay peer

        Args:
            state_dict: AGI state to stream
            payment_to: Optional peer wallet address
            amount: Optional payment amount

        Returns:
            Transaction hash if payment made, else None
        """
        # Stream context
        await self.stream_context(state_dict)

        # Atomic payment if requested
        if payment_to and amount:
            return await self.atomic_pay(payment_to, amount)

        return None

    def get_wallet_address(self) -> str:
        """
        Get self-custodial USDT wallet address

        Returns:
            EVM address (Base L2)
        """
        return self.wallet.address


async def main():
    """Example: Nutrient node with wallet"""
    import hashlib

    # Create node with deterministic seed
    seed = hashlib.sha256(b"nutrient-demo-1").digest()
    node = HyphaNutrient(seed=seed)

    # Start P2P
    await node.start()

    # Check fuel
    has_fuel = node.verify_fuel(min_usdt=5.0)

    if has_fuel:
        # Stream AGI state
        await node.stream_context({
            "model": "gpt-4",
            "checkpoint": "v1.0",
            "embeddings_dim": 1536
        })
    else:
        print(f"Insufficient fuel - top up wallet at {node.get_wallet_address()}")

    # Keep alive for a bit
    await asyncio.sleep(10)

    await node.stop()


if __name__ == "__main__":
    asyncio.run(main())
