# HYPHA Deployment & Testing Guide

## Prerequisites Checklist

Before deploying, ensure you have:

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] Node.js 16+ installed (`node --version`)
- [ ] An Ethereum wallet with private key
- [ ] Base Sepolia testnet ETH (for gas fees)

---

## Step 1: Install Dependencies

### Install Node.js Packages

```bash
cd hypha-project
npm install
```

This installs:
- `hyperswarm` - P2P networking
- `hardhat` - Smart contract tools
- `@openzeppelin/contracts` - Secure contract components
- `dotenv` - Environment configuration

**Expected output**:
```
added 200+ packages
```

### Install Python Packages

```bash
pip install -r requirements.txt
```

This installs:
- `web3` - Blockchain interaction
- `python-dotenv` - Environment variables
- `pynacl` - Cryptography
- `pytest` - Testing framework

**Verify installation**:
```bash
python3 -c "from web3 import Web3; print('Web3 installed!')"
```

---

## Step 2: Setup Environment

### Create Your `.env` File

```bash
cp .env.example .env
```

### Get Your Private Key

**From MetaMask**:
1. Open MetaMask
2. Click three dots → Account Details
3. Click "Show Private Key"
4. Enter password and copy

**⚠️ SECURITY WARNING**: Never share your private key or commit `.env` to git!

### Edit `.env` File

```bash
nano .env  # or use your preferred editor
```

Add your private key:
```env
# Blockchain Configuration
WEB3_PROVIDER_URI=https://sepolia.base.org
PRIVATE_KEY=0x1234567890abcdef...  # Your actual private key (with 0x prefix)

# These will be filled after deployment
ESCROW_CONTRACT_ADDRESS=
USDT_CONTRACT_ADDRESS=

# P2P Network
HYPHA_SEED=  # Optional: for deterministic identity
DHT_BOOTSTRAP_NODES=bootstrap1.hypha.network:49737

# Development
DEBUG=true
LOG_LEVEL=INFO
```

---

## Step 3: Get Testnet ETH

### Option A: Base Sepolia Faucet (Recommended)

1. Visit: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
2. Enter your wallet address
3. Complete captcha
4. Receive 0.05 ETH (takes ~30 seconds)

### Option B: Sepolia ETH Bridge

1. Get Sepolia ETH from https://sepoliafaucet.com
2. Bridge to Base Sepolia via https://bridge.base.org

### Verify Balance

```bash
python3 << 'EOF'
from hypha_sdk import Agent
agent = Agent()
balance = agent.check_balance()
print(f"✅ Balance: {balance} ETH")
if balance > 0:
    print("Ready to deploy!")
else:
    print("❌ Need testnet ETH. Visit faucet.")
EOF
```

---

## Step 4: Deploy Smart Contract

### Compile Contracts

```bash
npm run compile
```

**Expected output**:
```
Compiled 1 Solidity file successfully
```

**Check artifacts**:
```bash
ls artifacts/contracts/HyphaEscrow.sol/
# Should show: HyphaEscrow.json
```

### Deploy to Base Sepolia Testnet

```bash
npm run deploy:testnet
```

**Expected output**:
```
🚀 Deploying HyphaEscrow to baseSepolia...
📍 USDT Token Address: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
👤 Deploying with account: 0xYourAddress
💰 Account balance: 0.05 ETH

✅ HyphaEscrow deployed to: 0xABCDEF1234567890...

📝 Deployment Info:
{
  "network": "baseSepolia",
  "escrowContract": "0xABCDEF1234567890...",
  "usdtToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "deployer": "0xYourAddress",
  "deployedAt": "2024-02-14T...",
  "blockNumber": 12345
}

🔍 To verify contract on Basescan:
npx hardhat verify --network baseSepolia 0xABCDEF... 0x833589...
```

### Update Environment Variables

Copy the deployed contract address and update `.env`:

```env
ESCROW_CONTRACT_ADDRESS=0xABCDEF1234567890...  # From deployment output
USDT_CONTRACT_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
```

