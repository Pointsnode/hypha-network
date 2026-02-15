"""
HYPHA Core P2P Connectivity Primitive
Blitz-ready production code for agent coordination
"""

import hashlib
import json
import subprocess
import sys
from typing import Optional, Dict, Any

class NetworkError(Exception):
    """Deterministic P2P network error."""
    pass

class HyphaNode:
    """Core P2P node with Hyperswarm integration"""

    def __init__(self, seed: Optional[str] = None):
        self.seed = seed or self._generate_seed()
        self.keypair = self._derive_keypair(self.seed)
        self.node_id = self.keypair['public'][:16]

    def _generate_seed(self) -> str:
        """Generate cryptographic seed"""
        return hashlib.sha256(os.urandom(32)).hexdigest()

    def _derive_keypair(self, seed: str) -> dict:
        """Deterministic key derivation from seed"""
        secret = hashlib.pbkdf2_hmac(
            'sha256', seed.encode(), b'hypha-identity',
            100000, dklen=32
        )
        public = hashlib.sha256(secret + b'public').digest()
        return {'public': public.hex(), 'secret': secret.hex()}

    def announce(self, topic: str) -> bool:
        """Announce availability on DHT topic"""
        try:
            # Bridge to Node.js Hyperswarm
            result = subprocess.run(
                ['node', 'src/discovery/bridge.js', 'announce', topic],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            raise NetworkError(f"Announce failed: {e}")

    def lookup(self, topic: str) -> list:
        """Lookup peers on DHT topic"""
        try:
            result = subprocess.run(
                ['node', 'src/discovery/bridge.js', 'lookup', topic],
                capture_output=True,
                timeout=30,
                text=True
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            raise NetworkError(f"Lookup failed: {e}")

if __name__ == "__main__":
    import os
    import argparse

    parser = argparse.ArgumentParser(description="HYPHA P2P Node")
    parser.add_argument('--mode', choices=['provider', 'buyer'], required=True)
    parser.add_argument('--seed', type=str, help='Seed phrase')
    args = parser.parse_args()

    node = HyphaNode(seed=args.seed)
    print(f"Node ID: {node.node_id}")
    print(f"Mode: {args.mode}")

    topic = "hypha-test"
    if args.mode == 'provider':
        print(f"Announcing on topic: {topic}")
        node.announce(topic)
    else:
        print(f"Looking up peers on topic: {topic}")
        peers = node.lookup(topic)
        print(f"Found {len(peers)} peers")
