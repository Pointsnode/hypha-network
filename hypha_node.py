#!/usr/bin/env python3
"""
HYPHA Neural Node - AGI-Native P2P Connection
Seijaku (Stillness) Principle: Binary metrics only
"""

import os
import sys
import time
import json
import struct
import asyncio
import hashlib
import subprocess
from typing import Dict, Any, Optional
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder

# Import unified seed manager
try:
    from hypha_sdk.seed_manager import SeedManager
except ImportError:
    # Fallback if running standalone
    import importlib.util
    spec = importlib.util.spec_from_file_location("seed_manager", os.path.join(os.path.dirname(__file__), "hypha_sdk", "seed_manager.py"))
    seed_manager_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seed_manager_module)
    SeedManager = seed_manager_module.SeedManager


class NeuralNode:
    """AGI-native P2P node using Hyperswarm"""

    # Protocol constants
    TOPIC = b"hypha.neural.v1"
    PROTOCOL_VERSION = 1
    MSG_HANDSHAKE = 0x01
    MSG_HEARTBEAT = 0x02
    MSG_CONTEXT_STREAM = 0x03

    def __init__(self, seed: Optional[bytes] = None):
        """
        Initialize neural node with unified seed

        Args:
            seed: 32-byte seed (optional, generates random if None)
        """
        # Use SeedManager for unified identity
        self.seed_manager = SeedManager(seed)

        # P2P identity from seed manager
        self.signing_key = self.seed_manager.p2p_signing_key
        self.verify_key = self.signing_key.verify_key
        self.node_id = self.seed_manager.node_id

        # Wallet seed (for WDK initialization later)
        self._wallet_seed_hex = self.seed_manager.wallet_seed_hex

        # Connection state
        self.peers = {}  # {peer_id: connection_info}
        self.node_process = None
        self._running = False

    def get_topic_hash(self) -> bytes:
        """Generate DHT topic hash"""
        return hashlib.sha256(self.TOPIC).digest()

    async def start(self):
        """Start Hyperswarm node for P2P discovery"""
        topic_hex = self.get_topic_hash().hex()

        # Start Node.js Hyperswarm bridge
        bridge_script = self._get_bridge_script()

        self.node_process = await asyncio.create_subprocess_exec(
            'node', '-e', bridge_script, topic_hex,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )

        self._running = True

        # Start listening for connections
        asyncio.create_task(self._listen_loop())

    def _get_bridge_script(self) -> str:
        """Generate Node.js bridge script for Hyperswarm"""
        return """
const Hyperswarm = require('hyperswarm');
const crypto = require('crypto');

const topicHex = process.argv[2];
const topic = Buffer.from(topicHex, 'hex');

const swarm = new Hyperswarm();

swarm.join(topic, { server: true, client: true });

swarm.on('connection', (conn, info) => {
    // Send connection event to Python
    const peerInfo = {
        type: 'peer_connected',
        peer_id: info.publicKey ? info.publicKey.toString('hex') : 'unknown',
        client: info.client,
        server: info.server
    };
    process.stdout.write(JSON.stringify(peerInfo) + '\\n');

    // Forward data between conn and stdin/stdout
    conn.on('data', (data) => {
        const msg = {
            type: 'peer_data',
            data: data.toString('base64')
        };
        process.stdout.write(JSON.stringify(msg) + '\\n');
    });

    // Read from stdin and send to peer
    process.stdin.on('data', (data) => {
        conn.write(data);
    });

    conn.on('error', () => {});
    conn.on('close', () => {
        const closeInfo = { type: 'peer_disconnected' };
        process.stdout.write(JSON.stringify(closeInfo) + '\\n');
    });
});

process.on('SIGTERM', () => {
    swarm.destroy();
    process.exit(0);
});
"""

    async def _listen_loop(self):
        """Listen for incoming connections and data"""
        if not self.node_process or not self.node_process.stdout:
            return

        while self._running:
            try:
                line = await asyncio.wait_for(
                    self.node_process.stdout.readline(),
                    timeout=1.0
                )

                if not line:
                    continue

                event = json.loads(line.decode().strip())
                await self._handle_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

    async def _handle_event(self, event: Dict[str, Any]):
        """Handle events from Hyperswarm"""
        event_type = event.get('type')

        if event_type == 'peer_connected':
            peer_id = event.get('peer_id', 'unknown')
            self.peers[peer_id] = {
                'connected_at': time.time(),
                'bytes_sent': 0,
                'bytes_received': 0
            }

            # Immediately send handshake
            await self._send_handshake()

            # Metrics only (Seijaku principle)
            print(f"{int(time.time())} PEER_JOIN {peer_id[:16]}")

        elif event_type == 'peer_data':
            data_b64 = event.get('data', '')
            if data_b64:
                data = bytes.fromhex(data_b64) if len(data_b64) % 2 == 0 else b''
                await self._handle_message(data)

        elif event_type == 'peer_disconnected':
            print(f"{int(time.time())} PEER_LEAVE")

    async def _send_handshake(self):
        """Send handshake with public key"""
        if not self.node_process or not self.node_process.stdin:
            return

        # Message format: [version:1][msg_type:1][pubkey:32][signature:64]
        msg = struct.pack('BB', self.PROTOCOL_VERSION, self.MSG_HANDSHAKE)
        msg += self.node_id

        # Sign the handshake
        signature = self.signing_key.sign(msg, encoder=RawEncoder).signature
        msg += signature

        self.node_process.stdin.write(msg)
        await self.node_process.stdin.drain()

        # Metrics
        for peer_id in self.peers:
            self.peers[peer_id]['bytes_sent'] += len(msg)

        print(f"{int(time.time())} TX_HANDSHAKE {len(msg)}B")

    async def _handle_message(self, data: bytes):
        """Process incoming binary message"""
        if len(data) < 2:
            return

        version, msg_type = struct.unpack('BB', data[:2])

        if version != self.PROTOCOL_VERSION:
            return

        if msg_type == self.MSG_HANDSHAKE:
            await self._handle_handshake(data)
        elif msg_type == self.MSG_HEARTBEAT:
            await self._handle_heartbeat(data)
        elif msg_type == self.MSG_CONTEXT_STREAM:
            await self._handle_context_stream(data)

    async def _handle_handshake(self, data: bytes):
        """Process peer handshake"""
        if len(data) < 98:  # version(1) + type(1) + pubkey(32) + sig(64)
            return

        peer_pubkey = data[2:34]
        signature = data[34:98]

        # Metrics only
        print(f"{int(time.time())} RX_HANDSHAKE PEER={peer_pubkey.hex()[:16]}")

        # Send heartbeat in response
        await self._send_heartbeat()

    async def _send_heartbeat(self):
        """Send heartbeat signal"""
        if not self.node_process or not self.node_process.stdin:
            return

        msg = struct.pack('BB', self.PROTOCOL_VERSION, self.MSG_HEARTBEAT)
        msg += struct.pack('Q', int(time.time() * 1000))  # timestamp ms

        self.node_process.stdin.write(msg)
        await self.node_process.stdin.drain()

        for peer_id in self.peers:
            self.peers[peer_id]['bytes_sent'] += len(msg)

        print(f"{int(time.time())} TX_HEARTBEAT {len(msg)}B")

    async def _handle_heartbeat(self, data: bytes):
        """Process peer heartbeat"""
        if len(data) < 10:
            return

        timestamp_ms = struct.unpack('Q', data[2:10])[0]
        latency = int(time.time() * 1000) - timestamp_ms

        print(f"{int(time.time())} RX_HEARTBEAT LAT={latency}ms")

    async def stream_context(self, data_dict: Dict[str, Any]):
        """
        Stream AGI context to peers (binary serialization)

        Args:
            data_dict: Python dict representing AGI internal state
        """
        if not self.node_process or not self.node_process.stdin:
            return

        # Serialize to JSON, then to bytes
        payload = json.dumps(data_dict, separators=(',', ':')).encode('utf-8')

        # Message format: [version:1][msg_type:1][length:4][payload:n]
        msg = struct.pack('BB', self.PROTOCOL_VERSION, self.MSG_CONTEXT_STREAM)
        msg += struct.pack('I', len(payload))
        msg += payload

        # Send
        start = time.time()
        self.node_process.stdin.write(msg)
        await self.node_process.stdin.drain()
        elapsed = time.time() - start

        # Update metrics
        for peer_id in self.peers:
            self.peers[peer_id]['bytes_sent'] += len(msg)

        # Metrics: transfer rate
        rate_mbps = (len(msg) * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0
        print(f"{int(time.time())} TX_CONTEXT {len(msg)}B {rate_mbps:.2f}Mbps")

    async def _handle_context_stream(self, data: bytes):
        """Process incoming context stream"""
        if len(data) < 6:
            return

        payload_len = struct.unpack('I', data[2:6])[0]

        if len(data) < 6 + payload_len:
            return

        payload_bytes = data[6:6+payload_len]

        # Update metrics
        for peer_id in self.peers:
            self.peers[peer_id]['bytes_received'] += len(data)

        # Deserialize
        try:
            context_dict = json.loads(payload_bytes.decode('utf-8'))
            print(f"{int(time.time())} RX_CONTEXT {len(data)}B KEYS={len(context_dict)}")

            # Return deserialized context for processing
            return context_dict
        except Exception:
            print(f"{int(time.time())} RX_CONTEXT_ERR {len(data)}B")
            return None

    async def stop(self):
        """Stop the neural node"""
        self._running = False

        if self.node_process:
            self.node_process.terminate()
            await self.node_process.wait()

        print(f"{int(time.time())} NODE_STOP")


async def main():
    """Example: Run a neural node"""
    # Create node with deterministic identity
    seed = hashlib.sha256(b"demo-agi-node-1").digest()
    node = NeuralNode(seed=seed)

    print(f"{int(time.time())} NODE_START ID={node.node_id.hex()[:16]}")

    # Start P2P
    await node.start()

    # Keep alive and periodically stream context
    try:
        for i in range(60):  # Run for 60 seconds
            await asyncio.sleep(5)

            # Stream simulated AGI state
            agi_state = {
                "iteration": i,
                "model_checkpoint": f"v{i}",
                "loss": 0.1 / (i + 1),
                "embeddings_hash": hashlib.sha256(str(i).encode()).hexdigest()[:16]
            }

            await node.stream_context(agi_state)

    except KeyboardInterrupt:
        pass
    finally:
        await node.stop()


if __name__ == "__main__":
    asyncio.run(main())
