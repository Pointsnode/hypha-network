# HYPHA Deployment Guide

Complete guide to deploying HYPHA contracts and configuring the SDK for production use.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Testnet Deployment](#testnet-deployment)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

- **Node.js** >= 16.0.0 (for Hyperswarm and Hardhat)
- **Python** >= 3.8 (for SDK)
- **Git** (for version control)

```bash
# Verify installations
node --version
python --version
git --version
```

### Required Accounts

- **Ethereum Account**: With private key for deployment
- **Base Sepolia ETH**: For testnet deployment (~0.1 ETH for gas)
- **Base Mainnet ETH**: For production deployment (~0.5 ETH recommended)

### Get Testnet ETH

1. Visit [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-sepolia-faucet)
2. Connect your wallet
3. Request testnet ETH

## Testnet Deployment

### 1. Install Dependencies

```bash
cd hypha-project

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -e .
```

### 2. Configure Environment

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your testnet configuration:

```env
# Ethereum Account
PRIVATE_KEY=0x...your...private...key...

# Base Sepolia RPC
WEB3_PROVIDER_URI=https://sepolia.base.org

# Contracts (leave empty, will be populated after deployment)
ESCROW_CONTRACT_ADDRESS=
USDT_CONTRACT_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# Logging
LOG_LEVEL=INFO
```

### 3. Deploy Contracts

```bash
# Deploy to Base Sepolia
npm run deploy:testnet
```

Expected output:
```
🚀 Deploying HyphaEscrow to baseSepolia...
📍 USDT Token Address: 0x036CbD53842c5426634e7929541eC2318f3dCF7e
👤 Deploying with account: 0x...
💰 Account balance: 0.1 ETH

✅ HyphaEscrow deployed to: 0xABC...123
```

### 4. Update Environment

Copy the deployed contract address to `.env`:

```env
ESCROW_CONTRACT_ADDRESS=0xABC...123  # From deployment output
```

### 5. Verify Deployment

Run health check:

```python
from hypha_sdk import Agent
from hypha_sdk.health import HealthCheck
import asyncio

async def check_health():
    agent = Agent()
    health = HealthCheck(agent)
    status = await health.check_all()
    print(health.get_summary(status))

asyncio.run(check_health())
```

Expected output:
```
HYPHA Health Check - HEALTHY
Timestamp: 1234567890

Web3: healthy
Account: healthy
Contracts: healthy
Messaging: healthy
```

### 6. Test End-to-End

```bash
# Terminal 1: Start provider
python examples/messaging_demo.py --mode provider

# Terminal 2: Start buyer
python examples/messaging_demo.py --mode buyer
```

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests passing: `pytest tests/`
- [ ] Contract tests passing: `npm run test:contracts`
- [ ] Security audit complete
- [ ] Input validation tested
- [ ] Sufficient ETH for deployment (0.5+ ETH recommended)
- [ ] Backup of private keys stored securely
- [ ] Multi-sig wallet configured (recommended)

### 1. Production Environment

Update `.env` for mainnet:

```env
# Production Private Key (SECURE THIS!)
PRIVATE_KEY=0x...

# Base Mainnet RPC
WEB3_PROVIDER_URI=https://mainnet.base.org

# Production USDC (used as USDT)
USDT_CONTRACT_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913

# Logging
LOG_LEVEL=WARNING
```

### 2. Deploy to Mainnet

```bash
# Deploy to Base Mainnet
npm run deploy:mainnet
```

### 3. Verify Contract on Basescan

```bash
npx hardhat verify --network base <ESCROW_ADDRESS> <USDT_ADDRESS>
```

Visit Basescan to verify:
```
https://basescan.org/address/<ESCROW_ADDRESS>
```

### 4. Production Testing

**CRITICAL**: Test with small amounts first!

```python
from hypha_sdk import Agent
import asyncio

async def production_test():
    agent = Agent()

    # Test with small amount (0.01 USDT)
    escrow_id = await agent.hire(
        peer="0x...",
        amount=0.01,
        task="Production test task"
    )

    print(f"Test escrow created: {escrow_id}")

    # Verify on blockchain
    status = agent.get_escrow_status(escrow_id)
    print(f"Status: {status}")

asyncio.run(production_test())
```

### 5. Monitor Deployment

Set up monitoring for:
- Transaction failures
- Gas price spikes
- Contract balance changes
- Error logs

## Environment Configuration

### Required Variables

```env
PRIVATE_KEY=0x...              # Required: Ethereum private key
WEB3_PROVIDER_URI=https://...  # Required: RPC endpoint
ESCROW_CONTRACT_ADDRESS=0x...  # Required: Deployed escrow contract
USDT_CONTRACT_ADDRESS=0x...    # Required: USDT/USDC token contract
```

### Optional Variables

```env
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
HYPHA_DEFAULT_TOPIC=hypha-agents  # P2P network topic
```

### Security Best Practices

1. **Never commit `.env` to version control**
   ```bash
   # Ensure .gitignore includes:
   .env
   .env.local
   .env.production
   ```

2. **Use environment-specific files**
   ```bash
   .env.development  # Local development
   .env.staging      # Staging environment
   .env.production   # Production only
   ```

3. **Encrypt sensitive values**
   ```bash
   # Use tools like:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Encrypted .env files
   ```

4. **Rotate keys regularly**
   - Schedule key rotation every 90 days
   - Use different keys for dev/staging/prod

## Verification

### Health Check

```python
from hypha_sdk import Agent
from hypha_sdk.health import HealthCheck
import asyncio
import json

async def verify_deployment():
    agent = Agent()
    health = HealthCheck(agent)

    # Run all checks
    status = await health.check_all()

    # Print detailed status
    print(json.dumps(status, indent=2))

    # Verify each component
    assert status['overall'] == 'healthy', "System unhealthy!"
    assert status['web3']['connected'], "Web3 not connected!"
    assert status['account']['configured'], "Account not configured!"
    assert status['contracts']['status'] == 'healthy', "Contracts not ready!"

    print("✅ All systems operational")

asyncio.run(verify_deployment())
```

### Contract Verification

```bash
# Check contract is deployed
npx hardhat console --network baseSepolia

> const escrow = await ethers.getContractAt("HyphaEscrow", "0x...")
> await escrow.usdtToken()  # Should return USDT address
```

### Integration Test

Run complete workflow:

```bash
python examples/complete_workflow.py
```

## Troubleshooting

### Deployment Fails

**Issue**: `insufficient funds for gas`

**Solution**:
```bash
# Check balance
cast balance <YOUR_ADDRESS> --rpc-url https://sepolia.base.org

# Get more testnet ETH from faucet
```

**Issue**: `nonce too low`

**Solution**:
```bash
# Reset nonce in Hardhat config or wait for pending txs to clear
```

### Contract Not Working

**Issue**: `execution reverted`

**Solution**:
```bash
# Check contract has USDT approval
# Check escrow contract has correct USDT address
# Verify account has USDT balance
```

### Health Check Fails

**Issue**: `Web3: unhealthy`

**Solution**:
```python
# Test connection manually
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))
print(w3.is_connected())  # Should be True
```

**Issue**: `Contracts: unhealthy - No code at contract address`

**Solution**:
```bash
# Verify deployment succeeded
# Check you're on the correct network
# Verify contract address in .env matches deployment
```

### P2P Connection Issues

**Issue**: Messages not received

**Solution**:
```bash
# Check Node.js is installed
which node

# Test Hyperswarm directly
node src/messaging/receive_bridge.js test-topic

# Check firewall isn't blocking P2P
```

## Post-Deployment

### Security

1. **Contract Verification**: Verify source code on Basescan
2. **Access Control**: Limit who has access to private keys
3. **Monitoring**: Set up alerting for suspicious transactions
4. **Audits**: Regular security audits of smart contracts

### Monitoring

Monitor these metrics:
- Gas costs per transaction
- Transaction success rate
- Average confirmation time
- Contract balance changes
- Error rates in logs

### Backup

1. **Private Keys**: Store encrypted backups in multiple locations
2. **Contract Addresses**: Document all deployed contracts
3. **Configuration**: Version control all config files (except secrets)

### Support

- **GitHub Issues**: https://github.com/hypha-network/hypha-sdk/issues
- **Documentation**: https://github.com/hypha-network/hypha-sdk/tree/main/docs
- **Discord**: [Community Discord]

## Next Steps

1. Read [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation
2. Review [MESSAGING.md](MESSAGING.md) for P2P messaging details
3. Check [examples/](../examples/) for usage patterns
4. Set up monitoring and alerting
5. Plan for key rotation and security audits
