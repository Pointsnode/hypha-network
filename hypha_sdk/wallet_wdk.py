"""
HYPHA Wallet — Pure Python USDT settlement on Base L2

One seed controls identity + wallet. No Node.js required.

Protocol fee: 0.5% of each payment goes to the Hypha Foundation wallet
to fund protocol development and maintenance. This fee is transparent
and can be disabled per-transaction via include_fee=False.
"""
from web3 import Web3
from eth_account import Account
from typing import Optional
import logging

log = logging.getLogger(__name__)

# Base L2 USDT contract (6 decimals)
BASE_USDT_ADDRESS = "0x..."  # TODO: mainnet address TBD
BASE_SEPOLIA_USDT = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"

# Minimal ERC-20 ABI for transfer + balanceOf
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

# Hypha Foundation fee wallet
FOUNDATION_WALLET = "0x5C8827E46E27a188dbcA9B100f72bf48f01dfA2E"  # Hypha Foundation
PROTOCOL_FEE_BPS = 50  # 0.5% = 50 basis points


class Wallet:
    """
    Pure Python USDT wallet for HYPHA agents.

    Derives EVM address from the same seed used for P2P identity.
    Settles payments in USDT on Base L2 with automatic 0.5% protocol fee.

    The protocol fee (0.5%) is sent to the Hypha Foundation wallet on each
    payment when include_fee=True (default). This funds protocol development.
    """

    def __init__(self, private_key: str, web3_provider: str = "https://sepolia.base.org", usdt_address: Optional[str] = None):
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        usdt_addr = usdt_address or BASE_SEPOLIA_USDT
        self.usdt = self.w3.eth.contract(
            address=Web3.to_checksum_address(usdt_addr),
            abi=ERC20_ABI
        )

    def balance(self) -> float:
        """Get USDT balance in human-readable units (6 decimals)"""
        raw = self.usdt.functions.balanceOf(self.address).call()
        return raw / 1e6

    def verify_fuel(self, min_usdt: float = 1.0) -> bool:
        """Check if wallet has enough USDT to transact"""
        return self.balance() >= min_usdt

    def send_payment(self, to: str, amount_usdt: float, include_fee: bool = True) -> dict:
        """
        Send USDT payment with optional protocol fee.

        If include_fee=True (default), splits payment:
          - 99.5% goes to `to`
          - 0.5% goes to Hypha Foundation (PROTOCOL_FEE_BPS / 10000)

        Args:
            to: Recipient address
            amount_usdt: Total amount in USDT
            include_fee: Whether to include the 0.5% protocol fee

        Returns:
            Dict with tx_hash(es) and amounts
        """
        to = Web3.to_checksum_address(to)
        total_units = int(amount_usdt * 1e6)

        results = {}

        if include_fee and FOUNDATION_WALLET != "0x...":
            fee_units = total_units * PROTOCOL_FEE_BPS // 10000
            payment_units = total_units - fee_units

            # Send main payment
            results['payment_tx'] = self._transfer(to, payment_units)
            results['payment_amount'] = payment_units / 1e6

            # Send fee
            if fee_units > 0:
                results['fee_tx'] = self._transfer(FOUNDATION_WALLET, fee_units)
                results['fee_amount'] = fee_units / 1e6
        else:
            results['payment_tx'] = self._transfer(to, total_units)
            results['payment_amount'] = total_units / 1e6

        return results

    def _transfer(self, to: str, amount_units: int) -> str:
        """Execute ERC-20 transfer, return tx hash"""
        tx = self.usdt.functions.transfer(to, amount_units).build_transaction({
            'from': self.address,
            'nonce': self.w3.eth.get_transaction_count(self.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
        })
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()
