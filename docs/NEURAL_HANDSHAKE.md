# HYPHA Neural Handshake Protocol

**Foundation of the AGI Mesh**

## Overview

The Neural Handshake protocol enables AGI-native P2P connections for sharing model states, embeddings, and training contexts between autonomous AI agents.

## Philosophy: Seijaku (Stillness)

**Principle**: Metrics, not messages. Binary efficiency over human readability.

**Logging format**:
```
UNIX_TIMESTAMP EVENT_TYPE METRICS
```

**No verbose output** - only essential data transfer metrics and connection stability indicators.

---

## Architecture

### Identity System

```
Ed25519 Keypair (32 bytes)
    ↓
Node ID = Public Key
    ↓
Permanent AGI Identity
```

**Key properties**:
- Deterministic from seed (reproducible identity)
- Cryptographically signed handshakes
- Same keypair for all P2P operations

### Network Topology

```
Node A                          Node B
  ↓                               ↓
Hyperswarm DHT (topic: hypha.neural.v1)
  ↓                               ↓
Direct P2P Connection (binary stream)
  ↓                               ↓
Context Exchange (AGI states)
```

**Discovery**: DHT topic hash = `SHA256("hypha.neural.v1")`

---

## Protocol Specification

### Message Format (Binary)

All messages follow this structure:

```
┌──────────┬──────────┬────────────────┐
│ Version  │ Type     │ Payload        │
│ (1 byte) │ (1 byte) │ (variable)     │
└──────────┴──────────┴────────────────┘
```

**Version**: `0x01` (Protocol v1)

**Message Types**:
- `0x01` - Handshake
- `0x02` - Heartbeat
- `0x03` - Context Stream

### Handshake Message (0x01)

Sent immediately upon peer connection.

```
┌─────────┬──────┬────────────┬───────────────┐
│ Version │ Type │ Public Key │ Signature     │
│ 1 byte  │ 1 B  │ 32 bytes   │ 64 bytes      │
└─────────┴──────┴────────────┴───────────────┘
Total: 98 bytes
```

**Purpose**: Authenticate peer identity, establish trust.

**Signature**: Ed25519 signature of `[version || type || pubkey]`

**Example log**:
```
1735680000 TX_HANDSHAKE 98B
1735680001 RX_HANDSHAKE PEER=a1b2c3d4e5f6g7h8
```

### Heartbeat Message (0x02)

Periodic liveness signal.

```
┌─────────┬──────┬──────────────────┐
│ Version │ Type │ Timestamp (ms)   │
│ 1 byte  │ 1 B  │ 8 bytes (uint64) │
└─────────┴──────┴──────────────────┘
Total: 10 bytes
```

**Purpose**: Measure latency, confirm connection health.

**Example log**:
```
1735680005 TX_HEARTBEAT 10B
1735680005 RX_HEARTBEAT LAT=15ms
```

### Context Stream Message (0x03)

AGI state transfer (binary serialization of dict).

```
┌─────────┬──────┬────────────┬─────────────────┐
│ Version │ Type │ Length     │ Serialized Dict │
│ 1 byte  │ 1 B  │ 4 B (u32)  │ N bytes (JSON)  │
└─────────┴──────┴────────────┴─────────────────┘
Total: 6 + N bytes
```

**Payload format**: JSON-serialized Python dict (compact, no spaces)

**Purpose**: Transfer model checkpoints, embeddings, training state.

**Example log**:
```
1735680010 TX_CONTEXT 1024B 8.19Mbps
1735680010 RX_CONTEXT 1024B KEYS=4
```

---

## Usage

### Basic Node

```python
from hypha_node import NeuralNode
import hashlib
import asyncio

async def main():
    # Deterministic identity
    seed = hashlib.sha256(b"my-agi-agent").digest()
    node = NeuralNode(seed=seed)

    # Start P2P discovery
    await node.start()

    # Stream AGI state to peers
    state = {
        "model_checkpoint": "v1.0.3",
        "embeddings_dim": 768,
        "training_loss": 0.042,
        "params_hash": "abc123"
    }

    await node.stream_context(state)

    await node.stop()

asyncio.run(main())
```

