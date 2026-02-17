"""
HYPHA P2P Discovery — Pure Python using Kademlia DHT
Replaces the Node.js Hyperswarm-based discovery.
"""

import asyncio
import json
import logging
from typing import Optional, List, Dict, Any

from kademlia.network import Server

log = logging.getLogger(__name__)

# Default bootstrap nodes (empty = local-only testing)
DEFAULT_BOOTSTRAP: List[tuple] = []


class Discovery:
    """Kademlia-based peer discovery for HYPHA agents."""

    def __init__(
        self,
        port: int = 8468,
        bootstrap_nodes: Optional[List[tuple]] = None,
        node_id: Optional[bytes] = None,
    ):
        """
        Args:
            port: UDP port for the DHT
            bootstrap_nodes: List of (host, port) tuples to bootstrap from
            node_id: Optional 20-byte Kademlia node ID derived from seed.
                     If provided, the DHT node will use this deterministic ID
                     instead of a random one.
        """
        self.port = port
        self.bootstrap_nodes = bootstrap_nodes if bootstrap_nodes is not None else DEFAULT_BOOTSTRAP
        self._node_id = node_id
        self.server: Optional[Server] = None
        self._started = False

    async def start(self):
        """Bootstrap into the DHT."""
        if self._started:
            return
        self.server = Server()
        if self._node_id:
            # Override the random node ID with our seed-derived one
            self.server.node.id = self._node_id
        await self.server.listen(self.port)
        if self.bootstrap_nodes:
            await self.server.bootstrap(self.bootstrap_nodes)
        self._started = True
        log.info(f"Kademlia DHT listening on port {self.port}")

    async def stop(self):
        if self.server:
            self.server.stop()
            self._started = False

    async def announce(self, topic: str, agent_info: Dict[str, Any]) -> bool:
        """
        Announce this agent under *topic* in the DHT.

        Args:
            topic: Discovery topic (e.g. "hypha-agents")
            agent_info: Dict with agent_id, capabilities, wallet_address, etc.

        Returns:
            True on success
        """
        if not self._started:
            await self.start()

        key = f"hypha:{topic}"
        # Read existing peers list, append ourselves
        existing_raw = await self.server.get(key)
        peers: list = []
        if existing_raw:
            try:
                peers = json.loads(existing_raw)
            except (json.JSONDecodeError, TypeError):
                peers = []

        # Deduplicate by agent_id
        peers = [p for p in peers if p.get("agent_id") != agent_info.get("agent_id")]
        peers.append(agent_info)

        await self.server.set(key, json.dumps(peers))
        log.info(f"Announced on topic '{topic}': {agent_info.get('agent_id')}")
        return True

    async def discover_peers(self, topic: str) -> List[Dict[str, Any]]:
        """
        Look up peers registered under *topic*.

        Returns:
            List of agent info dicts.
        """
        if not self._started:
            await self.start()

        key = f"hypha:{topic}"
        raw = await self.server.get(key)
        if not raw:
            return []
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
