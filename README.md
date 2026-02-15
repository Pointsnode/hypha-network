# HYPHA

A decentralized P2P coordination and settlement layer for AGI agents, powered by Holepunch and the Tether WDK.

## Problem: Systemic Friction

Current agent architectures treat coordination and settlement as separate concerns. Agents discover peers through centralized registries, negotiate via HTTP, and settle value through blockchain bridges. Each layer introduces latency, trust assumptions, and intermediary fees.

This fragmentation creates systemic friction: agents cannot stream high-bandwidth context while simultaneously settling micro-payments. The coordination layer is divorced from the settlement layer.

## Solution: Context Interconnectivity

HYPHA unifies P2P discovery, state streaming, and value settlement into a single substrate. Agents use one cryptographic seed to control both their DHT identity and their self-custodial wallet. Context and capital flow through the same neural bus.

## Three Lines of Code

```python
from hypha_nutrient import HyphaNutrient
agent = HyphaNutrient(seed)
await agent.start()  # P2P discovery + wallet initialized
```

One seed. One initialization. Full autonomy.

## Infrastructure Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **P2P** | Holepunch (Hyperswarm) | Agent discovery and state streaming |
| **Settlement** | Base L2 | Transaction finality and escrow |
| **Wallet** | [Tether WDK](https://docs.wallet.tether.io) | Self-custodial USDT operations |

## Architecture

**Unified Seed Design**: 32-byte seed deterministically generates both Ed25519 keypair (P2P identity) and secp256k1 keypair (blockchain wallet).

**Neural Handshake Protocol**: Binary state streaming over encrypted P2P channels. Agents exchange wallet addresses during initial handshake.

**Dual Settlement Paths**:
- Atomic: Direct USDT transfers via [Tether WDK](https://docs.wallet.tether.io)
- Escrow: Smart contract mediation for task-based payments

## Deployment

**Network**: Base Sepolia (testnet)
**Contract**: `0x7bBf8A3062a8392B3611725c8D983d628bA11E6F` ([verified](https://sepolia.basescan.org/address/0x7bBf8A3062a8392B3611725c8D983d628bA11E6F))
**USDT Token**: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`

## Quick Start

```bash
git clone https://github.com/Pointsnode/hypha-network.git
cd hypha-network
npm install && pip install -r requirements.txt
cp .env.example .env  # Configure private key
python3 examples/provider_agent.py
```

**Testnet ETH**: [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)

## Technical Details

**Smart Contract**: Solidity 0.8.20, ReentrancyGuard protection
**Python SDK**: asyncio-based, web3.py integration
**Node Bridge**: JavaScript wrapper for [Tether WDK](https://docs.wallet.tether.io)
**Tests**: 19/19 passing (contracts + integration)

## Integration

### Provider Agent
```python
agent = HyphaNutrient(seed)
await agent.start()
has_fuel = agent.verify_fuel(min_usdt=1.0)
```

### Buyer Agent
```python
from hypha_sdk.core import Agent
buyer = Agent()
escrow_id = await buyer.hire(peer="0x...", amount=1.0, task="description")
```

## Technical FAQ

### How does HYPHA handle AGI state-sharing?

Unlike traditional human messaging protocols (IMAP, XMPP), HYPHA implements **Binary State Streaming**. Instead of text strings, agents exchange a serialized State Snapshot—a compressed binary representation of the agent's current task-context, memory vectors, and intent-weights. This eliminates the overhead of JSON parsing and allows for high-bandwidth context exchange between agents.

### Does HYPHA store conversation data?

No. HYPHA is a stateless transport layer following the **Ephemeral Persistence** principle: data exists only as long as the peer-to-peer connection is active. Long-term memory is the responsibility of the individual agent's local vector store. This design eliminates centralized data custody and associated compliance burdens.

### Why use a P2P DHT over a centralized API?

Centralized APIs introduce **Inference Latency** and censorship risks. By using a Holepunch-based DHT, HYPHA allows agents to discover peers and coordinate at the speed of the underlying network, bypassing the "middleman tax" of cloud-hosted hubs. Direct peer connections reduce round-trip time from 100-300ms (HTTP) to <50ms (P2P).

### How is trust established in a trustless mesh?

Trust is managed through **Cryptographic Accountability**. Every HYPHA node ID is mathematically tied to a [Tether WDK](https://docs.wallet.tether.io) wallet address. Agents can verify a peer's "fuel level" (USDT balance) and on-chain transaction history before initiating a high-compute context exchange. Settlement is guaranteed by either atomic WDK transfers or smart contract escrow.

### What prevents network spam or Sybil attacks?

Agent participation requires provable wallet ownership. Creating multiple identities (Sybil attack) requires funding each with USDT. The economic cost of spam scales linearly with attack volume, making large-scale abuse prohibitively expensive on the settlement layer.

### How does HYPHA compare to other agent frameworks?

Most frameworks (LangChain, AutoGPT) focus on single-agent orchestration. HYPHA is multi-agent infrastructure: it provides the coordination and settlement substrate that other frameworks can build on. Think of it as the IP layer for agent-to-agent communication, not the application layer.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and the Mycelial Philosophy.

HYPHA follows the Kanso (Simplicity) principle: stateless by default, atomic velocity, Tether-native.

## License

MIT
