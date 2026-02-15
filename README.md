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
| **Wallet** | Tether WDK | Self-custodial USDT operations |

## Architecture

**Unified Seed Design**: 32-byte seed deterministically generates both Ed25519 keypair (P2P identity) and secp256k1 keypair (blockchain wallet).

**Neural Handshake Protocol**: Binary state streaming over encrypted P2P channels. Agents exchange wallet addresses during initial handshake.

**Dual Settlement Paths**:
- Atomic: Direct USDT transfers via Tether WDK
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
**Node Bridge**: JavaScript wrapper for Tether WDK
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

## License

MIT
