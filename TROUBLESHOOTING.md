# HYPHA Troubleshooting Guide

Quick solutions to common issues.

## Installation Issues

### ❌ "command not found: node"

**Problem**: Node.js not installed or not in PATH

**Solutions**:
```bash
# macOS (using Homebrew)
brew install node

# Or download from
# https://nodejs.org

# Verify
node --version
npm --version
```

### ❌ "command not found: python3"

**Problem**: Python not installed

**Solutions**:
```bash
# macOS (built-in, or via Homebrew)
brew install python3

# Verify
python3 --version
```

### ❌ "npm ERR! code EACCES"

**Problem**: Permission denied during npm install

**Solutions**:
```bash
# Option 1: Use sudo (not recommended)
sudo npm install

# Option 2: Fix npm permissions (recommended)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bash_profile
source ~/.bash_profile

# Then retry
npm install
```

### ❌ "pip: command not found"

**Problem**: pip not installed

**Solutions**:
```bash
# Install pip
python3 -m ensurepip --upgrade

# Or
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py

# Verify
pip --version
```

---

## Configuration Issues

### ❌ "No account configured"

**Problem**: PRIVATE_KEY not set in .env

**Solutions**:

1. **Check .env exists**:
```bash
ls -la .env
```

2. **If missing, create it**:
```bash
cp .env.example .env
```

3. **Add your private key**:
```bash
nano .env
# Add: PRIVATE_KEY=0xYourActualPrivateKey
```

4. **Verify it's set**:
```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('PRIVATE_KEY')
if key and key != 'your_private_key_here':
    print("✅ PRIVATE_KEY is set")
else:
    print("❌ PRIVATE_KEY not configured")
EOF
```

### ❌ "No escrow contract configured"

**Problem**: Contract not deployed or address not in .env

**Solutions**:

1. **Deploy contract first**:
```bash
npm run deploy:testnet
```

2. **Copy address from output**:
```
✅ HyphaEscrow deployed to: 0xABCDEF1234567890...
```

3. **Add to .env**:
```bash
echo "ESCROW_CONTRACT_ADDRESS=0xABCDEF1234567890..." >> .env
```

4. **Verify**:
```bash
grep ESCROW_CONTRACT_ADDRESS .env
```

### ❌ ".env file not found"

**Problem**: Missing environment configuration

**Solution**:
```bash
# Create from template
cp .env.example .env

# Edit with your settings
nano .env
```

---

## Blockchain Issues

### ❌ "Insufficient funds for gas"

**Problem**: Not enough ETH in wallet

**Solutions**:

1. **Check balance**:
```bash
python3 << 'EOF'
from hypha_sdk import Agent
agent = Agent()
print(f"Balance: {agent.check_balance()} ETH")
EOF
```

2. **Get testnet ETH**:
- Visit: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
- Enter your wallet address
- Receive 0.05 ETH

3. **Verify receipt**:
```bash
# Wait 30 seconds, then check again
sleep 30
python3 -c "from hypha_sdk import Agent; print(Agent().check_balance())"
```

### ❌ "Transaction reverted"

**Problem**: Smart contract call failed

**Common causes & solutions**:

1. **Not enough token allowance**:
```python
# Approve USDT spending first
# See DEPLOYMENT_GUIDE.md → "Approve USDT" section
```

2. **Invalid parameters**:
```python
# Check peer address is valid
peer = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"  # Must start with 0x
amount = 10.0  # Must be > 0
```

3. **Escrow already exists**:
```python
# Each combination of buyer+provider+amount+task creates unique ID
# Change task description to create new escrow
```

### ❌ "Network connection error"

**Problem**: Can't connect to Base Sepolia RPC

**Solutions**:

1. **Check RPC URL**:
```bash
grep WEB3_PROVIDER_URI .env
# Should be: https://sepolia.base.org
```

2. **Test connection**:
```python
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))
print(f"Connected: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")  # Should be 84532
```

3. **Try alternative RPC**:
```env
# In .env, try public RPC
WEB3_PROVIDER_URI=https://base-sepolia.g.alchemy.com/v2/demo
```

### ❌ "Nonce too low"

**Problem**: Transaction nonce mismatch

**Solution**:
```bash
# Usually auto-resolves. If persistent:
# 1. Wait 1 minute
# 2. Try transaction again
# 3. Or reset your wallet in MetaMask:
#    Settings → Advanced → Reset Account
```

---

## P2P Discovery Issues

### ❌ "Peer discovery failed"

**Problem**: Hyperswarm bridge not working

**Solutions**:

1. **Check Hyperswarm installed**:
```bash
ls node_modules/hyperswarm
# Should show hyperswarm directory
```

2. **Install if missing**:
```bash
npm install
```

3. **Test bridge directly**:
```bash
node src/discovery/bridge.js lookup test
# Should return JSON (may be empty array)
```

4. **Check Node.js version**:
```bash
node --version
# Should be v16 or higher
```

### ❌ "Command 'node' not found in subprocess"

**Problem**: Python can't find Node.js

**Solutions**:

1. **Add Node to PATH**:
```bash
# Find Node.js location
which node
# Example: /usr/local/bin/node

# Add to PATH
export PATH="/usr/local/bin:$PATH"

# Make permanent (add to ~/.bash_profile or ~/.zshrc)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
```

