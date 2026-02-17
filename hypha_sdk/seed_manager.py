"""
Unified Seed Manager - One seed for P2P and Wallet
"""

import os
import hashlib
from typing import Optional
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder
from eth_account import Account


class SeedManager:
    """
    Manages unified 32-byte seed for both:
    - P2P identity (Ed25519)
    - EVM wallet (via WDK)
    """

    def __init__(self, seed_bytes: Optional[bytes] = None):
        """
        Initialize with 32-byte seed

        Args:
            seed_bytes: 32-byte master seed (generates random if None)
        """
        if seed_bytes is None:
            seed_bytes = os.urandom(32)

        if len(seed_bytes) != 32:
            raise ValueError("Seed must be exactly 32 bytes")

        self._master_seed = seed_bytes

        # Derive P2P identity (Ed25519)
        p2p_seed = hashlib.sha256(self._master_seed + b'hypha.p2p').digest()
        self._p2p_signing_key = SigningKey(p2p_seed)
        self._p2p_verify_key = self._p2p_signing_key.verify_key
        self._node_id = self._p2p_verify_key.encode(encoder=RawEncoder)

        # Derive wallet seed (for WDK)
        self._wallet_seed = hashlib.sha256(self._master_seed + b'hypha.wallet').digest()

    @property
    def node_id(self) -> bytes:
        """Get P2P node ID (32 bytes)"""
        return self._node_id

    @property
    def node_id_hex(self) -> str:
        """Get P2P node ID as hex string (first 16 chars for display)"""
        return self._node_id.hex()[:16]

    @property
    def p2p_signing_key(self) -> SigningKey:
        """Get Ed25519 signing key for P2P messages"""
        return self._p2p_signing_key

    @property
    def wallet_seed_hex(self) -> str:
        """Get wallet seed as hex string (for WDK initialization)"""
        return self._wallet_seed.hex()

    @property
    def wallet_address(self) -> str:
        """Derive EVM wallet address from wallet seed (used as private key)"""
        acct = Account.from_key(self._wallet_seed)
        return acct.address

    @property
    def wallet_private_key(self) -> str:
        """Get wallet private key hex (the wallet_seed IS the private key)"""
        return '0x' + self._wallet_seed.hex()

    def get_master_seed(self) -> bytes:
        """
        Get master seed (use with caution - should remain secret)

        WARNING: Never log or expose this value
        """
        return self._master_seed

    @classmethod
    def from_hex(cls, hex_string: str) -> 'SeedManager':
        """
        Create SeedManager from hex string

        Args:
            hex_string: 64-character hex string (32 bytes)
        """
        seed_bytes = bytes.fromhex(hex_string)
        return cls(seed_bytes)

    @classmethod
    def from_string(cls, seed_string: str) -> 'SeedManager':
        """
        Create SeedManager from arbitrary string (hashed to 32 bytes)

        Args:
            seed_string: Any string (will be SHA256 hashed)
        """
        seed_bytes = hashlib.sha256(seed_string.encode()).digest()
        return cls(seed_bytes)