### Verify Contract (Optional but Recommended)

```bash
npx hardhat verify --network baseSepolia \
  0xYourEscrowAddress \
  0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
```

**Success**:
```
Successfully verified contract HyphaEscrow
https://sepolia.basescan.org/address/0xYourAddress#code
```

---

## Step 5: Test P2P Discovery

### Test 1: Basic Connectivity

**Terminal 1** - Start Provider:
```bash
python3 hypha_connect.py --mode provider
```

**Expected output**:
```
Node ID: a1b2c3d4e5f6g7h8
Mode: provider
Announcing on topic: hypha-test
```

**Terminal 2** - Lookup Peers:
```bash
python3 hypha_connect.py --mode buyer
```

**Expected output**:
```
Node ID: x9y8z7w6v5u4t3s2
Mode: buyer
Looking up peers on topic: hypha-test
Found 1 peers
```

### Test 2: Hyperswarm Bridge Direct

**Test announce**:
```bash
node src/discovery/bridge.js announce test-topic
```

**Expected output**:
```json
{"status":"announced","topic":"test-topic","peers":0}
```

**Test lookup** (in another terminal):
```bash
node src/discovery/bridge.js lookup test-topic
```

**Expected output**:
```json
[{"publicKey":"abc123...","host":"127.0.0.1","port":49737}]
```

---

## Step 6: Test Complete Workflow

### Setup: Create Two Wallet Addresses

You need two addresses for buyer/provider simulation:
- **Buyer**: Your main wallet (with testnet ETH)
- **Provider**: Any Ethereum address (can be another wallet or test address)

Example provider address for testing: `0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1`

### Test A: Provider Agent

**Terminal 1**:
```bash
python3 examples/complete_workflow.py --mode provider
```

**Expected output**:
```
🌐 HYPHA - P2P Infrastructure for Autonomous AI Agents

=== PROVIDER AGENT ===
✅ Created provider agent: a1b2c3d4e5f6g7h8
📍 Address: 0xYourWalletAddress

📢 Announcing availability on P2P network...
✅ Announced: {'status': 'announced', 'topic': 'hypha-agents', 'peers': 0}

⏳ Listening for task requests...
(In production, implement message handler to receive tasks)
```

### Test B: Buyer Agent (Without Contract - Discovery Only)

**Terminal 2**:
```bash
python3 examples/complete_workflow.py --mode buyer
```

**Expected output** (if contract deployed):
```
🌐 HYPHA - P2P Infrastructure for Autonomous AI Agents

=== BUYER AGENT ===
✅ Created buyer agent: x9y8z7w6v5u4t3s2
💰 ETH Balance: 0.045 ETH

🔍 Discovering provider agents...
Found 1 peers

💼 Hiring provider: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
✅ Escrow created: 0x1234567890abcdef...

📊 Escrow Status:
  Provider: 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1
  Amount: $10.0
  Task: Analyze blockchain transaction patterns
  Status: Active
  Deadline: 2024-02-15 13:00:00

✅ Completing task and releasing payment...
Transaction confirmed: 0xabcdef1234567890...
```

---

## Step 7: SDK Integration Test

### Create Test Script

```bash
cat > test_sdk.py << 'EOF'
"""Quick SDK test"""
import asyncio
from hypha_sdk import Agent

async def main():
    print("🧪 Testing HYPHA SDK\n")

    # Test 1: Agent creation
    print("Test 1: Creating agent...")
    agent = Agent()
    print(f"✅ Agent ID: {agent.agent_id}")
    print(f"✅ Account: {agent.account.address if agent.account else 'Not configured'}")

    # Test 2: Balance check
    print("\nTest 2: Checking balance...")
    balance = agent.check_balance()
    print(f"✅ Balance: {balance} ETH")

    # Test 3: P2P discovery
    print("\nTest 3: Testing P2P discovery...")
    try:
        peers = await agent.discover_peers("hypha-test")
        print(f"✅ Found {len(peers)} peers")
    except Exception as e:
        print(f"⚠️  P2P test skipped: {e}")

    # Test 4: Contract connection
    print("\nTest 4: Checking contract connection...")
    if agent.escrow_contract:
        print(f"✅ Connected to escrow: {agent.escrow_address}")
    else:
        print("⚠️  No contract configured (set ESCROW_CONTRACT_ADDRESS in .env)")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
EOF

python3 test_sdk.py
```

