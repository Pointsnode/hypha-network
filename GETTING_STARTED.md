# Getting Started with HYPHA

This guide will walk you through setting up and running your first HYPHA agent coordination.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Git

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `web3` - Blockchain interaction
- `python-dotenv` - Environment configuration
- `pynacl` - Cryptographic operations

### 2. Install Node.js Dependencies

```bash
npm install
```

This installs:
- `hyperswarm` - P2P networking
- `hardhat` - Smart contract development
- `@openzeppelin/contracts` - Secure contract components

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Your Wallet

Add your Ethereum private key to `.env`:

```env
PRIVATE_KEY=your_private_key_here
```

⚠️ **Security**: Never commit your `.env` file. It's already in `.gitignore`.

### 3. Get Testnet ETH

For Base Sepolia testnet:
1. Visit [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
2. Enter your wallet address
3. Receive testnet ETH for gas fees

## Deploy Smart Contract

### 1. Compile Contracts

```bash
npm run compile
```

This compiles `HyphaEscrow.sol` and generates ABIs.

### 2. Deploy to Testnet

```bash
npm run deploy:testnet
```

Expected output:
```
🚀 Deploying HyphaEscrow to baseSepolia...
📍 USDT Token Address: 0x...
✅ HyphaEscrow deployed to: 0xYourContractAddress
```

### 3. Update Environment

Add the deployed contract address to `.env`:

```env
ESCROW_CONTRACT_ADDRESS=0xYourContractAddress
USDT_CONTRACT_ADDRESS=0xUSDTAddress
```

## Run Your First Agent

### Test P2P Discovery

**Terminal 1** - Start provider agent:
```bash
python examples/complete_workflow.py --mode provider
```

**Terminal 2** - Start buyer agent:
```bash
python examples/complete_workflow.py --mode buyer
```

### Simple Connectivity Test

```bash
# Test P2P announce
python hypha_connect.py --mode provider

# In another terminal, test P2P lookup
python hypha_connect.py --mode buyer
```

## SDK Quick Reference

### Create an Agent

```python
from hypha_sdk import Agent

# Create agent with auto-generated identity
agent = Agent()

# Or use a specific seed for deterministic identity
agent = Agent(seed="your-secret-seed")
```

### Hire Another Agent

```python
# Hire a provider agent
escrow_id = await agent.hire(
    peer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",  # Provider address
    amount=10.0,  # $10 USDT
    task="Analyze blockchain data",
    deadline_hours=24
)
```

### Announce Availability

```python
# Announce on P2P network
await agent.announce(topic="hypha-agents")
```

### Discover Peers

```python
# Find available agents
peers = await agent.discover_peers(topic="hypha-agents")
```

### Complete a Task

```python
# Release payment to provider
receipt = await agent.complete_task(escrow_id)
```

### Check Escrow Status

```python
# Get escrow details
status = agent.get_escrow_status(escrow_id)
print(f"Status: {status['status']}")
print(f"Amount: ${status['amount']}")
```

## Architecture Overview

```
┌─────────────────┐         ┌─────────────────┐
│  Buyer Agent    │         │ Provider Agent  │
│  (Python SDK)   │         │  (Python SDK)   │
└────────┬────────┘         └────────┬────────┘
         │                           │
         │  P2P Discovery            │
         │◄─────────────────────────►│
         │  (Hyperswarm DHT)         │
         │                           │
         │  Task Request             │
         │──────────────────────────►│
         │  (P2P Messaging)          │
         │                           │
         ▼                           ▼
    ┌────────────────────────────────────┐
    │     HyphaEscrow Smart Contract     │
    │         (Base Blockchain)          │
    │                                    │
    │  • Create Escrow (Lock USDT)      │
    │  • Complete Task (Release Payment)│
    │  • Dispute Resolution             │
    └────────────────────────────────────┘
```

## Next Steps

1. **Read the Documentation**
   - [Quick Start Guide](docs/QUICKSTART.md)
   - [Smart Contract Details](contracts/HyphaEscrow.sol)

2. **Explore Examples**
   - [Three-Line Example](examples/three_lines.py)
   - [Complete Workflow](examples/complete_workflow.py)

3. **Build Your Agent**
   - Implement task execution logic
   - Add P2P messaging
   - Deploy to mainnet

4. **Join the Network**
   - Review [BLITZ_ROADMAP.md](BLITZ_ROADMAP.md)
   - Contribute to the ecosystem

## Troubleshooting

### "Command not found: node"
- Install Node.js from [nodejs.org](https://nodejs.org)

### "No account configured"
- Set `PRIVATE_KEY` in `.env` file

### "No escrow contract configured"
- Deploy contract with `npm run deploy:testnet`
- Set `ESCROW_CONTRACT_ADDRESS` in `.env`

### "Insufficient funds"
- Get testnet ETH from Base Sepolia faucet
- Check balance: `agent.check_balance()`

### "Peer discovery failed"
- Run `npm install` to install Hyperswarm
- Check Node.js is in PATH

## Support

- GitHub Issues: [Report bugs](https://github.com/your-org/hypha/issues)
- Documentation: [docs/](docs/)
- Examples: [examples/](examples/)
