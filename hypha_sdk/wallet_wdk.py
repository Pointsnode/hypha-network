"""
Tether WDK Wallet Interface
Python wrapper for Node.js WDK bridge

NOTE: Currently using mock WDK bridge until Tether packages can be installed.
Replace bridge with real WDK implementation once npm cache is fixed.
"""

import os
import json
import subprocess
from typing import Dict, Any, Optional


def _get_wallet_bridge_path() -> str:
    """Get path to wallet bridge script"""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Try development structure
    dev_path = os.path.join(os.path.dirname(current_dir), 'src', 'wallet', 'wallet_bridge.js')
    if os.path.exists(dev_path):
        return dev_path

    # Try installed package structure
    pkg_path = os.path.join(current_dir, '..', 'src', 'wallet', 'wallet_bridge.js')
    if os.path.exists(pkg_path):
        return pkg_path

    raise FileNotFoundError("wallet_bridge.js not found")


class WDKWallet:
    """
    Tether WDK Wallet Interface

    Manages USDT on Base L2 via Tether's official WDK
    """

    def __init__(self, seed_hex: str):
        """
        Initialize WDK wallet from seed

        Args:
            seed_hex: 64-character hex string (32 bytes)
        """
        if len(seed_hex) != 64:
            raise ValueError("Seed hex must be 64 characters (32 bytes)")

        self._seed_hex = seed_hex
        self._address = None
        self._initialize()

    def _run_bridge(self, command: str, *args) -> Dict[str, Any]:
        """
        Run wallet bridge command

        Args:
            command: Command name (init, balance, send)
            *args: Additional arguments

        Returns:
            Response dict from bridge

        Raises:
            RuntimeError: If bridge call fails
        """
        bridge_path = _get_wallet_bridge_path()

        result = subprocess.run(
            ['node', bridge_path, command, *args],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"Bridge call failed: {result.stderr}")

        response = json.loads(result.stdout)

        if not response.get('success'):
            raise RuntimeError(f"WDK error: {response.get('error')}")

        return response

    def _initialize(self):
        """Initialize wallet and get address"""
        response = self._run_bridge('init', self._seed_hex)
        self._address = response['address']

    @property
    def address(self) -> str:
        """Get wallet address"""
        return self._address

    def get_balance(self) -> float:
        """
        Get USDT balance

        Returns:
            USDT balance (float)
        """
        response = self._run_bridge('balance', self._seed_hex, self._address)
        return float(response['balance'])

    def send_payment(self, to_address: str, amount_usdt: float) -> str:
        """
        Send USDT payment

        Args:
            to_address: Recipient address
            amount_usdt: Amount in USDT (e.g., 10.5)

        Returns:
            Transaction hash
        """
        response = self._run_bridge(
            'send',
            self._seed_hex,
            to_address,
            str(amount_usdt)
        )

        return response['txHash']

    def verify_fuel(self, min_balance: float = 1.0) -> bool:
        """
        Verify wallet has minimum USDT balance

        Args:
            min_balance: Minimum required balance

        Returns:
            True if balance >= min_balance
        """
        balance = self.get_balance()
        return balance >= min_balance