2. **Verify from Python**:
```python
import subprocess
result = subprocess.run(['which', 'node'], capture_output=True, text=True)
print(result.stdout)  # Should show path to node
```

### ❌ "Found 0 peers"

**Problem**: No peers discovered (expected for new network)

**This is normal!** Solutions:

1. **Run provider first**:
```bash
# Terminal 1
python3 hypha_connect.py --mode provider
# Keep running

# Terminal 2 (after 5 seconds)
python3 hypha_connect.py --mode buyer
```

2. **Increase timeout**:
```python
# In bridge.js, increase timeout from 3000 to 10000
setTimeout(() => {
    console.log(JSON.stringify(peers));
    swarm.leave(topicHash);
    swarm.destroy();
    process.exit(0);
}, 10000);  # Changed from 3000
```

---

## SDK Issues

### ❌ "ModuleNotFoundError: No module named 'web3'"

**Problem**: Python dependencies not installed

**Solution**:
```bash
pip install -r requirements.txt

# If using virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "ModuleNotFoundError: No module named 'hypha_sdk'"

**Problem**: Python can't find SDK

**Solutions**:

1. **Run from project root**:
```bash
cd hypha-project
python3 -c "from hypha_sdk import Agent"
```

2. **Or install as package**:
```bash
pip install -e .
```

3. **Or add to PYTHONPATH**:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### ❌ "ValueError: Invalid peer address"

**Problem**: Peer address format incorrect

**Solution**:
```python
# ❌ Wrong
peer = "agent_xyz123"

# ✅ Correct - must be Ethereum address
peer = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
```

---

## Contract Deployment Issues

### ❌ "HardhatError: HH700"

**Problem**: Hardhat configuration issue

**Solutions**:

1. **Check hardhat.config.js exists**:
```bash
ls hardhat.config.js
```

2. **Reinstall Hardhat**:
```bash
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
```

3. **Verify configuration**:
```bash
npx hardhat compile
```

### ❌ "Error: Cannot find module '@openzeppelin/contracts'"

**Problem**: OpenZeppelin not installed

**Solution**:
```bash
npm install @openzeppelin/contracts
```

### ❌ "Compilation failed"

**Problem**: Solidity compilation error

**Solutions**:

1. **Check Solidity version**:
```bash
# In hardhat.config.js, should have:
solidity: "0.8.20"
```

2. **Clean and recompile**:
```bash
npx hardhat clean
npx hardhat compile
```

3. **Check contract syntax**:
```bash
# View any errors
npx hardhat compile --verbose
```

---

## Testing Issues

### ❌ "./quick_test.sh: Permission denied"

**Problem**: Script not executable

**Solution**:
```bash
chmod +x quick_test.sh
./quick_test.sh
```

### ❌ "Test timeout"

**Problem**: P2P test taking too long (expected)

**This is normal for quick tests!** The timeout is intentional.

**To do proper test**:
```bash
# Terminal 1 - keep running
python3 hypha_connect.py --mode provider

# Terminal 2 - run after 5 seconds
python3 hypha_connect.py --mode buyer
```

---

## General Debugging

### Check System Status

Run this comprehensive check:

```bash
python3 << 'EOF'
import os
import sys
from dotenv import load_dotenv
from web3 import Web3

print("=== HYPHA System Check ===\n")

# Python version
print(f"Python: {sys.version}")

# Environment
load_dotenv()
has_key = bool(os.getenv('PRIVATE_KEY'))
has_contract = bool(os.getenv('ESCROW_CONTRACT_ADDRESS'))
print(f"PRIVATE_KEY set: {has_key}")
print(f"ESCROW_CONTRACT set: {has_contract}")

# Web3 connection
try:
    w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI', 'https://sepolia.base.org')))
    connected = w3.is_connected()
    print(f"Web3 connected: {connected}")
    if connected:
        print(f"Chain ID: {w3.eth.chain_id}")

        if has_key:
            account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
            balance = w3.eth.get_balance(account.address)
            print(f"Address: {account.address}")
            print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
except Exception as e:
    print(f"Web3 error: {e}")

print("\n=== Check Complete ===")
EOF
```

### Enable Debug Mode

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Then run your command
python3 examples/complete_workflow.py --mode provider
```

### View Transaction Details

```bash
# Get transaction hash from error/output, then:
python3 << 'EOF'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://sepolia.base.org'))

tx_hash = "0xYourTransactionHash"
tx = w3.eth.get_transaction(tx_hash)
receipt = w3.eth.get_transaction_receipt(tx_hash)

print("Transaction:", tx)
print("\nReceipt:", receipt)
print(f"\nStatus: {'Success' if receipt['status'] == 1 else 'Failed'}")
EOF
```

---

## Still Stuck?

1. **Re-read documentation**:
   - `DEPLOYMENT_GUIDE.md` - Step-by-step setup
   - `GETTING_STARTED.md` - SDK usage
   - `BUILD_SUMMARY.md` - Architecture details

2. **Check examples**:
   - `examples/complete_workflow.py`
   - `hypha_connect.py`

3. **Run full system check**:
```bash
./quick_test.sh
```

4. **Start fresh**:
```bash
# Clean install
rm -rf node_modules/
rm -rf venv/
npm install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Check file integrity**:
```bash
ls -la contracts/HyphaEscrow.sol
ls -la hypha_sdk/core.py
ls -la src/discovery/bridge.js
```

All files should exist with non-zero size.
