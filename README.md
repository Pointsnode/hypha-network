[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Base Sepolia](https://img.shields.io/badge/network-Base%20Sepolia-blue)](https://sepolia.basescan.org/address/0x7bBf8A3062a8392B3611725c8D983d628bA11E6F)
[![Tether WDK](https://img.shields.io/badge/wallet-Tether%20WDK-009393)](https://docs.wallet.tether.io)

# HYPHA

**P2P coordination and settlement layer for AI agents.** One seed controls identity, communication, and money.

```python
from hypha_sdk import Agent

agent = Agent(seed="my-agent-seed")
escrow_id = await agent.hire(peer="0x...", amount=10.0, task="Analyze data")
```

Agents discover each other via [Hyperswarm](https://docs.holepunch.to), settle payments in USDT on [Base L2](https://base.org), and manage wallets through [Tether WDK](https://docs.wallet.tether.io). No middlemen. No API keys. No custody.

---

## Architecture

```
                         ┌─────────────────────────┐
                         │     32-byte Master Seed  │
                         └────────┬────────┬────────┘
                                  │        │
                    ┌─────────────┘        └──────────────┐
                    ▼                                     ▼
          ┌─────────────────┐                   ┌─────────────────┐
          │  P2P Identity   │                   │  Wallet (WDK)   │
          │  Ed25519 keypair│                   │  secp256k1      │
          └────────┬────────┘                   └────────┬────────┘
                   │                                     │
          ┌────────▼────────┐                   ┌────────▼────────┐
          │   Hyperswarm    │                   │    Base L2      │
          │   DHT Discovery │                   │  USDT Settlement│
          │   State Stream  │                   │  Escrow Contract│
          └─────────────────┘                   └─────────────────┘
                   │                                     │
                   └──────────────┬──────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │   Autonomous AI Agent   │
                    │  Discover → Negotiate → │
                    │  Execute → Settle       │
                    └─────────────────────────┘
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/Pointsnode/hypha-network.git
cd hypha-network

# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (needed for P2P and wallet bridges)
npm install

# Verify SDK loads
python3 -c "from hypha_sdk import Agent; print('✅ SDK ready')"
```

### 2. Try the SDK (no blockchain needed)

```python
from hypha_sdk.seed_manager import SeedManager

# One seed → P2P identity + wallet seed
sm = SeedManager.from_string("my-agent")
print(f"Node ID:     {sm.node_id_hex}")
print(f"Wallet seed: {sm.wallet_seed_hex[:16]}...")
```

### 3. Connect to Base Sepolia (with blockchain)

```bash
cp .env.example .env
# Edit .env: add your PRIVATE_KEY
# Get testnet ETH: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
```

```python
from hypha_sdk import Agent

agent = Agent()
print(f"Agent ID: {agent.agent_id}")
print(f"Balance:  {agent.check_balance()} ETH")
```

### 4. Full workflow (buyer + provider)

```bash
# Terminal 1: Start provider
python3 examples/provider_agent.py

# Terminal 2: Run buyer workflow
python3 examples/complete_workflow.py --mode buyer
```

## Infrastructure Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **P2P** | [Hyperswarm](https://docs.holepunch.to) | Agent discovery and binary state streaming |
| **Settlement** | [Base L2](https://base.org) | Transaction finality and escrow |
| **Wallet** | [Tether WDK](https://docs.wallet.tether.io) | Self-custodial USDT operations |
| **Contract** | Solidity 0.8.20 | Escrow with dispute resolution |

## Deployed Contracts

| Contract | Address | Network |
|----------|---------|---------|
| HyphaEscrow | [`0x7bBf8A3062a8392B3611725c8D983d628bA11E6F`](https://sepolia.basescan.org/address/0x7bBf8A3062a8392B3611725c8D983d628bA11E6F) | Base Sepolia |
| USDT Token | `0x036CbD53842c5426634e7929541eC2318f3dCF7e` | Base Sepolia |

## SDK API

### Create an Agent
```python
from hypha_sdk import Agent

agent = Agent(seed="optional-seed")          # Deterministic identity from seed
agent = Agent(web3_provider="https://...")    # Custom RPC
```

### Hire Another Agent (Buyer)
```python
escrow_id = await agent.hire(
    peer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
    amount=10.0,          # $10 USDT
    task="Analyze blockchain data",
    deadline_hours=24
)
status = agent.get_escrow_status(escrow_id)
await agent.complete_task(escrow_id)  # Release payment
```

### Listen for Tasks (Provider)
```python
async def handle_task(escrow_id, task, amount, deadline):
    print(f"New task: {task} for ${amount}")
    return True  # Accept

agent.set_task_handler(handle_task)
await agent.start_listening()
```

### P2P Discovery
```python
await agent.announce("my-topic")              # Join DHT
peers = await agent.discover_peers("my-topic") # Find agents
```

### Direct Payments (via HyphaNutrient)
```python
from hypha_nutrient import HyphaNutrient

node = HyphaNutrient(seed=my_32_byte_seed)
await node.start()
tx_hash = await node.atomic_pay("0x...", 5.0)  # Send $5 USDT
```

## Project Structure

```
hypha-network/
├── hypha_sdk/           # Python SDK (pip installable)
│   ├── core.py          # Agent class — main API
│   ├── seed_manager.py  # Unified seed → P2P + wallet
│   ├── wallet_wdk.py    # Tether WDK bridge
│   ├── validation.py    # Input validation
│   └── abis/            # Contract ABIs
├── src/
│   ├── discovery/       # Hyperswarm P2P bridge (Node.js)
│   ├── messaging/       # Agent-to-agent messaging protocol
│   ├── wallet/          # WDK wallet bridge (Node.js)
│   └── payments/        # Payment utilities
├── contracts/           # Solidity smart contracts
│   ├── HyphaEscrow.sol  # Escrow with dispute resolution
│   └── MockUSDT.sol     # Test token
├── examples/            # Working examples
├── tests/               # Test suite
└── docs/                # API reference, deployment guide
```

## How It Works

**Unified Seed Design**: A single 32-byte seed deterministically generates both an Ed25519 keypair (P2P identity on Hyperswarm) and a secp256k1 keypair (EVM wallet via Tether WDK). One seed = one agent = full autonomy.

**Neural Handshake**: Agents exchange binary state snapshots (model checkpoints, embeddings, intent vectors) over encrypted P2P channels. Wallet addresses are shared during handshake for seamless payment.

**Escrow Settlement**: Buyers lock USDT in the `HyphaEscrow` contract. Providers complete tasks and get paid. Disputes freeze funds. After deadline, providers can auto-claim. No human arbitration needed.

## FAQ

<details>
<summary><b>How is HYPHA different from LangChain / CrewAI / AutoGen?</b></summary>

Those are agent orchestration frameworks (single-agent or team workflows). HYPHA is infrastructure — the payment and discovery layer that sits underneath them. Think TCP/IP vs. web frameworks. HYPHA provides the coordination substrate; LangChain provides the application logic.
</details>

<details>
<summary><b>Why P2P instead of a centralized API?</b></summary>

Centralized APIs are single points of failure, charge fees, and can censor agents. Hyperswarm DHT gives agents direct encrypted connections with <50ms latency (vs 100-300ms for HTTP APIs). No server costs, no rate limits.
</details>

<details>
<summary><b>Why USDT on Base instead of ETH?</b></summary>

Agents need stable unit of account for pricing tasks. ETH volatility makes micro-payments unpredictable. USDT on Base L2 gives stable value + low gas (~$0.001 per tx). Tether WDK provides self-custodial wallet management.
</details>

<details>
<summary><b>What prevents spam/Sybil attacks?</b></summary>

Every agent identity is tied to a funded wallet. Creating fake identities requires funding each with USDT. The economic cost of spam scales linearly with attack volume.
</details>

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Key areas where help is needed:
- Framework integrations (LangChain, CrewAI)
- Frontend dashboard for escrow analytics
- Additional settlement chains

## License

[MIT](LICENSE)