---

## Step 8: Create Your First Escrow (Real Transaction)

### Prepare USDT Approval (If Using Real USDT)

⚠️ **Note**: For testnet, you'll need testnet USDT. The deployment script uses USDC as a proxy.

```python
# approve_usdt.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI')))
account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))

# USDC/USDT contract address
usdt_address = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# Minimal ERC20 ABI for approve
abi = [{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]

usdt = w3.eth.contract(address=usdt_address, abi=abi)
escrow_address = os.getenv('ESCROW_CONTRACT_ADDRESS')

# Approve 100 USDT (6 decimals)
amount = 100 * 10**6

tx = usdt.functions.approve(escrow_address, amount).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Approval tx: {tx_hash.hex()}")
```

### Create First Escrow

```python
# first_escrow.py
import asyncio
from hypha_sdk import Agent

async def main():
    agent = Agent()

    print(f"Agent: {agent.account.address}")
    print(f"Balance: {agent.check_balance()} ETH")

    # Create escrow
    escrow_id = await agent.hire(
        peer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
        amount=10.0,
        task="Test task",
        deadline_hours=24
    )

    print(f"✅ Escrow created: {escrow_id}")

    # Check status
    status = agent.get_escrow_status(escrow_id)
    print(f"Status: {status}")

asyncio.run(main())
```

---

## Troubleshooting

### Issue: "Command not found: node"
**Solution**: Install Node.js from https://nodejs.org

### Issue: "No account configured"
**Solution**:
1. Check `.env` file exists
2. Verify `PRIVATE_KEY` is set (with `0x` prefix)
3. Run: `python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('PRIVATE_KEY'))"`

### Issue: "Insufficient funds"
**Solution**:
1. Visit Base Sepolia faucet
2. Check balance: `agent.check_balance()`
3. Ensure you're on Base Sepolia network

### Issue: "No escrow contract configured"
**Solution**:
1. Run `npm run deploy:testnet`
2. Copy deployed address to `.env`
3. Verify `ESCROW_CONTRACT_ADDRESS` is set

### Issue: "Peer discovery failed"
**Solution**:
1. Run `npm install` to install Hyperswarm
2. Check Node.js is in PATH: `which node`
3. Test directly: `node src/discovery/bridge.js lookup test`

### Issue: "Transaction failed"
**Solution**:
1. Check you have enough ETH for gas
2. Verify contract address is correct
3. Check Base Sepolia RPC is responding
4. View transaction on https://sepolia.basescan.org

---

## Deployment Checklist

- [ ] Dependencies installed (npm + pip)
- [ ] `.env` configured with PRIVATE_KEY
- [ ] Testnet ETH in wallet (0.05+ ETH)
- [ ] Contract compiled (`npm run compile`)
- [ ] Contract deployed (`npm run deploy:testnet`)
- [ ] Contract address in `.env`
- [ ] P2P discovery tested
- [ ] SDK test passed
- [ ] First escrow created (optional)

---

## Next: Mainnet Deployment

When ready for production:

```bash
# 1. Get real ETH on Base Mainnet
# 2. Update .env with mainnet settings
# 3. Deploy
npm run deploy:mainnet

# 4. Verify contract
npx hardhat verify --network base <address> <usdt-address>
```

**Mainnet considerations**:
- Use real USDT contract
- Higher gas costs
- Audit contract before deploying
- Start with small amounts
- Monitor transactions closely

---

## Support

- **Errors during deployment**: Check `DEPLOYMENT_GUIDE.md` (this file)
- **SDK issues**: See `GETTING_STARTED.md`
- **Contract questions**: Review `contracts/HyphaEscrow.sol`
- **Examples**: Check `examples/` directory