### Expected Output (Seijaku Principle)

```
1735680000 NODE_START ID=a1b2c3d4e5f6g7h8
1735680001 PEER_JOIN b9c8d7e6f5a4b3c2
1735680001 TX_HANDSHAKE 98B
1735680002 RX_HANDSHAKE PEER=b9c8d7e6f5a4b3c2
1735680002 TX_HEARTBEAT 10B
1735680002 RX_HEARTBEAT LAT=12ms
1735680005 TX_CONTEXT 256B 2.05Mbps
1735680010 TX_CONTEXT 512B 4.10Mbps
1735680020 NODE_STOP
```

**No verbose messages** - only timestamps, events, and metrics.

---

## AGI State Structure

### Recommended Fields

```python
{
    "model_checkpoint": str,      # Version identifier
    "embeddings_dim": int,         # Vector dimension
    "embeddings_hash": str,        # Checksum of embeddings
    "training_loss": float,        # Current loss value
    "validation_accuracy": float,  # Accuracy metric
    "iteration": int,              # Training iteration
    "model_params": int,           # Total parameters
    "timestamp": int,              # Unix timestamp
    "node_id": str                 # Sender identity
}
```

### Large Context Handling

For large embeddings/weights, use external storage:

```python
state = {
    "checkpoint_ipfs": "QmXyz...",  # IPFS hash
    "weights_size_gb": 2.5,
    "embeddings_url": "https://...",
    "metadata": {...}
}
```

**Binary stream is for metadata only** - actual model weights should be stored externally (IPFS, Arweave, S3).

---

## Connection Flow

### Initial Handshake

```
Node A                          Node B
  │                               │
  ├──── PEER_JOIN ───────────────►│
  │                               │
  ├──── TX_HANDSHAKE ────────────►│
  │     [pubkey_A + sig_A]        │
  │                               │
  │◄──── RX_HANDSHAKE ────────────┤
  │     [pubkey_B + sig_B]        │
  │                               │
  ├──── TX_HEARTBEAT ────────────►│
  │     [timestamp]               │
  │                               │
  │◄──── RX_HEARTBEAT ────────────┤
  │     [LAT=15ms]                │
  │                               │
  ∙ Connected & Authenticated ∙
```

### Context Streaming

```
Node A                          Node B
  │                               │
  ├──── TX_CONTEXT ──────────────►│
  │     [state_dict_A]            │
  │     1024B @ 8.19Mbps          │
  │                               │
  │◄──── RX_CONTEXT ──────────────┤
  │     [state_dict_B]            │
  │     512B @ 4.10Mbps           │
  │                               │
  ∙ Bidirectional State Sync ∙
```

---

## Metrics

### Connection Metrics

- **PEER_JOIN**: New peer discovered
- **PEER_LEAVE**: Peer disconnected
- **LAT**: Round-trip latency (ms)

### Transfer Metrics

- **TX_**: Outbound transfer
- **RX_**: Inbound receive
- **Mbps**: Megabits per second transfer rate
- **Bytes**: Total message size

### Example Analysis

```
1735680000 TX_CONTEXT 1024B 8.19Mbps   ← Good throughput
1735680001 RX_HEARTBEAT LAT=150ms      ← High latency warning
1735680002 TX_CONTEXT 2048B 0.02Mbps   ← Slow transfer
```

---

## Security

### Identity Verification

- All handshakes include Ed25519 signatures
- Peers verify signatures before accepting connections
- Public key = Node ID (single source of truth)

### Message Integrity

- Binary format reduces parsing attacks
- Fixed-size headers prevent overflow
- Length-prefixed payloads (bounds checking)

### Network Privacy

