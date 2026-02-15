# Quick Deploy Commands

Copy-paste these commands in order to deploy and test HYPHA.

## 1️⃣ Installation (5 minutes)

```bash
# Navigate to project
cd hypha-project

# Install dependencies
npm install
pip install -r requirements.txt

# Run quick test
./quick_test.sh
```

---

## 2️⃣ Configuration (2 minutes)

```bash
# Create environment file
cp .env.example .env

# Edit with your private key
nano .env
# Or: code .env (if using VS Code)
# Or: open .env (opens default editor)
```

**Add this to `.env`**:
```env
PRIVATE_KEY=0xYourPrivateKeyHere
WEB3_PROVIDER_URI=https://sepolia.base.org
```

---

## 3️⃣ Get Testnet ETH (3 minutes)

1. **Get your wallet address**:
```bash
python3 << 'EOF'
from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv()
w3 = Web3()
account = w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
print(f"Your address: {account.address}")
EOF
```

2. **Visit faucet**:
   - Go to: https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
   - Paste your address
   - Get 0.05 ETH

3. **Verify balance**:
```bash
python3 << 'EOF'
from hypha_sdk import Agent
agent = Agent()
print(f"Balance: {agent.check_balance()} ETH")
EOF
```

---

## 4️⃣ Deploy Smart Contract (2 minutes)

```bash
# Compile contract
npm run compile

# Deploy to testnet
npm run deploy:testnet
```

**Copy the deployed contract address from output**, then:

```bash
# Add to .env (replace 0xYOUR_CONTRACT with actual address)
echo "ESCROW_CONTRACT_ADDRESS=0xYOUR_CONTRACT_ADDRESS" >> .env
echo "USDT_CONTRACT_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" >> .env
```

---

## 5️⃣ Test P2P Discovery (1 minute)

**Terminal 1**:
```bash
python3 hypha_connect.py --mode provider
```

**Terminal 2** (new terminal):
```bash
cd hypha-project
python3 hypha_connect.py --mode buyer
```

---

## 6️⃣ Test Complete Workflow (2 minutes)

**Terminal 1**:
```bash
python3 examples/complete_workflow.py --mode provider
```

**Terminal 2**:
```bash
python3 examples/complete_workflow.py --mode buyer
```

---

## 7️⃣ Verify Everything Works

```bash
python3 << 'EOF'
import asyncio
from hypha_sdk import Agent

async def test():
    agent = Agent()
    print("✅ Agent created:", agent.agent_id)
    print("✅ Account:", agent.account.address if agent.account else "Not configured")
    print("✅ Balance:", agent.check_balance(), "ETH")
    print("✅ Contract:", agent.escrow_address or "Not configured")

    # Test P2P
    try:
        peers = await agent.discover_peers("test")
        print(f"✅ P2P works - found {len(peers)} peers")
    except Exception as e:
        print(f"⚠️  P2P: {e}")

    print("\n🎉 HYPHA is ready!")

asyncio.run(test())
EOF
```

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `npm install` | Install Node.js packages |
| `pip install -r requirements.txt` | Install Python packages |
| `npm run compile` | Compile smart contracts |
| `npm run deploy:testnet` | Deploy to Base Sepolia |
| `npm run deploy:mainnet` | Deploy to Base Mainnet |
| `./quick_test.sh` | Run test suite |
| `python3 hypha_connect.py --mode provider` | Test P2P as provider |
| `python3 hypha_connect.py --mode buyer` | Test P2P as buyer |

---

## 🆘 Common Issues

### "Command not found: npm"
```bash
# Install Node.js from https://nodejs.org
# Or use package manager:
brew install node  # macOS
```

### "No account configured"
```bash
# Check .env file
cat .env | grep PRIVATE_KEY

# Make sure it starts with 0x
# Example: PRIVATE_KEY=0x1234567890abcdef...
```

### "Insufficient funds"
```bash
# Check balance
python3 -c "from hypha_sdk import Agent; print(Agent().check_balance())"

# Get more from faucet
# https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet
```

### "Module not found"
```bash
# Reinstall Python packages
pip install -r requirements.txt --force-reinstall

# Check Python path
which python3
python3 --version
```

---

## 🚀 All-in-One Deploy Script

Save this as `deploy_all.sh` and run:

```bash
#!/bin/bash
set -e

echo "🚀 HYPHA Deployment Starting..."

# Install
echo "📦 Installing dependencies..."
npm install
pip install -r requirements.txt

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  Creating .env from template..."
    cp .env.example .env
    echo "❌ Please edit .env and add your PRIVATE_KEY, then run this script again"
    exit 1
fi

# Check private key
if grep -q "your_private_key_here" .env; then
    echo "❌ Please set PRIVATE_KEY in .env file"
    exit 1
fi

# Compile
echo "🔨 Compiling contracts..."
npm run compile

# Deploy
echo "🚀 Deploying to Base Sepolia..."
npm run deploy:testnet

echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Add ESCROW_CONTRACT_ADDRESS to .env"
echo "2. Run: python3 examples/complete_workflow.py --mode provider"
```

---

## 📊 Expected Timeline

- ✅ Install dependencies: 5 min
- ✅ Configure .env: 2 min
- ✅ Get testnet ETH: 3 min
- ✅ Deploy contract: 2 min
- ✅ Test P2P: 1 min
- ✅ Full workflow test: 2 min

**Total: ~15 minutes** from zero to working system! 🎉