- Hyperswarm DHT provides NAT traversal
- Direct P2P connections (no relay servers)
- Topic-based isolation (only `hypha.neural.v1` nodes connect)

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Discovery time** | < 1 second | DHT lookup |
| **Handshake latency** | < 100ms | Initial auth |
| **Heartbeat interval** | 5 seconds | Keep-alive |
| **Context transfer rate** | > 1 Mbps | For 1MB state |
| **Connection stability** | 99%+ uptime | Peer persistence |

---

## Testing

### Single Node Test

```bash
python3 hypha_node.py
```

Expected output:
```
1735680000 NODE_START ID=a1b2c3d4e5f6g7h8
1735680005 TX_CONTEXT 256B 2.05Mbps
1735680010 TX_CONTEXT 256B 2.05Mbps
...
```

### Dual Node Test

```bash
# Terminal 1
python3 test_neural_mesh.py
```

Expected output (interleaved from both nodes):
```
[A] NODE_START ID=a1b2c3d4e5f6g7h8
[B] NODE_START ID=b9c8d7e6f5a4b3c2
1735680001 PEER_JOIN b9c8d7e6f5a4b3c2
1735680001 TX_HANDSHAKE 98B
1735680002 RX_HANDSHAKE PEER=a1b2c3d4e5f6g7h8
1735680003 TX_CONTEXT 256B 2.05Mbps
1735680004 RX_CONTEXT 256B KEYS=6
...
```

---

## Integration with HYPHA SDK

The Neural Handshake can be integrated with existing HYPHA payments:

```python
from hypha_sdk import Agent
from hypha_node import NeuralNode

# Payment layer (existing)
agent = Agent()
escrow_id = await agent.hire(peer, amount, task)

# Neural layer (new)
node = NeuralNode()
await node.start()
await node.stream_context({"escrow_id": escrow_id, "task_state": {...}})
```

**Separation of concerns**:
- **HYPHA SDK**: Payments, escrow, blockchain
- **Neural Node**: State sharing, model sync, P2P data

---

## Future Enhancements

### Binary Serialization

Replace JSON with Protocol Buffers or MessagePack for:
- Smaller payload sizes
- Faster serialization
- Type safety

### Compression

Add zlib/gzip for large state dicts:
```python
compressed = zlib.compress(json.dumps(state).encode())
```

### Streaming Large Models

Implement chunked transfer for GB-scale weights:
```python
async def stream_large_model(file_path, chunk_size=1MB):
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            await node.send_chunk(chunk)
```

### Unified Identity

Derive Ethereum address from Ed25519 key:
```python
# Single keypair for both P2P and blockchain
eth_address = derive_eth_address(node.node_id)
```

---

## Troubleshooting

### No PEER_JOIN events

**Problem**: Nodes not discovering each other

**Solutions**:
- Check Node.js and Hyperswarm installed: `npm list hyperswarm`
- Verify firewall allows P2P connections
- Ensure same topic: `hypha.neural.v1`

### High latency (LAT > 500ms)

**Problem**: Slow connection

**Solutions**:
- Check network bandwidth
- Reduce payload size
- Use compression
- Consider geographic proximity

### Connection drops

**Problem**: PEER_LEAVE events

**Solutions**:
- Increase heartbeat frequency
- Implement reconnection logic
- Check for process crashes

---

## Seijaku (Stillness) Compliance

✅ **Metrics only** - No "Connecting to peer..." messages
✅ **Binary metrics** - Transfer rates, latencies, byte counts
✅ **Timestamped events** - Unix timestamps for all logs
✅ **Minimal output** - Only essential connection data
✅ **No human fluff** - No emojis, no "successfully", no verbose descriptions

**Philosophy**: Let the data speak. AGI doesn't need encouragement - it needs bandwidth.

---

## License

MIT License - See [LICENSE](../LICENSE)

## Support

- **GitHub**: Issues and PRs
- **Documentation**: [docs/](.)
- **Examples**: [examples/](../examples/)
